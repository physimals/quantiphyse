"""
Quantiphyse - classes which draw data views

An OrthoDataView is associated with a QpData object and is responsible for
drawing it onto a OrthoSliceView.

Each OrthoDataView maintains its own set of GraphicsItems (images, contour lines etc)
for each OrthoSliceView it is asked to draw into. View parameters can be set on
a OrthoDataView - it must decide whether to signal a fresh redraw or whether it can
just update its GraphicsItems witihout redrawing.

Copyright (c) 2013-2019 University of Oxford
"""

from __future__ import division, unicode_literals, absolute_import, print_function

import collections
import logging

try:
    from PySide import QtGui, QtCore, QtGui as QtWidgets
except ImportError:
    from PySide2 import QtGui, QtCore, QtWidgets

import numpy as np

import pyqtgraph as pg

from quantiphyse.utils import get_lut, get_pencol, get_icon
from quantiphyse.gui.widgets import RoiCombo, OverlayCombo

LOG = logging.getLogger(__name__)

class MaskableImage(pg.ImageItem):
    """
    Minor addition to ImageItem to allow it to be masked by an ROI
    """
    def __init__(self, image=None, **kwargs):
        pg.ImageItem.__init__(self, image, **kwargs)
        self.mask = None
        self.boundary = OrthoDataView.BOUNDARY_TRANS

    def set_boundary_mode(self, mode):
        """
        Set the boundary mode, i.e. how data outside the colour map
        range is treated. It can be made transparent or clamped to
        the max/min colour

        :param mode: OrthoDataView.BOUNDARY_TRANS or OrthoDataView.BOUNDARY_CLAMP
        """
        self.boundary = mode

    def render(self):
        """
        Custom masked renderer based on PyQtGraph code
        """
        if self.image is None or self.image.size == 0:
            return
        if isinstance(self.lut, collections.Callable):
            lut = self.lut(self.image)
        else:
            lut = self.lut

        argb, alpha = pg.functions.makeARGB(self.image, lut=lut, levels=self.levels)
        if self.image.size > 1:
            if self.mask is not None:
                argb[:, :, 3][self.mask == 0] = 0

            if self.boundary == OrthoDataView.BOUNDARY_TRANS:
                # Make out of range values transparent
                trans = np.logical_or(self.image < self.levels[0], self.image > self.levels[1])
                argb[:, :, 3][trans] = 0
            elif self.boundary == OrthoDataView.BOUNDARY_LOWERTRANS:
                # Make out of range values transparent
                trans = self.image < self.levels[0]
                argb[:, :, 3][trans] = 0
            elif self.boundary == OrthoDataView.BOUNDARY_UPPERTRANS:
                # Make out of range values transparent
                trans = self.image > self.levels[1]
                argb[:, :, 3][trans] = 0

        self.qimage = pg.functions.makeQImage(argb, alpha)

class OrthoDataView(QtCore.QObject):
    """
    View of a data item
    """

    BOUNDARY_TRANS = 0
    BOUNDARY_CLAMP = 1
    BOUNDARY_LOWERTRANS = 2
    BOUNDARY_UPPERTRANS = 3

    # Signals when view parameters are changed
    sig_changed = QtCore.Signal(object)

    def __init__(self, data):
        super(OrthoDataView, self).__init__()
        self.data = data

        self.default_options = {
            "visible" : True,
            "roi_only" : False,
            "boundary" : self.BOUNDARY_TRANS,
            "alpha" : 255,
            "cmap_range" : _cmap_range(self.data),
            "z_value" : -1,
            "interp_order" : 0,
            "cmap" : "jet",
        }
        self.redraw_options = [
            "visible",
            "roi_only",
            "z_value",
            "interp_order"
            "shade",
            "contour",
        ]
        self.ortho_views = {}
        self.histogram = None
        self.mask = None
        self.sig_changed.connect(self.update)

    def __getattr__(self, opt):
        return self.data.metadata.get(opt, self.default_options.get(opt, None))

    def set_view_opt(self, name, value):
        """
        Set a data view option

        Depending on the option being set, the data view may be redrawn

        :param name: Option name
        :param value: Option value
        """
        self.data.metadata[name] = value
        self.update()
        if name in self.redraw_options:
            self.redraw()

    def add_ortho_view(self, ortho_view):
        """
        """
        name = ortho_view.vb.name
        self.ortho_views[name] = ortho_view
        img = MaskableImage()
        self.imgs[name] = img
        if self.histogram is not None:
            self.histogram.add_img(img)

    def set_roi(self, roi):
        """
        Set the associated ROI. The images may (if specified)
        be masked by the ROI
        """
        if roi is not None:
            self.mask = roi.resample(self.data.grid)
        else:
            self.mask = None

    def redraw(self, *ortho_views):
        """
        Redraw graphics items
        """
        if not ortho_views:
            ortho_views = self.ortho_views.values()

        self.update(ortho_views)
        for ortho_view in ortho_views:
            name = ortho_view.vb.name
            img = self.imgs[name]
            if img.isVisible():
                slicedata, slicemask, scale, offset = self.data.slice_data(ortho_view.slice_plane,
                                                                           vol=ortho_view.slice_vol,
                                                                           interp_order=self.interp_order)
                img.setTransform(QtGui.QTransform(scale[0, 0], scale[0, 1],
                                                  scale[1, 0], scale[1, 1],
                                                  offset[0], offset[1]))
                img.setImage(slicedata, autoLevels=False)

                if self.mask is not None and self.roi_only:
                    maskdata, _, _, _ = self.mask.slice_data(ortho_view.slice_plane)
                    img.mask = np.logical_and(maskdata, slicemask)
                else:
                    img.mask = slicemask

    def update(self, *ortho_views):
        """
        Update image view parameters without redrawing
        """
        if not ortho_views:
            ortho_views = self.ortho_views.values()

        for ortho_view in ortho_views:
            name = ortho_view.vb.name
            img = self.imgs[name]
            img.setVisible(self.data is not None and self.visible)
            img.setZValue(self.z_value)
            img.set_boundary_mode(self.boundary)
            img.setLevels(self.cmap_range)

class RoiView(OrthoDataView):
    """
    View of a ROI,

    ROIs are drawn in different styles to data items (contour, shaded, etc)
    """

    def __init__(self, ivm):
        super(RoiView, self).__init__(ivm)
        self.default_options.update({
            "shade" : True,
            "contour" : False,
            "alpha" : 150,
            "outline_width" : 3.0,
            "z_value" : 1,
        })
        self.contours = {}

    def add_ortho_view(self, ortho_view):
        self.contours[ortho_view.vb.name] = []
        OrthoDataView.add_ortho_view(self, ortho_view)

    def redraw(self, *ortho_views):
        if not ortho_views:
            ortho_views = self.ortho_views.values()

        self.update(ortho_views)
        for ortho_view in ortho_views:
            name = ortho_view.vb.name
            img = self.imgs[name]
            if img.isVisible():
                slicedata, _, scale, offset = self.data.slice_data(slice_plane=ortho_view.slice_plane)
                transform = QtGui.QTransform(scale[0, 0], scale[0, 1],
                                             scale[1, 0], scale[1, 1],
                                             offset[0], offset[1])
                img.setImage(slicedata, autoLevels=False)
            img.setTransform(transform)

            contours = self.contours[name]
            n_contours = 0
            if self.contour:
                # Update data and level for existing contour items, and create new ones if needed
                for val in self.data.regions:
                    pencol = get_pencol(self.data, val)
                    if val != 0:
                        if n_contours == len(contours):
                            contours.append(pg.IsocurveItem())
                            ortho_view.vb.addItem(contours[n_contours])

                        contour = contours[n_contours]
                        contour.setTransform(transform)
                        contour.setData((slicedata == val).astype(np.int))
                        contour.setLevel(1)
                        contour.setPen(pg.mkPen(pencol, width=self.outline_width))
                        n_contours += 1

            # Clear data from contours not required - FIXME delete them?
            for idx in range(n_contours, len(contours)):
                contours[idx].setData(None)

    def update(self, *ortho_views):
        if not ortho_views:
            ortho_views = self.ortho_views.values()

        for ortho_view in ortho_views:
            name = ortho_view.vb.name
            img = self.imgs[name]
            img.setVisible(self.data is not None and self.shade)
            img.setZValue(self.z_value)
            img.set_boundary_mode(self.boundary)
            lut = get_lut(self.data, self.alpha)
            img.setLookupTable(lut)
            img.setLevels([0, len(lut)-1], update=True)

class MainDataView(OrthoDataView):
    """
    View of main data

    Just the same as a regular overlay but always grey and at the back
    """
    def __init__(self, data):
        OrthoDataView.__init__(self, data)
        self._cmap_range = _cmap_range(self.data, percentile=99)

    def __getattr__(self, name):
        if name == "cmap":
            return "grey"
        elif name == "z_value":
            return -999
        elif name == "cmap_range":
            return self._cmap_range
        else:
            return OrthoDataView.__getattr__(self, name)

    def set_view_opt(self, name, value):
        if name not in ("cmap", "cmap_range", "z_value"):
            OrthoDataView.set_view_opt(self, name, value)
        elif name == "cmap_range":
            self._cmap_range = value

class RoiViewWidget(QtGui.QGroupBox):
    """ Change view options for ROI """
    def __init__(self, ivl, view):
        QtGui.QGroupBox.__init__(self)
        self.ivl = ivl
        self.ivm = ivl.ivm
        self.view = view

        grid = QtGui.QGridLayout()
        grid.setVerticalSpacing(2)
        grid.setContentsMargins(5, 5, 5, 5)
        self.setLayout(grid)

        grid.addWidget(QtGui.QLabel("ROI"), 0, 0)
        self.roi_combo = RoiCombo(self.ivm, none_option=True, set_first=False)
        grid.addWidget(self.roi_combo, 0, 1)
        grid.addWidget(QtGui.QLabel("View"), 1, 0)
        self.roi_view_combo = QtGui.QComboBox()
        self.roi_view_combo.addItem("Shaded")
        self.roi_view_combo.addItem("Contour")
        self.roi_view_combo.addItem("Both")
        self.roi_view_combo.addItem("None")
        grid.addWidget(self.roi_view_combo, 1, 1)
        grid.addWidget(QtGui.QLabel("Alpha"), 2, 0)
        self.roi_alpha_sld = QtGui.QSlider(QtCore.Qt.Horizontal, self)
        self.roi_alpha_sld.setFocusPolicy(QtCore.Qt.NoFocus)
        self.roi_alpha_sld.setRange(0, 255)
        self.roi_alpha_sld.setValue(150)
        grid.addWidget(self.roi_alpha_sld, 2, 1)
        grid.setRowStretch(3, 1)

        self.roi_combo.currentIndexChanged.connect(self._combo_changed)
        self.roi_view_combo.currentIndexChanged.connect(self._view_changed)
        self.roi_alpha_sld.valueChanged.connect(self._alpha_changed)
        view.sig_changed.connect(self._update)

    def _update(self, view):
        if view is not None:
            try:
                self.roi_view_combo.blockSignals(True)
                self.roi_alpha_sld.blockSignals(True)
                self.roi_combo.blockSignals(True)

                if view.shade and view.contour:
                    self.roi_view_combo.setCurrentIndex(2)
                elif view.shade:
                    self.roi_view_combo.setCurrentIndex(0)
                elif view.contour:
                    self.roi_view_combo.setCurrentIndex(1)
                else:
                    self.roi_view_combo.setCurrentIndex(3)
                self.roi_alpha_sld.setValue(view.alpha)

                if view.data is not None:
                    idx = self.roi_combo.findText(view.data.name)
                    self.roi_combo.setCurrentIndex(idx)
                else:
                    self.roi_combo.setCurrentIndex(-1)

            finally:
                self.roi_view_combo.blockSignals(False)
                self.roi_alpha_sld.blockSignals(False)
                self.roi_combo.blockSignals(False)

    def _combo_changed(self, idx):
        if idx > 0:
            roi = self.roi_combo.itemText(idx)
            self.ivl.ivm.set_current_roi(roi)
        else:
            self.ivl.ivm.set_current_roi(None)

    def _view_changed(self, idx):
        self.view.set_view_opt("shade", idx in (0, 2))
        self.view.set_view_opt("contour", idx in (1, 2))

    def _alpha_changed(self, alpha):
        """ Set the ROI transparency """
        self.view.set_view_opt("alpha", alpha)

class OverlayViewWidget(QtGui.QGroupBox):
    """ Change view options for ROI """
    def __init__(self, ivl, view):
        QtGui.QGroupBox.__init__(self)
        self.ivl = ivl
        self.ivm = ivl.ivm
        self.view = view

        grid = QtGui.QGridLayout()
        grid.setVerticalSpacing(2)
        grid.setContentsMargins(5, 5, 5, 5)
        self.setLayout(grid)

        grid.addWidget(QtGui.QLabel("Overlay"), 0, 0)
        self.overlay_combo = OverlayCombo(self.ivm, none_option=True, set_first=False)
        grid.addWidget(self.overlay_combo, 0, 1)
        grid.addWidget(QtGui.QLabel("View"), 1, 0)
        self.ov_view_combo = QtGui.QComboBox()
        self.ov_view_combo.addItem("All")
        self.ov_view_combo.addItem("Only in ROI")
        self.ov_view_combo.addItem("None")
        grid.addWidget(self.ov_view_combo, 1, 1)
        grid.addWidget(QtGui.QLabel("Color map"), 2, 0)
        hbox = QtGui.QHBoxLayout()
        self.ov_cmap_combo = QtGui.QComboBox()
        self.ov_cmap_combo.addItem("jet")
        self.ov_cmap_combo.addItem("hot")
        self.ov_cmap_combo.addItem("gist_heat")
        self.ov_cmap_combo.addItem("flame")
        self.ov_cmap_combo.addItem("bipolar")
        self.ov_cmap_combo.addItem("spectrum")
        hbox.addWidget(self.ov_cmap_combo)
        self.ov_levels_btn = QtGui.QPushButton()
        self.ov_levels_btn.setIcon(QtGui.QIcon(get_icon("levels.png")))
        self.ov_levels_btn.setFixedSize(16, 16)
        self.ov_levels_btn.setToolTip("Adjust colour map levels")
        self.ov_levels_btn.clicked.connect(self._show_ov_levels)
        self.ov_levels_btn.setEnabled(False)
        hbox.addWidget(self.ov_levels_btn)
        grid.addLayout(hbox, 2, 1)
        grid.addWidget(QtGui.QLabel("Alpha"), 3, 0)
        self.ov_alpha_sld = QtGui.QSlider(QtCore.Qt.Horizontal, self)
        self.ov_alpha_sld.setFocusPolicy(QtCore.Qt.NoFocus)
        self.ov_alpha_sld.setRange(0, 255)
        self.ov_alpha_sld.setValue(255)
        grid.addWidget(self.ov_alpha_sld, 3, 1)
        grid.setRowStretch(4, 1)

        self.overlay_combo.currentIndexChanged.connect(self._combo_changed)
        self.ov_view_combo.currentIndexChanged.connect(self._view_changed)
        self.ov_cmap_combo.currentIndexChanged.connect(self._cmap_changed)
        self.ov_alpha_sld.valueChanged.connect(self._alpha_changed)
        self.view.sig_changed.connect(self._update)

    def _update(self, view):
        widgets = [self.ov_view_combo, self.ov_cmap_combo,
                   self.ov_alpha_sld, self.overlay_combo]
        try:
            for widget in widgets:
                widget.blockSignals(True)

            if not view.visible:
                self.ov_view_combo.setCurrentIndex(2)
            elif view.roi_only:
                self.ov_view_combo.setCurrentIndex(1)
            else:
                self.ov_view_combo.setCurrentIndex(0)

            # 'Custom' only appears as a flag to indicate the user has messed with the
            # LUT using the histogram widget. Otherwise is is hidden
            cmap = view.cmap
            if cmap == "custom":
                idx = self.ov_cmap_combo.findText("custom")
                if idx >= 0:
                    self.ov_cmap_combo.setCurrentIndex(idx)
                else:
                    self.ov_cmap_combo.addItem("custom")
                    idx = self.ov_cmap_combo.findText("custom")
                    self.ov_cmap_combo.setCurrentIndex(idx)
            else:
                idx = self.ov_cmap_combo.findText("custom")
                if idx >= 0:
                    self.ov_cmap_combo.removeItem(idx)
                idx = self.ov_cmap_combo.findText(view.cmap)
                self.ov_cmap_combo.setCurrentIndex(idx)

            self.ov_alpha_sld.setValue(view.alpha)

            self.ov_levels_btn.setEnabled(view.data is not None)
            if view.data is not None:
                idx = self.overlay_combo.findText(view.data.name)
                self.overlay_combo.setCurrentIndex(idx)
            else:
                self.overlay_combo.setCurrentIndex(-1)
        except:
            import traceback
            traceback.print_exc()
        finally:
            for widget in widgets:
                widget.blockSignals(False)

    def _combo_changed(self, idx):
        if idx > 0:
            data_name = self.overlay_combo.itemText(idx)
            self.ivm.set_current_data(data_name)
        else:
            self.ivl.ivm.set_current_data(None)

    def _cmap_changed(self, idx):
        cmap = self.ov_cmap_combo.itemText(idx)
        self.view.set_view_opt("cmap", cmap)

    def _view_changed(self, idx):
        """ Viewing style (all or within ROI only) changed """
        self.view.set_view_opt("visible", idx in (0, 1))
        self.view.set_view_opt("roi_only", (idx == 1))

    def _alpha_changed(self, alpha):
        """ Set the data transparency """
        self.view.set_view_opt("alpha", alpha)

    def _show_ov_levels(self):
        dlg = LevelsDialog(self, self.ivl, self.ivm, self.view)
        dlg.exec_()

class LevelsDialog(QtGui.QDialog):
    """
    Dialog box used to set the colourmap max/min for a data view
    """

    def __init__(self, parent, ivl, ivm, view):
        super(LevelsDialog, self).__init__(parent)
        self.ivl = ivl
        self.ivm = ivm
        self.view = view

        self.setWindowTitle("Levels for %s" % view.data.name)
        vbox = QtGui.QVBoxLayout()

        grid = QtGui.QGridLayout()
        self.min_spin = self._add_spin(grid, "Minimum", 0)
        self.max_spin = self._add_spin(grid, "Maximum", 1)

        grid.addWidget(QtGui.QLabel("Percentage of data range"), 2, 0)
        hbox = QtGui.QHBoxLayout()
        self.percentile_spin = QtGui.QSpinBox()
        self.percentile_spin.setMaximum(100)
        self.percentile_spin.setMinimum(1)
        self.percentile_spin.setValue(100)
        hbox.addWidget(self.percentile_spin)
        btn = QtGui.QPushButton("Reset")
        btn.clicked.connect(self._reset)
        hbox.addWidget(btn)
        self.use_roi = QtGui.QCheckBox("Within ROI")
        hbox.addWidget(self.use_roi)
        grid.addLayout(hbox, 2, 1)

        grid.addWidget(QtGui.QLabel("Values outside range are"), 4, 0)
        self.combo = QtGui.QComboBox()
        self.combo.addItem("Transparent")
        self.combo.addItem("Clamped to max/min colour")
        self.combo.addItem("Transparent at lower, clamped at upper")
        self.combo.addItem("Clamped at lower, transparent at upper")
        self.combo.setCurrentIndex(self.view.boundary)
        self.combo.currentIndexChanged.connect(self._bound_changed)
        grid.addWidget(self.combo, 4, 1)
        vbox.addLayout(grid)

        bbox = QtGui.QDialogButtonBox(QtGui.QDialogButtonBox.Ok)
        bbox.accepted.connect(self.close)
        vbox.addWidget(bbox)

        self.setLayout(vbox)

    def _add_spin(self, grid, label, row):
        grid.addWidget(QtGui.QLabel(label), row, 0)
        spin = QtGui.QDoubleSpinBox()
        spin.setMaximum(1e20)
        spin.setMinimum(-1e20)
        spin.setValue(self.view.cmap_range[row])
        spin.valueChanged.connect(self._val_changed(row))
        grid.addWidget(spin, row, 1)
        return spin

    def _val_changed(self, row):
        def _changed(val):
            cmap_range = list(self.view.cmap_range)
            cmap_range[row] = val
            self.view.set_view_opt("cmap_range", cmap_range)
        return _changed

    def _bound_changed(self, idx):
        self.view.set_view_opt("boundary", idx)

    def _reset_view_opt(self):
        percentile = self.percentile_spin.value()
        flat = self.view.data.volume(self.ivl.focus()[3]).flatten()
        if self.use_roi.isChecked() and self.ivm.current_roi is not None:
            flat = self.view.data.mask(self.ivm.current_roi, output_flat=True)

        cmin, cmax = _cmap_range(flat, percentile)
        self.min_spin.setValue(cmin)
        self.max_spin.setValue(cmax)
        self.view.set_view_opt("cmap_range", [cmin, cmax])

def _cmap_range(data, percentile=100):
    data = data.volume(int(data.nvols/2)).flatten()
    # This ignores infinite values too unlike np.nanmin/np.nanmax
    nonans = np.isfinite(data)
    cmin, cmax = np.min(data[nonans]), np.max(data[nonans])
    # Issue #101: if min is exactly zero, make it slightly more
    # as a heuristic for data sets where zero=background
    if cmin == 0:
        cmin = 1e-7*cmax

    if percentile < 100:
        perc_max = np.nanpercentile(data, percentile)
        if perc_max > cmin:
            cmax = perc_max

    return cmin, cmax
