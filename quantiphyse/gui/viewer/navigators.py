"""
Quantiphyse - Widgets to manipulate point of focus

Copyright (c) 2013-2018 University of Oxford
"""

from __future__ import division, unicode_literals, absolute_import

try:
    from PySide import QtGui, QtCore, QtGui as QtWidgets
except ImportError:
    from PySide2 import QtGui, QtCore, QtWidgets

from quantiphyse.utils import LogSource
from quantiphyse.gui.widgets import OptionsButton

class Navigator(LogSource):
    """
    Slider control which alters position along an axis
    """

    def __init__(self, ivl, label, axis, layout_grid, layout_ypos):
        LogSource.__init__(self)
        self.ivl = ivl
        self.axis = axis
        self.data_axis = axis
        self.data_grid = None
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

        self.ivl.ivm.sig_main_data.connect(self._main_data_changed)
        self.ivl.sig_focus_changed.connect(self._focus_changed)

    def _changed(self, value):
        if value != self._pos and self.data_grid is not None:
            pos = self.ivl.focus(self.data_grid)
            pos[self.data_axis] = value
            self.ivl.set_focus(pos, self.data_grid)

    def _main_data_changed(self, data):
        if data is not None:
            self.data_grid = data.grid
            self.data_axis = data.grid.get_ras_axes()[self.axis]

            if self.axis < 3:
                self._set_size(self.data_grid.shape[self.data_axis])
            else:
                self._set_size(data.nvols)

            self._focus_changed()
        else:
            self.data_grid = None
            self.data_axis = self.axis
            self._set_size(1)
            self._pos = 0

    def _focus_changed(self):
        if self.data_grid is not None:
            self._pos = int(self.ivl.focus(self.data_grid)[self.data_axis]+0.5)
            self.debug("Pos for slider %i %i", self.axis, self._pos)
            try:
                self.slider.blockSignals(True)
                self.spin.blockSignals(True)
                self.slider.setValue(self._pos)
                self.spin.setValue(self._pos)
            finally:
                self.slider.blockSignals(False)
                self.spin.blockSignals(False)

    def _set_size(self, size):
        try:
            self.slider.blockSignals(True)
            self.spin.blockSignals(True)
            self.slider.setRange(0, size-1)
            self.spin.setMaximum(size-1)
        finally:
            self.slider.blockSignals(False)
            self.spin.blockSignals(False)

class VolumeNavigator(Navigator):
    """
    Slider navigator control specifically for the volume axis
    """

    def __init__(self, *args, **kwargs):
        Navigator.__init__(self, label="Volume", axis=3, *args, **kwargs)
        self.ivl.ivm.sig_all_data.connect(self._data_changed)

    def _main_data_changed(self, data):
        if data is not None:
            self.data_grid = data.grid
        self._data_changed()

    def _data_changed(self):
        max_num_vols = max([d.nvols for d in self.ivl.ivm.data.values()] + [1, ])
        self._set_size(max_num_vols)
        self._focus_changed()

class NavigationBox(QtGui.QGroupBox):
    """
    Box containing 4D navigators
    """
    def __init__(self, ivl):
        QtGui.QGroupBox.__init__(self)
        self.ivl = ivl

        grid = QtGui.QGridLayout()
        grid.setVerticalSpacing(2)
        grid.setContentsMargins(5, 5, 5, 5)
        self.setLayout(grid)

        self.navs = []
        self.navs.append(Navigator(ivl, "Axial", 2, grid, 0))
        self.navs.append(Navigator(ivl, "Sagittal", 0, grid, 1))
        self.navs.append(Navigator(ivl, "Coronal", 1, grid, 2))
        self.navs.append(VolumeNavigator(ivl, layout_grid=grid, layout_ypos=3))
        grid.setColumnStretch(0, 0)
        grid.setColumnStretch(1, 2)
