"""
Quantiphyse - Widgets allowing the user to build simple ROIs

Copyright (c) 2013-2018 University of Oxford
"""

from __future__ import division, unicode_literals, absolute_import, print_function

import collections

import numpy as np

from PySide import QtGui

from quantiphyse.data import NumpyData
from quantiphyse.gui.dialogs import error_dialog
from quantiphyse.gui.widgets import QpWidget, HelpButton, TitleWidget
from quantiphyse.gui.pickers import PickMode
from quantiphyse.utils import get_icon, debug

from .tools import *

DESC = """
Widget for creating test ROIs and basic manual segmentation
"""

TOOLS = [CrosshairsTool(), PenTool(), WalkerTool(), EraserTool(), RectTool(), EllipseTool(), PolygonTool(), PickTool(), BucketTool()]

class RoiBuilderWidget(QpWidget):
    """
    Widget for building ROIs
    """

    def __init__(self, **kwargs):
        super(RoiBuilderWidget, self).__init__(name="ROI Builder", icon="roi_builder", desc=DESC,  
                                               group="ROIs", **kwargs)
        self.history = collections.deque(maxlen=10)

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

        grid.addWidget(QtGui.QLabel("ROI name"), 0, 0)
        self.name_edit = QtGui.QLineEdit("ROI_BUILDER")
        self.name_edit.editingFinished.connect(self.name_changed)
        self.new_roi_name = self.name_edit.text()
        grid.addWidget(self.name_edit, 0, 1)

        grid.addWidget(QtGui.QLabel("Current label"), 1, 0)
        self.label_spin = QtGui.QSpinBox()
        self.label_spin.setMinimum(1)
        self.label_spin.valueChanged.connect(self.label_changed)
        grid.addWidget(self.label_spin, 1, 1)

        self.undo_btn = QtGui.QPushButton("Undo last change")
        self.undo_btn.clicked.connect(self.undo)
        self.undo_btn.setEnabled(False)
        grid.addWidget(self.undo_btn, 2, 0)

        hbox.addWidget(optbox)
        hbox.addStretch(1)
        layout.addLayout(hbox)

        # Toolbox buttons
        hbox = QtGui.QHBoxLayout()
        toolbox = QtGui.QGroupBox()
        toolbox.setTitle("Toolbox")
        self.tools_grid = QtGui.QGridLayout()
        toolbox.setLayout(self.tools_grid)

        self.tool = None
        x, y, cols = 0, 0, 4
        for tool in TOOLS:
            self.add_tool(tool, y, x)
            x += 1
            if x == cols:
                y += 1
                x = 0

        hbox.addWidget(toolbox)
        hbox.addStretch(1)
        layout.addLayout(hbox)

        # Tool options box - initially invisible
        hbox = QtGui.QHBoxLayout()
        self.tool_optbox = QtGui.QGroupBox()
        self.tool_optbox.setVisible(False)

        hbox.addWidget(self.tool_optbox)
        hbox.addStretch(1)
        layout.addLayout(hbox)

        layout.addStretch(1)
        self.setLayout(layout)
        self.grid = self.ivl.grid

        self.ivm.sig_main_data.connect(self._main_data_changed)

    def activate(self):
        self._main_data_changed(self.ivm.main)
        self.ivl.set_picker(PickMode.SINGLE)
        if self.tool is not None:
            self.tool.selected()

    def deactivate(self):
        self.ivl.set_picker(PickMode.SINGLE)
        if self.tool is not None:
            self.tool.deselected()

    def _main_data_changed(self, data):
        if data is not None:
            self.grid = data.grid

    def add_tool(self, tool, x, y):
        tool.ivm = self.ivm
        tool.ivl = self.ivl
        tool.label = self.label_spin.value()
        tool.new_roi_name = self.name_edit.text()
        tool.builder = self
        btn = QtGui.QPushButton()
        btn.setIcon(QtGui.QIcon(get_icon(tool.name.lower())))
        btn.setToolTip(tool.tooltip)
        btn.setFixedSize(32, 32)
        btn.clicked.connect(self.tool_clicked(tool))
        tool.btn = btn
        self.tools_grid.addWidget(btn, x, y)

    def tool_clicked(self, tool):
        def tool_clicked():
            if self.ivm.main is None:
                return

            if self.tool is not None:
                self.tool.btn.setStyleSheet("")
                self.tool.deselected()
            
            self.tool = tool
            self.tool.btn.setStyleSheet("border: 2px solid QLinearGradient( x1: 0, y1: 0, x2: 0, y2: 1, stop: 0 #ffa02f, stop: 1 #d7801a);")
            self.tool.selected()
            # Replace the old tool options with the new one. Need to reparent the
            # existing layout to a temporary widget which will then get deleted 
            QtGui.QWidget().setLayout(self.tool_optbox.layout())
            self.tool_optbox.setLayout(self.tool.interface())
            self.tool_optbox.setTitle(tool.name)
            self.tool_optbox.setVisible(True)

        return tool_clicked
    
    def label_changed(self, label):
        for tool in TOOLS:
            tool.label = label
        
    def name_changed(self):
        self.new_roi_name = self.name_edit.text()
        if self.tool is not None:
            self.tool.new_roi_name = self.new_roi_name
      
    def add_to_roi(self, roi_new, axis=None, pos=None, erase=False):
        if self.new_roi_name in self.ivm.rois:
            roi_orig = self.ivm.rois[self.new_roi_name].resample(self.grid).raw()
        else:
            roi_orig = np.zeros(self.grid.shape)

        slices = [slice(None)] * 3
        if axis is not None and pos is not None:
            slices[axis] = pos
            slice_orig = roi_orig[slices]
            if roi_new.ndim == 3: 
                slice_new = roi_new[slices]
            else:
                slice_new = roi_new
        else:
            slice_orig = roi_orig
            slice_new = roi_new

        self.history.append((self.new_roi_name, axis, pos, np.copy(slice_orig)))
        if erase:
            slice_orig[slice_new == 0] = 0
        else:
            slice_orig[slice_new > 0] = slice_new[slice_new > 0]
            
        roi_orig[slices] = slice_orig

        debug("Num nonzero new: ", np.count_nonzero(roi_new))
        debug("Num nonzero: ", np.count_nonzero(roi_orig))
        self.ivm.add_roi(NumpyData(roi_orig, grid=self.grid, name=self.new_roi_name), make_current=True)
        self.undo_btn.setEnabled(True)

    def undo(self):
        debug("ROI undo: ", len(self.history))
        if len(self.history) == 0: return

        roi_name, axis, pos, roi_slice_orig = self.history.pop()
        debug("Undoing: ", roi_name, axis, pos)
        roi = self.ivm.rois.get(roi_name, None)
        if roi is not None:
            data = roi.raw()
            slices = [slice(None)] * 3
            if axis is not None and pos is not None:
                slices[axis] = pos
            data[slices] = roi_slice_orig
            self.ivm.add_roi(NumpyData(data, grid=roi.grid, name=roi_name), make_current=True)
        self.undo_btn.setEnabled(len(self.history) > 0)
