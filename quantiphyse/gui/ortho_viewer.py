"""
Quantiphyse - 3D orthographic viewer

Plan for multi-volume viewing

In single-overlay mode only one data / ROI visible at a time
In multi-overlay mode, multiple display possible

On loading new data/ROI, previously visible data is made invisible
Unless user had previously explicitly turned it on
'Current' data/ROI is selected from the volume overview or the overlay menu
This is the overlay which allows you to change colourmap etc and shows on the histogram

Copyright (c) 2013-2018 University of Oxford
"""

from __future__ import division, unicode_literals, absolute_import

from PySide import QtCore, QtGui
import numpy as np

from quantiphyse.utils import LogSource
from quantiphyse.data import DataGrid

from .widgets import OptionsButton
from .pickers import PICKERS, PointPicker
from .slice_viewer import OrthoSliceViewer
from .histogram_widget import MultiImageHistogramWidget

class DataSummary(QtGui.QWidget):
    """ 
    Data summary bar
    """
    def __init__(self, ivl):
        self.opts = ivl.opts
        self.ivl = ivl

        QtGui.QWidget.__init__(self)
        hbox = QtGui.QHBoxLayout()
        hbox.setContentsMargins(0, 0, 0, 0)
        self.vol_name = QtGui.QLineEdit()
        policy = self.vol_name.sizePolicy()
        policy.setHorizontalPolicy(QtGui.QSizePolicy.Expanding)
        self.vol_name.setSizePolicy(policy)
        hbox.addWidget(self.vol_name)
        hbox.setStretchFactor(self.vol_name, 1)
        self.vol_data = QtGui.QLineEdit()
        self.vol_data.setFixedWidth(70)
        hbox.addWidget(self.vol_data)
        self.roi_region = QtGui.QLineEdit()
        self.roi_region.setFixedWidth(70)
        hbox.addWidget(self.roi_region)
        self.ov_data = QtGui.QLineEdit()
        self.ov_data.setFixedWidth(70)
        hbox.addWidget(self.ov_data)
        self.view_options_btn = OptionsButton(self)
        hbox.addWidget(self.view_options_btn)
        self.setLayout(hbox)

        ivl.ivm.sig_main_data.connect(self._main_changed)
        ivl.sig_focus_changed.connect(self._update)
        ivl.ivm.sig_current_data.connect(self._update)

    def show_options(self):
        """
        Show the view options dialog
        """
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
        self._update()

    def _update(self):
        pos, grid = self.ivl.focus(), self.ivl.grid
        main, roi, data = self.ivl.ivm.main, self.ivl.ivm.current_roi, self.ivl.ivm.current_data
        if main is not None:
            self.vol_data.setText(main.value(pos, grid, as_str=True))
        if roi is not None:
            roi_value = roi.regions.get(int(roi.value(pos, grid)), "")
            if roi_value == "":
                roi_value = "1"
            self.roi_region.setText(roi_value)
        if data is not None:
            self.ov_data.setText(data.value(pos, grid, as_str=True))

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

class OrthoViewer(QtGui.QSplitter, LogSource):
    """
    Widget containing three orthogonal slice views, two histogram/LUT widgets plus
    navigation sliders and data summary view.

    The viewer maintains two main pieces of data: a grid defining the main co-ordinate
    system of the viewer and a point of focus, in co-ordinates relative to the viewing grid.

    In addition, the viewer supports 'arrows' to mark positions in space, and variable
    pickers which control the selection of data.

    The grid is generally either a straightforward 1mm RAS grid, or an approximate RAS grid
    derived from the grid of the main data. Although the focus position is provided and set
    according to this grid by default, the ``focus`` and ``set_focus`` methods allow for
    the co-ordinates to be set or retrieved according to another arbitrary grid.

    :ivar grid: Grid the OrthoViewer uses as the basis for the orthogonal slices.
                This is typically an RAS-aligned version of the main data grid, or
                alternatively an RAS world-grid
    """

    # Signal emitted when point of focus is changed
    sig_focus_changed = QtCore.Signal(list)

    # Signal emitted when the set of marker arrows has changed
    sig_arrows_changed = QtCore.Signal(list)

    # Signal emitted when the picker mode is changed
    sig_picker_changed = QtCore.Signal(object)

    # Signale mitted when the set of selected points is changed.
    # Emission of this signal depends on the picking mode selected
    sig_selection_changed = QtCore.Signal(object)

    def __init__(self, ivm, opts):
        LogSource.__init__(self)
        QtGui.QSplitter.__init__(self, QtCore.Qt.Vertical)

        self.grid = DataGrid([1, 1, 1], np.identity(4))
        self._pos = [0, 0, 0, 0]

        self.ivm = ivm
        self.opts = opts
        self.picker = PointPicker(self)
        self.arrows = []

        # Create three orthogonal slice viewers
        # For each viewer, we pass the xyz axis mappings and the labels
        ax_map = [[0, 1, 2], [0, 2, 1], [1, 2, 0]]
        ax_labels = [("L", "R"), ("P", "A"), ("I", "S")]
        self.ortho_views = {}
        for i in range(3):
            win = OrthoSliceViewer(self, self.ivm, ax_map[i], ax_labels)
            win.sig_pick.connect(self._pick)
            win.sig_drag.connect(self._drag)
            win.sig_doubleclick.connect(self._toggle_maximise)
            self.ortho_views[win.zaxis] = win

        # Histogram which controls colour map and levels for main volume
        self.main_histogram = MultiImageHistogramWidget()

        # Histogram which controls colour map and levels for the current data
        self.data_histogram = MultiImageHistogramWidget()

        # Layout of the ortho slice viewers and histograms
        gview = QtGui.QWidget()
        self.layout_grid = QtGui.QGridLayout()
        gview.setLayout(self.layout_grid)

        self.layout_grid.setHorizontalSpacing(2)
        self.layout_grid.setVerticalSpacing(2)
        self.layout_grid.setContentsMargins(0, 0, 0, 0)
        self.layout_grid.addWidget(self.ortho_views[1], 0, 0,)
        self.layout_grid.addWidget(self.ortho_views[0], 0, 1)
        self.layout_grid.addWidget(self.ortho_views[2], 1, 0)
        self.layout_grid.addWidget(self.main_histogram, 0, 2)
        self.layout_grid.addWidget(self.data_histogram, 1, 2)
        self.layout_grid.setColumnStretch(0, 3)
        self.layout_grid.setColumnStretch(1, 3)
        self.layout_grid.setColumnStretch(2, 1)
        self.layout_grid.setRowStretch(0, 1)
        self.layout_grid.setRowStretch(1, 1)

        # Navigation controls layout
        control_box = QtGui.QWidget()
        vbox = QtGui.QVBoxLayout()
        vbox.setSpacing(5)
        control_box.setLayout(vbox)

        # Navigation sliders and the ROI/Overlay view controls
        #vbox.addWidget(DataSummary(self))
        hbox = QtGui.QHBoxLayout()
        nav_box = NavigationBox(self)
        hbox.addWidget(nav_box)
        #roi_box = RoiViewWidget(self, self.current_roi_view)
        #hbox.addWidget(roi_box)
        #ovl_box = OverlayViewWidget(self, self.current_data_view)
        #hbox.addWidget(ovl_box)
        vbox.addLayout(hbox)

        # Overall layout with the viewers above and the controls below
        self.addWidget(gview)
        self.addWidget(control_box)
        self.setStretchFactor(0, 5)
        self.setStretchFactor(1, 1)

        # Connect to signals
        self.ivm.sig_main_data.connect(self._main_data_changed)
        self.opts.sig_options_changed.connect(self._opts_changed)

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
            world = self.grid.grid_to_world(self._pos)
            return list(grid.world_to_grid(world))

    def set_focus(self, pos, grid=None):
        """
        Set the current focus position

        :param grid: Specify position using co-ordinates relative to this grid.
                     If not specified, position is in current view grid co-ordinates
        """
        if grid is not None:
            world = grid.grid_to_world(pos)
            pos = self.grid.world_to_grid(world)

        self._pos = list(pos)
        if len(self._pos) != 4:
            raise Exception("Position must be 4D")

        self.debug("Cursor position: %s", self._pos)
        self.sig_focus_changed.emit(self._pos)

    def set_picker(self, pickmode):
        """
        Set the picking mode

        :param pickmode: Picking mode from :class:`PickMode`
        """
        self.picker.cleanup()
        self.picker = PICKERS[pickmode](self)
        self.sig_picker_changed.emit(self.picker)

    def add_arrow(self, pos, grid=None, col=None):
        """
        Add an arrow to mark a particular position

        :param pos:  Position co-ordinates
        :param grid: Grid co-ordinates are relative to, if not specified
                     uses viewing grid
        :param col:  Colour as RGB sequence, if not specified uses a default
        """
        if grid is not None:
            world = grid.grid_to_world(pos)
            pos = self.grid.world_to_grid(world)

        if col is None:
            # Default to grey arrow
            col = [127, 127, 127]

        self.arrows.append((pos, col))
        self.sig_arrows_changed.emit(self.arrows)

    def remove_arrows(self):
        """
        Remove all the arrows that have been placed
        """
        self.arrows = []
        self.sig_arrows_changed.emit(self.arrows)

    def _pick(self, win, pos):
        """
        Called when a point is picked in one of the viewing windows
        """
        self.picker.pick(win, pos)
        self.sig_selection_changed.emit(self.picker)

    def _drag(self, win, pos):
        """
        Called when a drag selection is changed in one of the viewing windows
        """
        self.picker.drag(win, pos)
        self.sig_selection_changed.emit(self.picker)

    def _toggle_maximise(self, win, state=-1):
        """
        Maximise/Minimise view window
        If state=1, maximise, 0=show all, -1=toggle
        """
        win1 = (win+1) % 3
        win2 = (win+2) % 3
        if state == 1 or (state == -1 and self.ortho_views[win1].isVisible()):
            # Maximise
            self.layout_grid.addWidget(self.ortho_views[win], 0, 0, 2, 2)
            self.ortho_views[win1].setVisible(False)
            self.ortho_views[win2].setVisible(False)
            self.ortho_views[win].setVisible(True)
        elif state == 0 or (state == -1 and not self.ortho_views[win1].isVisible()):
            # Show all three
            self.layout_grid.addWidget(self.ortho_views[1], 0, 0)
            self.layout_grid.addWidget(self.ortho_views[0], 0, 1)
            self.layout_grid.addWidget(self.ortho_views[2], 1, 0)
            for oview in range(3):
                self.ortho_views[oview].setVisible(True)
                self.ortho_views[oview].update()

    def _opts_changed(self):
        # View options have been changed
        z_roi = int(self.opts.display_order == self.opts.ROI_ON_TOP)
        # FIXME
        #self.current_roi_view.set("z_value", z_roi)
        #self.current_data_view.set("z_value", 1-z_roi)
        #self.current_data_view.set("interp_order", self.opts.interp_order)

    def _main_data_changed(self, data):
        if data is not None:
            self.grid = data.grid.get_standard()
            self.debug("Main data raw grid")
            self.debug(data.grid.affine)
            self.debug("RAS aligned")
            self.debug(self.grid.affine)

            # HACK force a change of focus
            self.set_focus([0, 0, 0, data.nvols], grid=data.grid)
            initial_focus = [float(int(v/2)) for v in data.grid.shape] + [int(data.nvols/2)]
            self.debug("Initial focus (data): %s", initial_focus)
            self.set_focus(initial_focus, grid=data.grid)
            self.debug("Initial focus (std): %s", self._pos)

            # If one of the dimensions has size 1 the data is 2D so
            # maximise the relevant slice. If not, go to standard
            # 3-slice view
            self._toggle_maximise(0, state=0)
            data_axes = data.grid.get_ras_axes()
            for idx in range(3):
                self.ortho_views[idx].reset()
                if data.grid.shape[data_axes[idx]] == 1:
                    self._toggle_maximise(idx, state=1)
