
"""
Quantiphyse - Picker classes for ImageView

Copyright (c) 2013-2018 University of Oxford
"""

from __future__ import division, unicode_literals, absolute_import, print_function

from PySide import QtCore, QtGui
import numpy as np
import pyqtgraph as pg
from PIL import Image, ImageDraw

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
        self.ivl.sig_point_picked.emit(self)

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
        self.ivl.sig_point_picked.emit(self)
    
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

        self.ivl.sig_point_picked.emit(self)

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
