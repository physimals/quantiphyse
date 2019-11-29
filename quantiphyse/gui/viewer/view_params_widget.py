"""
Quantiphyse - widget which allows a data sets view metadata to be changed

Copyright (c) 2013-2019 University of Oxford
"""

from __future__ import division, unicode_literals, absolute_import, print_function

import logging

try:
    from PySide import QtGui, QtCore, QtGui as QtWidgets
except ImportError:
    from PySide2 import QtGui, QtCore, QtWidgets

import numpy as np

from quantiphyse.data.qpdata import Visible
from quantiphyse.utils import get_icon
from quantiphyse.gui.widgets import RoiCombo, OverlayCombo

LOG = logging.getLogger(__name__)

class DataViewParamsWidget(QtGui.QGroupBox):
    """
    Change view options for data set
    """
    def __init__(self, ivl):
        QtGui.QGroupBox.__init__(self)
        self.ivm = ivl.ivm
        self._qpdata = None

        grid = QtGui.QGridLayout()
        grid.setVerticalSpacing(2)
        grid.setContentsMargins(5, 5, 5, 5)
        self.setLayout(grid)

        grid.addWidget(QtGui.QLabel("Overlay"), 0, 0)
        self.overlay_combo = OverlayCombo(self.ivm, none_option=True, set_first=True, follow_current=True)
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
        hbox.addWidget(self.ov_levels_btn)
        grid.addLayout(hbox, 2, 1)
        grid.addWidget(QtGui.QLabel("Alpha"), 3, 0)
        self.ov_alpha_sld = QtGui.QSlider(QtCore.Qt.Horizontal, self)
        self.ov_alpha_sld.setFocusPolicy(QtCore.Qt.NoFocus)
        self.ov_alpha_sld.setRange(0, 255)
        self.ov_alpha_sld.setValue(255)
        grid.addWidget(self.ov_alpha_sld, 3, 1)
        grid.setRowStretch(4, 1)

        self._widgets = [self.ov_view_combo, self.ov_cmap_combo,
                         self.ov_alpha_sld, self.overlay_combo,
                         self.ov_levels_btn]

        self.overlay_combo.currentIndexChanged.connect(self._combo_changed)
        self.ov_view_combo.currentIndexChanged.connect(self._view_changed)
        self.ov_cmap_combo.currentIndexChanged.connect(self._cmap_changed)
        self.ov_alpha_sld.valueChanged.connect(self._alpha_changed)
        self._combo_changed(-1)

    def _update_widgets(self):
        try:
            for widget in self._widgets:
                widget.blockSignals(True)

            if not self._qpdata.view.visible:
                self.ov_view_combo.setCurrentIndex(2)
            elif self._qpdata.view.roi_only:
                self.ov_view_combo.setCurrentIndex(1)
            else:
                self.ov_view_combo.setCurrentIndex(0)

            # 'Custom' only appears as a flag to indicate the user has messed with the
            # LUT using the histogram widget. Otherwise is is hidden
            cmap = self._qpdata.view.cmap
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
                idx = self.ov_cmap_combo.findText(self._qpdata.view.cmap)
                self.ov_cmap_combo.setCurrentIndex(idx)

            self.ov_alpha_sld.setValue(self._qpdata.view.alpha)

            if self._qpdata is not None:
                idx = self.overlay_combo.findText(self._qpdata.name)
                self.overlay_combo.setCurrentIndex(idx)
            else:
                self.overlay_combo.setCurrentIndex(-1)
        finally:
            for widget in self._widgets:
                widget.blockSignals(False)

    def _combo_changed(self, idx):
        if self._qpdata is not None:
            self._qpdata.view.sig_changed.disconnect(self._update_widgets)
        if idx > 0:
            self._qpdata = self.ivm.data[self.overlay_combo.itemText(idx)]
            self._qpdata.view.sig_changed.connect(self._update_widgets)
            self._update_widgets()
        else:
            self._qpdata = None
        for widget in self._widgets:
            if widget != self.overlay_combo:
                widget.setEnabled(self._qpdata is not None)

    def _cmap_changed(self, idx):
        cmap = self.ov_cmap_combo.itemText(idx)
        self._qpdata.view.cmap = cmap

    def _view_changed(self, idx):
        """ Viewing style (all or within ROI only) changed """
        if idx in (0, 1):
            self._qpdata.view.visible = Visible.VISIBLE
        else:
            self._qpdata.view.visible = Visible.INVISIBLE
        self._qpdata.view.roi_only = (idx == 1)

    def _alpha_changed(self, alpha):
        """ Set the data transparency """
        self._qpdata.view.alpha = alpha

    def _show_ov_levels(self):
        dlg = LevelsDialog(self, self.ivm, self._qpdata)
        dlg.exec_()

class LevelsDialog(QtGui.QDialog):
    """
    Dialog box used to set the colourmap max/min for a data view
    """

    def __init__(self, parent, ivm, qpdata):
        super(LevelsDialog, self).__init__(parent)
        self.ivm = ivm
        self._qpdata = qpdata

        self.setWindowTitle("Levels for %s" % self._qpdata.name)
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
        self.combo.setCurrentIndex(self._qpdata.view.boundary)
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
        spin.setValue(self._qpdata.view.cmap_range[row])
        spin.valueChanged.connect(self._val_changed(row))
        grid.addWidget(spin, row, 1)
        return spin

    def _val_changed(self, row):
        def _changed(val):
            cmap_range = list(self._qpdata.view.cmap_range)
            cmap_range[row] = val
            self._qpdata.view.cmap_range = cmap_range
        return _changed

    def _bound_changed(self, idx):
        self._qpdata.view.boundary = idx

    def _reset(self):
        percentile = self.percentile_spin.value()
        # FIXME broken
        if self.use_roi.isChecked() and self.ivm.current_roi is not None:
            flat = self._qpdata.mask(self.ivm.current_roi, output_flat=True)

        cmin, cmax = self._qpdata._cmap_range(vol=self.ivl.focus()[3], percentile=percentile)
        self.min_spin.setValue(cmin)
        self.max_spin.setValue(cmax)
        self._qpdata.view.cmap_range = [cmin, cmax]
