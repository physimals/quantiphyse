"""
Quantiphyse - 2d ortho slice image viewer

Copyright (c) 2013-2018 University of Oxford
"""

from __future__ import division, unicode_literals, absolute_import

from PySide import QtCore, QtGui

import pyqtgraph as pg

from quantiphyse.utils import LogSource
from quantiphyse.data import OrthoSlice

from .slice_data_views import SliceDataView, MainSliceDataView

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
        self.dragging = False
        self._arrow_items = []
        self.data_views = {}
        self.focus_pos = self.ivl.focus()
        self._set_slice()
        self.debug("axes=%i, %i, %i", self.xaxis, self.yaxis, self.zaxis)

        # View box to display graphics items
        self.vb = pg.ViewBox(name="view%i" % self.zaxis, border=pg.mkPen((0, 0, 255), width=3.0))
        self.vb.setAspectLocked(True)
        self.vb.setBackgroundColor([0, 0, 0])
        self.vb.enableAutoRange()
        self.setCentralItem(self.vb)

        # Crosshairs
        self.vline = pg.InfiniteLine(angle=90, movable=False)
        self.vline.setZValue(2)
        self.vline.setPen(pg.mkPen((0, 255, 0), width=1.0, style=QtCore.Qt.DashLine))
        self.vline.setVisible(False)

        self.hline = pg.InfiniteLine(angle=0, movable=False)
        self.hline.setZValue(2)
        self.hline.setPen(pg.mkPen((0, 255, 0), width=1.0, style=QtCore.Qt.DashLine))
        self.hline.setVisible(False)

        self.vb.addItem(self.vline, ignoreBounds=True)
        self.vb.addItem(self.hline, ignoreBounds=True)

        # Dummy image item for some reason?
        self.dummy = pg.ImageItem()
        self.dummy.setVisible(False)
        self.vb.addItem(self.dummy, ignoreBounds=True)

        # Static labels for the view directions
        self.labels = []
        for axis in [self.xaxis, self.yaxis]:
            self.labels.append(QtGui.QLabel(ax_labels[axis][0], parent=self))
            self.labels.append(QtGui.QLabel(ax_labels[axis][1], parent=self))
        for label in self.labels:
            label.setAttribute(QtCore.Qt.WA_TranslucentBackground)

        # Connect to signals to update the view
        self.ivl.sig_focus_changed.connect(self._focus_changed)
        self.ivl.sig_arrows_changed.connect(self._arrows_changed)
        self.ivm.sig_all_data.connect(self._data_changed)
        self.ivm.sig_main_data.connect(self._main_data_changed)

        # Need to intercept the default resize event
        # FIXME why can't call superclass method normally?
        self.resizeEventOrig = self.resizeEvent
        self.resizeEvent = self._window_resized

    def reset(self):
        """
        """
        # Adjust axis scaling to that of the viewing grid
        self.vb.setAspectLocked(True, ratio=(self.ivl.grid.spacing[self.xaxis] / self.ivl.grid.spacing[self.yaxis]))
        self.vb.autoRange()
        self._redraw_labels()
        self.debug("reset")

    def _redraw_labels(self):
        # Flip left/right depending on the viewing convention selected
        if self.xaxis == 0:
            # X-axis is left/right
            self.vb.invertX(self.ivl.opts.orientation == 0)
            if self.ivl.opts.orientation == self.ivl.opts.RADIOLOGICAL:
                left, right = 1, 0
            else:
                left, right = 0, 1
            self.labels[right].setText("R")
            self.labels[left].setText("L")

    def _redraw_crosshairs(self):
        self.vline.setPos(float(self.focus_pos[self.xaxis]))
        self.hline.setPos(float(self.focus_pos[self.yaxis]))
        self.vline.setVisible(self.ivl.opts.crosshairs == self.ivl.opts.SHOW)
        self.hline.setVisible(self.ivl.opts.crosshairs == self.ivl.opts.SHOW)

    def _redraw_arrows(self):
        """
        Update arrows so only those visible are shown
        """
        current_zpos = int(self.focus_pos[self.zaxis] + 0.5)
        for pos, _, item in self._arrow_items:
            arrow_zpos = int(pos[self.zaxis] + 0.5)
            item.setVisible(current_zpos == arrow_zpos)

    def _arrows_changed(self, arrows):
        item_num = 0
        for pos, col in arrows:
            if item_num == len(self._arrow_items):
                item = pg.ArrowItem()
                self.vb.addItem(item)
                self._arrow_items.append((pos, col, item))
            _, _, item = self._arrow_items[item_num]
            item.setPos(float(pos[self.xaxis]), float(pos[self.yaxis]))
            item.setPen(pg.mkPen(col))
            item.setBrush(pg.mkBrush(col))
            item.setZValue(2)
            self._arrow_items[item_num] = (pos, col, item)
            item_num += 1

        for _, _, item in self._arrow_items[item_num:]:
            self.vb.removeItem(item)

        self._arrow_items = self._arrow_items[:item_num]
        self._redraw_arrows()

    def _focus_changed(self):
        self.focus_pos = self.ivl.focus()
        self.debug("focus=%s", self.focus_pos)

        if self.isVisible():
            self.debug("visible")
            self._redraw_crosshairs()

            if self.focus_pos[self.zaxis] != self.slice_z or self.slice_vol != self.focus_pos[3]:
                self._set_slice()

    def _set_slice(self):
        self.slice_z = self.focus_pos[self.zaxis]
        self.slice_vol = self.focus_pos[3]
        self.slice_plane = OrthoSlice(self.ivl.grid, self.zaxis, self.slice_z)
        for view in self.data_views.values():
            view.plane = self.slice_plane
            view.vol = self.slice_vol

        self.debug("set slice: %f %i", self.slice_z, self.slice_vol)

    def _data_changed(self, data_names):
        new_data = [name for name in data_names if name not in self.data_views]
        removed_data = [name for name in self.data_views if name != "" and name not in data_names]

        for name in removed_data:
            self._remove_data(name)

        for name in new_data:
            self.data_views[name] = SliceDataView(self.ivm.data[name], self.vb, self.slice_plane, self.slice_vol)

    def _main_data_changed(self, data):
        self._remove_data("")
        self.debug("Main data changed")
        self.data_views[""] = MainSliceDataView(data, self.vb, self.slice_plane, self.slice_vol)
        #self.ivl.main_histogram.add_view(self.data_views[""])

    def _remove_data(self, name):
        if name in self.data_views:
            #self.ivm.main_histogram.remove_view(self.data_views[""])
            self.data_views[name].remove()
            del self.data_views[name]

    def _window_resized(self, event):
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
            coords = self.dummy.mapFromScene(event.pos())
            pos = self.ivl.focus()
            pos[self.xaxis] = coords.x()
            pos[self.yaxis] = coords.y()
            self.ivl.set_focus(pos)

            if self.ivl.picker.use_drag:
                self.dragging = True
            self.sig_pick.emit(self.zaxis, self.ivl.focus())

    def mouseReleaseEvent(self, event):
        """
        Called when mouse button is released on the view
        """
        super(OrthoSliceViewer, self).mouseReleaseEvent(event)
        self.dragging = False

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
        if self.dragging:
            coords = self.dummy.mapFromScene(event.pos())
            pos = self.ivl.focus()
            pos[self.xaxis] = coords.x()
            pos[self.yaxis] = coords.y()
            self.sig_drag.emit(self.zaxis, pos)
        else:
            super(OrthoSliceViewer, self).mouseMoveEvent(event)
