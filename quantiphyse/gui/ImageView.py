"""
Quantiphyse - 2d ortho slice image viewer

Copyright (c) 2013-2018 University of Oxford
"""

from __future__ import division, unicode_literals, absolute_import, print_function

import collections

from PySide import QtCore, QtGui
import warnings
import numpy as np

import pyqtgraph as pg
from pyqtgraph.exporters.ImageExporter import ImageExporter

from quantiphyse.utils import get_icon, debug
from quantiphyse.volumes import OrthoSlice, Transform, DataGrid
from quantiphyse.gui.widgets import OptionsButton

from .HistogramWidget import MultiImageHistogramWidget
from .pickers import DragMode, PICKERS, PointPicker
from .data_views import MainDataView, OverlayView, RoiView

class OrthoView(pg.GraphicsView):
    """
    A single slice view of data and ROI
    """

    # Signals when point is selected
    sig_pick = QtCore.Signal(tuple, int)

    # Signals when view is maximised/minimised
    sig_maxmin = QtCore.Signal(int)

    def __init__(self, ivl, ivm, ax_map, ax_labels):
        pg.GraphicsView.__init__(self)
        self.ivl = ivl
        self.ivm = ivm
        self.xaxis, self.yaxis, self.zaxis = ax_map
        self.dragging = False
        self.contours = []
        self.arrows = []
        self.focus_pos = [0, 0, 0, 0]
        self.slice_plane = None
        self.slice_vol = 0

        self.vline = pg.InfiniteLine(angle=90, movable=False)
        self.vline.setZValue(2)
        self.vline.setPen(pg.mkPen((0, 255, 0), width=1.0, style=QtCore.Qt.DashLine))
        self.vline.setVisible(False)

        self.hline = pg.InfiniteLine(angle=0, movable=False)
        self.hline.setZValue(2)
        self.hline.setPen(pg.mkPen((0, 255, 0), width=1.0, style=QtCore.Qt.DashLine))
        self.hline.setVisible(False)

        self.vb = pg.ViewBox(name="view%i" % self.zaxis, border=pg.mkPen((0, 0, 255), width=3.0))
        self.vb.setAspectLocked(True)
        self.vb.setBackgroundColor([0, 0, 0])
        self.vb.enableAutoRange()
        self.setCentralItem(self.vb)

        # Create static labels for the view directions
        self.labels = []
        for ax in [self.xaxis, self.yaxis]:
            self.labels.append(QtGui.QLabel(ax_labels[ax][0], parent=self))
            self.labels.append(QtGui.QLabel(ax_labels[ax][1], parent=self))
        for l in self.labels:
            l.setVisible(False)
            l.setAttribute(QtCore.Qt.WA_TranslucentBackground)
        self.resizeEventOrig = self.resizeEvent
        self.resizeEvent = self.resize_win

        self.ivl.sig_focus_changed.connect(self.update)
        self.ivl.main_data_view.sig_changed.connect(self.update)
        self.ivl.current_data_view.sig_changed.connect(self.update)
        self.ivl.current_roi_view.sig_changed.connect(self.update)

    def update(self):
        """
        Update the ortho view
        """
        # Get the current position and slice
        self.focus_pos = self.ivl.focus()
        self.slice_plane = OrthoSlice(self.ivl.grid, self.zaxis, self.focus_pos[self.zaxis])
        self.slice_vol = self.focus_pos[3]

        # Adjust axis scaling depending on whether voxel size scaling is enabled
        if self.ivl.opts.size_scaling == self.ivl.opts.SCALE_VOXELS:
            self.vb.setAspectLocked(True, ratio=(self.ivl.grid.spacing[self.xaxis] / self.ivl.grid.spacing[self.yaxis]))
        else:
            self.vb.setAspectLocked(True, ratio=1)

        self._update_labels()
        self._update_crosshairs()
        self._update_arrows()
        self.ivl.main_data_view.update(self.vb, self.slice_plane, self.slice_vol)
        self.ivl.current_data_view.update(self.vb, self.slice_plane, self.slice_vol)
        self.ivl.current_roi_view.update(self.vb, self.slice_plane, self.slice_vol)

    def add_arrow(self, pos, col):
        arrow = pg.ArrowItem(pen=col, brush=col)
        arrow.setPos(float(pos[self.xaxis]), float(pos[self.yaxis]))
        arrow.setVisible(pos[self.zaxis] == pos[self.zaxis])
        arrow.setZValue(2)
        self.vb.addItem(arrow)
        self.arrows.append((pos[self.zaxis], arrow))

    def remove_arrows(self):
        """ Remove all the arrows that have been placed """
        for zpos, arrow in self.arrows:
            self.vb.removeItem(arrow)
        self.arrows = []

    def _update_labels(self):
        for l in self.labels:
            l.setVisible(True)

        # Flip left/right depending on the viewing convention selected
        if self.xaxis == 0:
            # X-axis is left/right
            self.vb.invertX(self.ivl.opts.orientation == 0)
            if self.ivl.opts.orientation == self.ivl.opts.RADIOLOGICAL:
                l, r = 1, 0
            else:
                l, r = 0, 1
            self.labels[r].setText("R")
            self.labels[l].setText("L")

    def _update_crosshairs(self):
        self.vline.setPos(float(self.focus_pos[self.xaxis]))
        self.hline.setPos(float(self.focus_pos[self.yaxis]))
        self.vline.setVisible(self.ivl.opts.crosshairs == self.ivl.opts.SHOW)
        self.hline.setVisible(self.ivl.opts.crosshairs == self.ivl.opts.SHOW)
        self.vb.addItem(self.vline, ignoreBounds=True)
        self.vb.addItem(self.hline, ignoreBounds=True)

    def _update_arrows(self):
        """
        Update arrows so only those visible are shown
        """
        current_zpos = self.ivl.focus()[self.zaxis]
        for zpos, arrow in self.arrows:
            arrow.setVisible(current_zpos == zpos)

    def resize_win(self, event):
        """
        Called when window is resized - updates the position
        of the text labels and then calls the original resize method
        """
        w = self.geometry().width()
        h = self.geometry().height()
        self.labels[0].setGeometry(0, h/2, 10, 10)
        self.labels[1].setGeometry(w-10, h/2, 10, 10)
        self.labels[2].setGeometry(w/2, h-10, 10, 10)
        self.labels[3].setGeometry(w/2, 0, 10, 10)
        self.resizeEventOrig(event)

    def wheelEvent(self, event):
        """
        Subclassed to remove scroll to zoom from pg.ImageItem
        and instead trigger a scroll through the volume
        """
        dz = int(event.delta()/120)
        pos = self.ivl.focus(self.ivm.main.grid)
        pos[self.zaxis] += dz
        if pos[self.zaxis] >= self.ivm.main.grid.shape[self.zaxis] or pos[self.zaxis] < 0:
            return

        self.ivl.set_focus(pos + [pos[3], ], self.ivm.main.grid)

    def mousePressEvent(self, event):
        super(OrthoView, self).mousePressEvent(event)
        if self.ivm.main is None: return

        if event.button() == QtCore.Qt.LeftButton:
            self.dragging = (self.ivl.drag_mode == DragMode.PICKER_DRAG)
            coords = self.ivl.main_data_view.imgs[self.vb.name].mapFromScene(event.pos())
            #print(self.transform())
            #print(event.pos())
            mx = int(coords.x())
            my = int(coords.y())

            if mx < 0 or mx >= self.ivm.main.grid.shape[self.xaxis]: return
            if my < 0 or my >= self.ivm.main.grid.shape[self.yaxis]: return

            # Convert to view grid
            pos = self.ivl.focus(self.ivm.main.grid)
            pos[self.xaxis] = mx
            pos[self.yaxis] = my
            t = Transform(self.ivl.grid, self.ivm.main.grid)
            std_pos = list(t.transform_position(pos[:3]))
            self.ivl.set_focus(pos + [pos[3], ], self.ivm.main.grid)
            self.sig_pick.emit(self.ivl.focus(), self.zaxis)

    def mouseReleaseEvent(self, event):
        super(OrthoView, self).mouseReleaseEvent(event)
        self.dragging = False

    def mouseDoubleClickEvent(self, event):
        super(OrthoView, self).mouseDoubleClickEvent(event)
        if event.button() == QtCore.Qt.LeftButton:
            self.sig_maxmin.emit(self.zaxis)

    def mouseMoveEvent(self, event):
        if self.dragging:
            coords = self.ivl.main_data_view.imgs[self.vb.name].mapFromScene(event.pos())
            mx = int(coords.x())
            my = int(coords.y())
            pos = self.ivl.focus()
            pos[self.xaxis] = mx
            pos[self.yaxis] = my
            self.sig_pick.emit(pos, self.zaxis)
        else:
            super(OrthoView, self).mouseMoveEvent(event)

class Navigator:
    """
    Slider control which alters position along an axis
    """

    def __init__(self, ivl, label, axis, layout_grid, layout_ypos):
        self.ivl = ivl
        self.axis = axis
        self._pos = -1

        layout_grid.addWidget(QtGui.QLabel(label), layout_ypos, 0)
        self.slider = QtGui.QSlider(QtCore.Qt.Horizontal)
        self.slider.setFocusPolicy(QtCore.Qt.NoFocus)
        self.slider.setMinimumWidth(100)
        self.slider.valueChanged.connect(self._changed)
        layout_grid.addWidget(self.slider, layout_ypos, 1)

        self.spin = QtGui.QSpinBox()
        self.spin.valueChanged.connect(self._changed)
        layout_grid.addWidget(self.spin, layout_ypos, 2)

    def _changed(self, value):
        if value != self._pos:
            self.set_pos(value)
            pos = self.ivl.focus()
            pos[self.axis] = value
            self.ivl.set_focus(pos)
 
    def set_size(self, size):
        try:
            self.slider.blockSignals(True)
            self.spin.blockSignals(True)
            self.slider.setRange(0, size-1)
            self.spin.setMaximum(size-1)
        finally:
            self.slider.blockSignals(False)
            self.spin.blockSignals(False)

    def set_pos(self, pos):
        self._pos = pos
        try:
            self.slider.blockSignals(True)
            self.spin.blockSignals(True)
            self.slider.setValue(pos)
            self.spin.setValue(pos)
        finally:
            self.slider.blockSignals(False)
            self.spin.blockSignals(False)

class DataSummary(QtGui.QWidget):
    """ Data summary bar """
    def __init__(self, ivl):
        self.opts = ivl.opts
        self.ivl = ivl

        QtGui.QWidget.__init__(self)
        hbox = QtGui.QHBoxLayout()
        hbox.setContentsMargins(0, 0, 0, 0)
        self.vol_name = QtGui.QLineEdit()
        p = self.vol_name.sizePolicy()
        p.setHorizontalPolicy(QtGui.QSizePolicy.Expanding)
        self.vol_name.setSizePolicy(p)
        hbox.addWidget(self.vol_name)
        hbox.setStretchFactor(self.vol_name, 1)
        self.vol_data = QtGui.QLineEdit()
        self.vol_data.setFixedWidth(65)
        hbox.addWidget(self.vol_data)
        self.roi_region = QtGui.QLineEdit()
        self.roi_region.setFixedWidth(30)
        hbox.addWidget(self.roi_region)
        self.ov_data = QtGui.QLineEdit()
        self.ov_data.setFixedWidth(65)
        hbox.addWidget(self.ov_data)
        self.view_options_btn = OptionsButton(self)
        hbox.addWidget(self.view_options_btn)
        self.setLayout(hbox)

        ivl.ivm.sig_main_data.connect(self._main_changed)
        ivl.sig_focus_changed.connect(self._focus_changed)

    def show_options(self):
        self.opts.show()
        self.opts.raise_()

    def _main_changed(self, data):
        name = ""
        if data is not None:
            if data.fname is not None:
                name = data.fname
            else:
                name = data.name
        self.vol_name.setText(name)

    def _focus_changed(self, pos):
        if self.ivl.ivm.main is not None:
            self.vol_data.setText(self.ivl.ivm.main.value(pos, self.ivl.grid, str=True))
        if self.ivl.ivm.current_roi is not None:
            self.roi_region.setText(self.ivl.ivm.current_roi.value(pos, self.ivl.grid, str=True))
        if self.ivl.ivm.current_data is not None:
            self.ov_data.setText(self.ivl.ivm.current_data.value(pos, self.ivl.grid, str=True))

class NavigationBox(QtGui.QGroupBox):
    """ Box containing 4D navigators """
    def __init__(self, ivl):
        self.ivl = ivl

        QtGui.QGroupBox.__init__(self, "Navigation")
        grid = QtGui.QGridLayout()
        self.setLayout(grid)

        self.navs = []
        self.navs.append(Navigator(ivl, "Axial", 2, grid, 0))
        self.navs.append(Navigator(ivl, "Sagittal", 0, grid, 1))
        self.navs.append(Navigator(ivl, "Coronal", 1, grid, 2))
        self.navs.append(Navigator(ivl, "Volume", 3, grid, 3))
        grid.setColumnStretch(0, 0)
        grid.setColumnStretch(1, 2)

        ivl.ivm.sig_main_data.connect(self._main_data_changed)
        ivl.sig_focus_changed.connect(self._focus_changed)

    def _main_data_changed(self, data):
        for nav in self.navs:
            if data is not None:
                if nav.axis < 3:
                    nav.set_size(self.ivl.grid.shape[nav.axis])
                else:
                    nav.set_size(data.nvols)
            else:
                nav.set_size(1)
            nav.set_pos(self.ivl.focus()[nav.axis])

    def _focus_changed(self, pos):
        for nav in self.navs:
            nav.set_pos(pos[nav.axis])

class RoiViewWidget(QtGui.QGroupBox):
    """ Change view options for ROI """
    def __init__(self, ivl, view):
        self.ivl = ivl
        self.ivm = ivl.ivm
        self.view = view

        QtGui.QGroupBox.__init__(self, "ROI")
        grid = QtGui.QGridLayout()
        self.setLayout(grid)

        grid.addWidget(QtGui.QLabel("ROI"), 0, 0)
        self.roi_combo = QtGui.QComboBox()
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
        self.ivm.sig_all_rois.connect(self._rois_changed)
        view.sig_changed.connect(self._update)

    def _update(self, view):
        if view is not None:
            try:
                self.roi_view_combo.blockSignals(True)
                self.roi_alpha_sld.blockSignals(True)
                self.roi_combo.blockSignals(True)

                if view.opts["shade"] and view.opts["contour"]:
                    self.roi_view_combo.setCurrentIndex(2)
                elif view.opts["shade"]:
                    self.roi_view_combo.setCurrentIndex(0)
                elif view.opts["contour"]:
                    self.roi_view_combo.setCurrentIndex(1)
                else:
                    self.roi_view_combo.setCurrentIndex(3)
                self.roi_alpha_sld.setValue(view.opts["alpha"])

                if view.data is not None:
                    idx = self.roi_combo.findText(view.data.name)
                    self.roi_combo.setCurrentIndex(idx)

            finally:
                self.roi_view_combo.blockSignals(False)
                self.roi_alpha_sld.blockSignals(False)
                self.roi_combo.blockSignals(False)

    def _combo_changed(self, idx):
        if idx >= 0:
            roi = self.roi_combo.itemText(idx)
            self.ivl.ivm.set_current_roi(roi)

    def _view_changed(self, idx):
        self.view.opts["shade"] = idx in (0, 2)
        self.view.opts["contour"] = idx in (1, 2)
        self.view.sig_changed.emit(self.view)

    def _alpha_changed(self, alpha):
        """ Set the ROI transparency """
        self.view.opts["alpha"] = alpha
        self.view.sig_changed.emit(self.view)

    def _rois_changed(self, rois):
        """ Repopulate ROI combo, without sending signals """
        try:
            self.roi_combo.blockSignals(True)
            self.roi_combo.clear()
            for roi in rois:
                self.roi_combo.addItem(roi)
            self.roi_combo.updateGeometry()
        finally:
            self.roi_combo.blockSignals(False)

class OverlayViewWidget(QtGui.QGroupBox):
    """ Change view options for ROI """
    def __init__(self, ivl, view):
        QtGui.QGroupBox.__init__(self, "Overlay")
        self.ivl = ivl
        self.ivm = ivl.ivm
        self.view = view

        grid = QtGui.QGridLayout()
        self.setLayout(grid)

        grid.addWidget(QtGui.QLabel("Overlay"), 0, 0)
        self.overlay_combo = QtGui.QComboBox()
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
        self.ivm.sig_all_data.connect(self._data_changed)
        self.view.sig_changed.connect(self._update)

    def _update(self, view):
        widgets = [self.ov_view_combo, self.ov_cmap_combo,
                   self.ov_alpha_sld, self.overlay_combo]
        try:
            for w in widgets:
                w.blockSignals(True)

            if not view.opts["visible"]:
                self.ov_view_combo.setCurrentIndex(2)
            elif view.opts["roi_only"]:
                self.ov_view_combo.setCurrentIndex(1)
            else:
                self.ov_view_combo.setCurrentIndex(0)

            # 'Custom' only appears as a flag to indicate the user has messed with the 
            # LUT using the histogram widget. Otherwise is is hidden
            cmap = view.opts["cmap"]
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
                idx = self.ov_cmap_combo.findText(view.opts["cmap"])
                self.ov_cmap_combo.setCurrentIndex(idx)

            self.ov_alpha_sld.setValue(view.opts["alpha"])

            self.ov_levels_btn.setEnabled(view.data is not None)
            if view.data is not None:
                idx = self.overlay_combo.findText(view.data.name)
                debug("New current data: ", view.data.name, idx)
                self.overlay_combo.setCurrentIndex(idx)
            else:
                self.overlay_combo.setCurrentIndex(-1)

        finally:
            for w in widgets:
                w.blockSignals(False)

    def _combo_changed(self, idx):
        if idx >= 0:
            ov = self.overlay_combo.itemText(idx)
            self.ivm.set_current_data(ov)

    def _cmap_changed(self, idx):
        cmap = self.ov_cmap_combo.itemText(idx)
        self.view.opts["cmap"] = cmap
        self.view.sig_changed.emit(self.view)

    def _view_changed(self, idx):
        """ Viewing style (all or within ROI only) changed """
        self.view.opts["visible"] = idx in (0, 1)
        self.view.opts["roi_only"] = (idx == 1)
        self.view.sig_changed.emit(self.view)

    def _alpha_changed(self, alpha):
        """ Set the data transparency """
        self.view.opts["alpha"] = alpha
        self.view.sig_changed.emit(self.view)

    def _show_ov_levels(self):
        dlg = LevelsDialog(self, self.ivm, self.view)
        dlg.exec_()

    def _data_changed(self, data):
        """ Repopulate data combo, without sending signals"""
        try:
            self.overlay_combo.blockSignals(True)
            self.overlay_combo.clear()
            for ov in data:
                self.overlay_combo.addItem(ov)
            self.overlay_combo.updateGeometry()
        finally:
            self.overlay_combo.blockSignals(False)

class LevelsDialog(QtGui.QDialog):

    def __init__(self, parent, ivm, view):
        super(LevelsDialog, self).__init__(parent)
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
        self.combo.setCurrentIndex(self.view.opts["boundary"])
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
        spin.setValue(self.view.opts["cmap_range"][row])
        spin.valueChanged.connect(self._val_changed(row))
        grid.addWidget(spin, row, 1)
        return spin

    def _val_changed(self, row):
        def val_changed(val):
            self.view.opts["cmap_range"][row] = val
            self.view.sig_changed.emit(self.view)
        return val_changed

    def _bound_changed(self, idx):
        self.view.opts["boundary"] = idx
        self.view.sig_changed.emit(self.view)
    
    def _reset(self):
        percentile = float(100 - self.percentile_spin.value()) / 2
        cmin, cmax = list(self.view.data.range)
        if percentile > 0:
            if self.use_roi.isChecked() and self.ivm.current_roi is not None:
                flat = self.view.data.mask(self.ivm.current_roi, output_flat=True)
            else:
                flat = self.view.data.raw().reshape(-1)    
            cmin = np.percentile(flat, percentile)
            cmax = np.percentile(flat, 100-percentile)
        self.min_spin.setValue(cmin)
        self.max_spin.setValue(cmax)
        self.view.opts["cmap_range"] = [cmin, cmax]
        self.view.sig_changed.emit(self.view)

class ImageView(QtGui.QSplitter):
    """
    Widget containing three orthogonal slice views, two histogram/LUT widgets plus 
    navigation sliders and data summary view.

    :ivar grid: Grid the ImageView uses as the basis for the orthogonal slices. 
                This is typically an RAS-aligned version of the main data grid, or
                alternatively an RAS world-grid
    """

    # Signals when point of focus is changed
    sig_focus_changed = QtCore.Signal(tuple)

    # Signals when the selected points / region have changed
    sig_sel_changed = QtCore.Signal(object)

    def __init__(self, ivm, opts):
        super(ImageView, self).__init__(QtCore.Qt.Vertical)

        self.grid = DataGrid([1, 1, 1], np.identity(4))
        self._pos = [0, 0, 0, 0]

        self.ivm = ivm
        self.opts = opts
        self.ivm.sig_main_data.connect(self._main_data_changed)
        self.opts.sig_options_changed.connect(self._opts_changed)

        # Visualisation information for data and ROIs
        self.main_data_view = MainDataView(self.ivm)
        self.current_data_view = OverlayView(self.ivm)
        self.current_roi_view = RoiView(self.ivm)

        # Navigation controls layout
        control_box = QtGui.QWidget()
        vbox = QtGui.QVBoxLayout()
        control_box.setLayout(vbox)  

        # Create the navigation sliders and the ROI/Overlay view controls
        vbox.addWidget(DataSummary(self))
        hbox = QtGui.QHBoxLayout()
        self.nav_box = NavigationBox(self)
        hbox.addWidget(self.nav_box)
        self.roi_box = RoiViewWidget(self, self.current_roi_view)
        hbox.addWidget(self.roi_box)
        self.ovl_box = OverlayViewWidget(self, self.current_data_view)
        hbox.addWidget(self.ovl_box)
        vbox.addLayout(hbox)  

        # Histogram which controls colour map and levels for main volume
        self.main_data_view.histogram = MultiImageHistogramWidget(self, self.main_data_view, percentile=99)
        
        # Histogram which controls colour map and levels for data
        self.current_data_view.histogram = MultiImageHistogramWidget(self, self.current_data_view)

        # For each view window, this is the volume indices of the x, y and z axes for the view
        self.ax_map = [[0, 1, 2], [0, 2, 1], [1, 2, 0]]
        self.ax_labels = [("L", "R"), ("P", "A"), ("I", "S")]

        # Create three orthogonal views
        self.win = {}
        for i in range(3):
            win = OrthoView(self, self.ivm, self.ax_map[i], self.ax_labels)
            win.sig_pick.connect(self._pick)
            win.sig_maxmin.connect(self._toggle_maximise)
            self.win[win.zaxis] = win

        # Main graphics layout
        #gview = pg.GraphicsView(background='k')
        gview = QtGui.QWidget()
        self.layout_grid = QtGui.QGridLayout()
        self.layout_grid.setHorizontalSpacing(2)
        self.layout_grid.setVerticalSpacing(2)
        self.layout_grid.setContentsMargins(0, 0, 0, 0)
        self.layout_grid.addWidget(self.win[1], 0, 0,)
        self.layout_grid.addWidget(self.win[0], 0, 1)
        self.layout_grid.addWidget(self.main_data_view.histogram, 0, 2)
        self.layout_grid.addWidget(self.win[2], 1, 0)
        self.layout_grid.addWidget(self.current_data_view.histogram, 1, 2)
        self.layout_grid.setColumnStretch(0, 3)
        self.layout_grid.setColumnStretch(1, 3)
        self.layout_grid.setColumnStretch(2, 1)
        self.layout_grid.setRowStretch(0, 1)
        self.layout_grid.setRowStretch(1, 1)
        gview.setLayout(self.layout_grid)
        self.addWidget(gview)
        self.addWidget(control_box)
        self.setStretchFactor(0, 5)
        self.setStretchFactor(1, 1)

        self.picker = PointPicker(self) 
        self.drag_mode = DragMode.DEFAULT
      
    def focus(self, grid=None):
        """
        Get the current focus position

        :param grid: Report position using co-ordinates relative to this grid. 
                     If not specified, report current view grid co-ordinates
        :return: 4D sequence containing position plus the current data volume index
        """
        if grid is None:
            return list(self._pos)
        else:
            world = self.grid.grid_to_world(self._pos[:3])
            return list(grid.world_to_grid(world)) + [self._pos[3], ]

    def set_focus(self, pos, grid=None):
        """
        Set the current focus position

        :param grid: Specify position using co-ordinates relative to this grid. 
                     If not specified, position is in current view grid co-ordinates
        """
        if grid is not None:
            world = grid.grid_to_world(pos[:3])
            pos = list(self.grid.world_to_grid(world)) + [pos[3], ]

        self._pos = list(pos)
        debug("Cursor position: ", self._pos)
        self.sig_focus_changed.emit(self._pos)

    def set_picker(self, pickmode, drag_mode=DragMode.DEFAULT):
        self.picker.cleanup()
        self.picker = PICKERS[pickmode](self)
        self.drag_mode = drag_mode
        
    def capture_view_as_image(self, window, outputfile):
        """ Export an image using pyqtgraph """
        if window not in (1, 2, 3):
            raise RuntimeError("No such window: %i" % window)

        expimg = self.win[window-1].img
        exporter = ImageExporter(expimg)
        exporter.parameters()['width'] = 2000
        exporter.export(str(outputfile))

    def _pick(self, pos, win):
        if self.picker.win is not None and win != self.picker.win:
            # Bit of a hack. Ban focus changes in other windows when we 
            # have a single-window picker because it will change the slice 
            # visible in the pick window
            return
        self.picker.add_point(pos, win)

    def _toggle_maximise(self, win, state=-1):
        """ 
        Maximise/Minimise view window
        If state=1, maximise, 0=show all, -1=toggle 
        """
        o1 = (win+1) % 3
        o2 = (win+2) % 3
        if state == 1 or (state == -1 and self.win[o1].isVisible()):
            # Maximise
            self.layout_grid.addWidget(self.win[win], 0, 0, 2, 2)
            self.win[o1].setVisible(False)
            self.win[o2].setVisible(False)
            self.win[win].setVisible(True)
        elif state == 0 or (state == -1 and not self.win[o1].isVisible()):
            # Show all three
            self.layout_grid.addWidget(self.win[1], 0, 0, )
            self.layout_grid.addWidget(self.win[0], 0, 1)
            self.layout_grid.addWidget(self.win[2], 1, 0)
            self.win[o1].setVisible(True)
            self.win[o2].setVisible(True)
            self.win[win].setVisible(True)

    def _opts_changed(self):
        z_roi = int(self.opts.display_order == self.opts.ROI_ON_TOP)
        self.current_roi_view.opts["z_value"] = img.setZValue(z_roi)
        self.current_data_view.opts["z_value"] = img.setZValue(1-z_roi)

    def _main_data_changed(self, data):
        if data is not None:
            self.grid = data.grid.get_standard()
            debug("Main data raw grid")
            debug(data.grid.affine)
            debug("RAS aligned")
            debug(self.grid.affine)

            # If one of the dimensions has size 1 the data is 2D so
            # maximise the relevant slice
            # FIXME
            #self._toggle_maximise(0, state=0)
            #for d in range(3):
            #    if self.grid.shape[d] == 1:
            #        self._toggle_maximise(d, state=1)
