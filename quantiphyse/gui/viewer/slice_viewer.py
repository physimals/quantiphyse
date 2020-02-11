"""
Quantiphyse - 2d ortho slice image viewer

Copyright (c) 2013-2018 University of Oxford
"""

from __future__ import division, unicode_literals, absolute_import

try:
    from PySide import QtGui, QtCore, QtGui as QtWidgets
except ImportError:
    from PySide2 import QtGui, QtCore, QtWidgets

import numpy as np
import pyqtgraph as pg

from quantiphyse.utils import LogSource
from quantiphyse.utils.enums import Orientation, DisplayOrder, Visibility, Boundary
from quantiphyse.data import OrthoSlice
from quantiphyse.data.qpdata import Metadata
from quantiphyse.gui.colors import get_lut, get_col

from .maskable_image import MaskableImage

MAIN_DATA = ""

# An arbitrary 'big number' expected to be larger than the largest number of 
# data sets the viewer is ever likely to hold
MAX_NUM_DATA_SETS = 1000

class SliceDataView(LogSource):
    """
    Draws a slice through a data item
    """ 

    def __init__(self, ivm, qpdata, viewbox, plane, vol, view_metadata=None):
        """
        :param qpdata: QpData instance
        :param viewbox: pyqtgraph ViewBox instance
        :param view_metadata: View parameters
        """
        LogSource.__init__(self)
        self._ivm = ivm
        self._qpdata = qpdata
        self._viewbox = viewbox
        self._plane = plane
        self._vol = vol
        self._view = self._qpdata.view
        if view_metadata is not None:
            self._view = view_metadata
        
        self._redraw_options = [
            "visible",
            "roi",
            "z_order",
            "interp_order",
            "contour",
        ]
        self._img = MaskableImage()
        self._contours = []
        self._viewbox.addItem(self._img)
        self._lut = get_lut(self._view.cmap, self._view.alpha)
        self.update()
        self.redraw()
        self._view.sig_changed.connect(self._view_metadata_changed)

    @property
    def plane(self):
        """ Current SlicePlane the viewer is displaying """
        return self._plane

    @plane.setter
    def plane(self, plane):
        if plane != self._plane:
            self.debug("Plane changed - redrawing")
            self._plane = plane
            self.redraw()

    @property
    def vol(self):
        """ Current data volume being displayed """
        return self._vol

    @vol.setter
    def vol(self, vol):
        if vol != self._vol and vol < self._qpdata.nvols:
            self.debug("Volume changed - redrawing")
            self._vol = vol
            self.redraw()

    def _view_metadata_changed(self, key, value):
        self.debug("View params changed: %s=%s", key, value)
        if key in ("cmap", "lut"):
            if self._view.cmap != "custom":
                self._lut = get_lut(self._view.cmap, self._view.alpha)
            else:
                self._lut = self._view.lut
        elif key == "alpha":
            self._lut = [list(row[:3]) + [self._view.alpha] for row in self._lut]
        self.update()
        if key in self._redraw_options:
            self.redraw()

    def update(self):
        """
        Update the image without re-slicing the data
        """
        self.debug("visible? %s", self._view.visible)
        self._img.setVisible(self._view.visible == Visibility.SHOW and (not self._qpdata.roi or bool(self._view.shade)))
        self._img.set_boundary_mode(self._view.boundary)
        self._img.setLookupTable(self._lut, update=True)
        self._img.setLevels(self._view.cmap_range)
        self.debug("overlay cmap range %s", self._view.cmap_range)

    def redraw(self, interp_order=0):
        """
        Update the image when the slice data may have changed
        and therefore may need re-extracting.

        This is more expensive than just changing image parameters so it
        is only triggered when required
        """
        self.debug("slicedataview: redrawing image")
        self.debug(self._vol)
        self.debug("%s, %s", self._plane.basis, self._plane.normal)

        self._z_order = self._view.z_order
        if self._qpdata.roi:
            # FIXME ROIs always on top - should be option
            self._z_order += MAX_NUM_DATA_SETS

        if self._img.isVisible() or self._view.contour:
            slicedata, slicemask, scale, offset = self._qpdata.slice_data(self._plane, vol=self._vol,
                                                                          interp_order=interp_order)
            self.debug("Image data range: %f, %f", np.min(slicedata), np.max(slicedata))
            qtransform = QtGui.QTransform(scale[0, 0], scale[0, 1],
                                          scale[1, 0], scale[1, 1],
                                          offset[0], offset[1])
        if self._img.isVisible():
            self._img.setTransform(qtransform)
            self._img.setImage(slicedata, autoLevels=False)
            self._img.setZValue(self._z_order)

            if self._view.roi:
                roi = self._ivm.data[self._view.roi]
                resampled_roi = roi.resample(self._qpdata.grid)
                maskdata, _, _, _ = resampled_roi.slice_data(self._plane)
                self._img.mask = np.logical_and(maskdata, slicemask)
            else:
                self._img.mask = slicemask

        n_contours = 0
        if self._qpdata.roi and self._view.contour and self._view.visible == Visibility.SHOW:
            # Update data and level for existing contour items, and create new ones if needed
            max_region = max(self._qpdata.regions.keys())
            for val in self._qpdata.regions:
                pencol = get_col(self._lut, val, max_region)
                if val != 0:
                    if n_contours == len(self._contours):
                        self._contours.append(pg.IsocurveItem())
                        self._viewbox.addItem(self._contours[n_contours])

                    contour = self._contours[n_contours]
                    contour.setTransform(qtransform)
                    contour.setData((slicedata == val).astype(np.int))
                    contour.setLevel(1)
                    contour.setPen(pg.mkPen(pencol, width=3))
                    contour.setZValue(self._z_order)
                    n_contours += 1

        # Clear data from contours not required - FIXME delete them?
        for idx in range(n_contours, len(self._contours)):
            self._contours[idx].setData(None)

    def remove(self):
        """
        Remove the view from the viewbox
        """
        self.debug("Removing slice view")
        self._viewbox.removeItem(self._img)
        for contour in self._contours:
            self._viewbox.removeItem(contour)

class OrthoSliceViewer(pg.GraphicsView, LogSource):
    """
    Displays an orthographic slice through data/ROIs relative to the
    a main viewer grid

    This viewer takes its grid and focus point from a Viewer object
    and maintains its own set of SliceDataView objects. It optionally
    displays the main data as a greyscale background image
    """

    # Signals when point is selected
    sig_pick = QtCore.Signal(int, list)

    # Signals when mouse is draggged. Only emitted if
    # active picker uses drag selection
    sig_drag = QtCore.Signal(int, list)

    # Signals when view is double clicked
    sig_doubleclick = QtCore.Signal(int)

    def __init__(self, ivl, ivm, ax_map, ax_labels):
        """
        :param ivl: Viewer
        :param ivm: ImageVolumeManagement
        :param ax_map: Sequence defining the x, y, z axis of the slice viewer
                       in terms of RAS axis sequence indexes
        :param ax_labels: Sequence of labels for the RAS axes
        """
        LogSource.__init__(self)
        pg.GraphicsView.__init__(self)
        self._ivl = ivl
        self.ivm = ivm
        self.xaxis, self.yaxis, self.zaxis = ax_map
        self._slicez = 0
        self._vol = 0
        self._plane = OrthoSlice(self._ivl.grid, self.zaxis, self._slicez)
        self._main_view = None
        self._dragging = False
        self._arrow_items = []
        self._data_views = {}
        self.debug("axes=%i, %i, %i", self.xaxis, self.yaxis, self.zaxis)

        # View box to display graphics items
        self._viewbox = pg.ViewBox(name="view%i" % self.zaxis, border=pg.mkPen((0x6c, 0x6c, 0x6c), width=2.0))
        self._viewbox.setAspectLocked(True)
        self._viewbox.setBackgroundColor([0, 0, 0])
        self._viewbox.enableAutoRange()
        self.setCentralItem(self._viewbox)

        # Crosshairs
        self._vline = pg.InfiniteLine(angle=90, movable=False)
        self._vline.setZValue(2*MAX_NUM_DATA_SETS)
        self._vline.setPen(pg.mkPen((0, 255, 0), width=1.0, style=QtCore.Qt.DashLine))

        self._hline = pg.InfiniteLine(angle=0, movable=False)
        self._hline.setZValue(2*MAX_NUM_DATA_SETS)
        self._hline.setPen(pg.mkPen((0, 255, 0), width=1.0, style=QtCore.Qt.DashLine))

        self._viewbox.addItem(self._vline, ignoreBounds=True)
        self._viewbox.addItem(self._hline, ignoreBounds=True)

        # Dummy image item which enables us to translate click co-ordinates
        # into image space co-ordinates even when there is no data in the view
        self._dummy = pg.ImageItem()
        self._dummy.setVisible(False)
        self._viewbox.addItem(self._dummy, ignoreBounds=True)

        # Static labels for the view directions
        self._labels = []
        for axis in [self.xaxis, self.yaxis]:
            self._labels.append(QtGui.QLabel(ax_labels[axis][0], parent=self))
            self._labels.append(QtGui.QLabel(ax_labels[axis][1], parent=self))
        for label in self._labels:
            label.setAttribute(QtCore.Qt.WA_TranslucentBackground)

        self._grid_changed(self._ivl.grid)
        self._focus_changed(self._ivl.focus())
        self._update_crosshairs()
        self._update_orientation()

        # Connect to signals from the parent viewer
        self._ivl.sig_grid_changed.connect(self._grid_changed)
        self._ivl.sig_focus_changed.connect(self._focus_changed)
        self._ivl.sig_arrows_changed.connect(self._arrows_changed)
        self._ivl.opts.sig_changed.connect(self._view_opts_changed)

        # Connect to data change signals
        self.ivm.sig_all_data.connect(self._data_changed)
        self.ivm.sig_main_data.connect(self._main_data_changed)

        # Need to intercept the default resize event
        # FIXME why can't call superclass method normally?
        self.resizeEventOrig = self.resizeEvent
        self.resizeEvent = self._window_resized

    def reset(self):
        """ Reset the viewer to show all data sets"""
        self.debug("Auto range")
        self._viewbox.autoRange()

    def redraw(self):
        """ Force a redraw of the viewer, e.g. if data has changed """
        for view in self._data_views.values():
            view.redraw()

    def _view_opts_changed(self, key, value):
        if key in ("orientation", "labels"):
            self._update_orientation()
        elif key == "crosshairs":
            self._update_crosshairs()
        elif key == "main_data":
            self._update_main_data()

    def _grid_changed(self, grid):
        """
        Set the grid that the slice viewer is relative to
        """
        # Adjust axis scaling to that of the viewing grid so voxels have correct relative size
        self._viewbox.setAspectLocked(True, ratio=(grid.spacing[self.xaxis] / grid.spacing[self.yaxis]))
        self._update_slice()
        self.reset()

    def _focus_changed(self, focus):
        self.debug("focus=%s", focus)

        if self.isVisible():
            self._vline.setPos(float(focus[self.xaxis]))
            self._hline.setPos(float(focus[self.yaxis]))

            if focus[self.zaxis] != self._slicez or self._vol != focus[3]:
                self._update_slice()
                self._update_visible_arrows()

    def _arrows_changed(self, arrows):
        """
        Set the locations and colours of arrows to be drawn

        :param arrows: Sequence of tuples: (position, color). Position
                       is a XYZ tuple, color is anything that can
                       be passed to pyqtgraph.mkPen (e.g. color name
                       or RGB tuple)
        """
        item_num = 0
        for pos, col in arrows:
            if item_num == len(self._arrow_items):
                item = pg.ArrowItem()
                self._viewbox.addItem(item)
                self._arrow_items.append((pos, col, item))
            _, _, item = self._arrow_items[item_num]
            item.setPos(float(pos[self.xaxis]), float(pos[self.yaxis]))
            item.setPen(pg.mkPen(col))
            item.setBrush(pg.mkBrush(col))
            item.setZValue(2)
            self._arrow_items[item_num] = (pos, col, item)
            item_num += 1

        for _, _, item in self._arrow_items[item_num:]:
            self._viewbox.removeItem(item)

        self._arrow_items = self._arrow_items[:item_num]
        self._update_visible_arrows()

    def _data_changed(self, data_names):
        self.debug("data changed")
        for name, view in list(self._data_views.items()):
            if name not in data_names and name != MAIN_DATA:
                view.remove()
                del self._data_views[name]

        for name in data_names:
            if name not in self._data_views:
                qpdata = self.ivm.data[name]
                self._data_views[name] = SliceDataView(self.ivm, qpdata, self._viewbox, self._plane, self._vol)

        self._update_crosshairs()
        self._update_orientation()

    def _main_data_changed(self):
        self._update_main_data()

    def _update_main_data(self):
        if MAIN_DATA in self._data_views:
            self._data_views[MAIN_DATA].remove()
            del self._data_views[MAIN_DATA]

        if self.ivm.main is not None and self._ivl.opts.main_data == Visibility.SHOW:
            self._data_views[MAIN_DATA] = SliceDataView(self.ivm, self.ivm.main, self._viewbox, self._plane, self._vol, self._ivl.main_view_md)
        self.reset()

    def _update_crosshairs(self):
        crosshairs_visible = len(self._data_views) > 0 and self._ivl.opts.crosshairs == Visibility.SHOW
        self._vline.setVisible(crosshairs_visible)
        self._hline.setVisible(crosshairs_visible)

    def _update_orientation(self):
        labels_visible = len(self._data_views) > 0 and self._ivl.opts.labels == Visibility.SHOW
        for label in self._labels:
            label.setVisible(labels_visible)

        if self.xaxis == 0:
            if self._ivl.opts.orientation == Orientation.NEUROLOGICAL:
                left, right, invert = 0, 1, False
            else:
                left, right, invert = 1, 0, True
            self._viewbox.invertX(invert)
            self._labels[right].setText("R")
            self._labels[left].setText("L")

    def _update_slice(self):
        self._slicez = self._ivl.focus()[self.zaxis]
        self._vol = self._ivl.focus()[3]
        self._plane = OrthoSlice(self._ivl.grid, self.zaxis, self._slicez)
        for view in self._data_views.values():
            view.plane = self._plane
            view.vol = self._vol
        self.debug("set slice: %f %i", self._slicez, self._vol)

    def _update_visible_arrows(self):
        """
        Update arrows so only those visible are shown
        """
        current_zpos = int(self._ivl.focus()[self.zaxis] + 0.5)
        for pos, _, item in self._arrow_items:
            arrow_zpos = int(pos[self.zaxis] + 0.5)
            item.setVisible(current_zpos == arrow_zpos)

    def _window_resized(self, event):
        """
        Called when window is resized - updates the position
        of the text labels and then calls the original resize method
        """
        w = self.geometry().width()
        h = self.geometry().height()
        self._labels[0].setGeometry(0, h/2, 10, 10)
        self._labels[1].setGeometry(w-10, h/2, 10, 10)
        self._labels[2].setGeometry(w/2, h-10, 10, 10)
        self._labels[3].setGeometry(w/2, 0, 10, 10)
        self.resizeEventOrig(event)

    def wheelEvent(self, event):
        """
        Subclassed to remove scroll to zoom from pg.ImageItem
        and instead trigger a scroll through the volume
        """
        dz = int(event.delta()/120)
        pos = self._ivl.focus()
        pos[self.zaxis] += dz
        self._ivl.set_focus(pos)

    def mousePressEvent(self, event):
        """
        Called when mouse button is pressed on the view
        """
        super(OrthoSliceViewer, self).mousePressEvent(event)
        if self.ivm.main is None:
            return

        if event.button() == QtCore.Qt.LeftButton:
            # Convert co-ords to view grid
            coords = self._dummy.mapFromScene(event.pos())
            pos = self._ivl.focus()
            pos[self.xaxis] = coords.x()
            pos[self.yaxis] = coords.y()
            self._ivl.set_focus(pos)

            if self._ivl.picker.use_drag:
                self._dragging = True
            self.sig_pick.emit(self.zaxis, self._ivl.focus())

    def mouseReleaseEvent(self, event):
        """
        Called when mouse button is released on the view
        """
        super(OrthoSliceViewer, self).mouseReleaseEvent(event)
        self._dragging = False

    def mouseDoubleClickEvent(self, event):
        """
        Called when mouse button is double clicked on the view

        This is used to maximise/minimise the view window
        """
        super(OrthoSliceViewer, self).mouseDoubleClickEvent(event)
        if event.button() == QtCore.Qt.LeftButton:
            self.sig_doubleclick.emit(self.zaxis)

    def mouseMoveEvent(self, event):
        """
        Called when the mouse is moved over the window.

        The default behaviour is used unless we are dragging a
        selection region
        """
        if self._dragging:
            coords = self._dummy.mapFromScene(event.pos())
            pos = self._ivl.focus()
            pos[self.xaxis] = coords.x()
            pos[self.yaxis] = coords.y()
            self.sig_drag.emit(self.zaxis, pos)
        else:
            super(OrthoSliceViewer, self).mouseMoveEvent(event)
