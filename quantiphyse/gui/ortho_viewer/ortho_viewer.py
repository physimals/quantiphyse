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

from collections import OrderedDict

try:
    from PySide import QtGui, QtCore, QtGui as QtWidgets
except ImportError:
    from PySide2 import QtGui, QtCore, QtWidgets

import numpy as np

from quantiphyse.utils import LogSource
from quantiphyse.data.qpdata import DataGrid, MetaSignaller
from quantiphyse.gui.colors import initial_cmap_range, get_lut

from .pickers import PICKERS, PointPicker
from .slice_viewer import OrthoSliceViewer
from .histogram_widget import MultiImageHistogramWidget
from .view_params_widget import DataViewParamsWidget
from .maskable_image import Boundary
from .navigators import NavigationBox

MAIN_DATA = ""

DEFAULT_MAIN_VIEW = {
    "visible" : True,
    "roi_only" : False,
    "boundary" : Boundary.CLAMP,
    "alpha" : 255,
    "z_value" : -999,
    "interp_order" : 0,
    "cmap" : "grey",
}

DEFAULT_DATA_VIEW = {
    "visible" : True,
    "roi_only" : False,
    "boundary" : Boundary.TRANS,
    "alpha" : 255,
    "interp_order" : 0,
    "cmap" : "jet",
}

DEFAULT_ROI_VIEW = {
    "visible" : True,
    "alpha" : 127,
    "shade" : True,
    "contour" : False,
    "interp_order" : 0,
}

class DataView(object):

    def __init__(self, defaults=None):
        self._dict = {}
        if defaults:
            self._dict.update(defaults)
        self._signaller = MetaSignaller()

    @property
    def sig_changed(self):
        """ Signals when a key's value has been changed """
        return self._signaller.sig_changed
    
    def __getattr__(self, name):
        return self._dict.get(name, None)

    def __setattr__(self, name, value):
        if name[0] == "_":
            object.__setattr__(self, name, value)
        elif self._dict.get(name, None) != value:
            self._dict[name] = value
            # Update lookup table when colormap or alpha changed
            if name == "cmap" or "lut" not in self._dict:
                self._dict["lut"] = get_lut(self.cmap, alpha=self.alpha)
            if name == "alpha":
                self._dict["lut"] = [list(rgba)[:3] + [self.alpha] for rgba in self.lut]

            self.sig_changed.emit(name, value)

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

    # Signal emitted when the view parameters on a data item are changed
    sig_data_view_changed = QtCore.Signal(str, str)
    
    def __init__(self, ivm, opts):
        LogSource.__init__(self)
        QtGui.QSplitter.__init__(self, QtCore.Qt.Vertical)

        self.grid = DataGrid([1, 1, 1], np.identity(4))
        self._pos = [0, 0, 0, 0]

        self.ivm = ivm
        self.opts = opts
        self.picker = PointPicker(self)
        self._data_views = OrderedDict()
        self._singleview = True
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
        self.ivm.sig_all_data.connect(self._data_changed)
        #self.opts.sig_options_changed.connect(self._opts_changed)

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

    
    def data_view(self, name):
        if name not in self._data_views:
            raise KeyError("No such data: %s" % name)
        else:
            return self._data_views[name]
            
    def _update_vis(self, key, value):
        # In single-view mode hide existing data of same type
        if key == "visible" and value == True and self._singleview:
            for existing_name, view in self._data_views.items():
                if existing_name != name and existing_name != MAIN_DATA and self.ivm.data[existing_name].roi == qpdata.roi:
                    view.visible = False
                    
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
            self._data_views[MAIN_DATA] = DataView(DEFAULT_MAIN_VIEW)
            self._data_views[MAIN_DATA].cmap_range = initial_cmap_range(data, 99)

            for idx in range(3):
                self.ortho_views[idx].set_grid(self.grid)
                self.ortho_views[idx].add_data_view(data, self._data_views[MAIN_DATA], name=MAIN_DATA)
                self.ortho_views[idx].reset()
                if data.grid.shape[data_axes[idx]] == 1:
                    self._toggle_maximise(idx, state=1)

    def _data_changed(self, data_names):
        new_data = [name for name in data_names if name not in self._data_views]
        removed_data = [name for name in self._data_views if name != MAIN_DATA and name not in data_names]

        for name in removed_data:
            for idx in range(3):
                self.ortho_views[idx].remove_data_view(name)

        max_z_value = max([view.z_value for view in self._data_views.values()])
        for new_idx, name in enumerate(new_data):
            qpdata = self.ivm.data[name]
            if qpdata.roi:
                self._data_views[name] = DataView(DEFAULT_ROI_VIEW)
            else:
                self._data_views[name] = DataView(DEFAULT_DATA_VIEW)

            self._data_views[name].cmap_range = initial_cmap_range(qpdata)
            self._data_views[name].z_value = max_z_value + new_idx + 1

            # Regenerate z values for remaining data
            for idx, view in enumerate(sorted(self._data_views.items(), 
                                       key=lambda view: view[1].z_value)):
                self._data_views[name].z_value = idx

            for idx in range(3):
                self.ortho_views[idx].add_data_view(qpdata, self._data_views[name])

 