
"""
Quantiphyse - Picker classes for ImageView

Copyright (c) 2013-2018 University of Oxford
"""

from __future__ import division, unicode_literals, absolute_import, print_function

from PySide import QtCore, QtGui
import numpy as np
import pyqtgraph as pg
from PIL import Image, ImageDraw

from quantiphyse.utils import debug

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
        self.use_drag = False

    def pick(self, win, pos):
        """
        Point has been picked
        
        :param win: ID of the window sending the event
        :param pos: Position picked
        """
        pass
    
    def drag(self, win, pos):
        """
        Mouse has been dragged with left button down

        :param win: ID of the window sending the event
        :param pos: Current position
        """
        pass

    def selection(self, grid=None):
        """
        Return the selection. This may be:

         - A single point 
         - A list of points
         - A dictionary of colour to list of points
         - A region defined by a binary mask

        The return type is determined by the picker type so the caller
        must know what type of picking they are doing and what kind
        of object they expect in return

        :param grid: Return point co-ordinates relative to this grid.
                     If not specified, use viewer grid
        """
        return []

    def cleanup(self):
        """ 
        Remove picker objects from the view 
        """
        pass

class PointPicker(Picker):
    """
    Basic picker which just stores a single point
    """
    def __init__(self, ivl):
        Picker.__init__(self, ivl)
        self._point = None

    def pick(self, win, pos):
        self._point = pos

    def selection(self, grid=None):
        """
        :return: The selected point as a 4D co-ordinate list
        """
        if grid is not None:
            return grid.grid_to_grid(self._point, from_grid=self.ivl.grid)
        else:
            return self._point

class MultiPicker(Picker):
    """
    Picker which picks multiple points, potentially in different colours
    """
    def __init__(self, ivl, col=(255, 0, 0)):
        Picker.__init__(self, ivl)
        self.col = col
        self._points = {}

    def pick(self, win, pos):
        if self.col not in self._points: 
            self._points[self.col] = []
        self._points[self.col].append(pos)
        self.ivl.add_arrow(pos, col=self.col)
    
    def selection(self, grid=None):
        """
        :return: Dictionary of colour : list of picked points as 4D co-ords
        """
        if grid is not None:
            ret = {}
            for col, pts in self._points.items():
                ret[col] = [grid.grid_to_grid(pos, from_grid=self.ivl.grid) for pos in pts]
            return ret
        else:
            return self._points

    def cleanup(self):
        self.ivl.remove_arrows()

class SliceMultiPicker(MultiPicker):
    """
    MultiPicker which is restricted to a single window
    """
    def __init__(self, iv, col=(255, 0, 0)):
        MultiPicker.__init__(self, iv, col)

    def pick(self, win, pos):
        if self.win is None:
            self.win = win
            self.zaxis = self.ivl.ortho_views[win].zaxis
            self.zpos = pos[self.zaxis]

        if win == self.win and pos[self.zaxis] == self.zpos:
            MultiPicker.pick(self, win, pos)

class PolygonPicker(Picker): 
    """
    Picker which selects a polygon region
    """

    def __init__(self, iv):
        Picker.__init__(self, iv)
        self.roisel = None
        self._points = []
        self.view = None
           
    def pick(self, win, pos):
        if self.win is None: 
            self.win = win
            self.roisel = pg.PolyLineROI([], pen=(255, 0, 0))
            self.view = self.ivl.ortho_views[self.win]
            self.view.vb.addItem(self.roisel)
        elif win != self.win:
            return

        xy = self._xy_coords(pos)
        self._points.append(xy)
        self.roisel.setPoints(self._points)

    def selection(self, grid=None, label=1):
        """ 
        Get the selected points as an ROI
        """
        if self.win is None: return None    

        if grid is None:
            grid = self.ivl.grid

        gridx, gridy, gridz, points = self._grid_points(grid)
        w, h = grid.shape[gridx], grid.shape[gridy]
        img = Image.new('L', (w, h), 0)
        ImageDraw.Draw(img).polygon(points, outline=label, fill=label)
        
        ret = np.zeros(grid.shape, dtype=np.int)
        slice_mask = np.array(img).T

        slices = [slice(None)] * 3
        zpos = int(self.ivl.focus(grid)[gridz] + 0.5)
        if zpos >= 0 and zpos < grid.shape[gridz]:
            slices[gridz] = zpos
            ret[slices] = slice_mask
        return ret

    def cleanup(self):
        if self.view is not None: 
            self.view.vb.removeItem(self.roisel)

    def _xy_coords(self, pos):
        return float(pos[self.view.xaxis]), float(pos[self.view.yaxis])

    def _grid_points(self, grid):
        grid_axes = grid.get_ras_axes()
        gridx = grid_axes[self.view.xaxis]
        gridy = grid_axes[self.view.yaxis]
        gridz = grid_axes[self.view.zaxis]

        # NB we are assuming here that the supplied grid is orthogonal to the
        # viewer grid, otherwise things will not work. 
        debug("points in std space are: ", self._points)
        points = []
        for x, y in self._points:
            std_pt = [0, 0, 0, 0]
            std_pt[self.view.xaxis] = x
            std_pt[self.view.yaxis] = y
            std_pt[self.view.zaxis] = 0
            grid_pt = grid.grid_to_grid(std_pt, from_grid=self.ivl.grid)
            points.append((int(grid_pt[gridx]+0.5), int(grid_pt[gridy]+0.5)))
        debug("points in grid space are: ", points)
        return gridx, gridy, gridz, points

class RectPicker(PolygonPicker): 
    """
    Picker which selects a rectangular region
    """
    def __init__(self, iv):
        PolygonPicker.__init__(self, iv)
        self.use_drag = True

    def pick(self, win, pos):
        self.cleanup()

        self.win = win
        self.view = self.ivl.ortho_views[self.win]
        
        fx, fy = float(pos[self.view.xaxis]), float(pos[self.view.yaxis])
        self.roisel = pg.RectROI((fx, fy), (1, 1), pen=(255, 0, 255))
        self.view.vb.addItem(self.roisel)
        self.ox, self.oy = fx, fy
        self._points = [(fx, fy), (fx, fy+1), (fx+1, fy+1), (fx+1, fy)]

    def drag(self, win, pos):
        fx, fy = self._xy_coords(pos)
        sx, sy = fx-self.ox, fy-self.oy
        self.roisel.setSize((sx, sy))
        self._points = [(self.ox, self.oy), (self.ox, fy), (fx, fy), (fx, self.oy)]

class EllipsePicker(PolygonPicker): 
    """
    Picker which selects an elliptical region
    """

    def __init__(self, iv):
        PolygonPicker.__init__(self, iv)
        self.use_drag = True

    def pick(self, win, pos):
        self.cleanup()

        self.win = win
        self.view = self.ivl.ortho_views[self.win]
        
        fx, fy = self._xy_coords(pos)
        self.roisel = pg.EllipseROI((fx, fy), (1, 1), pen=(255, 0, 255))
        self.view.vb.addItem(self.roisel)
        self.ox, self.oy = fx, fy
        self._points = [(fx, fy), (fx, fy+1), (fx+1, fy+1), (fx+1, fy)]

    def drag(self, win, pos):
        fx, fy = self._xy_coords(pos)
        sx, sy = fx-self.ox, fy-self.oy
        if sx == 0: sx = 1
        if sy == 0: sy = 1
        self.roisel.setSize((sx, sy))
        self._points = [(self.ox, self.oy), (fx, fy)]

    def selection(self, grid=None, label=1):
        """ 
        Get the selected points as an ROI
        """
        if self.win is None: return None    

        if grid is None:
            grid = self.ivl.grid

        gridx, gridy, gridz, points = self._grid_points(grid)
        # Ellipse seems to require points in ascending order for some reason
        points = [(min(points[0][0], points[1][0]), min(points[0][1], points[1][1])),
                  (max(points[0][0], points[1][0]), max(points[0][1], points[1][1]))]
        w, h = grid.shape[gridx], grid.shape[gridy]
        debug("getting selection with dimensions", w, h, label)
        img = Image.new('L', (w, h), 0)
        ImageDraw.Draw(img).ellipse(points, outline=label, fill=label)
        
        ret = np.zeros(grid.shape, dtype=np.int)
        slice_mask = np.array(img).T
        debug("selection nonzero: ", np.count_nonzero(slice_mask))

        slices = [slice(None)] * 3
        zpos = int(self.ivl.focus(grid)[gridz] + 0.5)
        debug("zpos in grid space", zpos)
        if zpos >= 0 and zpos < grid.shape[gridz]:
            slices[gridz] = zpos
            ret[slices] = slice_mask
        return ret

class FreehandPicker(PolygonPicker): 
    """
    Picker which selects a region by dragging around the boundary
    """
    def __init__(self, iv):
        PolygonPicker.__init__(self, iv)
        self.path = None
        self.pathitem = None
        self.use_drag = True

    def pick(self, win, pos):
        self.cleanup()
        self.win = win
        self.view = self.ivl.ortho_views[self.win]
            
        fx, fy = float(pos[self.view.xaxis]), float(pos[self.view.yaxis])
        self._points.append((fx, fy))

        self.roisel = QtGui.QGraphicsPathItem() 
        self.pen = QtGui.QPen(QtCore.Qt.darkMagenta, 1, QtCore.Qt.SolidLine, 
                              QtCore.Qt.SquareCap, QtCore.Qt.BevelJoin)
        self.roisel.setPen(self.pen)
        self.view.vb.addItem(self.roisel)
        self.path = QtGui.QPainterPath(QtCore.QPointF(fx, fy))
        self.roisel.setPath(self.path)

    def drag(self, win, pos):
        if self.roisel is None: 
            raise RuntimeError("roisel is None")
        else:
            fx, fy = float(pos[self.view.xaxis]), float(pos[self.view.yaxis])
            self._points.append((fx, fy))
            self.path.lineTo(fx, fy)
            self.roisel.setPath(self.path)

PICKERS = {PickMode.SINGLE : PointPicker,
           PickMode.MULTIPLE : MultiPicker,
           PickMode.SLICE_MULTIPLE : SliceMultiPicker,
           PickMode.LASSO : PolygonPicker,
           PickMode.RECT : RectPicker,
           PickMode.ELLIPSE : EllipsePicker,
           PickMode.FREEHAND : FreehandPicker
          }

class DragMode:
    DEFAULT = 0
    PICKER_DRAG = 1
