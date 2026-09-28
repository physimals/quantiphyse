"""
Quantiphyse - 3D volume rendering view

Copyright (c) 2013-2020 University of Oxford

Licensed under the Apache License, Version 2.0 (the "License");
you may not use this file except in compliance with the License.
You may obtain a copy of the License at

    http://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and
limitations under the License.
"""

from __future__ import division, unicode_literals, absolute_import

from PySide2 import QtCore, QtWidgets

import numpy as np
import scipy.ndimage

from quantiphyse.utils import LogSource
from quantiphyse.utils.enums import Visibility, Boundary
from quantiphyse.data.qpdata import DataGrid
from quantiphyse.gui.colors import get_lut

from .slice_viewer import MAX_NUM_DATA_SETS

# Largest number of voxels composited for rendering. Larger grids are
# downsampled by an integer stride to keep memory use and update time modest
MAX_RENDER_VOXELS = 8000000

# Delay before recompositing, so bursts of view changes (e.g. dragging a
# colour map range) only trigger one update
UPDATE_DELAY_MS = 200

DEFAULT_OPACITY_PERCENT = 20

# Slicing modes, cycled through by the slicing button
SLICE_OFF, SLICE_PLANES, SLICE_PLANES_VOLUME, SLICE_CUT = range(4)
SLICE_MODE_NAMES = ["Off", "Slice planes", "Planes + volume", "Cut away"]

# Composited RGBA data used by the 3D view, and which data sets each includes
COMPOSITE_LAYERS = {"background" : "background", "overlays" : "overlays", "slices" : "all"}

def render_grid(grid, max_voxels=MAX_RENDER_VOXELS):
    """
    Get the grid used for rendering: the viewer grid, downsampled by an
    integer stride if it has more than ``max_voxels`` voxels
    """
    shape = np.array(grid.shape)
    stride = 1
    while np.prod(np.ceil(shape / stride)) > max_voxels:
        stride += 1
    if stride == 1:
        return grid
    affine = np.dot(grid.affine, np.diag([stride, stride, stride, 1]))
    return DataGrid([int(n) for n in np.ceil(shape / stride)], affine)

def _view_lut(view):
    if view.cmap == "custom" and view.lut is not None:
        lut = view.lut
    else:
        lut = get_lut(view.cmap)
    return np.asarray(lut)[:, :3].astype(np.float32) / 255

def _layer_rgba(values, view, mask=None, roi=False, slice_style=False):
    """
    Colour and opacity for one data set, using the same colour map and range
    as the ortho slice views

    For volume rendering, opacity ramps from zero at the bottom of the colour
    map range to the view's alpha at the top, so that low values do not hide
    the rest of the volume. With ``slice_style``, opacity is the view's alpha
    throughout, as in the ortho views. ROIs use the view's alpha for every
    non-zero voxel.

    :return: Tuple of RGB array (..., 3) and opacity array (...) in range 0-1
    """
    lut = _view_lut(view)
    cmin, cmax = view.cmap_range
    finite = np.isfinite(values)
    values = np.where(finite, values, cmin).astype(np.float32)
    if cmax > cmin:
        pos = (values - cmin) / (cmax - cmin)
    else:
        pos = (values >= cmax).astype(np.float32)

    in_range = np.clip(pos, 0, 1)
    rgb = lut[(in_range * (len(lut) - 1)).astype(int)]
    alpha = (view.alpha if view.alpha is not None else 255) / 255
    if roi:
        opacity = np.where(values != 0, alpha, 0).astype(np.float32)
    elif slice_style:
        opacity = np.full(values.shape, alpha, dtype=np.float32)
    else:
        opacity = in_range * alpha

    if view.boundary in (Boundary.TRANS, Boundary.UPPERTRANS):
        opacity[pos > 1] = 0
    if view.boundary in (Boundary.TRANS, Boundary.LOWERTRANS):
        opacity[pos < 0] = 0
    if mask is not None:
        opacity[~mask] = 0
    opacity[~finite] = 0
    return rgb, opacity

def visible_layers(ivm, ivl):
    """
    Data sets displayed in the ortho slice views, in drawing order (bottom first)

    :return: Sequence of (QpData, view metadata) tuples
    """
    layers = []
    if ivm.main is not None and ivl.opts.main_data == Visibility.SHOW and \
       ivl.main_view_md.visible == Visibility.SHOW:
        layers.append((ivl.main_view_md.z_order or 0, ivm.main, ivl.main_view_md))

    for qpdata in ivm.data.values():
        view = qpdata.view
        if view.visible != Visibility.SHOW or view.cmap_range is None:
            continue
        if qpdata.roi and not (view.shade or view.contour):
            continue
        z_order = view.z_order or 0
        if qpdata.roi:
            # ROIs are always drawn on top of data, as in the ortho slice views
            z_order += MAX_NUM_DATA_SETS
        layers.append((z_order, qpdata, view))

    # Stable sort so that main data stays below other data with the same z order
    layers.sort(key=lambda layer: layer[0])
    return [(qpdata, view) for _, qpdata, view in layers]

def composite_rgba(ivm, ivl, grid, vol, slice_style=False, which="all"):
    """
    Composite visible data sets onto a single RGBA volume

    :param grid: DataGrid to render on
    :param vol: Volume index for 4D data, as in the ortho views
    :param slice_style: If True, use the opacity of the ortho slice views
                        rather than the volume rendering opacity ramp
    :param which: "all" for every visible data set, "background" for the
                  main data background only, "overlays" for everything else
    :return: uint8 array of shape grid.shape + (4,), or None if nothing is visible
    """
    layers = visible_layers(ivm, ivl)
    if which == "background":
        layers = [(qpdata, view) for qpdata, view in layers if view is ivl.main_view_md]
    elif which == "overlays":
        layers = [(qpdata, view) for qpdata, view in layers if view is not ivl.main_view_md]
    if not layers:
        return None

    shape = tuple(grid.shape)
    acc_rgb = np.zeros(shape + (3,), dtype=np.float32)
    acc_alpha = np.zeros(shape, dtype=np.float32)
    for qpdata, view in layers:
        values = qpdata.volume(vol, qpdata=True).resample(grid, order=0).raw()
        mask = None
        if view.roi and view.roi in ivm.data:
            mask = ivm.data[view.roi].resample(grid, order=0).raw() > 0
            if mask.ndim == 4:
                mask = mask[..., 0]
        rgb, opacity = _layer_rgba(values, view, mask, roi=qpdata.roi, slice_style=slice_style)

        # Standard 'over' compositing, with colours premultiplied by opacity
        acc_rgb *= (1 - opacity)[..., np.newaxis]
        acc_rgb += rgb * opacity[..., np.newaxis]
        acc_alpha *= (1 - opacity)
        acc_alpha += opacity

    # VTK expects colours which are not premultiplied
    with np.errstate(invalid="ignore", divide="ignore"):
        rgb = np.where(acc_alpha[..., np.newaxis] > 0, acc_rgb / acc_alpha[..., np.newaxis], 0)

        # Give transparent voxels the mean colour of their visible neighbours. They
        # stay invisible, but otherwise interpolation between voxels blends
        # the edges of visible regions towards black
        transparent = acc_alpha == 0
        if np.any(transparent):
            weight = scipy.ndimage.uniform_filter(acc_alpha, 3)
            for channel in range(3):
                neighbours = scipy.ndimage.uniform_filter(acc_rgb[..., channel], 3) / weight
                rgb[..., channel][transparent] = np.nan_to_num(neighbours[transparent])
    rgba = np.concatenate([rgb, acc_alpha[..., np.newaxis]], axis=-1)
    return (np.clip(rgba, 0, 1) * 255).astype(np.uint8)

class _RgbaVolume(object):
    """
    A VTK volume showing RGBA data, where the 4th component is mapped to
    opacity by a linear scalar opacity function
    """

    def __init__(self, vtk_classes, renderer):
        self._vtk = vtk_classes
        self.opacity_fn = self._vtk.vtkPiecewiseFunction()
        self._property = self._vtk.vtkVolumeProperty()
        self._property.IndependentComponentsOff()
        self._property.SetScalarOpacity(self.opacity_fn)
        self._property.SetInterpolationTypeToLinear()
        self._property.ShadeOff()

        self.mapper = self._vtk.vtkSmartVolumeMapper()
        self.volume = self._vtk.vtkVolume()
        self.volume.SetMapper(self.mapper)
        self.volume.SetProperty(self._property)
        self.volume.VisibilityOff()
        self.shape = None
        renderer.AddVolume(self.volume)

    def set_max_opacity(self, max_opacity):
        """ Set the opacity per voxel of fully opaque data """
        self.opacity_fn.RemoveAllPoints()
        self.opacity_fn.AddPoint(0, 0)
        self.opacity_fn.AddPoint(255, max_opacity)

    def set_data(self, image, matrix, grid):
        """ Set the RGBA image to show, or None to show nothing """
        self.shape = None
        if image is not None:
            self.mapper.SetInputData(image)
            self.volume.SetUserMatrix(matrix)
            self._property.SetScalarOpacityUnitDistance(float(min(grid.spacing)))
            self.shape = image.GetDimensions()

class VtkVolumeView(object):
    """
    VTK render window showing RGBA volumes with standard rotate/zoom interaction,
    optionally sliced at a focus point

    The main data background and the overlays are separate volumes, with the
    overlays drawn in a second renderer layer so that they always appear on top
    of the background, as in the ortho views.

    All VTK imports are done here so that VTK is only required if the 3D view
    is actually used
    """

    def __init__(self, parent):
        import types
        import vtkmodules.qt
        # Quantiphyse uses PySide2 - don't let VTK pick another Qt binding
        # which happens to be installed
        vtkmodules.qt.PyQtImpl = "PySide2"
        from vtkmodules.qt.QVTKRenderWindowInteractor import QVTKRenderWindowInteractor
        # Imported for their side effect of registering the OpenGL implementations
        import vtkmodules.vtkRenderingOpenGL2 # pylint: disable=unused-import
        import vtkmodules.vtkRenderingVolumeOpenGL2 # pylint: disable=unused-import
        from vtkmodules.vtkCommonMath import vtkMatrix4x4
        from vtkmodules.vtkCommonDataModel import vtkImageData, vtkPiecewiseFunction
        from vtkmodules.vtkInteractionStyle import vtkInteractorStyleTrackballCamera
        from vtkmodules.vtkInteractionWidgets import vtkOrientationMarkerWidget
        from vtkmodules.vtkRenderingAnnotation import vtkAnnotatedCubeActor
        from vtkmodules.vtkRenderingCore import vtkRenderer, vtkVolume, vtkVolumeProperty, vtkImageActor
        from vtkmodules.vtkRenderingVolumeOpenGL2 import vtkSmartVolumeMapper
        from vtkmodules.util.numpy_support import numpy_to_vtk

        vtk_classes = types.SimpleNamespace(vtkPiecewiseFunction=vtkPiecewiseFunction,
                                            vtkVolumeProperty=vtkVolumeProperty,
                                            vtkSmartVolumeMapper=vtkSmartVolumeMapper,
                                            vtkVolume=vtkVolume)
        self._vtkImageData = vtkImageData
        self._vtkMatrix4x4 = vtkMatrix4x4
        self._numpy_to_vtk = numpy_to_vtk

        self._mode = SLICE_OFF
        self._focus = None
        self._grid = None
        self._slice_shape = None

        self.widget = QVTKRenderWindowInteractor(parent)
        self._render_window = self.widget.GetRenderWindow()
        self._render_window.AlphaBitPlanesOff()
        # Layer 0: background volume and slice planes. Layer 1: overlays.
        # The orientation marker adds its own layer on top
        self._render_window.SetNumberOfLayers(2)

        self._renderer = vtkRenderer()
        self._renderer.SetBackground(0, 0, 0)
        # VTK defaults to a transparent background and an alpha channel in the
        # framebuffer, which lets a compositing window manager show whatever is
        # behind the window through the view
        self._renderer.SetBackgroundAlpha(1.0)
        self._render_window.AddRenderer(self._renderer)

        self._overlay_renderer = vtkRenderer()
        self._overlay_renderer.SetLayer(1)
        self._overlay_renderer.InteractiveOff()
        self._overlay_renderer.SetActiveCamera(self._renderer.GetActiveCamera())
        self._render_window.AddRenderer(self._overlay_renderer)

        interactor = self._render_window.GetInteractor()
        interactor.SetInteractorStyle(vtkInteractorStyleTrackballCamera())

        self._background = _RgbaVolume(vtk_classes, self._renderer)
        # Overlay opacity comes directly from the data alpha, so an overlay
        # with 100% alpha is opaque
        self._overlays = _RgbaVolume(vtk_classes, self._overlay_renderer)
        self._overlays.set_max_opacity(1.0)
        self._volumes = [self._background, self._overlays]

        # One image actor per orthogonal slice plane. They share a single RGBA
        # image and only differ in which slice of it they display
        self._slice_actors = []
        for _axis in range(3):
            actor = vtkImageActor()
            actor.InterpolateOff()
            actor.VisibilityOff()
            self._renderer.AddActor(actor)
            self._slice_actors.append(actor)

        # The octant cut away in 'cut' mode is the one facing the camera,
        # so it needs updating as the view is rotated
        self._renderer.GetActiveCamera().AddObserver("ModifiedEvent", self._camera_moved)

        # RAS orientation cube in the corner of the view
        cube = vtkAnnotatedCubeActor()
        for face, text in (("XPlus", "R"), ("XMinus", "L"), ("YPlus", "A"),
                           ("YMinus", "P"), ("ZPlus", "S"), ("ZMinus", "I")):
            getattr(cube, "Set%sFaceText" % face)(text)
        cube.GetCubeProperty().SetColor(0.3, 0.3, 0.3)
        self._orientation_marker = vtkOrientationMarkerWidget()
        self._orientation_marker.SetOrientationMarker(cube)
        self._orientation_marker.SetInteractor(interactor)
        self._orientation_marker.SetViewport(0.0, 0.0, 0.2, 0.2)
        self._orientation_marker.EnabledOn()
        self._orientation_marker.InteractiveOff()

        self.set_opacity(DEFAULT_OPACITY_PERCENT / 100)
        self.widget.Initialize()

    def set_opacity(self, max_opacity):
        """ Set the opacity per voxel of the fully opaque background """
        self._background.set_max_opacity(max_opacity)
        self.render()

    def _image(self, rgba):
        if rgba is None:
            return None
        image = self._vtkImageData()
        image.SetDimensions(*rgba.shape[:3])
        # VTK point data is ordered with x varying fastest
        flat = np.ascontiguousarray(np.transpose(rgba, (2, 1, 0, 3)).reshape(-1, 4))
        image.GetPointData().SetScalars(self._numpy_to_vtk(flat, deep=True))
        return image

    def _matrix(self, grid):
        # Images are in voxel co-ordinates, the grid affine maps them to world space
        matrix = self._vtkMatrix4x4()
        for row in range(4):
            for col in range(4):
                matrix.SetElement(row, col, float(grid.affine[row, col]))
        return matrix

    def set_data(self, grid, background=None, overlays=None, slices=None):
        """
        Set the data to display. Each data item is a uint8 array of shape
        grid.shape + (4,), or None

        :param grid: DataGrid giving the voxel to world transformation
        :param background: RGBA data for volume rendering of the main data background
        :param overlays: RGBA data for volume rendering of overlays and ROIs
        :param slices: RGBA data for the slice planes
        """
        self._grid = grid
        matrix = self._matrix(grid) if grid is not None else None
        self._background.set_data(self._image(background), matrix, grid)
        self._overlays.set_data(self._image(overlays), matrix, grid)

        self._slice_shape = None
        if slices is not None:
            image = self._image(slices)
            for actor in self._slice_actors:
                actor.GetMapper().SetInputData(image)
                actor.SetUserMatrix(matrix)
            self._slice_shape = slices.shape[:3]

        self._update_slicing()

    def set_mode(self, mode):
        """ Set the slicing mode, one of the SLICE_* constants """
        self._mode = mode
        self._update_slicing()

    def set_focus(self, focus):
        """ Set the slicing point, in voxel co-ordinates of the grid passed to set_data """
        self._focus = focus
        self._update_slicing()

    def _focus_index(self, shape):
        if self._focus is None:
            return [int(n / 2) for n in shape]
        return [int(min(max(round(pos), 0), n - 1)) for pos, n in zip(self._focus, shape)]

    def _update_slicing(self):
        show_volumes = self._mode != SLICE_PLANES
        for volume in self._volumes:
            volume.volume.SetVisibility(show_volumes and volume.shape is not None)
            volume.mapper.SetCropping(show_volumes and self._mode == SLICE_CUT)

        show_slices = self._slice_shape is not None and self._mode in (SLICE_PLANES, SLICE_PLANES_VOLUME)
        if show_slices:
            focus = self._focus_index(self._slice_shape)
            for axis, actor in enumerate(self._slice_actors):
                extent = []
                for dim, size in enumerate(self._slice_shape):
                    if dim == axis:
                        extent += [focus[dim], focus[dim]]
                    else:
                        extent += [0, size - 1]
                actor.SetDisplayExtent(*extent)
        for actor in self._slice_actors:
            actor.SetVisibility(show_slices)

        self._update_cut()
        self.render()

    def _camera_moved(self, _caller, _event):
        # Called during rendering so must not trigger another render
        self._update_cut()

    def _update_cut(self):
        """
        Crop away the octant of the volumes which is on the camera side of
        the focus point in all three dimensions
        """
        if self._grid is None or self._mode != SLICE_CUT:
            return

        shape = self._grid.shape
        focus = self._focus_index(shape)
        camera = np.append(self._renderer.GetActiveCamera().GetPosition(), 1)
        camera = np.dot(np.linalg.inv(self._grid.affine), camera)[:3]

        # Cropping planes are in voxel co-ordinates and define 3x3x3 regions.
        # For each axis make the middle region span from the focus point to
        # the edge of the volume nearest the camera, then remove the central
        # region (index 13) which is the octant facing the camera
        planes = []
        for dim, size in enumerate(shape):
            if camera[dim] > focus[dim]:
                planes += [focus[dim], size]
            else:
                planes += [-1, focus[dim]]
        for volume in self._volumes:
            volume.mapper.SetCroppingRegionPlanes(*[float(p) for p in planes])
            volume.mapper.SetCroppingRegionFlags(0x7ffffff & ~(1 << 13))

    def reset_camera(self):
        """ View from the front (anterior) with superior upwards """
        camera = self._renderer.GetActiveCamera()
        camera.SetFocalPoint(0, 0, 0)
        camera.SetPosition(0, 1, 0)
        camera.SetViewUp(0, 0, 1)
        if self._grid is not None:
            # Fit the whole grid, as the background may be hidden with only overlays visible
            corners = np.array([[i, j, k, 1] for i in (0, self._grid.shape[0] - 1)
                                for j in (0, self._grid.shape[1] - 1)
                                for k in (0, self._grid.shape[2] - 1)], dtype=float)
            world = np.dot(self._grid.affine, corners.T)[:3]
            bounds = [val for axis in world for val in (axis.min(), axis.max())]
            self._renderer.ResetCamera(*bounds)
        else:
            self._renderer.ResetCamera()
        self.render()

    def render(self):
        """ Redraw the view """
        self._render_window.Render()

    def finalize(self):
        """ Release the render window. Required before exit to avoid crashes on some platforms """
        self.widget.Finalize()

class VolumeViewer(QtWidgets.QWidget, LogSource):
    """
    3D volume rendering of the data shown in the ortho slice views

    Initially shows only a button to enable the 3D view, so that VTK is not
    imported or initialized unless it is wanted. The view can optionally be
    sliced at the crosshair position of the ortho views, otherwise it only
    depends on the volume index of 4D data.
    """

    def __init__(self, ivl, ivm):
        LogSource.__init__(self)
        QtWidgets.QWidget.__init__(self)
        self._ivl = ivl
        self._ivm = ivm
        self._view = None
        self._vol = 0
        self._grid = None
        self._slice_mode = SLICE_OFF
        self._cache = {}
        self._watched_views = {}
        self._dirty = False
        self._reset_camera = True

        self._update_timer = QtCore.QTimer(self)
        self._update_timer.setSingleShot(True)
        self._update_timer.setInterval(UPDATE_DELAY_MS)
        self._update_timer.timeout.connect(self._update)

        self._stack = QtWidgets.QStackedLayout()
        self.setLayout(self._stack)

        placeholder = QtWidgets.QWidget()
        vbox = QtWidgets.QVBoxLayout()
        placeholder.setLayout(vbox)
        vbox.addStretch(1)
        self._enable_btn = QtWidgets.QPushButton("Enable 3D view")
        self._enable_btn.clicked.connect(self._enable)
        vbox.addWidget(self._enable_btn, 0, QtCore.Qt.AlignCenter)
        self._message = QtWidgets.QLabel()
        self._message.setWordWrap(True)
        self._message.setAlignment(QtCore.Qt.AlignCenter)
        self._message.setVisible(False)
        vbox.addWidget(self._message)
        vbox.addStretch(1)
        self._stack.addWidget(placeholder)

    @property
    def enabled(self):
        """ True if the 3D view has been enabled """
        return self._view is not None

    @property
    def slice_mode(self):
        """ Current slicing mode, one of the SLICE_* constants """
        return self._slice_mode

    def _enable(self):
        if self.enabled:
            return

        try:
            self._view = VtkVolumeView(self)
        except ImportError as exc:
            self.warn("Could not import VTK: %s", exc)
            self._show_message("The 3D view requires VTK - install it using: pip install vtk\n(%s)" % exc)
            return
        except Exception as exc: # pylint: disable=broad-except
            self.warn("Could not initialize 3D view: %s", exc)
            self._show_message("Could not initialize 3D view: %s" % exc)
            return

        page = QtWidgets.QWidget()
        vbox = QtWidgets.QVBoxLayout()
        vbox.setContentsMargins(0, 0, 0, 0)
        vbox.setSpacing(2)
        page.setLayout(vbox)
        vbox.addWidget(self._view.widget, 1)

        hbox = QtWidgets.QHBoxLayout()
        self._slice_btn = QtWidgets.QPushButton()
        self._slice_btn.setToolTip("Click to cycle through slicing modes. Slicing follows the crosshairs")
        self._slice_btn.clicked.connect(self._next_slice_mode)
        hbox.addWidget(self._slice_btn)
        self._opacity_label = QtWidgets.QLabel("Background opacity")
        hbox.addWidget(self._opacity_label)
        self._opacity_slider = QtWidgets.QSlider(QtCore.Qt.Horizontal)
        self._opacity_slider.setRange(1, 100)
        self._opacity_slider.setValue(DEFAULT_OPACITY_PERCENT)
        self._opacity_slider.valueChanged.connect(self._opacity_changed)
        hbox.addWidget(self._opacity_slider, 1)
        reset_btn = QtWidgets.QPushButton("Reset view")
        reset_btn.clicked.connect(self._view.reset_camera)
        hbox.addWidget(reset_btn)
        vbox.addLayout(hbox)
        self._update_slice_btn()

        self._stack.addWidget(page)
        self._stack.setCurrentWidget(page)

        self._ivm.sig_main_data.connect(self._main_data_changed)
        self._ivm.sig_all_data.connect(self._all_data_changed)
        self._ivl.sig_focus_changed.connect(self._focus_changed)
        self._ivl.opts.sig_changed.connect(self._viewer_opts_changed)
        self._ivl.main_view_md.sig_changed.connect(self._view_changed)
        QtWidgets.QApplication.instance().aboutToQuit.connect(self._view.finalize)

        self._vol = self._ivl.focus()[3]
        self._all_data_changed(list(self._ivm.data.keys()))

    def set_slice_mode(self, mode):
        """ Set the slicing mode, one of the SLICE_* constants """
        self._slice_mode = mode
        if self.enabled:
            self._update_slice_btn()
            self._view.set_mode(mode)
            # Composite any data the new mode needs which has not been computed yet
            self._update()

    def _next_slice_mode(self):
        self.set_slice_mode((self._slice_mode + 1) % len(SLICE_MODE_NAMES))

    def _update_slice_btn(self):
        self._slice_btn.setText("Slicing: %s" % SLICE_MODE_NAMES[self._slice_mode])
        uses_volume = self._slice_mode != SLICE_PLANES
        self._opacity_label.setEnabled(uses_volume)
        self._opacity_slider.setEnabled(uses_volume)

    def _show_message(self, text):
        self._message.setText(text)
        self._message.setVisible(True)

    def _opacity_changed(self, value):
        self._view.set_opacity(value / 100)

    def _main_data_changed(self, _data):
        self._reset_camera = True
        self._data_changed()

    def _all_data_changed(self, data_names):
        for name in list(self._watched_views):
            if name not in data_names:
                self._watched_views.pop(name).sig_changed.disconnect(self._view_changed)
        for name in data_names:
            if name not in self._watched_views:
                view = self._ivm.data[name].view
                view.sig_changed.connect(self._view_changed)
                self._watched_views[name] = view
        self._data_changed()

    def _focus_changed(self, focus):
        if focus[3] != self._vol:
            self._vol = focus[3]
            self._data_changed()
        # Moving the crosshairs only changes where the view is sliced, which is cheap
        if self._slice_mode != SLICE_OFF and self._grid is not None and self.isVisible():
            self._view.set_focus(self._grid_focus(focus))

    def _grid_focus(self, focus):
        """ Crosshair position in voxel co-ordinates of the render grid """
        return self._grid.world_to_grid(self._ivl.grid.grid_to_world(focus[:3]))

    def _viewer_opts_changed(self, key, _value):
        if key == "main_data":
            self._data_changed()

    def _view_changed(self, _key, _value):
        self._data_changed()

    def _data_changed(self):
        self._cache = {}
        self._update_timer.start()

    def showEvent(self, event):
        """ Catch up with changes made while hidden, e.g. when an ortho view was maximised """
        super(VolumeViewer, self).showEvent(event)
        if self._dirty:
            self._update_timer.start()
        elif self.enabled and self._grid is not None:
            self._view.set_focus(self._grid_focus(self._ivl.focus()))

    def _update(self):
        if not self.enabled:
            return
        if not self.isVisible():
            self._dirty = True
            return
        self._dirty = False

        needed = []
        if self._slice_mode != SLICE_PLANES:
            needed += ["background", "overlays"]
        if self._slice_mode in (SLICE_PLANES, SLICE_PLANES_VOLUME):
            needed.append("slices")
        if all(key in self._cache for key in needed) and self._grid is not None:
            return

        self._grid = None
        if self._ivm.main is not None:
            self._grid = render_grid(self._ivl.grid)
            for key in needed:
                if key not in self._cache:
                    # Overlays use the opacity of the ortho views so that they are
                    # opaque at 100% alpha, rather than the background's opacity ramp
                    self._cache[key] = composite_rgba(self._ivm, self._ivl, self._grid, int(self._vol),
                                                      slice_style=(key != "background"),
                                                      which=COMPOSITE_LAYERS[key])

        if self._grid is not None:
            self._view.set_focus(self._grid_focus(self._ivl.focus()))
        self._view.set_data(self._grid, **self._cache)
        has_data = any(rgba is not None for rgba in self._cache.values())
        if has_data and self._reset_camera:
            self._view.reset_camera()
            self._reset_camera = False
