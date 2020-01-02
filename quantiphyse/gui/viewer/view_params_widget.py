"""
Quantiphyse - widget which allows a data sets view metadata to be changed

The widget automatically switches to show the 'current' data, whether it is
currently visible or not.

Copyright (c) 2013-2019 University of Oxford
"""

from __future__ import division, unicode_literals, absolute_import, print_function

import logging

try:
    from PySide import QtGui, QtCore, QtGui as QtWidgets
except ImportError:
    from PySide2 import QtGui, QtCore, QtWidgets

from quantiphyse.utils import get_icon, sf
from quantiphyse.utils.enums import Visibility
from quantiphyse.gui.widgets import RoiCombo, OverlayCombo
from quantiphyse.gui.options import OptionBox, DataOption, ChoiceOption, NumericOption, TextOption

LOG = logging.getLogger(__name__)

def no_update(f):
    def wrapper(self, *args, **kwargs):
        try:
            self._no_update = True
            f(self, *args, **kwargs)
        finally:
            self._no_update = False
    return wrapper

class ViewParamsWidget(OptionBox):

    def __init__(self, ivl, rois=True, data=True):
        OptionBox.__init__(self, border=True)
        self.ivl = ivl
        self.ivm = ivl.ivm
        self._qpdata = None
        self._no_update = False
        self.grid.setVerticalSpacing(2)

        self._view_btn = QtGui.QPushButton()
        self._view_btn.setIcon(QtGui.QIcon(get_icon("visible.png")))
        self._view_btn.setFixedSize(16, 16)
        self._view_btn.setToolTip("Visibility")
        self._view_btn.clicked.connect(self._view_btn_clicked)
        self._data = self.add("Data" if data else "ROI", DataOption(self.ivm, data=data, rois=rois, follow_current=True), self._view_btn, key="data")
        self._view_roi = self.add("View ROI", DataOption(self.ivm, data=False, rois=True), checked=True, key="view_roi")
        self._levels_btn = QtGui.QPushButton()
        self._levels_btn.setIcon(QtGui.QIcon(get_icon("levels.png")))
        self._levels_btn.setFixedSize(16, 16)
        self._levels_btn.setToolTip("Adjust colour map levels")
        self._levels_btn.clicked.connect(self._levels_clicked)
        self._cmap = self.add("Colour map", ChoiceOption(["jet", "hot", "gist_heat", "flame", "bipolar", "spectrum", "custom"]), self._levels_btn, key="cmap")
        self._alpha = self.add("Alpha", NumericOption(minval=0, maxval=255, default=255, edit=False, intonly=True), key="alpha")
        self._value_label = QtGui.QLabel()
        self.add("Value", self._value_label)
        self.add("", stretch=2)

        self._data.sig_changed.connect(self._data_changed)
        self._view_roi.sig_changed.connect(self._view_roi_changed)
        self._cmap.sig_changed.connect(self._cmap_changed)
        self._alpha.sig_changed.connect(self._alpha_changed)
        self.ivl.sig_focus_changed.connect(self._focus_changed)
        self.qpdata = None

    @property
    def qpdata(self):
        return self._qpdata

    @qpdata.setter
    def qpdata(self, qpdata):
        if self._qpdata is not None:
            self._qpdata.view.sig_changed.disconnect(self._view_md_changed)

        self._qpdata = qpdata

        self.option("alpha").setEnabled(qpdata is not None)
        self._view_btn.setEnabled(qpdata is not None)
        self.set_visible("cmap", qpdata is not None and not qpdata.roi)
        self._levels_btn.setVisible(qpdata is not None and not qpdata.roi)
        self.set_visible("view_roi", qpdata is not None and not qpdata.roi)

        if self._qpdata is not None:
            self._qpdata.view.sig_changed.connect(self._view_md_changed)
            self._view_md_changed()
            self.option("data").value = self._qpdata.name

    def _view_md_changed(self, _key=None, _value=None):
        if not self._no_update:
            try:
                self.blockSignals(True)
                if self._qpdata is not None:
                    self.option("alpha").value = self._qpdata.view.alpha

                    if not self._qpdata.roi:
                        self.set_checked("view_roi", bool(self._qpdata.view.roi))
                        if self._qpdata.view.roi:
                            self.option("view_roi").value = self._qpdata.view.roi
                        self.option("cmap").value = self._qpdata.view.cmap
                    self._view_btn.setIcon(self._get_visibility_icon())
            finally:
                self.blockSignals(False)

    def _data_changed(self):
        self.qpdata = self.ivm.data.get(self.option("data").value, None)
        if self.qpdata is not None:
            self.ivm.set_current_data(self.qpdata.name)

    @no_update
    def _view_roi_changed(self):
        if self._qpdata is not None:
            self._qpdata.view.roi = None if not self.option("view_roi").isEnabled() else self.option("view_roi").value

    @no_update
    def _cmap_changed(self):
        if self._qpdata is not None:
            self._qpdata.view.cmap = self.option("cmap").value

    @no_update
    def _alpha_changed(self):
        if self._qpdata is not None:
            self._qpdata.view.alpha = self.option("alpha").value

    def _levels_clicked(self):
        dlg = LevelsDialog(self, self.ivm, self.ivl, self._qpdata)
        dlg.exec_()

    def _focus_changed(self, focus):
        if self._qpdata is not None:
            value = self._qpdata.value(focus, self.ivl.grid)
            if self._qpdata.roi:
                region = int(value)
                if region == 0:
                    text = "(outside ROI)"
                else:
                    text = self._qpdata.regions.get(region, "")
                if text == "":
                    text = "1"
            else:
                text = sf(value, 4)
            self._value_label.setText(text)

    def _view_btn_clicked(self):
        if self._qpdata.roi:
            if self._qpdata.view.visible == Visibility.HIDE:
                vis, shade, contour = Visibility.SHOW, True, False
            elif self._qpdata.view.shade and not self._qpdata.view.contour:
                vis, shade, contour = Visibility.SHOW, True, True
            elif self._qpdata.view.shade and self._qpdata.view.contour:
                vis, shade, contour = Visibility.SHOW, False, True
            else:
                vis, shade, contour = Visibility.HIDE, True, False

            self._qpdata.view.visible = vis
            self._qpdata.view.shade = shade
            self._qpdata.view.contour = contour
        else:
            currently_visible = self._qpdata.view.visible == Visibility.SHOW
            self._qpdata.view.visible = Visibility.SHOW if not currently_visible else Visibility.HIDE

    def _get_visibility_icon(self):
        if self._qpdata.view.visible == Visibility.HIDE:
            icon = "invisible.png"
        elif self._qpdata.roi:
            if self._qpdata.view.contour and self._qpdata.view.shade:
                icon = "shade_contour.png"
            elif self._qpdata.view.contour:
                icon = "contour.png"
            elif self._qpdata.view.shade:
                icon = "shade.png"
            else:
                icon = "invisible.png"
        else:
            icon = "visible.png"
            
        return QtGui.QIcon(get_icon(icon))

class LevelsDialog(QtGui.QDialog):
    """
    Dialog box used to set the colourmap max/min for a data view
    """

    def __init__(self, parent, ivm, ivl, qpdata):
        super(LevelsDialog, self).__init__(parent)
        self.ivm = ivm
        self.ivl = ivl
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
        if self._qpdata.view.roi:
            roi = self.ivm.data[self._qpdata.view.roi]
        else:
            roi = None

        cmin, cmax = self._qpdata.suggest_cmap_range(vol=self.ivl.focus()[3], percentile=percentile, roi=roi)
        self.min_spin.setValue(cmin)
        self.max_spin.setValue(cmax)
        self._qpdata.view.cmap_range = [cmin, cmax]
