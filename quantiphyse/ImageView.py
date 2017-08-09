"""
Author: Benjamin Irving (benjamin.irv@gmail.com), Martin Craig (martin.craig@eng.ox.ac.uk)
Copyright (c) 2013-2015 University of Oxford
"""

from __future__ import division, unicode_literals, absolute_import, print_function

import sys
import matplotlib

from matplotlib import cm
from PySide import QtCore, QtGui
import warnings
import numpy as np
import weakref

import pyqtgraph as pg
from pyqtgraph.exporters.ImageExporter import ImageExporter
from PIL import Image, ImageDraw

from .utils import get_icon, get_lut

class MultiImageHistogramWidget(pg.HistogramLUTWidget):
    """
    A histogram widget which has one array of 'source' data
    (which it gets the histogram itself and the initial levels from)
    and multiple image item views which are affected by changes to the
    levels or LUT
    """
    def __init__(self, *args, **kwargs):
        super(MultiImageHistogramWidget, self).__init__(*args, **kwargs)
        self.imgs = []
        self.sigLevelChangeFinished.connect(self.levels_changed)
        self.sigLevelsChanged.connect(self.levels_changed)
        self.sigLookupTableChanged.connect(self.lut_changed)
        self.alpha = 255

    def setSourceData(self, arr, percentile=100):
        """
        Set the source data for the histogram widget. This is likely to be a
        3d or 4d volume, so we flatten it to 2d in order to use the PyQtGraph
        methods to extract a histogram

        @percentile specifies that the initial LUT range should be set to this
        percentile of the data - for main volume it is useful to set this 
        to 99% to improve visibility
        """
        self.region.setRegion([np.min(arr), np.max(arr)])
        self.region.setBounds([np.min(arr), None])
        self.region.lines[0].setValue(np.min(arr))
        self.region.lines[1].setValue(np.percentile(arr, percentile))
        fdim = 1
        for dim in arr.shape[1:]:
            fdim *= dim
        newarr = arr.reshape(arr.shape[0], fdim)
        ii = pg.ImageItem(newarr)
        h = ii.getHistogram()
        if h[0] is None: return
        self.plot.setData(*h)

    def setAlpha(self, alpha):
        self.alpha = alpha
        self.lut = None
        self.lut_changed()

    def setGradientName(self, name):
        self.cmap_name = name
        try:
            self.gradient.loadPreset(name)
        except KeyError:
            self.setMatplotlibGradient(name)

    def setMatplotlibGradient(self, name):
        """
        Slightly hacky method to copy MatPlotLib gradients to pyqtgraph.

        Is not perfect because Matplotlib specifies gradients in a different way to pyqtgraph
        (specifically there is a separate list of ticks for R, G and B). So we just sample
        the colormap at 10 points which is OK for most slowly varying gradients.
        """
        cmap = getattr(cm, name)
        ticks = [(pos, [255 * v for v in cmap(pos)]) for pos in np.linspace(0, 1, 10)]
        self.gradient.restoreState({'ticks': ticks, 'mode': 'rgb'})

    def getImageLut(self, img):
        lut = self.getLookupTable(img, alpha=True)

        for row in lut[1:]:
            row[3] = self.alpha

        lut[0][3] = 0
        self.lut = lut
        return lut

    def addImageItem(self, img):
        self.imgs.append(weakref.ref(img))
        img.setLookupTable(self.getImageLut)
        img.setLevels(self.region.getRegion())

    def levels_changed(self):
        for img in self.imgs:
            if img() is not None:
                img().setLevels(self.region.getRegion())

    def lut_changed(self):
        for img in self.imgs:
            if img() is not None:
                img().setLookupTable(self.getImageLut, update=True)

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
        self.iv = iv
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
        self.points[self.col] = []

    def add_point(self, pos, win):
        self.points[self.col] = [tuple(pos),]
        self.point = tuple(pos)
        self.iv.sig_sel_changed.emit(self)

class MultiPicker(PointPicker):
    def __init__(self, iv, col=(255, 0, 0)):
        PointPicker.__init__(self, iv, col)
        self.arrows = []

    def add_point(self, pos, win):
        if self.col not in self.points: 
            self.points[self.col] = []
        self.points[self.col].append(tuple(pos))
        for win in self.iv.win.values():
            win.add_arrow(pos, self.col)
        self.iv.sig_sel_changed.emit(self)
    
    def cleanup(self):
        for w in range(3):
            win = self.iv.win[w].remove_arrows()

class SliceMultiPicker(MultiPicker):
    def __init__(self, iv, col=(255, 0, 0)):
        MultiPicker.__init__(self, iv, col)

    def add_point(self, pos, win):
        if self.col not in self.points: 
            self.points[self.col] = []
        
        if self.win is None:
            self.win = win
            self.zaxis = self.iv.win[win].zaxis
            self.zpos = pos[self.zaxis]

        if win == self.win and pos[self.zaxis] == self.zpos:
            self.points[self.col].append(tuple(pos))
            self.iv.win[win].add_arrow(pos, self.col)

        self.iv.sig_sel_changed.emit(self)

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
            self.view = self.iv.win[self.win]
            self.view.vb.addItem(self.roisel)
        
        fx, fy = float(pos[self.view.xaxis])+0.5, float(pos[self.view.yaxis])+0.5
        self.points.append((fx, fy))

        self.roisel.setPoints(self.points)

    def get_roi(self, label=1):
        """ Get the selected points as an ROI"""
        if self.win is None: return None    

        w, h = self.iv.ivm.grid.shape[self.view.xaxis], self.iv.ivm.grid.shape[self.view.yaxis]
        img = Image.new('L', (w, h), 0)
        ImageDraw.Draw(img).polygon(self.points, outline=label, fill=label)
        
        ret = np.zeros(self.view.ivm.grid.shape)
        slice_mask = np.array(img).T
        slices = [slice(None)] * 3
        slices[self.view.zaxis] = self.view.ivm.cim_pos[self.view.zaxis]
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
            self.view = self.iv.win[self.win]
        
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
            self.view = self.iv.win[self.win]
        
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

        w, h = self.iv.ivm.grid.shape[self.view.xaxis], self.iv.ivm.grid.shape[self.view.yaxis]
        img = Image.new('L', (w, h), 0)
        ImageDraw.Draw(img).ellipse([int(p) for p in self.points], outline=label, fill=label)
        
        ret = np.zeros(self.view.ivm.grid.shape)
        slice_mask = np.array(img).T
        slices = [slice(None)] * 3
        slices[self.view.zaxis] = self.view.ivm.cim_pos[self.view.zaxis]
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
            self.view = self.iv.win[self.win]
            
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

class DataView:
    """
    View of a data item, storing details about visual parameters, e.g.
    color map and min/max range for color mapping
    """
    def __init__(self, ivm, ov_name):
        self.ivm = ivm
        self.ov_name = ov_name
        self.cmap = "jet"
        self.visible = True
        self.alpha = 255
        self.roi_only = True
        d = self.data()
        self.cmap_range = d.range

    def get_slice(self, *axes):
        if self.roi_only:
            return self.data().get_slice(axes, mask=self.ivm.current_roi)
        else:
            return self.data().get_slice(axes)

    def data(self):
        return self.ivm.data[self.ov_name]

class RoiView:
    """
    View of an ROI, storing details about visual parameters, e.g. contour plotting
    """
    def __init__(self, ivm, roi_name):
        self.ivm = ivm
        self.roi_name = roi_name
        #self.cmap = "jet"
        self.shade = True
        self.contour = False
        self.alpha = 150

    def roi(self):
        return self.ivm.rois[self.roi_name]

class OrthoView(pg.GraphicsView):
    """
    A single slice view of data and ROI
    """

    # Signals when point of focus is changed
    sig_focus = QtCore.Signal(tuple, int, bool)

    # Signals when view is maximised/minimised
    sig_maxmin = QtCore.Signal(int)

    def __init__(self, iv, ivm, ax_map, ax_labels):
        pg.GraphicsView.__init__(self)
        self.iv = iv
        self.ivm = ivm
        self.xaxis, self.yaxis, self.zaxis = ax_map
        self.dragging = False
        self.contours = []
        self.arrows = []

        self.img = pg.ImageItem(border='k')
        self.img_roi = pg.ImageItem(border='k')
        self.img_ovl = pg.ImageItem(border='k')

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
            return

        # Adjust axis scaling depending on whether voxel size scaling is enabled
        if self.iv.opts.size_scaling == self.iv.opts.SCALE_VOXELS:
            self.vb.setAspectLocked(True, ratio=(self.ivm.grid.spacing[self.xaxis] / self.ivm.grid.spacing[self.yaxis]))
        else:
            self.vb.setAspectLocked(True, ratio=1)
        for l in self.labels:
            l.setVisible(True)

        # Flip left/right depending on the viewing convention selected
        if self.xaxis == 0:
            # X-axis is left/right
            self.vb.invertX(self.iv.opts.orientation == 0)
            if self.iv.opts.orientation == self.iv.opts.RADIOLOGICAL: l, r = 1, 0
            else: l, r = 0, 1
            self.labels[r].setText("R")
            self.labels[l].setText("L")
        
        # Plot image slices
        pos = self.ivm.cim_pos
        slices = [(self.zaxis, pos[self.zaxis]), (3, pos[3])]
        slicedata = self.ivm.main.get_slice(slices)
        #print(pos)
        #print(slicedata.shape)
        self.img.setImage(self.ivm.main.get_slice(slices), autoLevels=False)

        self.vline.setPos(float(self.ivm.cim_pos[self.xaxis])+0.5)
        self.hline.setPos(float(self.ivm.cim_pos[self.yaxis])+0.5)
        self.vline.setVisible(self.iv.show_crosshairs)
        self.hline.setVisible(self.iv.show_crosshairs)

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
        roiview = self.iv.current_roi_view
        n = 0 # Number of contours - required at end
        if roiview is None:
            self.img_roi.setImage(np.zeros((1, 1)))
        else:
            roidata = roiview.roi()
            z = 0
            if self.iv.opts.display_order == self.iv.opts.ROI_ON_TOP: z=1

            pos = self.ivm.cim_pos
            lut = get_lut(roidata, roiview.alpha)
            roi_levels = roidata.range
            
            if roiview.shade:
                slicedata = roidata.get_slice([(self.zaxis, self.ivm.cim_pos[self.zaxis]), (3, self.ivm.cim_pos[3])])
                self.img_roi.setImage(slicedata, lut=lut, autoLevels=False, levels=roi_levels)
                self.img_roi.setZValue(z)
            else:
                self.img_roi.setImage(np.zeros((1, 1)))

            if roiview.contour:
                data = roidata.get_slice([(self.zaxis, pos[self.zaxis])])
                
                # Update data and level for existing contour items, and create new ones if needed
                n_conts = len(self.contours)
                create_new = False
                for val in roidata.regions:
                    pencol = roidata.get_pencol(val)
                    if val != 0:
                        if n == n_conts:
                            create_new = True

                        if create_new:
                            self.contours.append(pg.IsocurveItem())
                            self.vb.addItem(self.contours[n])

                        d = self._iso_prepare(data, val)
                        self.contours[n].setData(d)
                        self.contours[n].setLevel(1)
                        self.contours[n].setPen(pg.mkPen(pencol, width=self.iv.roi_outline_width))

                    n += 1

        # Set data to None for any existing contour items that we are not using right now 
        # FIXME should we delete these?
        for idx in range(n, len(self.contours)):
            self.contours[idx].setData(None)

    def _update_view_overlay(self):
        oview = self.iv.current_data_view
        if oview is None or not oview.visible:
            self.img_ovl.setImage(np.zeros((1, 1)), autoLevels=False)
        else:
            z = 1
            if self.iv.opts.display_order == self.iv.opts.ROI_ON_TOP: z=0
            self.img_ovl.setZValue(z)
            
            slicedata = oview.get_slice((self.zaxis, self.ivm.cim_pos[self.zaxis]),
                                        (3, self.ivm.cim_pos[3]))
            #print(self.ivm.cim_pos)
            #print(slicedata.shape)
            self.img_ovl.setImage(slicedata, autoLevels=False)

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
        if self.ivm.grid is None: return
        dz = int(event.delta()/120)
        pos = self.ivm.cim_pos[:]
        pos[self.zaxis] += dz
        if pos[self.zaxis] >= self.ivm.grid.shape[self.zaxis] or pos[self.zaxis] < 0:
            return

        self.sig_focus.emit(pos, self.zaxis, False)

    def mousePressEvent(self, event):
        super(OrthoView, self).mousePressEvent(event)
        if self.ivm.main is None: return
        
        if event.button() == QtCore.Qt.LeftButton:
            self.dragging = (self.iv.drag_mode == DragMode.PICKER_DRAG)
            
            coords = self.img.mapFromScene(event.pos())
            mx = int(coords.x())
            my = int(coords.y())
            if mx < 0 or mx >= self.ivm.grid.shape[self.xaxis]: return
            if my < 0 or my >= self.ivm.grid.shape[self.yaxis]: return
            pos = self.ivm.cim_pos[:]
            pos[self.xaxis] = mx
            pos[self.yaxis] = my
            self.sig_focus.emit(pos, self.zaxis, True)

    def add_arrow(self, pos, col):
        arrow = pg.ArrowItem(pen=col, brush=col)
        arrow.setPos(float(pos[self.xaxis])+0.5, float(pos[self.yaxis])+0.5)
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
        for zpos, arrow in self.arrows:
            arrow.setVisible(self.ivm.cim_pos[self.zaxis] == zpos)

    def mouseReleaseEvent(self, event):
        super(OrthoView, self).mouseReleaseEvent(event)
        self.dragging = False
        
    def mouseDoubleClickEvent(self, event):
        super(OrthoView, self).mouseDoubleClickEvent(event)
        if event.button() == QtCore.Qt.LeftButton:
            self.sig_maxmin.emit(self.zaxis)

    def mouseMoveEvent(self, event):
        #print("move")
        if self.dragging:
            coords = self.img.mapFromScene(event.pos())
            mx = int(coords.x())
            my = int(coords.y())
            #print("drag", mx, my)
            pos = self.ivm.cim_pos[:]
            pos[self.xaxis] = mx
            pos[self.yaxis] = my
            self.sig_focus.emit(pos, self.zaxis, True)
            #print("drag=", event)
        else:
            super(OrthoView, self).mouseMoveEvent(event)

class OvLevelsDialog(QtGui.QDialog):

    def __init__(self, parent, dv, hist):
        super(OvLevelsDialog, self).__init__(parent)
        self.dv = dv
        self.hist = hist

        self.setWindowTitle("Levels for %s" % dv.ov_name)
        vbox = QtGui.QVBoxLayout()

        grid = QtGui.QGridLayout()
        self.add_spin(grid, "Minimum", 0)
        self.add_spin(grid, "Maximum", 1)   
        grid.addWidget(QtGui.QLabel("Values outside range are"), 2, 0)
        self.combo = QtGui.QComboBox()
        self.combo.addItem("Transparent")
        self.combo.addItem("Clamped to max/min colour")
        self.combo.setEnabled(False)
        grid.addWidget(self.combo, 2, 1)
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

    def val_changed(self, row):
        def val_changed(val):
            self.dv.cmap_range[row] = val
            self.hist.region.setRegion(self.dv.cmap_range)
        return val_changed

class ImageView(QtGui.QSplitter):
    """
    Widget containing three orthogonal slice views, two histogram/LUT widgets plus 
    navigation sliders and data summary view
    """

    # Signals when point of focus is changed
    sig_focus_changed = QtCore.Signal(tuple)

    # Signals when the selected points / region have changed
    sig_sel_changed = QtCore.Signal(object)

    def __init__(self, ivm, opts):
        super(ImageView, self).__init__(QtCore.Qt.Vertical)

        self.ivm = ivm
        self.opts = opts
        self.ivm.sig_current_data.connect(self.current_data_changed)
        self.ivm.sig_current_roi.connect(self.current_roi_changed)
        self.ivm.sig_main_data.connect(self.main_volume_changed)
        self.ivm.sig_all_rois.connect(self.rois_changed)
        self.ivm.sig_all_data.connect(self.data_changed)
        self.opts.sig_options_changed.connect(self.update_ortho_views)

        # Viewer Options
        self.roi_outline_width = 3.0
        self.show_crosshairs = True
        
        # Visualisation information for data and ROIs
        self.data_views = {}
        self.current_data_view = None
        self.roi_views = {}
        self.current_roi_view = None

        # Create the navigation sliders
        gBox2 = QtGui.QGroupBox("Navigation")
        gBoxlay2 = QtGui.QGridLayout()

        gBoxlay2.addWidget(QtGui.QLabel('Axial'), 0, 0)
        self.sld1 = QtGui.QSlider(QtCore.Qt.Horizontal, self)
        self.sld1.setFocusPolicy(QtCore.Qt.NoFocus)
        self.sld1.setMinimumWidth(100)
        gBoxlay2.addWidget(self.sld1, 0, 1)
        lab_p1 = QtGui.QLabel('0')
        gBoxlay2.addWidget(lab_p1, 0, 2)

        gBoxlay2.addWidget(QtGui.QLabel('Coronal'), 1, 0)
        self.sld2 = QtGui.QSlider(QtCore.Qt.Horizontal, self)
        self.sld2.setFocusPolicy(QtCore.Qt.NoFocus)
        self.sld2.setMinimumWidth(100)
        gBoxlay2.addWidget(self.sld2, 1, 1)
        lab_p2 = QtGui.QLabel('0')
        gBoxlay2.addWidget(lab_p2, 1, 2)

        gBoxlay2.addWidget(QtGui.QLabel('Sagittal'), 2, 0)
        self.sld3 = QtGui.QSlider(QtCore.Qt.Horizontal, self)
        self.sld3.setFocusPolicy(QtCore.Qt.NoFocus)
        self.sld3.setMinimumWidth(100)
        gBoxlay2.addWidget(self.sld3, 2, 1)
        lab_p3 = QtGui.QLabel('0')
        gBoxlay2.addWidget(lab_p3, 2, 2)

        gBoxlay2.addWidget(QtGui.QLabel('Volume'), 3, 0)
        self.sld4 = QtGui.QSlider(QtCore.Qt.Horizontal, self)
        self.sld4.setFocusPolicy(QtCore.Qt.NoFocus)
        self.sld4.setMinimumWidth(100)
        gBoxlay2.addWidget(self.sld4, 3, 1)
        lab_p4 = QtGui.QLabel('0')
        gBoxlay2.addWidget(lab_p4, 3, 2)

        gBoxlay2.setColumnStretch(0, 0)
        gBoxlay2.setColumnStretch(1, 2)
        gBox2.setLayout(gBoxlay2)

        self.sld1.valueChanged[int].connect(self.set_pos(2))
        self.sld2.valueChanged[int].connect(self.set_pos(0))
        self.sld3.valueChanged[int].connect(self.set_pos(1))
        self.sld4.valueChanged[int].connect(self.set_pos(3))
        self.sld1.valueChanged[int].connect(lab_p1.setNum)
        self.sld2.valueChanged[int].connect(lab_p2.setNum)
        self.sld3.valueChanged[int].connect(lab_p3.setNum)
        self.sld4.valueChanged[int].connect(lab_p4.setNum)

        # Create the ROI/Overlay view controls
        gBox = QtGui.QGroupBox("ROI")
        grid = QtGui.QGridLayout()
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
        gBox.setLayout(grid)

        self.roi_combo.currentIndexChanged.connect(self.roi_combo_changed)
        self.roi_view_combo.currentIndexChanged.connect(self.roi_view_changed)
        self.roi_alpha_sld.valueChanged.connect(self.roi_alpha_changed)

        gBox3 = QtGui.QGroupBox("Overlay")
        grid = QtGui.QGridLayout()
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
        self.ov_levels_btn.clicked.connect(self.show_ov_levels)
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
        gBox3.setLayout(grid)

        self.overlay_combo.currentIndexChanged.connect(self.overlay_combo_changed)
        self.ov_view_combo.currentIndexChanged.connect(self.overlay_view_changed)
        self.ov_cmap_combo.currentIndexChanged.connect(self.overlay_cmap_changed)
        self.ov_alpha_sld.valueChanged.connect(self.overlay_alpha_changed)

        # Navigation controls layout
        gBox_all = QtGui.QWidget()
        gBoxlay_all = QtGui.QHBoxLayout()
        gBoxlay_all.addWidget(gBox2)
        gBoxlay_all.addWidget(gBox)
        gBoxlay_all.addWidget(gBox3)
        
        # Data summary bar
        hbox = QtGui.QHBoxLayout()
        self.vol_name = QtGui.QLineEdit()
        p = self.vol_name.sizePolicy()
        p.setHorizontalPolicy(QtGui.QSizePolicy.Expanding)
        self.vol_name.setSizePolicy(p)
        hbox.addWidget(self.vol_name)
        hbox.setStretchFactor(self.vol_name, 1)
        self.vol_data = QtGui.QLineEdit()
        self.vol_data.setFixedWidth(60)
        hbox.addWidget(self.vol_data)
        self.roi_region = QtGui.QLineEdit()
        self.roi_region.setFixedWidth(30)
        hbox.addWidget(self.roi_region)
        self.ov_data = QtGui.QLineEdit()
        self.ov_data.setFixedWidth(60)
        hbox.addWidget(self.ov_data)
        self.view_options_btn = QtGui.QPushButton()
        self.view_options_btn.setIcon(QtGui.QIcon(get_icon("options.png")))
        self.view_options_btn.setFixedSize(24, 24)
        self.view_options_btn.clicked.connect(self.view_options)
        hbox.addWidget(self.view_options_btn)

        vbox = QtGui.QVBoxLayout()
        vbox.addLayout(hbox)
        vbox.addLayout(gBoxlay_all)  
        gBox_all.setLayout(vbox)  

        # For each view window, this is the volume indices of the x, y and z axes for the view
        self.ax_map = [[0, 1, 2], [0, 2, 1], [1, 2, 0]]
        self.ax_labels = [("L", "R"), ("P", "A"), ("I", "S")]

        # Create three orthogonal views
        self.win = {}
        for i in range(3):
            win = OrthoView(self, self.ivm, self.ax_map[i], self.ax_labels)
            win.sig_focus.connect(self.view_focus)
            win.sig_maxmin.connect(self.max_min)
            self.win[win.zaxis] = win

        # Histogram which controls colour map and levels for main volume
        self.h1 = MultiImageHistogramWidget(fillHistogram=False)
        self.h1.addImageItem(self.win[0].img)
        self.h1.addImageItem(self.win[1].img)
        self.h1.addImageItem(self.win[2].img)
        self.h1.setBackground(background=None)
        
        # Histogram which controls colour map and levels for data
        self.h2 = MultiImageHistogramWidget(fillHistogram=False)
        self.h2.setBackground(background=None)
        self.h2.setGradientName("jet")
        for i in range(3):
            self.h2.addImageItem(self.win[i].img_ovl)

        # Main graphics layout
        #gview = pg.GraphicsView(background='k')
        gview = QtGui.QWidget()
        self.grid = QtGui.QGridLayout()
        self.grid.setHorizontalSpacing(2)
        self.grid.setVerticalSpacing(2)
        self.grid.setContentsMargins(0, 0, 0, 0)
        self.grid.addWidget(self.win[1], 0, 0,)
        self.grid.addWidget(self.win[0], 0, 1)
        self.grid.addWidget(self.h1, 0, 2)
        self.grid.addWidget(self.win[2], 1, 0)
        self.grid.addWidget(self.h2, 1, 2)
        self.grid.setColumnStretch(0, 3)
        self.grid.setColumnStretch(1, 3)
        self.grid.setColumnStretch(2, 1)
        self.grid.setRowStretch(0, 1)
        self.grid.setRowStretch(1, 1)
        gview.setLayout(self.grid)
        self.addWidget(gview)
        self.addWidget(gBox_all)
        self.setStretchFactor(0, 5)
        self.setStretchFactor(1, 1)

        self.picker = PointPicker(self) 
        self.drag_mode = DragMode.DEFAULT

    def view_options(self):
        self.opts.show()
        self.opts.raise_()
        
    def show_ov_levels(self):
        dlg = OvLevelsDialog(self, self.current_data_view, self.h2)
        dlg.exec_()

    def view_focus(self, pos, win, is_click):
        if self.picker.win is not None and win != self.picker.win:
            # Bit of a hack. Ban focus changes in other windows when we 
            # have a single-window picker because it will change the slice 
            # visible in the pick window
            return
        if is_click:
            self.picker.add_point(pos, win)
        
        self.ivm.cim_pos = pos
        self.update_nav_sliders()
        self.update_ortho_views()

        # FIXME should this be a signal from IVM?
        self.sig_focus_changed.emit(pos)

    def set_picker(self, pickmode, drag_mode = DragMode.DEFAULT):
        self.picker.cleanup()
        self.picker = PICKERS[pickmode](self)
        self.drag_mode = drag_mode
        
    def max_min(self, win, state=-1):
        """ Maximise/Minimise view window
        If state=1, maximise, 0=show all, -1=toggle """
        o1 = (win+1) % 3
        o2 = (win+2) % 3
        if state == 1 or (state == -1 and self.win[o1].isVisible()):
            # Maximise
            self.grid.addWidget(self.win[win], 0, 0, 2, 2)
            self.win[o1].setVisible(False)
            self.win[o2].setVisible(False)
            self.win[win].setVisible(True)
        elif state == 0 or (state == -1 and not self.win[o1].isVisible()):
            # Show all three
            self.grid.addWidget(self.win[1], 0, 0, )
            self.grid.addWidget(self.win[0], 0, 1)
            self.grid.addWidget(self.win[2], 1, 0)
            self.win[o1].setVisible(True)
            self.win[o2].setVisible(True)
            self.win[win].setVisible(True)

    def update_ortho_views(self):
        """ Update the image viewer windows """
        for win in self.win.values(): win.update()

    def set_pos(self, dim):
        def set_pos(value):
            if self.ivm.cim_pos[dim] != value:
                # Don't do any updating if the value has not changed
                self.ivm.cim_pos[dim] = value
                self.update_ortho_views()
        return set_pos

    def capture_view_as_image(self, window, outputfile):
        """ Export an image using pyqtgraph """
        if window not in (1, 2, 3):
            raise RuntimeError("No such window: %i" % window)

        expimg = self.win[window-1].img
        exporter = ImageExporter(expimg)
        exporter.parameters()['width'] = 2000
        exporter.export(str(outputfile))

    def main_volume_changed(self, vol):
        self.update_slider_range()
        self.update_nav_sliders()
        if vol is not None:
            self.vol_name.setText(vol.fname)
            self.h1.setSourceData(self.ivm.main.std, percentile=99)

            # If one of the dimensions has size 1 the data is 2D so
            # maximise the relevant slice
            self.max_min(0, state=0)
            for d in range(3):
                if self.ivm.grid.shape[d] == 1:
                    self.max_min(d, state=1)
        else:
            self.vol_name.setText("")

        self.update_ortho_views()

    def roi_combo_changed(self, idx):
        if idx >= 0:
            roi = self.roi_combo.itemText(idx)
            self.ivm.set_current_roi(roi)

    def rois_changed(self, rois):
        # Repopulate ROI combo, without sending signals
        try:
            self.roi_combo.blockSignals(True)
            self.roi_combo.clear()
            for roi in rois:
                self.roi_combo.addItem(roi)
        finally:
            self.roi_combo.blockSignals(False)
        self.current_roi_changed(self.ivm.current_roi)
        self.roi_combo.updateGeometry()

    def current_roi_changed(self, roi):
        # Update ROI combo to show the current ROI
        if roi is None:
            self.roi_combo.setCurrentIndex(-1)
            self.current_roi_view = None
        else:
            idx = self.roi_combo.findText(roi.name)
            if idx != self.roi_combo.currentIndex():
                try:
                    self.roi_combo.blockSignals(True)
                    self.roi_combo.setCurrentIndex(idx)
                finally:
                    self.roi_combo.blockSignals(False)

            if roi.name not in self.roi_views:
                # Create an ROI view if we don't already have one for this ROI
                self.roi_views[roi.name] = RoiView(self.ivm, roi.name)
            self.current_roi_view = self.roi_views[roi.name]

        self.update_view_widgets()
        self.update_ortho_views()

    def roi_view_changed(self, idx):
        if self.current_roi_view is not None:
            self.current_roi_view.shade = idx in (0, 2)
            self.current_roi_view.contour = idx in (1, 2)
        self.update_view_widgets()
        self.update_ortho_views()

    def roi_alpha_changed(self, alpha):
        """ Set the ROI transparency """
        if self.current_roi_view is not None:
            self.current_roi_view.alpha = alpha
        self.update_ortho_views()

    def overlay_combo_changed(self, idx):
        if idx >= 0:
            ov = self.overlay_combo.itemText(idx)
            self.ivm.set_current_data(ov)

    def overlay_cmap_changed(self, idx):
        cmap = self.ov_cmap_combo.itemText(idx)
        self.current_data_view.cmap = cmap
        self.update_view_widgets()

    def data_changed(self, data):
        # Repopulate data combo, without sending signals
        try:
            self.overlay_combo.blockSignals(True)
            self.overlay_combo.clear()
            for ov in data:
                self.overlay_combo.addItem(ov)
        finally:
            self.overlay_combo.blockSignals(False)
        self.current_data_changed(self.ivm.current_data)
        self.overlay_combo.updateGeometry()

    def current_data_changed(self, ov):
        self.ov_levels_btn.setEnabled(ov is not None)
        if ov is not None:
            # Update the overlay combo to show the current overlay
            #print(ov)
            idx = self.overlay_combo.findText(ov.name)
            if idx != self.overlay_combo.currentIndex():
                try:
                    self.overlay_combo.blockSignals(True)
                    self.overlay_combo.setCurrentIndex(idx)
                finally:
                    self.overlay_combo.blockSignals(False)

            if ov.name not in self.data_views:
                # Create a data view if we don't already have one for this overlay
                self.data_views[ov.name] = DataView(self.ivm, ov.name)

            if self.current_data_view is not None:
                # Update the view parameters from the existing overlay and free the within-ROI data
                self.current_data_view.cmap_range = list(self.h2.region.getRegion())
                self.current_data_view.cmap = self.h2.cmap_name

            self.current_data_view = self.data_views[ov.name]
            self.update_view_widgets()
        else:
            self.overlay_combo.setCurrentIndex(-1)
            self.current_data_view = None
        self.update_ortho_views()

    def overlay_view_changed(self, idx):
        """ Viewing style (all or within ROI only) changed """
        if self.current_data_view is not None:
            self.current_data_view.visible = idx in (0, 1)
            self.current_data_view.roi_only = (idx == 1)
        self.current_data_changed(self.ivm.current_data)

    def overlay_alpha_changed(self, alpha):
        """ Set the overlay transparency """
        if self.current_data_view is not None:
            self.current_data_view.alpha = alpha
        self.update_view_widgets()
            
    def update_view_widgets(self):
        if self.current_data_view:
            self.h2.setGradientName(self.current_data_view.cmap)
            self.h2.setSourceData(self.current_data_view.data().std)
            self.h2.region.setRegion(self.current_data_view.cmap_range)
            self.h2.setAlpha(self.current_data_view.alpha)

            if not self.current_data_view.visible:
                self.ov_view_combo.setCurrentIndex(2)
            elif self.current_data_view.roi_only:
                self.ov_view_combo.setCurrentIndex(1)
            else:
                self.ov_view_combo.setCurrentIndex(0)
            idx = self.ov_cmap_combo.findText(self.current_data_view.cmap)
            self.ov_cmap_combo.setCurrentIndex(idx)
            self.ov_alpha_sld.setValue(self.current_data_view.alpha)

        if self.current_roi_view:
            if self.current_roi_view.shade and self.current_roi_view.contour:
                self.roi_view_combo.setCurrentIndex(2)
            elif self.current_roi_view.shade:
                self.roi_view_combo.setCurrentIndex(0)
            elif self.current_roi_view.contour:
                self.roi_view_combo.setCurrentIndex(1)
            else:
                self.roi_view_combo.setCurrentIndex(3)
            self.roi_alpha_sld.setValue(self.current_roi_view.alpha)

    def update_slider_range(self):
        if self.ivm.grid is None: return
        try:
            self.sld1.blockSignals(True)
            self.sld2.blockSignals(True)
            self.sld3.blockSignals(True)
            self.sld4.blockSignals(True)
            self.sld1.setRange(0, self.ivm.grid.shape[2]-1)
            self.sld2.setRange(0, self.ivm.grid.shape[0]-1)
            self.sld3.setRange(0, self.ivm.grid.shape[1]-1)
            self.sld4.setRange(0, self.ivm.main.nvols-1)
        finally:
            self.sld1.blockSignals(False)
            self.sld2.blockSignals(False)
            self.sld3.blockSignals(False)
            self.sld4.blockSignals(False)
        
    def update_nav_sliders(self, pos=None):
        self.sld1.setValue(self.ivm.cim_pos[2])
        self.sld2.setValue(self.ivm.cim_pos[0])
        self.sld3.setValue(self.ivm.cim_pos[1])
        self.sld4.setValue(self.ivm.cim_pos[3])
        if self.ivm.main is not None: 
            self.vol_data.setText(self.ivm.main.strval(self.ivm.cim_pos))
        if self.ivm.current_roi is not None: 
            self.roi_region.setText(self.ivm.current_roi.strval(self.ivm.cim_pos))
        if self.ivm.current_data is not None: 
            self.ov_data.setText(self.ivm.current_data.strval(self.ivm.cim_pos))
            