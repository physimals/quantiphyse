"""
Quantiphyse - ROI builder tools

Copyright (c) 2013-2018 University of Oxford
"""

from __future__ import division, unicode_literals, absolute_import, print_function

import numpy as np
import skimage.segmentation
import scipy.ndimage

try:
    from PySide import QtGui, QtCore, QtGui as QtWidgets
except ImportError:
    from PySide2 import QtGui, QtCore, QtWidgets

from quantiphyse.data import NumpyData
from quantiphyse.gui.widgets import OverlayCombo, RoiCombo, NumericOption, NumericSlider
from quantiphyse.gui.viewer.pickers import PickMode
from quantiphyse.utils import LogSource
from quantiphyse.processes.feat_pca import PcaFeatReduce

class Tool(LogSource):
    """
    An ROI builder tool
    """

    def __init__(self, name, tooltip=""):
        """
        :param name: Name of tool
        :param tooltip: Descriptive text
        """
        LogSource.__init__(self)
        self.name = name
        self.tooltip = tooltip

    def selected(self):
        """
        Called when tool is selected by the user 
        """
        self.ivl.set_picker(PickMode.SINGLE)

    def deselected(self):
        """
        Called when tool is deselected by the user 

        *Must* reliably disconnect any signals connected in the selected() method
        """
        self.ivl.set_picker(PickMode.SINGLE)

    def interface(self):
        """
        Return a user interface 

        :return: QtCore.QLayout suitable for embedding in toolbox
        """
        grid = QtGui.QGridLayout()
        grid.addWidget(QtGui.QLabel(self.tooltip), 0, 0, 1, 2)
        return grid

    def _show_builder_roi(self):
        if self.builder.roiname in self.ivm.rois:
            self.ivm.set_current_roi(self.builder.roiname)

class CrosshairsTool(Tool):
    """
    'Tool' which does nothing but allow the user to navigate the views without
    any side effects
    """
    def __init__(self):
        Tool.__init__(self, "Crosshairs", "Navigate data without adding to ROI")
     
class PickedRegionTool(Tool):
    """
    Base class for tools which identify a picked region which can then be added
    erased or used as a mask
    """

    def __init__(self, name, desc, picker):
        Tool.__init__(self, name, desc)
        self._picker = picker

    def selected(self):
        Tool.selected(self)
        self.ivl.set_picker(self._picker)
   
    def interface(self):
        grid = Tool.interface(self)
        btn = QtGui.QPushButton("Add")
        btn.clicked.connect(self._change(self.builder.ADD))
        grid.addWidget(btn, 1, 0)
        btn = QtGui.QPushButton("Erase")
        btn.clicked.connect(self._change(self.builder.ERASE))
        grid.addWidget(btn, 1, 1)
        btn = QtGui.QPushButton("Mask")
        btn.clicked.connect(self._change(self.builder.MASK))
        grid.addWidget(btn, 2, 0)
        btn = QtGui.QPushButton("Discard")
        btn.clicked.connect(self.selected)
        grid.addWidget(btn, 2, 1)
        return grid

    def _change(self, mode):
        def _cb():
            selected_points = self.ivl.picker.selection(grid=self.builder.grid)
            self.builder.modify(vol=selected_points, mode=mode)
            self.selected()
        return _cb

class PolygonTool(PickedRegionTool):
    """ Tool which selects a polygon region """
    def __init__(self):
        PickedRegionTool.__init__(self, "Polygon", "Select regions using a series of straight lines", PickMode.POLYGON)

class PenTool(PickedRegionTool):
    """ Tool which selects a region drawn around in freehand """
    def __init__(self):
        PickedRegionTool.__init__(self, "Pen", "Draw around ROI region", PickMode.FREEHAND)
     
class RectTool(PickedRegionTool):
    """ Tool which selects a rectangular region """
    def __init__(self):
        PickedRegionTool.__init__(self, "Rectangle", "Click and drag to select rectangular region", PickMode.RECT)

class EllipseTool(PickedRegionTool):
    """ Tool which selects an elliptical region """
    def __init__(self):
        PickedRegionTool.__init__(self, "Ellipse", "Click and drag to select elliptical region", PickMode.ELLIPSE)
       
class PainterTool(Tool):
    """
    Tool which paints voxels when clicked
    """
    def __init__(self, name="Painter", desc="Paint voxels on the ROI"):
        Tool.__init__(self, name, desc)
        self._paint_mode = 1 # FIXME

    def selected(self):
        self.ivl.set_picker(PickMode.PAINT)
        self.ivl.sig_selection_changed.connect(self._point_picked)

    def deselected(self):
        self.ivl.sig_selection_changed.disconnect(self._point_picked)
        Tool.deselected(self)

    def interface(self):
        grid = Tool.interface(self)
        self.size = NumericOption("Brush size", grid, 1, 0, intonly=True, maxval=10, default=1, minval=1, step=2)
        return grid

    def _point_picked(self, picker):
        self.debug("Point picked")
        size = self.size.spin.value()
        points = picker.selection(grid=self.builder.grid)

        grid_axes = self.builder.grid.get_ras_axes()
        gridx = grid_axes[picker.view.xaxis]
        gridy = grid_axes[picker.view.yaxis]
        gridz = grid_axes[picker.view.zaxis]
        self.debug("Grid axes: %i, %i, %i", gridx, gridy, gridz)
        self.debug(str(points))
        grid_points = []
        for point in points:
            for xd in range(-int((size-1)/2), int((size-1)/2)+1, 1):
                for yd in range(-int((size-1)/2), int((size-1)/2)+1, 1):
                    grid_point = [int(v + 0.5) for v in point]
                    grid_point[gridx] = grid_point[gridx] + xd
                    grid_point[gridy] = grid_point[gridy] + yd
                    if not grid_points or grid_point != grid_points[-1]:
                        grid_points.append(grid_point)
        self.debug(str(grid_points))
        self.builder.modify(points=grid_points, mode=self._paint_mode)
        picker.reset()
      
class EraserTool(PainterTool):
    """
    Tool which erases voxels when clicked
    """
    def __init__(self):
        PainterTool.__init__(self, "Eraser", "Remove voxels from the ROI")
        self._paint_mode = 2 # FIXME

class PickTool(Tool):
    """
    Tool which adds entire regions from another ROI
    """
    def __init__(self):
        Tool.__init__(self, "Pick", "Pick regions of an existing ROI")
        self.roi_name = ""
        self.temp_name = "PickToolTempRoi"

    def interface(self):
        grid = Tool.interface(self)

        grid.addWidget(QtGui.QLabel("Existing ROI"), 1, 0)
        self.roi_combo = RoiCombo(self.ivm, none_option=True)
        self.roi_combo.currentIndexChanged.connect(self._existing_roi_changed)
        grid.addWidget(self.roi_combo, 1, 1)

        self.ok_btn = QtGui.QPushButton("Accept")
        self.ok_btn.setEnabled(False)
        self.ok_btn.clicked.connect(self._accepted)
        grid.addWidget(self.ok_btn, 2, 0)
        self.cancel_btn = QtGui.QPushButton("Cancel")
        self.cancel_btn.setEnabled(False)
        self.cancel_btn.clicked.connect(self._reset)
        grid.addWidget(self.cancel_btn, 2, 1)
        self.done_btn = QtGui.QPushButton("Done")
        self.done_btn.setEnabled(False)
        self.done_btn.clicked.connect(self._show_builder_roi)
        grid.addWidget(self.done_btn, 2, 2)
        return grid

    def selected(self):
        self.ivl.set_picker(PickMode.SINGLE)
        self._show_existing_roi()
        self.ivl.sig_selection_changed.connect(self._point_picked)

    def deselected(self):
        self.ivl.sig_selection_changed.disconnect(self._point_picked)
        self._show_builder_roi()
        Tool.deselected(self)

    def _reset(self):
        self.roi_new = None
        self.ivm.delete(self.temp_name)
        self.ok_btn.setEnabled(False)
        self.cancel_btn.setEnabled(False)
        self.done_btn.setEnabled(True)
        self.roi_combo.setEnabled(True)
        self._show_builder_roi()

    def _show_existing_roi(self):
        if self.roi_name in self.ivm.rois:
            self.ivm.set_current_roi(self.roi_name)

    def _existing_roi_changed(self):
        self.roi_name = self.roi_combo.currentText()
        self._show_existing_roi()

    def _accepted(self):
        self.builder.modify(vol=self.roi_new, mode=self.builder.ADD)
        self._reset()

    def _point_picked(self, picker):
        if self.roi_name == "": return

        pos = picker.selection(grid=self.builder.grid)
        roi_picked = self.ivm.rois[self.roi_name]
        picked_region = roi_picked.value(pos, grid=self.builder.grid)

        roi_picked_arr = roi_picked.resample(self.builder.grid).raw()
        self.roi_new = np.zeros(self.builder.grid.shape, dtype=np.int)
        self.roi_new[roi_picked_arr == picked_region] = 1

        self.ivm.add(NumpyData(self.roi_new, grid=self.builder.grid, name=self.temp_name, roi=True), make_current=True)
        self.ok_btn.setEnabled(True)
        self.cancel_btn.setEnabled(True)
        self.done_btn.setEnabled(False)
        self.roi_combo.setEnabled(False)
        
class WalkerTool(Tool):
    """
    Tool which uses the random walker method to select a region

    FIXME this does not work properly in slice mode at the moment because the zaxis/pos 
    given by the picker does not necessarily correspond to the data axes.
    """
    def __init__(self):
        Tool.__init__(self, "Walker", "Automatic segmentation using the random walk algorithm")
        self.segmode = 0
        self.pickmode = 0

    def interface(self):
        grid = Tool.interface(self)

        grid.addWidget(QtGui.QLabel("Source data: "), 1, 0)
        self.ov_combo = OverlayCombo(self.ivm)
        grid.addWidget(self.ov_combo)

        grid.addWidget(QtGui.QLabel("Click to select points: "), 2, 0)
        self.pickmode_combo = QtGui.QComboBox()
        self.pickmode_combo.addItem("Inside the ROI")
        self.pickmode_combo.addItem("Outside the ROI")
        self.pickmode_combo.currentIndexChanged.connect(self._pick_mode_changed)
        grid.addWidget(self.pickmode_combo, 2, 1)
        
        grid.addWidget(QtGui.QLabel("Segmentation mode: "), 3, 0)
        self.segmode_combo = QtGui.QComboBox()
        self.segmode_combo.addItem("Slice")
        self.segmode_combo.addItem("3D")
        self.segmode_combo.currentIndexChanged.connect(self._seg_mode_changed)
        grid.addWidget(self.segmode_combo, 3, 1)

        self.beta = NumericOption("Diffusion difficulty", grid, 4, 0, intonly=True, maxval=20000, default=10000, step=1000)

        btn = QtGui.QPushButton("Segment")
        btn.clicked.connect(self._segment)
        grid.addWidget(btn, 5, 0)
        btn = QtGui.QPushButton("Clear points")
        btn.clicked.connect(self._init)
        grid.addWidget(btn, 5, 1)

        return grid

    def _pick_mode_changed(self, idx=None):
        self.pickmode = idx
        if self.pickmode == 0:
            self.ivl.picker.col = (255, 0, 0)
        else:
            self.ivl.picker.col = (255, 255, 255)

    def _seg_mode_changed(self, idx=None):
        self.segmode = idx
        self._init()

    def _init(self):
        if self.segmode == 1:
            self.ivl.set_picker(PickMode.MULTIPLE)
        else:
            self.ivl.set_picker(PickMode.SLICE_MULTIPLE)
            
        self.labels = np.zeros(self.builder.grid.shape, dtype=np.int)
        self._pick_mode_changed(self.pickmode)

    def selected(self):
        self.pickmode = 0
        self.segmode = 0
        self.ivl.sig_selection_changed.connect(self._points_changed)
        self._init()
        
    def deselected(self):
        self.ivl.sig_selection_changed.disconnect(self._points_changed)
        Tool.deselected(self)

    def _points_changed(self):
        for col, points in self.ivl.picker.selection(grid=self.builder.grid).items():
            if col == ((255, 0, 0)):
                label = 1
            else:
                label = 2

            for pos in points:
                pos = [int(p+0.5) for p in pos]
                # Clamp points to within range of ROI
                for dim in range(3):
                    pos[dim] = min(max(pos[dim], 0), self.labels.shape[dim]-1)
                self.labels[pos[0], pos[1], pos[2]] = label
                
    def _segment(self):
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
            pca = PcaFeatReduce(n_components=5)
            arr = pca.get_training_features(arr, feature_volume=True)
            kwargs["multichannel"] = True
        else:
            # Normalize data
            arr = (arr / (np.max(arr)-np.min(arr))) + np.min(arr)
            kwargs["multichannel"] = False

        if self.segmode == 0:
            # Segment using 2D slice only
            zaxis = self.ivl.picker.zaxis
            zpos = int(self.ivl.picker.zpos + 0.5)
            #print(zaxis, zpos)
            sl = [slice(None)] * 3
            sl[zaxis] = zpos
            arr = arr[sl]
            labels = self.labels[sl]
            del spacing[zaxis] 
            #print(labels)
            #print(np.count_nonzero(labels))
            #print(np.count_nonzero(arr))

        seg = skimage.segmentation.random_walker(arr, labels, beta=self.beta.spin.value(), 
                                                 mode='cg_mg', spacing=spacing, **kwargs)

        if self.segmode == 0:
            # Create 3D volume using 2D slice
            seg_3d = np.zeros(self.builder.grid.shape, dtype=np.int)
            seg_3d[sl] = seg
            seg = seg_3d

        # Label 2 is used for 'outside region'
        seg[seg == 2] = 0
        
        self.builder.modify(vol=seg, mode=self.builder.ADD)
        self._init()
             
class BucketTool(Tool):
    """
    Tool which performs a thresholded bucket fill
    """

    def __init__(self):
        Tool.__init__(self, "Bucket", "2D or 3D flood fill with thresholding")
        self.point = None
        self.vol = 0

    def interface(self):
        grid = Tool.interface(self)

        #grid.addWidget(QtGui.QLabel("Segmentation mode: "), 3, 0)
        #self.segmode_combo = QtGui.QComboBox()
        #self.segmode_combo.addItem("Slice")
        #self.segmode_combo.addItem("3D")
        #self.segmode_combo.currentIndexChanged.connect(self._dims_changed)
        #grid.addWidget(self.segmode_combo, 3, 1)

        self.uthresh = NumericSlider("Upper threshold", grid, 4, 0, maxval=100, minval=0, default=50, hardmin=True)
        self.uthresh.sig_changed.connect(self._update_roi)
        self.lthresh = NumericSlider("Lower threshold", grid, 5, 0, maxval=0, minval=-100, default=-50, hardmax=True)
        self.lthresh.sig_changed.connect(self._update_roi)
        self.max_tile_size = NumericSlider("Max distance (voxels)", grid, 6, 0, intonly=True, maxval=500, minval=1, default=100, hardmin=True)
        self.max_tile_size.sig_changed.connect(self._update_roi)

        btn = QtGui.QPushButton("Add")
        btn.clicked.connect(self._add)
        grid.addWidget(btn, 7, 0)
        btn = QtGui.QPushButton("Erase")
        btn.clicked.connect(self._erase)
        grid.addWidget(btn, 7, 1)
        btn = QtGui.QPushButton("Mask")
        btn.clicked.connect(self._mask)
        grid.addWidget(btn, 8, 0)
        btn = QtGui.QPushButton("Discard")
        btn.clicked.connect(self._init)
        grid.addWidget(btn, 8, 1)
        return grid

    def _init(self):
        self.ivl.set_picker(PickMode.SINGLE)
        self._point = None
        if "_temp_bucket" in self.ivm.rois:
            self.ivm.delete("_temp_bucket")
        self._show_builder_roi()

    def selected(self):
        self.ivl.sig_selection_changed.connect(self._sel_changed)
        self._init()
        self._sel_changed()
        
    def deselected(self):
        self.ivl.sig_selection_changed.disconnect(self._sel_changed)
        Tool.deselected(self)
        self._init()

    def _sel_changed(self):
        focus = self.ivl.picker.selection(grid=self.builder.grid)
        self.point = [int(v+0.5) for v in focus[:3]]
        self.vol = focus[3]
        self._update_roi()
    
    def _update_roi(self):
        src_data = self.ivm.current_data.resample(self.builder.grid).volume(self.vol)
        focus_value = src_data[self.point[0], self.point[1], self.point[2]]
        thr_hi, thr_lo = focus_value + self.uthresh.value(), focus_value + self.lthresh.value()
        # Heuristic optimization for large data sets. Start by looking at a tile +- 50 voxels
        # around focus. If that contains the region, fine. If not, add 50 voxels to the tile
        # size and go again until we get nothing on the boundary or end up taking the whole
        # data set
        max_tile_size = self.max_tile_size.value()
        tile_size = min(50, max_tile_size)
        while 1:
            tile, offset = self._get_tile(src_data, self.point, tile_size, src_data.shape)
            binarised = ((tile <= thr_hi) & (tile >= thr_lo)).astype(np.int)
            labelled, _ = scipy.ndimage.measurements.label(binarised)
            scipy_label = labelled[self.point[0]-offset[0], self.point[1]-offset[1], self.point[2]-offset[2]]
            labelled[labelled != scipy_label] = 0
            labelled[labelled == scipy_label] = 1
            if labelled.shape == src_data.shape or tile_size == max_tile_size:
                self.debug("Reached full size, breaking: ", labelled.shape, src_data.shape)
                break
            elif (np.count_nonzero(labelled[:, :, 0]) == 0 and 
                  np.count_nonzero(labelled[:, :, -1]) == 0 and
                  np.count_nonzero(labelled[:, 0, :]) == 0 and
                  np.count_nonzero(labelled[:, -1, :]) == 0 and
                  np.count_nonzero(labelled[0, :, :]) == 0 and
                  np.count_nonzero(labelled[-1, :, :]) == 0):
                self.debug("Nothing on boundary, breaking")
                break
            tile_size = min(tile_size + 50, max_tile_size)

        self.roi = np.zeros(self.builder.grid.shape, dtype=np.int)
        tile_shape = labelled.shape
        self.roi[offset[0]:offset[0]+tile_shape[0], offset[1]:offset[1]+tile_shape[1], offset[2]:offset[2]+tile_shape[2]] = labelled
        self.ivm.add(self.roi, name="_temp_bucket", grid=self.builder.grid, roi=True, make_current=True)
        
    def _get_tile(self, arr, centre, size, shape):
        slices, offset = [], []
        for i in range(3):
            start, end = centre[i]-size, centre[i]+size
            if start < 0: start = 0
            if end > shape[i]: end = shape[i]
            slices.append(slice(start, end))
            offset.append(start)
        self.debug("Tile: ", slices, offset)
        return arr[slices], offset

    def _add(self):
        self.builder.modify(vol=self.roi, mode=self.builder.ADD)
        self._init()

    def _erase(self):
        self.builder.modify(vol=self.roi, mode=self.builder.ERASE)
        self._init()

    def _mask(self):
        self.builder.modify(vol=self.roi, mode=self.builder.MASK)
        self._init()

    def _dims_changed(self):
        pass
