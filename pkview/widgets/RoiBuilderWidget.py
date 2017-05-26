"""
Author: Martin Craig
Copyright (c) 2017 University of Oxford
"""

from __future__ import division, unicode_literals, absolute_import, print_function

import numpy as np
from PySide import QtCore, QtGui

from ..QtInherit.dialogs import error_dialog
from ..QtInherit import HelpButton
from ..ImageView import PickMode, DragMode
from ..utils import get_icon
from . import PkWidget

DESC = """
Widget for creating test ROIs and basic manual segmentation
"""

class Tool:
    def __init__(self, name, tooltip=""):
        self.name = name
        self.tooltip = tooltip

    def selected(self):
        self.ivl.set_picker(PickMode.SINGLE)

    def interface(self):
        grid = QtGui.QGridLayout()
        return grid

class PolygonTool(Tool):
    def __init__(self):
        Tool.__init__(self, "Polygon", "Select regions using a series of straight lines")

    def selected(self):
        Tool.selected(self)
        self.ivl.set_picker(PickMode.LASSO)

    def interface(self):
        grid = QtGui.QGridLayout()

        grid.addWidget(QtGui.QLabel("Click to add vertices"), 0, 0)

        btn = QtGui.QPushButton("Add")
        btn.clicked.connect(self.done)
        grid.addWidget(btn, 1, 0)
        btn = QtGui.QPushButton("Discard")
        btn.clicked.connect(self.selected)
        grid.addWidget(btn, 1, 1)

        return grid

    def done(self):
        slice_zaxis = self.ivl.picker.view.zaxis
        slice_z = self.ivm.cim_pos[slice_zaxis]
        roi_new = self.ivl.picker.get_roi(self.label)
        if roi_new is None: return

        if self.new_roi_name not in self.ivm.rois:
            self.ivm.add_roi(self.new_roi_name, roi_new, make_current=True)
        else:
            roi_orig = self.ivm.rois[self.new_roi_name]
            slices = [slice(None)] * 3
            slices[slice_zaxis] = slice_z
            slice_orig = roi_orig[slices]
            slice_new = roi_new[slices]
            slice_orig[slice_new > 0] = slice_new[slice_new > 0]
            roi_orig[slices] = slice_orig
            self.ivm.add_roi(self.new_roi_name, roi_orig, make_current=True)

        self.selected()

class EraserTool(Tool):
    def __init__(self):
        Tool.__init__(self, "Eraser", "Remove voxels from the ROI")

    def selected(self):
        self.ivl.set_picker(PickMode.SINGLE, DragMode.PICKER_DRAG)
        self.ivl.sig_sel_changed.connect(self.point_picked)

    def point_picked(self, picker):
        pos = picker.point
        print(pos)
        if self.new_roi_name not in self.ivm.rois:
            roi_new = np.zeros(self.ivm.shape[:3])
            self.ivm.add_roi(self.new_roi_name, roi_new, make_current=True)
        roi_new = self.ivm.rois[self.new_roi_name]
        roi_new[pos[:3]] = 0

class PickTool(Tool):
    def __init__(self):
        Tool.__init__(self, "Pick", "Pick regions of an existing ROI")

    def interface(self):
        grid = QtGui.QGridLayout()

        grid.addWidget(QtGui.QLabel("Existing ROI"), 0, 0)
        combo = QtGui.QComboBox()
        for key in self.ivm.rois:
            combo.addItem(key)
        combo.currentIndexChanged.connect(self.existing_roi_changed)
        grid.addWidget(combo, 0, 1)

        return grid

    def existing_roi_changed(self, idx):
        if idx >= 0:
            roi = self.roi_combo.itemText(idx)
            self.ivm.set_current_roi(roi, signal=True)

class PenTool(PolygonTool):
    def __init__(self):
        Tool.__init__(self, "Pen", "Select regions by freehand drawing")

    def interface(self):
        grid = QtGui.QGridLayout()

        grid.addWidget(QtGui.QLabel("Click and drag to encircle ROI region"), 0, 0)

        btn = QtGui.QPushButton("Add")
        btn.clicked.connect(self.done)
        grid.addWidget(btn, 1, 0)
        btn = QtGui.QPushButton("Discard")
        btn.clicked.connect(self.selected)
        grid.addWidget(btn, 1, 1)

        return grid

    def selected(self):
        self.ivl.set_picker(PickMode.FREEHAND, DragMode.PICKER_DRAG)
     
class RectTool(PolygonTool):
    def __init__(self):
        Tool.__init__(self, "Rectangle", "Select rectangular regions")

    def interface(self):
        grid = QtGui.QGridLayout()

        grid.addWidget(QtGui.QLabel("Click and drag to define rectangular ROI"), 0, 0)

        btn = QtGui.QPushButton("Add")
        btn.clicked.connect(self.done)
        grid.addWidget(btn, 1, 0)
        btn = QtGui.QPushButton("Discard")
        btn.clicked.connect(self.selected)
        grid.addWidget(btn, 1, 1)

        return grid

    def selected(self):
        self.ivl.set_picker(PickMode.RECT, DragMode.PICKER_DRAG)
        
class EllipseTool(PolygonTool):
    def __init__(self):
        Tool.__init__(self, "Ellipse", "Select elliptical regions")

    def interface(self):
        grid = QtGui.QGridLayout()

        grid.addWidget(QtGui.QLabel("Click and drag to define circular or elliptical ROI"), 0, 0)

        btn = QtGui.QPushButton("Add")
        btn.clicked.connect(self.done)
        grid.addWidget(btn, 1, 0)
        btn = QtGui.QPushButton("Discard")
        btn.clicked.connect(self.selected)
        grid.addWidget(btn, 1, 1)

        return grid

    def selected(self):
        self.ivl.set_picker(PickMode.ELLIPSE, DragMode.PICKER_DRAG)
        
class CrosshairsTool(Tool):
    def __init__(self):
        Tool.__init__(self, "Crosshairs", "Navigate data without adding to ROI")

TOOLS = [CrosshairsTool(), RectTool(), EllipseTool(), PolygonTool(), EraserTool(), PenTool(), PickTool()]

class RoiBuilderWidget(PkWidget):
    """
    Widget for building ROIs
    """

    def __init__(self, **kwargs):
        super(RoiBuilderWidget, self).__init__(name="ROI Builder", icon="roi_builder", desc="Build ROIs", **kwargs)

    def init_ui(self):
        layout = QtGui.QVBoxLayout()
        
        hbox = QtGui.QHBoxLayout()
        hbox.addWidget(QtGui.QLabel("<font size=5>ROI Builder</font>"))
        hbox.addStretch(1)
        help_btn = HelpButton(self, "roi_builder")
        hbox.addWidget(help_btn)
        layout.addLayout(hbox)
        
        desc = QtGui.QLabel(DESC)
        desc.setWordWrap(True)
        layout.addWidget(desc)

        # Generic options
        hbox = QtGui.QHBoxLayout()
        optbox = QtGui.QGroupBox()
        optbox.setTitle("Options")
        grid = QtGui.QGridLayout()
        optbox.setLayout(grid)

        grid.addWidget(QtGui.QLabel("ROI name"), 0, 0)
        self.name_edit = QtGui.QLineEdit("ROI_BUILDER")
        self.name_edit.editingFinished.connect(self.name_changed)
        grid.addWidget(self.name_edit, 0, 1)

        grid.addWidget(QtGui.QLabel("Current label"), 1, 0)
        self.label_spin = QtGui.QSpinBox()
        self.label_spin.setMinimum(1)
        self.label_spin.valueChanged.connect(self.label_changed)
        grid.addWidget(self.label_spin, 1, 1)

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

    def activate(self):
        self.ivl.set_picker(PickMode.SINGLE)
        if self.tool is not None:
            self.tool.selected()

    def deactivate(self):
        self.ivl.set_picker(PickMode.SINGLE)

    def add_tool(self, tool, x, y):
        tool.ivm = self.ivm
        tool.ivl = self.ivl
        tool.label = self.label_spin.value()
        tool.new_roi_name = self.name_edit.text()
        btn = QtGui.QPushButton()
        btn.setIcon(QtGui.QIcon(get_icon(tool.name.lower())))
        btn.setToolTip(tool.tooltip)
        btn.setFixedSize(32, 32)
        btn.clicked.connect(self.tool_clicked(tool))
        tool.btn = btn
        self.tools_grid.addWidget(btn, x, y)

    def tool_clicked(self, tool):
        def tool_clicked():
            if self.tool is not None:
                self.tool.btn.setStyleSheet("")
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
        if self.tool is not None:
            self.tool.label = label
        
    def name_changed(self, name):
        if self.tool is not None:
            self.tool.new_roi_name = name
        