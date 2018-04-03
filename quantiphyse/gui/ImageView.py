"""
Quantiphyse - 2d ortho slice image viewer

Copyright (c) 2013-2018 University of Oxford
"""

from __future__ import division, unicode_literals, absolute_import, print_function

import sys
import collections

from PySide import QtCore, QtGui
import warnings
import numpy as np
import weakref

import pyqtgraph as pg
from pyqtgraph.exporters.ImageExporter import ImageExporter
from PIL import Image, ImageDraw

from .HistogramWidget import MultiImageHistogramWidget
from quantiphyse.utils import get_icon, get_lut, get_pencol, debug
from quantiphyse.volumes import OrthoSlice, Transform, DataGrid
from quantiphyse.gui.widgets import OptionsButton

"""
How should picking work?

On activation, widget will typically put the viewer in a pick mode. Some widgets might change the
mode during use (e.g. ROI builder). The view will clear any existing selection at this point.

Once selection is initiated (generally by clicking in a window) a Picker is instantiated. Some pickers
(e.g. single/multi point selection) are not tied to a particular view windows, however others (lasso / freehand)
are. Clicks in other widows will not generate selection or focus events and will not change the focus point
(as this may alter the visible slice in the picking window).

Widgets can choose when to stop picking, however the picker may also emit the sel_finished signal (e.g. when
user goes back to the starting point in a lasso picker, or finishes drawing a selection box)

Changes to the selection will trigger sel_changed events. For freehand selection this will only occur
when mouse button is released.

Selected points are reported in IVL grid space, widgets can convert these easily to the coordinate space
of whatever data they are interested in. For region selection pickers, the get_roi method takes a 
QpData instance which is used to define the grid space on which the returned ROI is defined.
"""

class PickMode:
    """ Single point picking. pick_points contains a single point """
    SINGLE = 1

    """ Multi-point picking. pick_points contains a list of points """
    MULTIPLE = 2

    """ Multi-point picking in a single slice """
    SLICE_MULTIPLE = 3

    """ Select rectangular regions. pick_points contains opposite corners, get_pick_roi gets full set of points"""
    RECT = 4

    """ Select elliptical regions. pick_points contains opposite corners, get_pick_roi gets full set of points"""
    ELLIPSE = 5

    """ Polygon lasso. pick_points contains line segment ends. Use get_pick_roi to get full set """
    LASSO = 6
    
    """ Like LASSO but holding mouse down for continual freehand drawing."""
    FREEHAND = 7
    
    """ Pick an ROI region. pick_points contains a single point. get_pick_roi gets the full region"""
    ROI_REGION = 8

class Picker:
    def __init__(self, iv):
        self.ivl = iv
        self.win = None
        # Map from colour to selected points
        self.points = {}

    def add_point(self, pos, win):
        pass

    def update_view(self, pos):
        pass

    def cleanup(self):
        """ Remove picker objects from the view """
        pass

class PointPicker(Picker):
    def __init__(self, iv, col=(255, 255, 255)):
        Picker.__init__(self, iv)
        self.col = col
        self.points = {self.col : []}

    def add_point(self, pos, win):
        self.points = {self.col : [tuple(pos),]}
        self.point = tuple(pos)
        self.ivl.sig_sel_changed.emit(self)

class MultiPicker(PointPicker):
    def __init__(self, iv, col=(255, 0, 0)):
        PointPicker.__init__(self, iv, col)
        self.arrows = []

    def add_point(self, pos, win):
        if self.col not in self.points: 
            self.points[self.col] = []
        self.points[self.col].append(tuple(pos))
        for win in self.ivl.win.values():
            win.add_arrow(pos, self.col)
        self.ivl.sig_sel_changed.emit(self)
    
    def cleanup(self):
        for w in range(3):
            win = self.ivl.win[w].remove_arrows()

class SliceMultiPicker(MultiPicker):
    def __init__(self, iv, col=(255, 0, 0)):
        MultiPicker.__init__(self, iv, col)

    def add_point(self, pos, win):
        if self.col not in self.points: 
            self.points[self.col] = []
        
        if self.win is None:
            self.win = win
            self.zaxis = self.ivl.win[win].zaxis
            self.zpos = pos[self.zaxis]

        if win == self.win and pos[self.zaxis] == self.zpos:
            self.points[self.col].append(tuple(pos))
            self.ivl.win[win].add_arrow(pos, self.col)

        self.ivl.sig_sel_changed.emit(self)

class LassoPicker(Picker): 

    def __init__(self, iv):
        Picker.__init__(self, iv)
        self.roisel = None
        self.points = []
        self.view = None
           
    def add_point(self, pos, win):
        if self.win is None: 
            self.win = win
            self.roisel = pg.PolyLineROI([], pen=(255, 0, 0))
            self.view = self.ivl.win[self.win]
            self.view.vb.addItem(self.roisel)
        
        fx, fy = float(pos[self.view.xaxis])+0.5, float(pos[self.view.yaxis])+0.5
        self.points.append((fx, fy))

        self.roisel.setPoints(self.points)

    def get_roi(self, label=1):
        """ Get the selected points as an ROI"""
        if self.win is None: return None    

        w, h = self.ivl.grid.shape[self.view.xaxis], self.ivl.grid.shape[self.view.yaxis]
        img = Image.new('L', (w, h), 0)
        ImageDraw.Draw(img).polygon(self.points, outline=label, fill=label)
        
        ret = np.zeros(self.view.ivl.grid.shape)
        slice_mask = np.array(img).T
        slices = [slice(None)] * 3
        slices[self.view.zaxis] = self.ivl.focus()[self.view.zaxis]
        ret[slices] = slice_mask
        return ret

    def cleanup(self):
        if self.view is not None: 
            self.view.vb.removeItem(self.roisel)
        
class RectPicker(LassoPicker): 

    def __init__(self, iv):
        LassoPicker.__init__(self, iv)

    def add_point(self, pos, win):
        if self.win is None: 
            self.win = win
            self.view = self.ivl.win[self.win]
        
        fx, fy = float(pos[self.view.xaxis])+0.5, float(pos[self.view.yaxis])+0.5
        self.points.append((fx, fy))

        if self.roisel is None: 
            self.roisel = pg.RectROI((fx, fy), (1, 1), pen=(255, 0, 255))
            self.view.vb.addItem(self.roisel)
            self.ox, self.oy = fx, fy
        else:
            sx, sy = fx-self.ox, fy-self.oy
            self.roisel.setSize((sx, sy))
            
        self.points = [(self.ox, self.oy), (self.ox, fy), (fx, fy), (fx, self.oy)]

class EllipsePicker(LassoPicker): 

    def __init__(self, iv):
        LassoPicker.__init__(self, iv)

    def add_point(self, pos, win):
        if self.win is None: 
            self.win = win
            self.view = self.ivl.win[self.win]
        
        fx, fy = float(pos[self.view.xaxis])+0.5, float(pos[self.view.yaxis])+0.5
        self.points.append((fx, fy))

        if self.roisel is None: 
            self.roisel = pg.EllipseROI((fx, fy), (1, 1), pen=(255, 0, 0))
            self.view.vb.addItem(self.roisel)
            self.ox, self.oy = fx, fy
        else:
            sx, sy = fx-self.ox, fy-self.oy
            if sx == 0: sx = 1
            if sy == 0: sy = 1
            self.roisel.setSize((sx, sy))
            
        self.points = [min(self.ox, fx), min(self.oy, fy), max(self.ox, fx), max(self.oy, fy)]

    def get_roi(self, label=1):
        """ Get the selected points as an ROI"""
        if self.win is None: return None    

        w, h = self.ivl.grid.shape[self.view.xaxis], self.ivl.grid.shape[self.view.yaxis]
        img = Image.new('L', (w, h), 0)
        ImageDraw.Draw(img).ellipse([int(p) for p in self.points], outline=label, fill=label)
        
        ret = np.zeros(self.view.ivl.grid.shape)
        slice_mask = np.array(img).T
        slices = [slice(None)] * 3
        slices[self.view.zaxis] = self.ivl.focus()[self.view.zaxis]
        ret[slices] = slice_mask
        return ret

class FreehandPicker(LassoPicker): 

    def __init__(self, iv):
        LassoPicker.__init__(self, iv)
        self.path = None
        self.pathitem = None

    def add_point(self, pos, win):
        if self.win is None: 
            self.win = win
            self.view = self.ivl.win[self.win]
            
        fx, fy = float(pos[self.view.xaxis])+0.5, float(pos[self.view.yaxis])+0.5
        self.points.append((fx, fy))

        if self.roisel is None: 
            self.roisel = QtGui.QGraphicsPathItem() 
            self.pen = QtGui.QPen(QtCore.Qt.darkMagenta, 1, QtCore.Qt.SolidLine, QtCore.Qt.SquareCap, QtCore.Qt.BevelJoin)
            self.roisel.setPen(self.pen)
            self.view.vb.addItem(self.roisel)
            self.path = QtGui.QPainterPath(QtCore.QPointF(fx, fy))
        else:
            self.path.lineTo(fx, fy)
        self.roisel.setPath(self.path)
        
PICKERS = {PickMode.SINGLE : PointPicker,
           PickMode.MULTIPLE : MultiPicker,
           PickMode.SLICE_MULTIPLE : SliceMultiPicker,
           PickMode.LASSO : LassoPicker,
           PickMode.RECT : RectPicker,
           PickMode.ELLIPSE : EllipsePicker,
           PickMode.FREEHAND : FreehandPicker
          }

class DragMode:
    DEFAULT = 0
    PICKER_DRAG = 1

class DataView(QtCore.QObject):
    """
    View of a data item, storing details about visual parameters, e.g.
    color map and min/max range for color mapping
    """

    BOUNDARY_TRANS = 0
    BOUNDARY_CLAMP = 1

    # Signals when view parameters are changed
    sig_changed = QtCore.Signal(object)

    def __init__(self, ivm, name):
        super(DataView, self).__init__()
        self.ivm = ivm
        self.name = name
        self.cmap = "jet"
        self.visible = True
        self.alpha = 255
        self.roi_only = False
        self.boundary = self.BOUNDARY_TRANS

        # Initial colourmap range. 
        self.cmap_range = list(self.data().range)
        
    def data(self):
        # We do not keep a reference to the data object as it may change underneath us!
        data = self.ivm.data.get(self.name, None)
        if data is None:
            # Data no longer exists! Shouldn't really happen but currently does
            warnings.warn("Tried to get slice of data which does not exist")
        return data

class RoiView:
    """
    View of an ROI, storing details about visual parameters, e.g. contour plotting
    """
    def __init__(self, ivm, roi_name):
        self.ivm = ivm
        self.roi_name = roi_name
        self.shade = True
        self.contour = False
        self.alpha = 150

    def roi(self):
        return self.ivm.rois.get(self.roi_name, None)

class MaskableImage(pg.ImageItem):
    """
    Minor addition to ImageItem to allow it to be masked by an RoiView
    """
    def __init__(self, image=None, **kwargs):
        pg.ImageItem.__init__(self, image, **kwargs)
        self.mask = None
        self.boundary = DataView.BOUNDARY_TRANS
        self.border = None

    def setBoundaryMode(self, mode):
        self.boundary = mode

    def render(self):
        """
        Custom masked renderer based on PyQtGraph code
        """
        if self.image is None or self.image.size == 0:
            return
        if isinstance(self.lut, collections.Callable):
            lut = self.lut(self.image)
        else:
            lut = self.lut
            
        argb, alpha = pg.functions.makeARGB(self.image, lut=lut, levels=self.levels)
        if self.image.size > 1:
            if self.mask is not None:
                argb[:,:,3][self.mask == 0] = 0
        
            if self.boundary == DataView.BOUNDARY_TRANS:
                # Make out of range values transparent
                trans = np.logical_or(self.image < self.levels[0], self.image > self.levels[1])
                argb[:,:,3][trans] = 0

        self.qimage = pg.functions.makeQImage(argb, alpha)
    
class OrthoView(pg.GraphicsView):
    """
    A single slice view of data and ROI
    """

    # Signals when point of focus is changed
    sig_focus = QtCore.Signal(tuple, int, bool)

    # Signals when view is maximised/minimised
    sig_maxmin = QtCore.Signal(int)

    def __init__(self, ivl, ivm, ax_map, ax_labels):
        pg.GraphicsView.__init__(self)
        self.ivl = ivl
        self.ivm = ivm
        self.xaxis, self.yaxis, self.zaxis = ax_map
        self.dragging = False
        self.contours = []
        self.arrows = []

        self.img = MaskableImage(border='k')
        self.img.setBoundaryMode(DataView.BOUNDARY_CLAMP)
        self.img.setZValue(-1)
        self.img_roi = MaskableImage(border='k')
        self.img_roi.setBoundaryMode(DataView.BOUNDARY_TRANS)
        self.img_ovl = MaskableImage(border='k')

        self.vline = pg.InfiniteLine(angle=90, movable=False)
        self.vline.setPen(pg.mkPen((0, 255, 0), width=1.0, style=QtCore.Qt.DashLine))
        self.vline.setVisible(False)
        
        self.hline = pg.InfiniteLine(angle=0, movable=False)
        self.hline.setPen(pg.mkPen((0, 255, 0), width=1.0, style=QtCore.Qt.DashLine))
        self.hline.setVisible(False)

        self.vb = pg.ViewBox(name="view%i" % self.zaxis, border=pg.mkPen((0, 0, 255), width=3.0))
        self.vb.setAspectLocked(True)
        self.vb.setBackgroundColor([0, 0, 0])
        self.vb.addItem(self.img)
        self.vb.addItem(self.img_roi)
        self.vb.addItem(self.img_ovl)
        self.vb.addItem(self.vline, ignoreBounds=True)
        self.vb.addItem(self.hline, ignoreBounds=True)
        self.vb.enableAutoRange()
        self.setCentralItem(self.vb)

        # Create static labels for the view directions
        self.labels = []
        for ax in [self.xaxis, self.yaxis]:
            self.labels.append(QtGui.QLabel(ax_labels[ax][0], parent=self))
            self.labels.append(QtGui.QLabel(ax_labels[ax][1], parent=self))
        for l in self.labels:
            l.setVisible(False)
            l.setAttribute(QtCore.Qt.WA_TranslucentBackground)
        self.resizeEventOrig = self.resizeEvent
        self.resizeEvent = self.resize_win

    def update(self):
        if self.ivm.main is None: 
            self.img.setImage(np.zeros((1, 1)), autoLevels=False)
        else:
            # Adjust axis scaling depending on whether voxel size scaling is enabled
            if self.ivl.opts.size_scaling == self.ivl.opts.SCALE_VOXELS:
                self.vb.setAspectLocked(True, ratio=(self.ivl.grid.spacing[self.xaxis] / self.ivl.grid.spacing[self.yaxis]))
            else:
                self.vb.setAspectLocked(True, ratio=1)

            for l in self.labels:
                l.setVisible(True)

            # Flip left/right depending on the viewing convention selected
            if self.xaxis == 0:
                # X-axis is left/right
                self.vb.invertX(self.ivl.opts.orientation == 0)
                if self.ivl.opts.orientation == self.ivl.opts.RADIOLOGICAL:
                    l, r = 1, 0
                else: 
                    l, r = 0, 1
                self.labels[r].setText("R")
                self.labels[l].setText("L")

            # Get image slice
            pos = self.ivl.focus()
            plane = OrthoSlice(self.ivl.grid, self.zaxis, pos[self.zaxis])
            slicedata, scale, offset = self.ivm.main.slice_data(plane, vol=pos[3])
            #print(slicedata.shape, scale, offset)
            transform = QtGui.QTransform(scale[0, 0], scale[0, 1], scale[1,0], scale[1, 1], offset[0], offset[1])
            self.img.setTransform(transform)
            self.img.setImage(slicedata, autoLevels=False)

        self.vline.setPos(float(pos[self.xaxis]))
        self.hline.setPos(float(pos[self.yaxis]))
        self.vline.setVisible(self.ivl.opts.crosshairs == self.ivl.opts.SHOW)
        self.hline.setVisible(self.ivl.opts.crosshairs == self.ivl.opts.SHOW)

        self._update_view_roi()
        self._update_view_overlay()
        self.update_arrows()

    def _iso_prepare(self, arr, val):
        return arr == val
        out = arr.copy()
        for row in range(len(arr)):
            for col in range(len(arr[0])):
                if arr[row, col] == val:
                    out[row, col] = 1
                if arr[row, col] > val:
                    out[row, col] = 2
                if arr[row, col] < val:
                    out[row, col] = 2
        return out

    def _update_view_roi(self):
        roiview = self.ivl.current_roi_view
        n = 0 # Number of contours - required at end
        if roiview is None or roiview.roi() is None:
            self.img_roi.setImage(np.zeros((1, 1)))
        else:
            roidata = roiview.roi()
            z = 0
            if self.ivl.opts.display_order == self.ivl.opts.ROI_ON_TOP: z=1

            pos = self.ivl.focus()
            lut = get_lut(roidata, roiview.alpha)
            roi_levels = [0, len(lut)-1]
            
            plane = OrthoSlice(self.ivl.grid, self.zaxis, pos[self.zaxis])
            slicedata, scale, offset = roidata.slice_data(plane)

            if roiview.shade:
                self.img_roi.setImage(slicedata, lut=lut, autoLevels=False, levels=roi_levels)
                self.img_roi.setTransform(QtGui.QTransform(scale[0, 0], scale[0, 1], scale[1,0], scale[1, 1], offset[0], offset[1]))
                self.img_roi.setZValue(z)
            else:
                self.img_roi.setImage(np.zeros((1, 1)))

            if roiview.contour:
                # Update data and level for existing contour items, and create new ones if needed
                n_conts = len(self.contours)
                create_new = False
                for val in roidata.regions:
                    pencol = get_pencol(roidata, val)
                    if val != 0:
                        if n == n_conts:
                            create_new = True

                        if create_new:
                            self.contours.append(pg.IsocurveItem())
                            self.vb.addItem(self.contours[n])

                        d = self._iso_prepare(data, val)
                        self.contours[n].setData(d)
                        self.contours[n].setLevel(1)
                        self.contours[n].setPen(pg.mkPen(pencol, width=self.ivl.roi_outline_width))

                    n += 1

        # Set data to None for any existing contour items that we are not using right now 
        # FIXME should we delete these?
        for idx in range(n, len(self.contours)):
            self.contours[idx].setData(None)

    def _update_view_overlay(self):
        oview = self.ivl.current_data_view
        if oview is None or not oview.visible or oview.data() is None:
            self.img_ovl.setImage(np.zeros((1, 1)), autoLevels=False)
        else:
            z = 1
            if self.ivl.opts.display_order == self.ivl.opts.ROI_ON_TOP: z=0
            self.img_ovl.setZValue(z)
            
            pos = self.ivl.focus()
            plane = OrthoSlice(self.ivl.grid, self.zaxis, pos[self.zaxis])
            slicedata, scale, offset = oview.data().slice_data(plane, vol=pos[3])
            #debug(slicedata.shape, scale, offset)

            self.img_ovl.setBoundaryMode(oview.boundary)
            if oview.roi_only and self.ivm.current_roi is not None:
                mask, scale, offset = self.ivm.current_roi.get_slice(plane)
                self.img_ovl.mask = mask
            else:
                self.img_ovl.mask = None
            self.img_ovl.setImage(slicedata, autoLevels=False)
            self.img_ovl.setTransform(QtGui.QTransform(scale[0, 0], scale[0, 1], scale[1, 0], scale[1, 1], offset[0], offset[1]))

    def resize_win(self, event):
        """
        Called when window is resized - updates the position
        of the text labels and then calls the original resize method
        """
        w = self.geometry().width()
        h = self.geometry().height()
        self.labels[0].setGeometry(0, h/2, 10, 10)
        self.labels[1].setGeometry(w-10, h/2, 10, 10)
        self.labels[2].setGeometry(w/2, h-10, 10, 10)
        self.labels[3].setGeometry(w/2, 0, 10, 10)
        self.resizeEventOrig(event)

    def wheelEvent(self, event):
        """
        Subclassed to remove scroll to zoom from pg.ImageItem
        and instead trigger a scroll through the volume
        """
        dz = int(event.delta()/120)
        pos = self.ivl.focus(self.ivm.main.grid)
        pos[self.zaxis] += dz
        if pos[self.zaxis] >= self.ivm.main.grid.shape[self.zaxis] or pos[self.zaxis] < 0:
            return

        self.ivl.set_focus(pos + [pos[3], ], self.ivm.main.grid)
        #t = Transform(self.ivl.grid, self.ivm.main.grid)
        #std_pos = list(t.transform_position(pos[:3]))
        #self.sig_focus.emit(std_pos + [pos[3], ], self.zaxis, False)

    def mousePressEvent(self, event):
        super(OrthoView, self).mousePressEvent(event)
        if self.ivm.main is None: return
        
        if event.button() == QtCore.Qt.LeftButton:
            self.dragging = (self.ivl.drag_mode == DragMode.PICKER_DRAG)
            coords = self.img.mapFromScene(event.pos())
            mx = int(coords.x())
            my = int(coords.y())

            if mx < 0 or mx >= self.ivm.main.grid.shape[self.xaxis]: return
            if my < 0 or my >= self.ivm.main.grid.shape[self.yaxis]: return

            # Convert to view grid
            pos = self.ivl.focus(self.ivm.main.grid)
            pos[self.xaxis] = mx
            pos[self.yaxis] = my
            t = Transform(self.ivl.grid, self.ivm.main.grid)
            std_pos = list(t.transform_position(pos[:3]))
            self.ivl.set_focus(pos + [pos[3], ], self.ivm.main.grid)

    def add_arrow(self, pos, col):
        arrow = pg.ArrowItem(pen=col, brush=col)
        arrow.setPos(float(pos[self.xaxis]), float(pos[self.yaxis]))
        arrow.setVisible(pos[self.zaxis] == pos[self.zaxis]) 
        arrow.setZValue(2)
        self.vb.addItem(arrow)
        self.arrows.append((pos[self.zaxis], arrow))

    def remove_arrows(self):
        """ Remove all the arrows that have been placed """
        for zpos, arrow in self.arrows:
            self.vb.removeItem(arrow)
        self.arrows = []

    def update_arrows(self):
        """ Update arrows so only those visible are shown """
        current_zpos = self.ivl.focus()[self.zaxis]
        for zpos, arrow in self.arrows:
            arrow.setVisible(current_zpos == zpos)

    def mouseReleaseEvent(self, event):
        super(OrthoView, self).mouseReleaseEvent(event)
        self.dragging = False
        
    def mouseDoubleClickEvent(self, event):
        super(OrthoView, self).mouseDoubleClickEvent(event)
        if event.button() == QtCore.Qt.LeftButton:
            self.sig_maxmin.emit(self.zaxis)

    def mouseMoveEvent(self, event):
        if self.dragging:
            coords = self.mapFromScene(event.pos())
            mx = int(coords.x())
            my = int(coords.y())
            pos = self.ivl.focus()
            pos[self.xaxis] = mx
            pos[self.yaxis] = my
            self.sig_focus.emit(pos, self.zaxis, True)
        else:
            super(OrthoView, self).mouseMoveEvent(event)

class LevelsDialog(QtGui.QDialog):

    def __init__(self, parent, ivm, dv):
        super(LevelsDialog, self).__init__(parent)
        self.ivm = ivm
        self.dv = dv

        self.setWindowTitle("Levels for %s" % dv.name)
        vbox = QtGui.QVBoxLayout()

        grid = QtGui.QGridLayout()
        self.min_spin = self.add_spin(grid, "Minimum", 0)
        self.max_spin = self.add_spin(grid, "Maximum", 1)   

        grid.addWidget(QtGui.QLabel("Percentage of data range"), 2, 0)
        hbox = QtGui.QHBoxLayout()
        self.percentile_spin = QtGui.QSpinBox()
        self.percentile_spin.setMaximum(100)
        self.percentile_spin.setMinimum(1)
        self.percentile_spin.setValue(100)
        hbox.addWidget(self.percentile_spin)
        btn = QtGui.QPushButton("Reset")
        btn.clicked.connect(self._reset)
        hbox.addWidget(btn)
        self.use_roi = QtGui.QCheckBox("Within ROI")
        hbox.addWidget(self.use_roi)
        grid.addLayout(hbox, 2, 1)

        grid.addWidget(QtGui.QLabel("Values outside range are"), 4, 0)
        self.combo = QtGui.QComboBox()
        self.combo.addItem("Transparent")
        self.combo.addItem("Clamped to max/min colour")
        self.combo.setCurrentIndex(self.dv.boundary)
        self.combo.currentIndexChanged.connect(self.bound_changed)
        grid.addWidget(self.combo, 4, 1)
        vbox.addLayout(grid)

        self.buttonBox = QtGui.QDialogButtonBox(QtGui.QDialogButtonBox.Ok)
        self.buttonBox.accepted.connect(self.close)
        vbox.addWidget(self.buttonBox)

        self.setLayout(vbox)
    
    def add_spin(self, grid, label, row):
        grid.addWidget(QtGui.QLabel(label), row, 0)
        spin = QtGui.QDoubleSpinBox()
        spin.setMaximum(1e20)
        spin.setMinimum(-1e20)
        spin.setValue(self.dv.cmap_range[row])
        spin.valueChanged.connect(self.val_changed(row))
        grid.addWidget(spin, row, 1)
        return spin

    def val_changed(self, row):
        def val_changed(val):
            self.dv.cmap_range[row] = val
            self.dv.sig_changed.emit(self.dv)
        return val_changed

    def bound_changed(self, idx):
        self.dv.boundary = idx
        self.dv.sig_changed.emit(self.dv)
    
    def _reset(self):
        percentile = float(100 - self.percentile_spin.value()) / 2
        cmin, cmax = list(self.dv.data().range)
        within_roi = self.use_roi.isChecked()
        if percentile > 0 or within_roi: 
            data = self.dv.data().resample(self.ivl.grid)
            if within_roi and self.ivm.current_roi is not None:
                roidata = self.ivm.current_roi.resample(self.ivl.grid)
                data = data[roidata > 0]
            flat = data.reshape(-1)
            cmin = np.percentile(flat, percentile)
            cmax = np.percentile(flat, 100-percentile)
        self.dv.cmap_range = [cmin, cmax]
        self.min_spin.setValue(cmin)
        self.max_spin.setValue(cmax)

class Navigator:
    """
    Slider control which alters position along an axis
    """

    def __init__(self, ivl, label, axis, layout_grid, layout_ypos):
        self.ivl = ivl
        self.axis = axis
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
    
    def _changed(self, value):
        if value != self._pos:
            self.set_pos(value)
            pos = self.ivl.focus()
            pos[self.axis] = value
            self.ivl.set_focus(pos)
        
    def set_size(self, size):
        try:
            self.slider.blockSignals(True)
            self.spin.blockSignals(True)
            self.slider.setRange(0, size-1)
            self.spin.setMaximum(size-1)
        finally:
            self.slider.blockSignals(False)
            self.spin.blockSignals(False)

    def set_pos(self, pos):
        self._pos = pos
        try:
            self.slider.blockSignals(True)
            self.spin.blockSignals(True)
            self.slider.setValue(pos)
            self.spin.setValue(pos)
        finally:
            self.slider.blockSignals(False)
            self.spin.blockSignals(False)
        
class DataSummary(QtGui.QWidget):
    """ Data summary bar """
    def __init__(self, ivl):
        self.opts = ivl.opts
        self.ivl = ivl

        QtGui.QWidget.__init__(self)
        hbox = QtGui.QHBoxLayout()
        hbox.setContentsMargins(0, 0, 0, 0)
        self.vol_name = QtGui.QLineEdit()
        p = self.vol_name.sizePolicy()
        p.setHorizontalPolicy(QtGui.QSizePolicy.Expanding)
        self.vol_name.setSizePolicy(p)
        hbox.addWidget(self.vol_name)
        hbox.setStretchFactor(self.vol_name, 1)
        self.vol_data = QtGui.QLineEdit()
        self.vol_data.setFixedWidth(65)
        hbox.addWidget(self.vol_data)
        self.roi_region = QtGui.QLineEdit()
        self.roi_region.setFixedWidth(30)
        hbox.addWidget(self.roi_region)
        self.ov_data = QtGui.QLineEdit()
        self.ov_data.setFixedWidth(65)
        hbox.addWidget(self.ov_data)
        self.view_options_btn = OptionsButton(self)
        hbox.addWidget(self.view_options_btn)
        self.setLayout(hbox)

        ivl.ivm.sig_main_data.connect(self._main_changed)
        ivl.sig_focus_changed.connect(self._focus_changed)

    def show_options(self):
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

    def _focus_changed(self, pos):
        if self.ivl.ivm.main is not None: 
            self.vol_data.setText(self.ivl.ivm.main.strval(self.ivl.grid, pos))
        if self.ivl.ivm.current_roi is not None: 
            self.roi_region.setText(self.ivl.ivm.current_roi.strval(self.ivl.grid, pos))
        if self.ivl.ivm.current_data is not None: 
            self.ov_data.setText(self.ivl.ivm.current_data.strval(self.ivl.grid, pos))

class NavigationBox(QtGui.QGroupBox):
    """ Box containing 4D navigators """
    def __init__(self, ivl):
        self.ivl = ivl

        QtGui.QGroupBox.__init__(self, "Navigation")
        grid = QtGui.QGridLayout()
        self.setLayout(grid)

        self.navs = []
        self.navs.append(Navigator(ivl, "Axial", 2, grid, 0))
        self.navs.append(Navigator(ivl, "Sagittal", 0, grid, 1))
        self.navs.append(Navigator(ivl, "Coronal", 1, grid, 2))
        self.navs.append(Navigator(ivl, "Volume", 3, grid, 3))
        grid.setColumnStretch(0, 0)
        grid.setColumnStretch(1, 2)

        ivl.ivm.sig_main_data.connect(self._main_data_changed)
        ivl.sig_focus_changed.connect(self._focus_changed)

    def _main_data_changed(self, data):
        for nav in self.navs:
            if data is not None:
                if nav.axis < 3:
                    nav.set_size(self.ivl.grid.shape[nav.axis])
                else:
                    nav.set_size(data.nvols)
            else:
                nav.set_size(1)
            nav.set_pos(self.ivl.focus()[nav.axis])

    def _focus_changed(self, pos):
        for nav in self.navs:
            nav.set_pos(pos[nav.axis])

class RoiViewWidget(QtGui.QGroupBox):
    """ Change view options for ROI """
    def __init__(self, ivl):
        self.ivl = ivl
        self.ivm = ivl.ivm
        QtGui.QGroupBox.__init__(self, "ROI")
        grid = QtGui.QGridLayout()
        self.setLayout(grid)

        grid.addWidget(QtGui.QLabel("ROI"), 0, 0)
        self.roi_combo = QtGui.QComboBox()
        grid.addWidget(self.roi_combo, 0, 1)
        grid.addWidget(QtGui.QLabel("View"), 1, 0)
        self.roi_view_combo = QtGui.QComboBox()
        self.roi_view_combo.addItem("Shaded")
        self.roi_view_combo.addItem("Contour")
        self.roi_view_combo.addItem("Both")
        self.roi_view_combo.addItem("None")
        grid.addWidget(self.roi_view_combo, 1, 1)
        grid.addWidget(QtGui.QLabel("Alpha"), 2, 0)
        self.roi_alpha_sld = QtGui.QSlider(QtCore.Qt.Horizontal, self)
        self.roi_alpha_sld.setFocusPolicy(QtCore.Qt.NoFocus)
        self.roi_alpha_sld.setRange(0, 255)
        self.roi_alpha_sld.setValue(150)
        grid.addWidget(self.roi_alpha_sld, 2, 1)
        grid.setRowStretch(3, 1)

        self.roi_combo.currentIndexChanged.connect(self._combo_changed)
        self.roi_view_combo.currentIndexChanged.connect(self._view_changed)
        self.roi_alpha_sld.valueChanged.connect(self._alpha_changed)
        self.ivm.sig_all_rois.connect(self._rois_changed)
        self.ivm.sig_current_roi.connect(self._current_roi_changed)

    def update_from_roiview(self, view):
        if view is not None:
            if view.shade and view.contour:
                self.roi_view_combo.setCurrentIndex(2)
            elif view.shade:
                self.roi_view_combo.setCurrentIndex(0)
            elif view.contour:
                self.roi_view_combo.setCurrentIndex(1)
            else:
                self.roi_view_combo.setCurrentIndex(3)
            self.roi_alpha_sld.setValue(view.alpha)

    def _combo_changed(self, idx):
        if idx >= 0:
            roi = self.roi_combo.itemText(idx)
            self.ivm.set_current_roi(roi)

    def _view_changed(self, idx):
        if self.ivl.current_roi_view is not None:
            self.ivl.current_roi_view.shade = idx in (0, 2)
            self.ivl.current_roi_view.contour = idx in (1, 2)
        self.ivl._update_ortho_views()

    def _alpha_changed(self, alpha):
        """ Set the ROI transparency """
        if self.ivl.current_roi_view is not None:
            self.ivl.current_roi_view.alpha = alpha
        self.ivl._update_ortho_views()

    def _rois_changed(self, rois):
        # Repopulate ROI combo, without sending signals
        try:
            self.roi_combo.blockSignals(True)
            self.roi_combo.clear()
            for roi in rois:
                self.roi_combo.addItem(roi)
        finally:
            self.roi_combo.blockSignals(False)

        self._current_roi_changed(self.ivm.current_roi)
        self.roi_combo.updateGeometry()

    def _current_roi_changed(self, roi):
        # Update ROI combo to show the current ROI
        if roi is None:
            self.roi_combo.setCurrentIndex(-1)
        else:
            idx = self.roi_combo.findText(roi.name)
            if idx != self.roi_combo.currentIndex():
                try:
                    self.roi_combo.blockSignals(True)
                    self.roi_combo.setCurrentIndex(idx)
                finally:
                    self.roi_combo.blockSignals(False)

class OverlayViewWidget(QtGui.QGroupBox):
    """ Change view options for ROI """
    def __init__(self, ivl):
        self.ivl = ivl
        self.ivm = ivl.ivm
        QtGui.QGroupBox.__init__(self, "Overlay")
        grid = QtGui.QGridLayout()
        self.setLayout(grid)
        
        grid.addWidget(QtGui.QLabel("Overlay"), 0, 0)
        self.overlay_combo = QtGui.QComboBox()
        grid.addWidget(self.overlay_combo, 0, 1)
        grid.addWidget(QtGui.QLabel("View"), 1, 0)
        self.ov_view_combo = QtGui.QComboBox()
        self.ov_view_combo.addItem("All")
        self.ov_view_combo.addItem("Only in ROI")
        self.ov_view_combo.addItem("None")
        grid.addWidget(self.ov_view_combo, 1, 1)
        grid.addWidget(QtGui.QLabel("Color map"), 2, 0)
        hbox = QtGui.QHBoxLayout()
        self.ov_cmap_combo = QtGui.QComboBox()
        self.ov_cmap_combo.addItem("jet")
        self.ov_cmap_combo.addItem("hot")
        self.ov_cmap_combo.addItem("gist_heat")
        self.ov_cmap_combo.addItem("flame")
        self.ov_cmap_combo.addItem("bipolar")
        self.ov_cmap_combo.addItem("spectrum")
        hbox.addWidget(self.ov_cmap_combo)
        self.ov_levels_btn = QtGui.QPushButton()
        self.ov_levels_btn.setIcon(QtGui.QIcon(get_icon("levels.png")))
        self.ov_levels_btn.setFixedSize(16, 16)
        self.ov_levels_btn.setToolTip("Adjust colour map levels")
        self.ov_levels_btn.clicked.connect(self._show_ov_levels)
        self.ov_levels_btn.setEnabled(False)
        hbox.addWidget(self.ov_levels_btn)
        grid.addLayout(hbox, 2, 1)
        grid.addWidget(QtGui.QLabel("Alpha"), 3, 0)
        self.ov_alpha_sld = QtGui.QSlider(QtCore.Qt.Horizontal, self)
        self.ov_alpha_sld.setFocusPolicy(QtCore.Qt.NoFocus)
        self.ov_alpha_sld.setRange(0, 255)
        self.ov_alpha_sld.setValue(255)
        grid.addWidget(self.ov_alpha_sld, 3, 1)
        grid.setRowStretch(4, 1)

        self.overlay_combo.currentIndexChanged.connect(self._combo_changed)
        self.ov_view_combo.currentIndexChanged.connect(self._view_changed)
        self.ov_cmap_combo.currentIndexChanged.connect(self._cmap_changed)
        self.ov_alpha_sld.valueChanged.connect(self._alpha_changed)
        self.ivm.sig_all_data.connect(self._data_changed)
        self.ivm.sig_current_data.connect(self._current_data_changed)

    def _combo_changed(self, idx):
        if idx >= 0:
            ov = self.overlay_combo.itemText(idx)
            self.ivm.set_current_data(ov)

    def _cmap_changed(self, idx):
        cmap = self.ov_cmap_combo.itemText(idx)
        self.ivl.current_data_view.cmap = cmap
        self.ivl.current_data_view.sig_changed.emit(self.ivl.current_data_view)
  
    def _view_changed(self, idx):
        """ Viewing style (all or within ROI only) changed """
        if self.ivl.current_data_view is not None:
            self.ivl.current_data_view.visible = idx in (0, 1)
            self.ivl.current_data_view.roi_only = (idx == 1)
        self.ivl._current_data_changed(self.ivm.current_data)

    def _alpha_changed(self, alpha):
        """ Set the data transparency """
        if self.ivl.current_data_view is not None:
            self.ivl.current_data_view.alpha = alpha
            self.ivl.current_data_view.sig_changed.emit(self.ivl.current_data_view)
     
    def _show_ov_levels(self):
        dlg = LevelsDialog(self, self.ivm, self.ivl.current_data_view)
        dlg.exec_()

    def _data_changed(self, data):
        # Repopulate data combo, without sending signals
        try:
            self.overlay_combo.blockSignals(True)
            self.overlay_combo.clear()
            for ov in data:
                self.overlay_combo.addItem(ov)
        finally:
            self.overlay_combo.blockSignals(False)

        self._current_data_changed(self.ivm.current_data)
        self.overlay_combo.updateGeometry()

    def _current_data_changed(self, ov):
        self.ov_levels_btn.setEnabled(ov is not None)
        if ov is not None:
            # Update the data combo to show the current data
            idx = self.overlay_combo.findText(ov.name)
            debug("New current data: ", ov.name, idx)
            if idx != self.overlay_combo.currentIndex():
                try:
                    self.overlay_combo.blockSignals(True)
                    self.overlay_combo.setCurrentIndex(idx)
                finally:
                    self.overlay_combo.blockSignals(False)
        else:
            self.overlay_combo.setCurrentIndex(-1)
        self.update_from_dataview(self.ivl.current_data_view)

    def update_from_dataview(self, view):
        if view:
            if not view.visible:
                self.ov_view_combo.setCurrentIndex(2)
            elif view.roi_only:
                self.ov_view_combo.setCurrentIndex(1)
            else:
                self.ov_view_combo.setCurrentIndex(0)
            idx = self.ov_cmap_combo.findText(view.cmap)
            self.ov_cmap_combo.setCurrentIndex(idx)
            self.ov_alpha_sld.setValue(view.alpha)

class ImageView(QtGui.QSplitter):
    """
    Widget containing three orthogonal slice views, two histogram/LUT widgets plus 
    navigation sliders and data summary view.

    :ivar grid: Grid the ImageView uses as the basis for the orthogonal slices. 
                This is typically an RAS-aligned version of the main data grid, or
                alternatively an RAS world-grid
    """

    # Signals when point of focus is changed
    sig_focus_changed = QtCore.Signal(tuple)

    # Signals when the selected points / region have changed
    sig_sel_changed = QtCore.Signal(object)

    def __init__(self, ivm, opts):
        super(ImageView, self).__init__(QtCore.Qt.Vertical)

        self.grid = DataGrid([1, 1, 1], np.identity(4))
        self._pos = [0, 0, 0, 0]

        self.ivm = ivm
        self.opts = opts
        self.ivm.sig_current_data.connect(self._current_data_changed)
        self.ivm.sig_current_roi.connect(self._current_roi_changed)
        self.ivm.sig_main_data.connect(self._main_data_changed)
        self.ivm.sig_all_rois.connect(self._rois_changed)
        self.ivm.sig_all_data.connect(self._data_changed)
        self.opts.sig_options_changed.connect(self._update_ortho_views)

        # Viewer Options
        self.roi_outline_width = 3.0
        
        # Visualisation information for data and ROIs
        self.data_views = {}
        self.current_data_view = None
        self.roi_views = {}
        self.current_roi_view = None

        # Navigation controls layout
        control_box = QtGui.QWidget()
        vbox = QtGui.QVBoxLayout()
        control_box.setLayout(vbox)  

        # Create the navigation sliders and the ROI/Overlay view controls
        vbox.addWidget(DataSummary(self))
        hbox = QtGui.QHBoxLayout()
        self.nav_box = NavigationBox(self)
        hbox.addWidget(self.nav_box)
        self.roi_box = RoiViewWidget(self)
        hbox.addWidget(self.roi_box)
        self.ovl_box = OverlayViewWidget(self)
        hbox.addWidget(self.ovl_box)
        vbox.addLayout(hbox)  

        # For each view window, this is the volume indices of the x, y and z axes for the view
        self.ax_map = [[0, 1, 2], [0, 2, 1], [1, 2, 0]]
        self.ax_labels = [("L", "R"), ("P", "A"), ("I", "S")]

        # Create three orthogonal views
        self.win = {}
        for i in range(3):
            win = OrthoView(self, self.ivm, self.ax_map[i], self.ax_labels)
            win.sig_focus.connect(self._pick)
            win.sig_maxmin.connect(self._toggle_maximise)
            self.win[win.zaxis] = win

        # Histogram which controls colour map and levels for main volume
        self.h1 = MultiImageHistogramWidget(self.ivm, self, imgs=[w.img for w in self.win.values()], percentile=99)
        
        # Histogram which controls colour map and levels for data
        self.h2 = MultiImageHistogramWidget(self.ivm, self, imgs=[w.img_ovl for w in self.win.values()])

        # Main graphics layout
        #gview = pg.GraphicsView(background='k')
        gview = QtGui.QWidget()
        self.layout_grid = QtGui.QGridLayout()
        self.layout_grid.setHorizontalSpacing(2)
        self.layout_grid.setVerticalSpacing(2)
        self.layout_grid.setContentsMargins(0, 0, 0, 0)
        self.layout_grid.addWidget(self.win[1], 0, 0,)
        self.layout_grid.addWidget(self.win[0], 0, 1)
        self.layout_grid.addWidget(self.h1, 0, 2)
        self.layout_grid.addWidget(self.win[2], 1, 0)
        self.layout_grid.addWidget(self.h2, 1, 2)
        self.layout_grid.setColumnStretch(0, 3)
        self.layout_grid.setColumnStretch(1, 3)
        self.layout_grid.setColumnStretch(2, 1)
        self.layout_grid.setRowStretch(0, 1)
        self.layout_grid.setRowStretch(1, 1)
        gview.setLayout(self.layout_grid)
        self.addWidget(gview)
        self.addWidget(control_box)
        self.setStretchFactor(0, 5)
        self.setStretchFactor(1, 1)

        self.picker = PointPicker(self) 
        self.drag_mode = DragMode.DEFAULT
      
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
            world = self.grid.grid_to_world(self._pos[:3])
            return list(grid.world_to_grid(world)) + [self._pos[3], ]

    def set_focus(self, pos, grid=None):
        """
        Set the current focus position

        :param grid: Specify position using co-ordinates relative to this grid. 
                     If not specified, position is in current view grid co-ordinates
        """
        if grid is not None:
            world = grid.grid_to_world(pos[:3])
            pos = list(self.grid.world_to_grid(world)) + [pos[3], ]

        self._pos = list(pos)
        self._update_ortho_views()
        
        debug("Cursor position: ", self._pos)
        self.sig_focus_changed.emit(self._pos)

    def set_picker(self, pickmode, drag_mode = DragMode.DEFAULT):
        self.picker.cleanup()
        self.picker = PICKERS[pickmode](self)
        self.drag_mode = drag_mode
        
    def capture_view_as_image(self, window, outputfile):
        """ Export an image using pyqtgraph """
        if window not in (1, 2, 3):
            raise RuntimeError("No such window: %i" % window)

        expimg = self.win[window-1].img
        exporter = ImageExporter(expimg)
        exporter.parameters()['width'] = 2000
        exporter.export(str(outputfile))

    def _pick(self, pos, win, is_click):
        if self.picker.win is not None and win != self.picker.win:
            # Bit of a hack. Ban focus changes in other windows when we 
            # have a single-window picker because it will change the slice 
            # visible in the pick window
            return
        if is_click:
            self.picker.add_point(pos, win)

        self.set_focus(pos)

    def _toggle_maximise(self, win, state=-1):
        """ 
        Maximise/Minimise view window
        If state=1, maximise, 0=show all, -1=toggle 
        """
        o1 = (win+1) % 3
        o2 = (win+2) % 3
        if state == 1 or (state == -1 and self.win[o1].isVisible()):
            # Maximise
            self.layout_grid.addWidget(self.win[win], 0, 0, 2, 2)
            self.win[o1].setVisible(False)
            self.win[o2].setVisible(False)
            self.win[win].setVisible(True)
        elif state == 0 or (state == -1 and not self.win[o1].isVisible()):
            # Show all three
            self.layout_grid.addWidget(self.win[1], 0, 0, )
            self.layout_grid.addWidget(self.win[0], 0, 1)
            self.layout_grid.addWidget(self.win[2], 1, 0)
            self.win[o1].setVisible(True)
            self.win[o2].setVisible(True)
            self.win[win].setVisible(True)

    def _update_ortho_views(self):
        """ Update the image viewer windows """
        for win in self.win.values(): win.update()

    def _main_data_changed(self, data):
        if data is not None:
            self.grid = data.grid.get_standard()
            debug("Main data raw grid")
            debug(data.grid.affine)
            debug("RAS aligned")
            debug(self.grid.affine)

            main_dv = DataView(self.ivm, data.name)
            main_dv.cmap = "grey"
            self.h1.set_data_view(main_dv)

            # If one of the dimensions has size 1 the data is 2D so
            # maximise the relevant slice
            self._toggle_maximise(0, state=0)
            for d in range(3):
                if self.grid.shape[d] == 1:
                    self._toggle_maximise(d, state=1)
        self._update_ortho_views()

    def _rois_changed(self, rois):
        # Discard RoiView instances for data which has been deleted
        for name in self.roi_views.keys():
            if name not in rois:
                if self.roi_views[name] == self.current_roi_view:
                    self.current_roi_view = None
                del self.roi_views[name]

        self._current_roi_changed(self.ivm.current_roi)

    def _current_roi_changed(self, roi):
        # Update ROI combo to show the current ROI
        if roi is None:
            self.current_roi_view = None
        else:
            if roi.name not in self.roi_views:
                # Create an ROI view if we don't already have one for this ROI
                self.roi_views[roi.name] = RoiView(self.ivm, roi.name)
            self.current_roi_view = self.roi_views[roi.name]

        self.roi_box.update_from_roiview(self.current_roi_view)
        self._update_ortho_views()

    def _data_changed(self, data):
        debug("New data: ", data)
        # Discard DataView instances for data which has been deleted
        for name in self.data_views.keys():
            if name not in data:
                del self.data_views[name]

        self._current_data_changed(self.ivm.current_data)

    def _current_data_changed(self, ov):
        if self.current_data_view is not None:
            self.current_data_view.sig_changed.disconnect(self._dv_changed)
        if ov is not None:
            if ov.name not in self.data_views:
                # Create a data view if we don't already have one for this data
                self.data_views[ov.name] = DataView(self.ivm, ov.name)

            self.current_data_view = self.data_views[ov.name]
            self.current_data_view.sig_changed.connect(self._dv_changed)
        else:
            self.current_data_view = None
        self.h2.set_data_view(self.current_data_view)
        self._update_ortho_views()

    def _dv_changed(self, dv):
        self._update_ortho_views()
