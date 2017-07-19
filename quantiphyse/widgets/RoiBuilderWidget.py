"""
Author: Martin Craig
Copyright (c) 2017 University of Oxford
"""

from __future__ import division, unicode_literals, absolute_import, print_function

import collections
import time

import numpy as np
from skimage.segmentation import random_walker

from PySide import QtCore, QtGui

from ..QtInherit.dialogs import error_dialog
from ..QtInherit.widgets import OverlayCombo, RoiCombo, NumericOption
from ..QtInherit import HelpButton
from ..ImageView import PickMode, DragMode
from ..utils import get_icon
from ..analysis.feat_pca import PcaFeatReduce
from . import QpWidget

DESC = """
Widget for creating test ROIs and basic manual segmentation
"""

class Tool:
    def __init__(self, name, tooltip=""):
        self.name = name
        self.tooltip = tooltip

    def selected(self):
        self.ivl.set_picker(PickMode.SINGLE)

    def deselected(self):
        self.ivl.set_picker(PickMode.SINGLE)

    def interface(self):
        grid = QtGui.QGridLayout()
        grid.addWidget(QtGui.QLabel(self.tooltip), 0, 0, 1, 2)
        return grid

class PolygonTool(Tool):
    def __init__(self):
        Tool.__init__(self, "Polygon", "Select regions using a series of straight lines")

    def selected(self):
        Tool.selected(self)
        self.ivl.set_picker(PickMode.LASSO)

    def interface(self):
        grid = Tool.interface(self)
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
        self.builder.add_to_roi(roi_new, slice_zaxis, slice_z)
        
        self.selected()

class EraserTool(Tool):
    def __init__(self):
        Tool.__init__(self, "Eraser", "Remove voxels from the ROI")

    def selected(self):
        self.ivl.set_picker(PickMode.SINGLE, DragMode.PICKER_DRAG)
        self.ivl.sig_sel_changed.connect(self.point_picked)

    def deselected(self):
        Tool.deselected(self)
        self.ivl.sig_sel_changed.disconnect(self.point_picked)

    def point_picked(self, picker):
        pos = picker.point
        sl = np.ones(self.ivm.vol.shape[1:3])
        sl[pos[1], pos[2]] = 0
        self.builder.add_to_roi(sl, 0, pos[0], erase=True)

class PickTool(Tool):
    def __init__(self):
        Tool.__init__(self, "Pick", "Pick regions of an existing ROI")
        self.roi_name = ""
        self.temp_name = "PickToolTempRoi"

    def interface(self):
        grid = Tool.interface(self)

        grid.addWidget(QtGui.QLabel("Existing ROI"), 1, 0)
        self.roi_combo = RoiCombo(self.ivm)
        self.roi_combo.currentIndexChanged.connect(self.set_roi)
        grid.addWidget(self.roi_combo, 1, 1)

        self.ok_btn = QtGui.QPushButton("Accept")
        self.ok_btn.setEnabled(False)
        self.ok_btn.clicked.connect(self.accepted)
        grid.addWidget(self.ok_btn, 2, 0)
        self.cancel_btn = QtGui.QPushButton("Cancel")
        self.cancel_btn.setEnabled(False)
        self.cancel_btn.clicked.connect(self.reset)
        grid.addWidget(self.cancel_btn, 2, 1)

        return grid

    def set_roi(self):
        self.roi_name = self.roi_combo.currentText()
        self.show_roi()

    def show_roi(self):
        if self.roi_name != "":
            self.ivm.set_current_roi(self.roi_name)

    def selected(self):
        self.ivl.set_picker(PickMode.SINGLE)
        self.ivl.sig_sel_changed.connect(self.point_picked)
        self.show_roi()

    def deselected(self):
        Tool.deselected(self)
        self.ivl.sig_sel_changed.disconnect(self.point_picked)

    def accepted(self):
        self.builder.add_to_roi(self.roi_new)
        self.reset()

    def reset(self):
        self.roi_new = None
        self.ivm.delete_roi(self.temp_name)
        self.ok_btn.setEnabled(False)
        self.cancel_btn.setEnabled(False)
        self.roi_combo.setEnabled(True)
        self.selected()

    def point_picked(self, picker):
        if self.roi_name == "": return

        pos = picker.point
        roi_picked = self.ivm.rois[self.roi_name]
        picked_region = roi_picked[pos[0], pos[1], pos[2]]
        self.roi_new = np.zeros(roi_picked.shape)
        self.roi_new[roi_picked==picked_region] = self.label

        self.ivm.add_roi(self.temp_name, self.roi_new, make_current=True)
        self.ok_btn.setEnabled(True)
        self.cancel_btn.setEnabled(True)
        self.roi_combo.setEnabled(False)
        self.ivl.sig_sel_changed.disconnect(self.point_picked)
        
class PenTool(PolygonTool):
    def __init__(self):
        Tool.__init__(self, "Pen", "Draw around ROI region")

    def interface(self):
        grid = Tool.interface(self)

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
        Tool.__init__(self, "Rectangle", "Click and drag to select rectangular region")

    def interface(self):
        grid =  Tool.interface(self)

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
        Tool.__init__(self, "Ellipse", "Click and drag to select elliptical region")

    def interface(self):
        grid  = Tool.interface(self)

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
     
class WalkerTool(Tool):
    def __init__(self):
        Tool.__init__(self, "Walker", "Automatic segmentation using the random walk algorithm")
        self.segmode = 0
        self.pickmode = 0

    def interface(self):
        grid  = Tool.interface(self)

        grid.addWidget(QtGui.QLabel("Source data: "), 1, 0)
        self.ov_combo=OverlayCombo(self.ivm)
        grid.addWidget(self.ov_combo)

        grid.addWidget(QtGui.QLabel("Click to select points: "), 2, 0)
        self.pickmode_combo = QtGui.QComboBox()
        self.pickmode_combo.addItem("Inside the ROI")
        self.pickmode_combo.addItem("Outside the ROI")
        self.pickmode_combo.currentIndexChanged.connect(self.pickmode_changed)
        grid.addWidget(self.pickmode_combo, 2, 1)
        
        grid.addWidget(QtGui.QLabel("Segmentation mode: "), 3, 0)
        self.segmode_combo = QtGui.QComboBox()
        self.segmode_combo.addItem("Slice")
        self.segmode_combo.addItem("3D")
        self.segmode_combo.currentIndexChanged.connect(self.segmode_changed)
        grid.addWidget(self.segmode_combo, 3, 1)

        self.beta = NumericOption("Diffusion difficulty", grid, 4, 0, intonly=True, maxval=20000, default=10000, step=1000)

        btn = QtGui.QPushButton("Segment")
        btn.clicked.connect(self.segment)
        grid.addWidget(btn, 5, 0)
        btn = QtGui.QPushButton("Clear points")
        btn.clicked.connect(self.selected)
        grid.addWidget(btn, 5, 1)

        return grid

    def pickmode_changed(self, idx=None):
        self.pickmode = idx
        if self.pickmode == 0:
            self.ivl.picker.col = (255, 0, 0)
        else:
            self.ivl.picker.col = (255, 255, 255)

    def segmode_changed(self, idx=None):
        self.segmode = idx
        self.selected()

    def selected(self):
        if self.segmode == 1:
            self.ivl.set_picker(PickMode.MULTIPLE)
        else:
            self.ivl.set_picker(PickMode.SLICE_MULTIPLE)
            
        self.ivl.sig_sel_changed.connect(self.points_changed)
        self.labels = np.zeros(self.ivm.vol.shape[:3])
        self.pickmode_changed(self.pickmode)
        
    def deselected(self):
        Tool.deselected(self)
        self.ivl.sig_sel_changed.disconnect(self.points_changed)

    def points_changed(self):
        for col, points in self.ivl.picker.points.items():
            if (col == (255, 0, 0)):
                label = 1
            else:
                label = 2

            for p in points:
                self.labels[p[0], p[1], p[2]] = label

    def segment(self):
        data = self.ivm.overlays[self.ov_combo.currentText()]
        labels = self.labels

        kwargs = {}
        # Use voxel size correctly
        spacing = [self.ivm.voxel_sizes[0] / self.ivm.voxel_sizes[0],
                  self.ivm.voxel_sizes[0] / self.ivm.voxel_sizes[1],
                  self.ivm.voxel_sizes[0] / self.ivm.voxel_sizes[2]]

        if data.ndim > 3:
            # Reduce 4D data to PCA modes
            Pfeat = PcaFeatReduce(data)
            data, labels1 = Pfeat.get_training_features(feature_volume=True, n_components=5)
            kwargs["multichannel"] = True
        else:
            # Normalize data
            data = (data / (np.max(data)-np.min(data))) + np.min(data)
            kwargs["multichannel"] = False

        if self.segmode == 0:
            # Segment using 2D slice only
            zaxis = self.ivl.picker.zaxis
            zpos = self.ivl.picker.zpos
            sl = [slice(None)] * 3
            sl[zaxis] = zpos
            data = data[sl]
            labels = self.labels[sl]
            del spacing[zaxis] 
        else:
            zpos, zaxis = None, None

        seg = random_walker(data, labels, beta=self.beta.spin.value(), mode='cg_mg', spacing=spacing, **kwargs)

        # Label 2 is used for 'outside region'
        seg[seg==2] = 0
        
        self.builder.add_to_roi(seg, zaxis, zpos)
        self.selected()
        
TOOLS = [CrosshairsTool(), PenTool(), WalkerTool(), EraserTool(), RectTool(), EllipseTool(), PolygonTool(), PickTool()]

class RoiBuilderWidget(QpWidget):
    """
    Widget for building ROIs
    """

    def __init__(self, **kwargs):
        super(RoiBuilderWidget, self).__init__(name="ROI Builder", icon="roi_builder", desc="Build ROIs", **kwargs)
        self.history = collections.deque(maxlen=10)

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

    def activate(self):
        self.ivl.set_picker(PickMode.SINGLE)
        if self.tool is not None:
            self.tool.selected()

    def deactivate(self):
        self.ivl.set_picker(PickMode.SINGLE)
        if self.tool is not None:
            self.tool.deselected()

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
            if self.ivm.vol is None:
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
        roi_orig = self.ivm.rois.get(self.new_roi_name, np.zeros(self.ivm.shape[:3]))

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

        self.ivm.add_roi(self.new_roi_name, roi_orig, make_current=True)
        self.undo_btn.setEnabled(True)

    def undo(self):
        if len(self.history) == 0: return

        roi_name, axis, pos, roi_slice_orig = self.history.pop()
        if roi_name  in self.ivm.rois:
            slices = [slice(None)] * 3
            if axis is not None and pos is not None:
                slices[axis] = pos
            self.ivm.rois[roi_name][slices] = roi_slice_orig
            self.ivm.add_roi(roi_name, self.ivm.rois[roi_name])
        self.undo_btn.setEnabled(len(self.history) > 0)