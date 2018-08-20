"""
Quantiphyse - Widgets allowing the user to build simple ROIs

A new ROI is based on the grid of an existing data set - chosen by the user.

Copyright (c) 2013-2018 University of Oxford
"""

from __future__ import division, unicode_literals, absolute_import, print_function

import collections

import numpy as np

from PySide import QtGui

from quantiphyse.data import NumpyData
from quantiphyse.gui.options import DataOption
from quantiphyse.gui.widgets import QpWidget, TitleWidget
from quantiphyse.gui.pickers import PickMode
from quantiphyse.utils import get_icon

from .tools import CrosshairsTool, PenTool, WalkerTool, EraserTool, RectTool, EllipseTool, PolygonTool, PickTool, BucketTool

DESC = """
Widget for creating test ROIs and basic manual segmentation
"""

TOOLS = [CrosshairsTool(), PenTool(), WalkerTool(), EraserTool(), RectTool(), EllipseTool(), PolygonTool(), PickTool(), BucketTool()]

class RoiBuilderWidget(QpWidget):
    """
    Widget for building ROIs
    """

    ADD = 1
    ERASE = 2
    MASK = 3

    def __init__(self, **kwargs):
        super(RoiBuilderWidget, self).__init__(name="ROI Builder", icon="roi_builder", desc=DESC,  
                                               group="ROIs", **kwargs)
        self._history = collections.deque(maxlen=10)
        self._label = 1
        self._tool = None
        self.grid = None

    def init_ui(self):
        layout = QtGui.QVBoxLayout()
        
        title = TitleWidget(self, help="roibuilder", batch_btn=False)
        layout.addWidget(title)

        # Generic options
        hbox = QtGui.QHBoxLayout()

        optbox = QtGui.QGroupBox()
        optbox.setTitle("Options")
        grid = QtGui.QGridLayout()
        optbox.setLayout(grid)

        grid.addWidget(QtGui.QLabel("Data space for new ROI"), 0, 0)
        self.base_data = DataOption(self.ivm)
        self.base_data.sig_changed.connect(self._set_grid)
        grid.addWidget(self.base_data, 0, 1)

        grid.addWidget(QtGui.QLabel("ROI name"), 1, 0)
        self.name_edit = QtGui.QLineEdit("ROI_BUILDER")
        self.name_edit.editingFinished.connect(self._roi_name_changed)
        grid.addWidget(self.name_edit, 1, 1)

        grid.addWidget(QtGui.QLabel("Current label"), 2, 0)
        self.label_spin = QtGui.QSpinBox()
        self.label_spin.setMinimum(1)
        self.label_spin.valueChanged.connect(self._label_changed)
        grid.addWidget(self.label_spin, 2, 1)

        self.undo_btn = QtGui.QPushButton("Undo last change")
        self.undo_btn.clicked.connect(self.undo)
        self.undo_btn.setEnabled(False)
        grid.addWidget(self.undo_btn, 3, 0)

        hbox.addWidget(optbox)
        hbox.addStretch(1)
        layout.addLayout(hbox)

        # Add toolbox buttons in a grid
        hbox = QtGui.QHBoxLayout()
        toolbox = QtGui.QGroupBox()
        toolbox.setTitle("Toolbox")
        self.tools_grid = QtGui.QGridLayout()
        toolbox.setLayout(self.tools_grid)

        x, y, cols = 0, 0, 4
        for tool in TOOLS:
            self._add_tool(tool, y, x)
            x += 1
            if x == cols:
                y += 1
                x = 0

        hbox.addWidget(toolbox)
        hbox.addStretch(1)
        layout.addLayout(hbox)

        # Tool options box - initially invisible
        hbox = QtGui.QHBoxLayout()
        self._tool_options = QtGui.QGroupBox()
        self._tool_options.setVisible(False)

        hbox.addWidget(self._tool_options)
        hbox.addStretch(1)
        layout.addLayout(hbox)

        layout.addStretch(1)
        self.setLayout(layout)

    def activate(self):
        self._set_grid()
        self._roi_name_changed()
        self.ivl.set_picker(PickMode.SINGLE)
        if self._tool is not None:
            self._tool.selected()

    def deactivate(self):
        self.ivl.set_picker(PickMode.SINGLE)
        if self._tool is not None:
            self._tool.deselected()

    def modify(self, vol=None, slice2d=None, points=None, mode=None):
        """
        Make a change to the ROI we are building

        :param roi_new: Numpy array containing the updated ROI data on the current base grid
        :param vol: 3D Numpy array containing updated ROI data on the current base grid
        :param slice2d: Tuple of (2D Numpy array, axis index, position) for 2D slice based ROI data 
        :param axis: If specified, roi_new contains a slice normal to this axis
        :param pos: If specified, roi_new contains a slice in this position
        :param erase: If True, the specified data will be used to erase ROI regions rather 
                      than add to them
        """
        # Get a Numpy array of the ROI we are building on the current base grid
        roi_orig = self._get_roidata()

        slices = [slice(None)] * 3
        if vol is not None:
            data_new = vol
            data_orig = roi_orig
        elif slice2d is not None:
            # Update the slices to identify the part of the ROI we are affecting
            data_new, axis, pos = slice2d
            slices[axis] = pos
            data_orig = roi_orig[slices]
        elif points is not None:
            data_new = np.zeros(roi_orig.shape)
            for point in points:
                data_new[point[0], point[1], point[2]] = 1
            data_orig = roi_orig
        else:
            raise ValueError("Neither volume nor slice nor points provided")

        # Save the previous state of the data in the history list
        self._history.append((np.copy(data_orig), slices))

        if mode == self.ADD:
            self.debug("Adding: %i", np.count_nonzero(data_new))
            data_orig[data_new > 0] = self._label
        elif mode == self.ERASE:
            self.debug("Erasing: %i", np.count_nonzero(data_new))
            data_orig[data_new > 0] = 0
        elif mode == self.MASK:
            self.debug("Masking: %i", np.count_nonzero(data_new))
            data_orig[data_new == 0] = 0
        else:
            raise ValueError("Invalid mode: %i" % mode)
        
        roi_orig[slices] = data_orig

        self.ivm.add_roi(NumpyData(roi_orig, grid=self.grid, name=self.roi_name), make_current=True)
        self.undo_btn.setEnabled(True)

    def undo(self):
        """
        Undo the last change
        """
        self.debug("ROI undo: %i", len(self._history))
        if not self._history: 
            return

        data_prev, slices = self._history.pop()
        roidata = self._get_roidata()
        roidata[slices] = data_prev
        self.ivm.add_roi(NumpyData(roidata, grid=self.grid, name=self.roi_name), make_current=True)
        self.undo_btn.setEnabled(len(self._history) > 0)
      
    def _label_changed(self, label):
        self._label = label
        
    def _roi_name_changed(self):
        self.roi_name = self.name_edit.text()
        # Throw away old history. FIXME is this right, should we keep existing data and history?
        # Also should we cache old history in case we go back to this ROI?
        self._history = []
        self.undo_btn.setEnabled(False)
        
    def _set_grid(self):
        self.grid = None
        data_name = self.base_data.value
        if data_name is not None:
            base_data = self.ivm.data.get(data_name, self.ivm.rois.get(data_name, None))
            if base_data:
                self.grid = base_data.grid
        
        # Need to throw away history as it is defined on the old grid
        self._history = []
        self.undo_btn.setEnabled(False)

    def _get_roidata(self):
        if self.roi_name in self.ivm.rois:
            return self.ivm.rois[self.roi_name].resample(self.grid).raw()
        else:
            return np.zeros(self.grid.shape)

    def _tool_selected(self, tool):
        def _select():
            if self.ivm.main is None:
                return

            if self._tool is not None:
                self._tool.btn.setStyleSheet("")
                self._tool.deselected()
            
            self._tool = tool
            self._tool.btn.setStyleSheet("border: 2px solid QLinearGradient( x1: 0, y1: 0, x2: 0, y2: 1, stop: 0 #ffa02f, stop: 1 #d7801a);")
            self._tool.selected()
            # Replace the old tool options with the new one. Need to reparent the
            # existing layout to a temporary widget which will then get deleted 
            QtGui.QWidget().setLayout(self._tool_options.layout())
            self._tool_options.setLayout(self._tool.interface())
            self._tool_options.setTitle(tool.name)
            self._tool_options.setVisible(True)

        return _select
    
    def _add_tool(self, tool, x, y):
        tool.ivm = self.ivm
        tool.ivl = self.ivl
        tool.builder = self
        btn = QtGui.QPushButton()
        btn.setIcon(QtGui.QIcon(get_icon(tool.name.lower())))
        btn.setToolTip(tool.tooltip)
        btn.setFixedSize(32, 32)
        btn.clicked.connect(self._tool_selected(tool))
        tool.btn = btn
        self.tools_grid.addWidget(btn, x, y)
