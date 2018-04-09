"""
Quantiphyse - ROI builder tools

Copyright (c) 2013-2018 University of Oxford
"""

from __future__ import division, unicode_literals, absolute_import, print_function

import numpy as np
from skimage.segmentation import random_walker

from PySide import QtGui

from quantiphyse.volumes.load_save import NumpyData
from quantiphyse.gui.widgets import OverlayCombo, RoiCombo, NumericOption
from quantiphyse.gui.pickers import PickMode
from quantiphyse.utils import debug
from quantiphyse.analysis.feat_pca import PcaFeatReduce

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
        slice_z = self.ivl.focus()[slice_zaxis]

        roi_new = self.ivl.picker.selection(grid=self.builder.grid, label=self.label)
        self.builder.add_to_roi(roi_new)
        
        self.selected()

class EraserTool(Tool):
    def __init__(self):
        Tool.__init__(self, "Eraser", "Remove voxels from the ROI")

    def selected(self):
        self.ivl.set_picker(PickMode.SINGLE)
        self.ivl.sig_selection_changed.connect(self.point_picked)

    def deselected(self):
        Tool.deselected(self)
        self.ivl.sig_selection_changed.disconnect(self.point_picked)

    def point_picked(self, picker):
        pos = picker.selection(grid=self.builder.grid)
        pos = [int(v + 0.5) for v in pos]
        sl = np.ones(self.builder.grid.shape, dtype=np.int)
        sl[pos[0], pos[1], pos[2]] = 0
        self.builder.add_to_roi(sl, erase=True)

class PickTool(Tool):
    def __init__(self):
        Tool.__init__(self, "Pick", "Pick regions of an existing ROI")
        self.roi_name = ""
        self.temp_name = "PickToolTempRoi"

    def interface(self):
        grid = Tool.interface(self)

        grid.addWidget(QtGui.QLabel("Existing ROI"), 1, 0)
        self.roi_combo = RoiCombo(self.ivm, none_option=True)
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
        self.done_btn = QtGui.QPushButton("Done")
        self.done_btn.setEnabled(False)
        self.done_btn.clicked.connect(self.done)
        grid.addWidget(self.done_btn, 2, 2)

        return grid

    def set_roi(self):
        self.roi_name = self.roi_combo.currentText()
        self.show_roi()

    def show_roi(self):
        if self.roi_name in self.ivm.rois:
            self.ivm.set_current_roi(self.roi_name)

    def selected(self):
        self.ivl.set_picker(PickMode.SINGLE)
        self.ivl.sig_selection_changed.connect(self.point_picked)
        self.show_roi()

    def deselected(self):
        self.done()
        Tool.deselected(self)
        self.ivl.sig_selection_changed.disconnect(self.point_picked)

    def accepted(self):
        self.builder.add_to_roi(self.roi_new)
        self.reset()

    def done(self):
        self.ivm.set_current_roi(self.builder.new_roi_name)

    def reset(self):
        self.roi_new = None
        self.ivm.delete_roi(self.temp_name)
        self.ok_btn.setEnabled(False)
        self.cancel_btn.setEnabled(False)
        self.done_btn.setEnabled(True)
        self.roi_combo.setEnabled(True)
        self.selected()

    def point_picked(self, picker):
        if self.roi_name == "": return

        pos = picker.selection()
        roi_picked = self.ivm.rois[self.roi_name]
        picked_region = roi_picked.value(pos)

        roi_picked_arr = roi_picked.resample(self.builder.grid).raw()
        self.roi_new = np.zeros(self.builder.grid.shape)
        self.roi_new[roi_picked_arr==picked_region] = self.label

        self.ivm.add_roi(NumpyData(self.roi_new, grid=self.builder.grid, name=self.temp_name), make_current=True)
        self.ok_btn.setEnabled(True)
        self.cancel_btn.setEnabled(True)
        self.done_btn.setEnabled(False)
        self.roi_combo.setEnabled(False)
        self.ivl.sig_selection_changed.disconnect(self.point_picked)
        
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
        self.ivl.set_picker(PickMode.FREEHAND)
     
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
        self.ivl.set_picker(PickMode.RECT)
        
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
        self.ivl.set_picker(PickMode.ELLIPSE)
        
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
        self.init()

    def init(self):
        if self.segmode == 1:
            self.ivl.set_picker(PickMode.MULTIPLE)
        else:
            self.ivl.set_picker(PickMode.SLICE_MULTIPLE)
            
        self.labels = np.zeros(self.builder.grid.shape)
        self.pickmode_changed(self.pickmode)

    def selected(self):
        self.ivl.sig_selection_changed.connect(self.points_changed)
        self.init()
        
    def deselected(self):
        Tool.deselected(self)
        self.ivl.sig_selection_changed.disconnect(self.points_changed)

    def points_changed(self):
        for col, points in self.ivl.picker.selection(grid=self.builder.grid).items():
            if (col == (255, 0, 0)):
                label = 1
            else:
                label = 2

            for pos in points:
                pos =  [int(p+0.5) for p in pos]
                self.labels[pos[0], pos[1], pos[2]] = label

    def segment(self):
        data = self.ivm.data[self.ov_combo.currentText()].resample(self.builder.grid)
        labels = self.labels

        kwargs = {}
        # Use voxel size correctly
        spacing = [data.grid.spacing[0] / data.grid.spacing[0],
                   data.grid.spacing[0] / data.grid.spacing[1],
                   data.grid.spacing[0] / data.grid.spacing[2]]

        arr = data.raw()
        if arr.ndim > 3:
            # Reduce 4D data to PCA modes
            Pfeat = PcaFeatReduce(arr)
            arr, labels1 = Pfeat.get_training_features(feature_volume=True, n_components=5)
            kwargs["multichannel"] = True
        else:
            # Normalize data
            arr = (arr / (np.max(arr)-np.min(arr))) + np.min(arr)
            kwargs["multichannel"] = False

        if self.segmode == 0:
            # Segment using 2D slice only
            zaxis = self.ivl.picker.zaxis
            zpos = int(self.ivl.picker.zpos + 0.5)
            sl = [slice(None)] * 3
            sl[zaxis] = zpos
            arr = arr[sl]
            labels = self.labels[sl]
            del spacing[zaxis] 

        seg = random_walker(arr, labels, beta=self.beta.spin.value(), mode='cg_mg', 
                            spacing=spacing, **kwargs)

        if self.segmode == 0:
            # Create 3D volume using 2D slice
            seg_3d = np.zeros(self.builder.grid.shape)
            seg_3d[sl] = seg
            seg = seg_3d

        # Label 2 is used for 'outside region'
        seg[seg==2] = 0
        
        self.builder.add_to_roi(seg)
        self.init()
        