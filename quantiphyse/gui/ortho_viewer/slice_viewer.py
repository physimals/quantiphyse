"""
Quantiphyse - 2d ortho slice image viewer

Copyright (c) 2013-2018 University of Oxford
"""

from __future__ import division, unicode_literals, absolute_import

try:
    from PySide import QtGui, QtCore, QtGui as QtWidgets
except ImportError:
    from PySide2 import QtGui, QtCore, QtWidgets

import pyqtgraph as pg

from quantiphyse.utils import LogSource
from quantiphyse.data import OrthoSlice

from .slice_data_views import SliceDataView

class OrthoSliceViewer(pg.GraphicsView, LogSource):
    """
    Displays an orthographic slice through data/ROIs relative to the
    a main viewer grid
    """

    # Signals when point is selected
    sig_pick = QtCore.Signal(int, list)

    # Signals when mouse is draggged. Only emitted if
    # active picker uses drag selection
    sig_drag = QtCore.Signal(int, list)

    # Signals when view is double clicked
    sig_doubleclick = QtCore.Signal(int)

    def __init__(self, ivl, ivm, ax_map, ax_labels):
        """
        :param ivl: OrthoViewer
        :param ivm: ImageVolumeManagement
        :param ax_map: Sequence defining the x, y, z axis of the slice viewer
                       in terms of RAS axis sequence indexes
        :param ax_labels: Sequence of labels for the RAS axes
        """
        LogSource.__init__(self)
        pg.GraphicsView.__init__(self)
        self.ivl = ivl
        self.ivm = ivm
        self.xaxis, self.yaxis, self.zaxis = ax_map
        self._slicez = 0
        self._vol = 0
        self._grid = ivl.grid
        self._plane = OrthoSlice(self._grid, self.zaxis, self._slicez)
        self._dragging = False
        self._arrow_items = []
        self._data_views = {}
        self.debug("axes=%i, %i, %i", self.xaxis, self.yaxis, self.zaxis)

        # View box to display graphics items
        self._viewbox = pg.ViewBox(name="view%i" % self.zaxis, border=pg.mkPen((0, 0, 255), width=3.0))
        self._viewbox.setAspectLocked(True)
        self._viewbox.setBackgroundColor([0, 0, 0])
        self._viewbox.enableAutoRange()
        self.setCentralItem(self._viewbox)

        # Crosshairs
        self._vline = pg.InfiniteLine(angle=90, movable=False)
        self._vline.setZValue(2)
        self._vline.setPen(pg.mkPen((0, 255, 0), width=1.0, style=QtCore.Qt.DashLine))
        self._vline.setVisible(False)

        self._hline = pg.InfiniteLine(angle=0, movable=False)
        self._hline.setZValue(2)
        self._hline.setPen(pg.mkPen((0, 255, 0), width=1.0, style=QtCore.Qt.DashLine))
        self._hline.setVisible(False)

        self._viewbox.addItem(self._vline, ignoreBounds=True)
        self._viewbox.addItem(self._hline, ignoreBounds=True)

        # Dummy image item which enables us to translate click co-ordinates
        # into image space co-ordinates even when there is no data in the view
        self._dummy = pg.ImageItem()
        self._dummy.setVisible(False)
        self._viewbox.addItem(self._dummy, ignoreBounds=True)

        # Static labels for the view directions
        self._labels = []
        for axis in [self.xaxis, self.yaxis]:
            self._labels.append(QtGui.QLabel(ax_labels[axis][0], parent=self))
            self._labels.append(QtGui.QLabel(ax_labels[axis][1], parent=self))
        for label in self._labels:
            label.setAttribute(QtCore.Qt.WA_TranslucentBackground)
        self.set_orientation(self.ivl.opts.orientation)

        self.set_grid(self.ivl.grid)
        self.set_focus(self.ivl.focus())
        
        # Connect to signals to update the view
        self.ivl.sig_focus_changed.connect(self.set_focus)
        self.ivl.sig_arrows_changed.connect(self.set_arrows)

        # Need to intercept the default resize event
        # FIXME why can't call superclass method normally?
        self.resizeEventOrig = self.resizeEvent
        self.resizeEvent = self._window_resized

    def set_grid(self, grid):
        """
        Set the grid that the slice viewer is relative to
        """
        self._grid = grid
        # Adjust axis scaling to that of the viewing grid so voxels have correct relative size
        self._viewbox.setAspectLocked(True, ratio=(grid.spacing[self.xaxis] / grid.spacing[self.yaxis]))
        self.reset()

    def reset(self):
        self._viewbox.autoRange()

    def set_focus(self, focus_pos):
        self._focus = focus_pos
        self.debug("focus=%s", self._focus)

        if self.isVisible():
            self.debug("visible")
            self._vline.setPos(float(self._focus[self.xaxis]))
            self._hline.setPos(float(self._focus[self.yaxis]))

            if self._focus[self.zaxis] != self._slicez or self._vol != self._focus[3]:
                self._update_slice()
                self._update_visible_arrows()

    def set_orientation(self, orientation):
        """
        Set the left/right viewing orientation
        
        This only affects views which include the left/right axis (index 0, and always
        displayed as the x axis)
        """
        if self.xaxis == 0:
            if self.ivl.opts.orientation == self.ivl.opts.RADIOLOGICAL:
                left, right, invert = 1, 0, True
            else:
                left, right, invert = 0, 1, False
            self._viewbox.invertX(invert)
            self._labels[right].setText("R")
            self._labels[left].setText("L")

    def set_show_crosshairs(self, crosshairs):
        self._vline.setVisible(crosshairs == self.ivl.opts.SHOW)
        self._hline.setVisible(crosshairs == self.ivl.opts.SHOW)

    def add_data_view(self, qpdata, view, name=None):
        """
        Add a view of a data item to the viewer

        :param qpdata: QpData instance
        :param view_params: Dictionary of view parameters
        :param name: Name for the view - if not specified uses QpData name
        """
        if name is None:
            name = qpdata.name
        self.remove_data_view(name)
        self._data_views[name] = SliceDataView(qpdata, self._viewbox, self._plane, self._vol, view)

    def remove_data_view(self, name):
        """
        Remove a view from the viewer

        :param name: Name of QpData, or name provided in ``add_data_view``
        """
        if name in self._data_views:
            self._data_views[name].remove()
            del self._data_views[name]

    def set_arrows(self, arrows):
        """
        Set the locations and colours of arrows to be drawn

        :param arrows: Sequence of tuples: (position, color). Position
                       is a XYZ tuple, color is anything that can
                       be passed to pyqtgraph.mkPen (e.g. color name
                       or RGB tuple)
        """
        item_num = 0
        for pos, col in arrows:
            if item_num == len(self._arrow_items):
                item = pg.ArrowItem()
                self._viewbox.addItem(item)
                self._arrow_items.append((pos, col, item))
            _, _, item = self._arrow_items[item_num]
            item.setPos(float(pos[self.xaxis]), float(pos[self.yaxis]))
            item.setPen(pg.mkPen(col))
            item.setBrush(pg.mkBrush(col))
            item.setZValue(2)
            self._arrow_items[item_num] = (pos, col, item)
            item_num += 1

        for _, _, item in self._arrow_items[item_num:]:
            self._viewbox.removeItem(item)

        self._arrow_items = self._arrow_items[:item_num]
        self._update_visible_arrows()

    def _update_slice(self):
        self._slicez = self._focus[self.zaxis]
        self._vol = self._focus[3]
        self._plane = OrthoSlice(self._grid, self.zaxis, self._slicez)
        for view in self._data_views.values():
            view.plane = self._plane
            view.vol = self._vol

        self.debug("set slice: %f %i", self._slicez, self._vol)

    def _update_visible_arrows(self):
        """
        Update arrows so only those visible are shown
        """
        current_zpos = int(self._focus[self.zaxis] + 0.5)
        for pos, _, item in self._arrow_items:
            arrow_zpos = int(pos[self.zaxis] + 0.5)
            item.setVisible(current_zpos == arrow_zpos)

    def _window_resized(self, event):
        """
        Called when window is resized - updates the position
        of the text labels and then calls the original resize method
        """
        w = self.geometry().width()
        h = self.geometry().height()
        self._labels[0].setGeometry(0, h/2, 10, 10)
        self._labels[1].setGeometry(w-10, h/2, 10, 10)
        self._labels[2].setGeometry(w/2, h-10, 10, 10)
        self._labels[3].setGeometry(w/2, 0, 10, 10)
        self.resizeEventOrig(event)

    def wheelEvent(self, event):
        """
        Subclassed to remove scroll to zoom from pg.ImageItem
        and instead trigger a scroll through the volume
        """
        dz = int(event.delta()/120)
        pos = self.ivl.focus()
        pos[self.zaxis] += dz
        self.ivl.set_focus(pos)

    def mousePressEvent(self, event):
        """
        Called when mouse button is pressed on the view
        """
        super(OrthoSliceViewer, self).mousePressEvent(event)
        if self.ivm.main is None:
            return

        if event.button() == QtCore.Qt.LeftButton:
            # Convert co-ords to view grid
            coords = self._dummy.mapFromScene(event.pos())
            pos = self.ivl.focus()
            pos[self.xaxis] = coords.x()
            pos[self.yaxis] = coords.y()
            self.ivl.set_focus(pos)

            if self.ivl.picker.use_drag:
                self._dragging = True
            self.sig_pick.emit(self.zaxis, self.ivl.focus())

    def mouseReleaseEvent(self, event):
        """
        Called when mouse button is released on the view
        """
        super(OrthoSliceViewer, self).mouseReleaseEvent(event)
        self._dragging = False

    def mouseDoubleClickEvent(self, event):
        """
        Called when mouse button is double clicked on the view

        This is used to maximise/minimise the view window
        """
        super(OrthoSliceViewer, self).mouseDoubleClickEvent(event)
        if event.button() == QtCore.Qt.LeftButton:
            self.sig_doubleclick.emit(self.zaxis)

    def mouseMoveEvent(self, event):
        """
        Called when the mouse is moved over the window.

        The default behaviour is used unless we are dragging a
        selection region
        """
        if self._dragging:
            coords = self._dummy.mapFromScene(event.pos())
            pos = self.ivl.focus()
            pos[self.xaxis] = coords.x()
            pos[self.yaxis] = coords.y()
            self.sig_drag.emit(self.zaxis, pos)
        else:
            super(OrthoSliceViewer, self).mouseMoveEvent(event)
