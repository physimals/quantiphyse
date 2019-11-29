"""
Quantiphyse - Viewer for 3D and 4D data

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

try:
    from PySide import QtGui, QtCore
except ImportError:
    from PySide2 import QtGui, QtCore

import numpy as np

from quantiphyse.utils import LogSource
from quantiphyse.data.qpdata import DataGrid

from .pickers import PICKERS, PointPicker
from .slice_viewer import OrthoSliceViewer
from .histogram_widget import MultiImageHistogramWidget
from .view_params_widget import DataViewParamsWidget
from .navigators import NavigationBox

class Viewer(QtGui.QSplitter, LogSource):
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

    :ivar grid: Grid the Viewer uses as the basis for the orthogonal slices.
                This is typically an RAS-aligned version of the main data grid, or
                alternatively an RAS world-grid
    """

    # Signal emitted when point of focus is changed
    sig_focus_changed = QtCore.Signal(list)

    # Signal emitted when point of focus is changed
    sig_grid_changed = QtCore.Signal(object)

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

        self.ivm = ivm
        self._opts = opts
        self._grid = DataGrid([1, 1, 1], np.identity(4))
        self._focus = [0, 0, 0, 0]
        self._arrows = []
        self._picker = PointPicker(self)

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
        ovl_box = DataViewParamsWidget(self)
        hbox.addWidget(ovl_box)
        vbox.addLayout(hbox)

        # Overall layout with the viewers above and the controls below
        self.addWidget(gview)
        self.addWidget(control_box)
        self.setStretchFactor(0, 5)
        self.setStretchFactor(1, 1)

        # Connect to signals
        self.ivm.sig_main_data.connect(self._main_data_changed)
        #self._opts.sig_options_changed.connect(self._opts_changed)

    @property
    def picker(self):
        """ Current picker object """
        return self._picker

    @property
    def grid(self):
        """ DataGrid object used as the fundamental grid for the viewer """
        return self._grid

    @property
    def arrows(self):
        """ Sequence of arrows defined by the viewer """
        return self._arrows

    def focus(self, grid=None):
        """
        Get the current focus position

        :param grid: Report position using co-ordinates relative to this grid.
                     If not specified, report current view grid co-ordinates
        :return: 4D sequence containing position plus the current data volume index
        """
        if grid is None:
            return list(self._focus)
        else:
            world = self._grid.grid_to_world(self._focus)
            return list(grid.world_to_grid(world))

    def set_focus(self, pos, grid=None):
        """
        Set the current focus position

        :param grid: Specify position using co-ordinates relative to this grid.
                     If not specified, position is in current view grid co-ordinates
        """
        if grid is not None:
            world = grid.grid_to_world(pos)
            pos = self._grid.world_to_grid(world)

        self._focus = list(pos)
        if len(self._focus) != 4:
            raise Exception("Position must be 4D")

        self.debug("Cursor position: %s", self._focus)
        self.sig_focus_changed.emit(self._focus)

    def set_pickmode(self, pickmode):
        """
        Set the picking mode

        :param pickmode: Picking mode from :class:`PickMode`
        """
        self._picker.cleanup()
        self._picker = PICKERS[pickmode](self)
        self.sig_picker_changed.emit(self._picker)

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
            pos = self._grid.world_to_grid(world)

        if col is None:
            # Default to grey arrow
            col = [127, 127, 127]

        self._arrows.append((pos, col))
        self.sig_arrows_changed.emit(self._arrows)

    def remove_arrows(self):
        """
        Remove all the arrows that have been placed
        """
        self._arrows = []
        self.sig_arrows_changed.emit(self._arrows)

    def _pick(self, win, pos):
        """
        Called when a point is picked in one of the viewing windows
        """
        self._picker.pick(win, pos)
        self.sig_selection_changed.emit(self._picker)

    def _drag(self, win, pos):
        """
        Called when a drag selection is changed in one of the viewing windows
        """
        self._picker.drag(win, pos)
        self.sig_selection_changed.emit(self._picker)

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

    def _main_data_changed(self, data):
        if data is not None:
            self._grid = data.grid.get_standard()
            self.debug("Main data raw grid")
            self.debug(data.grid.affine)
            self.debug("RAS aligned")
            self.debug(self._grid.affine)

            # HACK force a change of focus
            self.set_focus([0, 0, 0, data.nvols], grid=data.grid)
            initial_focus = [float(int(v/2)) for v in data.grid.shape] + [int(data.nvols/2)]
            self.debug("Initial focus (data): %s", initial_focus)
            self.set_focus(initial_focus, grid=data.grid)
            self.debug("Initial focus (std): %s", self._focus)

            # If one of the dimensions has size 1 the data is 2D so
            # maximise the relevant slice. If not, go to standard
            # 3-slice view
            self._toggle_maximise(0, state=0)
            data_axes = data.grid.get_ras_axes()
            for idx in range(3):
                if data.grid.shape[data_axes[idx]] == 1:
                    self._toggle_maximise(idx, state=1)

            self.sig_grid_changed.emit(self._grid)
