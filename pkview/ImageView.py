"""

Author: Benjamin Irving (benjamin.irv@gmail.com)
Copyright (c) 2013-2015 University of Oxford, Benjamin Irving

"""

# TODO remove display of mutliple ROIs at once and instead select the ROIs

from __future__ import division, unicode_literals, absolute_import, print_function

import matplotlib

from matplotlib import cm
from PySide import QtCore, QtGui
import warnings
import numpy as np
import weakref

import pyqtgraph as pg
from pyqtgraph.exporters.ImageExporter import ImageExporter
# setting defaults for the library

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

    def setSourceData(self, arr):
        """
        Set the source data for the histogram widget. This is likely to be a
        3d or 4d volume, so we flatten it to 2d in order to use the PyQtGraph
        methods to extract a histogram
        """
        self.region.setRegion([np.min(arr), np.max(arr)])
        self.region.setBounds([np.min(arr), None])
        self.region.lines[0].setValue(np.min(arr))
        self.region.lines[1].setValue(np.max(arr))
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

class ImageMed(pg.ImageItem, object):
    """
    Subclassing ImageItem in order to change the wheeEvent action
    """
    # General signal that the mouse has been interacted with (used to be just for the wheel)
    sig_mouse_wheel = QtCore.Signal(int)
    # Signal that the mouse has been clicked in the image
    sig_click = QtCore.Signal(QtGui.QMouseEvent)
    sig_doubleClick = QtCore.Signal(QtGui.QMouseEvent)

    def __init__(self, border):
        super(ImageMed, self).__init__(border=border)

    def wheelEvent(self, event):

        """
        Subclassed to remove scroll to zoom from pg.ImageItem
        and instead trigger a scroll through the volume
        """

        # defines whether the change is negative or positive scroll
        chnge1 = int(event.delta()/120)
        self.sig_mouse_wheel.emit(chnge1)

    # Mouse clicked on widget
    def mousePressEvent(self, event):
        super(ImageMed, self).mousePressEvent(event)
        if event.button() == QtCore.Qt.LeftButton:
            self.sig_click.emit(event)

    # Mouse double clicked on widget
    def mouseDoubleClickEvent(self, event):
        super(ImageMed, self).mouseDoubleClickEvent(event)
        if event.button() == QtCore.Qt.LeftButton:
            self.sig_doubleClick.emit(event)

class PickMode:
    SINGLE = 1
    MULTIPLE = 2
    RECT = 3
    LASSO = 4

class ImageViewLayout(QtGui.QGraphicsView, object):
    """
    Re-implementing graphics layout class to include mouse press event.
    This defines the 3D image interaction with the cross hairs,
    provides slots to connect sliders and controls 3D/4D image view updates

    Signals:
            self.sig_mouse
    """

    # Signals (moving out of init means that the signal is shared by
    # each instance. Just how Qt appears to be set up)

    # signalling a mouse click
    sig_mouse_click = QtCore.Signal(bool)

    # Signals when the mouse is scrolling
    sig_mouse_scroll = QtCore.Signal(bool)

    # Signals when point of focus is changed
    sig_focus_changed = QtCore.Signal(list)

    # Signals when the selected points / region have changed
    sig_sel_changed = QtCore.Signal(tuple)

    def __init__(self):
        super(ImageViewLayout, self).__init__()

        #ViewerOptions
        self.options = {}

        # Automatically adjust threshold for each view
        # If false then use the same threshold for the entire volume
        self.options['view_thresh'] = False
        self.options['show_crosshairs'] = True

        # For each view window, this is the volume indices of the x, y and z axes for the view
        self.ax_map = [(0, 1, 2), (0, 2, 1), (1, 2, 0)]

        #empty array for arrows
        self.sizeScaling = False

        self.win = []
        self.view = []
        self.imgwin = []
        self.hline = []
        self.vline = []
        for i in range(3):
            
            imgwin = ImageMed(border='k')
            imgwin.sig_mouse_wheel.connect(self.step_axis(i))
            imgwin.sig_doubleClick.connect(self.expand_view(i))
            imgwin.sig_click.connect(self.mouse_pos(i))
            self.imgwin.append(imgwin)
            
            vline = pg.InfiniteLine(angle=90, movable=False)
            vline.setPen(pg.mkPen((0, 255, 0), width=1.0, style=QtCore.Qt.DashLine))
            vline.setVisible(False)
            self.vline.append(vline)
            
            hline = pg.InfiniteLine(angle=0, movable=False)
            hline.setPen(pg.mkPen((0, 255, 0), width=1.0, style=QtCore.Qt.DashLine))
            hline.setVisible(False)
            self.hline.append(hline)

            view = pg.ViewBox(name="view%i" % (i + 1), border=pg.mkPen((0, 0, 255), width=3.0))
            view.setAspectLocked(True)
            view.setBackgroundColor([0, 0, 0])
            view.addItem(imgwin)
            view.addItem(vline, ignoreBounds=True)
            view.addItem(hline, ignoreBounds=True)
            view.enableAutoRange()
            self.view.append(view)
            
            win = pg.GraphicsView()
            win.setCentralItem(view)
            self.win.append(win)

        # Adding a histogram LUT
        self.h1 = MultiImageHistogramWidget(fillHistogram=False)
        self.h1.addImageItem(self.imgwin[0])
        self.h1.addImageItem(self.imgwin[1])
        self.h1.addImageItem(self.imgwin[2])
        self.h1.setBackground(background=None)
        
        self.grid1 = QtGui.QGridLayout()

        self.grid1.addWidget(self.win[0], 0, 0,)
        self.grid1.addWidget(self.win[1], 0, 1)
        self.grid1.addWidget(self.win[2], 1, 0)
        self.grid1.addWidget(self.h1, 0, 2)

        self.grid1.setColumnStretch(0, 3)
        self.grid1.setColumnStretch(1, 3)
        self.grid1.setColumnStretch(2, 1)
        self.grid1.setRowStretch(0, 1)
        self.grid1.setRowStretch(1, 1)

        self.setLayout(self.grid1)

        self.roisel = pg.PolyLineROI([])
        self.arrows = []
        self.pick_col = (255, 0, 0)
        self.set_pickmode(PickMode.SINGLE)

    def expand_view(self, i):
        def expand():
            o1 = (i+1) % 3
            o2 = (i+2) % 3
            if self.win[o1].isVisible():
                self.win[o1].setVisible(False)
                self.win[o2].setVisible(False)
                self.grid1.addWidget(self.win[i], 0, 0, 2, 2)
            else:
                self.grid1.addWidget(self.win[0], 0, 0, )
                self.grid1.addWidget(self.win[1], 0, 1)
                self.grid1.addWidget(self.win[2], 1, 0)
                self.win[o1].setVisible(True)
                self.win[o2].setVisible(True)
        return expand

    def set_pickmode(self, pickmode):
        self.pickmode = pickmode
        self.sel = []
        self.remove_arrows()
        self.pick_win = -1

    def set_pick_color(self, c):
        self.pick_col = c

    def get_lasso_roi(self, ovname):
        if self.pick_win == -1: return
        ovl = self.ivm.overlays[ovname].data
        ret = None
        view = None
        if self.pick_win == 0:
            data = ovl[:, :, self.ivm.cim_pos[2]]
        elif self.pick_win == 1:
            data = ovl[:, self.ivm.cim_pos[1], :]
        elif self.pick_win == 2:
            data = ovl[self.ivm.cim_pos[0], :, :]
        ret = self.roisel.getArrayRegion(data, self.imgwin[i])
        self.roisel.clearPoints()
        self.view[i].removeItem(self.roisel)
        return ret

    def mouse_pos(self, i):
        """
        Capture mouse click events for window i
        """
        @QtCore.Slot()
        def mouse_pos(event):
            mx = int(event.pos().x())
            my = int(event.pos().y())

            self.ivm.cim_pos[self.ax_map[i][0]] = mx
            self.ivm.cim_pos[self.ax_map[i][1]] = my
            #print(self.ivm.vol.data[self.ivm.cim_pos[0], self.ivm.cim_pos[1], self.ivm.cim_pos[2], self.ivm.cim_pos[3]])

            if self.pickmode == PickMode.SINGLE:
                self.sel = [tuple(self.ivm.cim_pos), ]
            elif self.pickmode == PickMode.MULTIPLE:
                self.sel.append(tuple(self.ivm.cim_pos))
                self.add_arrow(i, (mx, my), self.ivm.cim_pos[self.ax_map[i][2]], self.pick_col)
            elif self.pickmode == PickMode.LASSO:
                if self.pick_win == -1:
                    self.view[i].addItem(self.roisel)
                    self.pick_win = i
                elif self.pick_win == i:
                    self.sel.append((mx, my))
                    self.roisel.setPoints(self.sel)
            elif self.pickmode == PickMode.RECT:
                pass

            self.sig_mouse_scroll.emit(1)
            self.sig_mouse_click.emit(1)
            self.sig_sel_changed.emit((self.pickmode, self.sel))

            # FIXME should this be a signal from IVM?
            self.sig_focus_changed.emit(self.ivm.cim_pos)
            self._update_view()
        return mouse_pos

    def add_arrow(self, win, pos, slice, pen1=(255, 0, 0)):
        """
        Place an arrow at the current position
        """
        aa = pg.ArrowItem(pen=pen1, brush=pen1)
        aa.setPos(float(pos[0])+0.5, float(pos[1])+0.5)
        self.view[win].addItem(aa)
        self.arrows.append((win, slice, aa))

    def remove_arrows(self):
        """
        Remove all the arrows that have been placed
        """
        for win, slice, arrow in self.arrows:
            self.view[win].removeItem(arrow)
        self.arrows = []

    def update_arrows(self):
        """
        Update arrows so only those visible are shown
        """
        for win, slice, arrow in self.arrows:
            if self.ivm.cim_pos[self.ax_map[win][2]] == slice:
                arrow.show()
            else:
                arrow.hide()

    def __update_crosshairs(self):
        """
        update cross hair positions based on cim_pos
        """
        show = self.options["show_crosshairs"]
        for i in range(3):
            self.vline[i].setPos(float(self.ivm.cim_pos[self.ax_map[i][0]])+0.5)
            self.hline[i].setPos(float(self.ivm.cim_pos[self.ax_map[i][1]])+0.5)
            self.vline[i].setVisible(show)
            self.hline[i].setVisible(show)

    def _update_view(self):
        """
        Update the image viewer to account for the new position
        """
        if self.ivm.vol is None:
            return

        if self.ivm.vol.ndims == 3:
            self.imgwin[0].setImage(self.ivm.vol.data[:, :, self.ivm.cim_pos[2]], autoLevels=False)
            self.imgwin[1].setImage(self.ivm.vol.data[:, self.ivm.cim_pos[1], :], autoLevels=False)
            self.imgwin[2].setImage(self.ivm.vol.data[self.ivm.cim_pos[0], :, :], autoLevels=False)
        elif self.ivm.vol.ndims == 4:
            self.imgwin[0].setImage(self.ivm.vol.data[:, :, self.ivm.cim_pos[2], self.ivm.cim_pos[3]], autoLevels=False)
            self.imgwin[1].setImage(self.ivm.vol.data[:, self.ivm.cim_pos[1], :, self.ivm.cim_pos[3]], autoLevels=False)
            self.imgwin[2].setImage(self.ivm.vol.data[self.ivm.cim_pos[0], :, :, self.ivm.cim_pos[3]], autoLevels=False)
        else:
            raise RuntimeError("Main image does not have 3 or 4 dimensions")

        self.update_arrows()
        self.__update_crosshairs()

    @QtCore.Slot(int)
    def set_time_pos(self, value):
        if self.ivm.cim_pos[3] != value:
            # don't do any updating if the values are the same
            self.ivm.cim_pos[3] = value
            self._update_view()

    def set_space_pos(self, dim):
        @QtCore.Slot(int)
        def set_pos(value):
            if self.ivm.cim_pos[dim] != value:
                # don't do any updating if the values are the same
                self.ivm.cim_pos[dim] = value
                self._update_view()
        return set_pos

    def step_axis(self, i):
        """
        Stepping through the axis when the scroll wheel is triggered
        """
        @QtCore.Slot(int)
        def step(value):
            z = self.ax_map[i][2]
            if self.ivm.cim_pos[z]+value >= self.ivm.vol.shape[z]:
                return

            if self.ivm.cim_pos[z]+value < 0:
                return

            self.ivm.cim_pos[z] += value
            self._update_view()
            # signal that the mouse is scrolling
            self.sig_mouse_scroll.emit(1)
            self.sig_focus_changed.emit(self.ivm.cim_pos)
        return step

    # Create an image from one of the windows
    @QtCore.Slot(int, str)
    def capture_view_as_image(self, window, outputfile):
        """
        Export an image using pyqtgraph
        """
        if window not in (1, 2, 3):
            raise RuntimeError("No such window: %i" % window)

        expimg = self.imgwin[window-1]
        exporter = ImageExporter(expimg)
        exporter.parameters()['width'] = 2000
        exporter.export(str(outputfile))

    @QtCore.Slot()
    def main_volume_changed(self):
        for v in self.view:
            v.setVisible(True)

        # update view
        if self.ivm.vol is not None:
            self.h1.setSourceData(self.ivm.vol.data)
        self._update_view()

    def set_size_scaling(self, state):
        """
        toggles whether voxel scaling is used
        """
        self.sizeScaling = state
        for i in range(3):
            if self.sizeScaling:
                x, y = self.ax_map[i][:2]
                self.view[i].setAspectLocked(True, ratio=(self.ivm.vol.voxel_sizes[x] / self.ivm.vol.voxel_sizes[y]))
            else:
                self.view[i].setAspectLocked(True, ratio=1)

        self._update_view()

class ImageViewOverlay(ImageViewLayout):
    """
    Adds the ability to view the ROI as a transparent overlay
    """
    def __init__(self):
        # Updating viewer to include second image layer
        super(ImageViewOverlay, self).__init__()

        # ROI Image windows
        self.imgwinb = [None, None, None]
        self.cont = [[], [], []]

        # Viewing options as a dictionary
        self.options['ShowOverlay'] = True
        self.options['ShowOverlayContour'] = False
        self.options['roi_outline_width'] = 3.0

        self.roi_alpha = 150

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

    def _update_view(self):
        """
        Update the images

        Returns:

        """
        super(ImageViewOverlay, self)._update_view()

        if self.imgwinb[0] is None:
            # If an ROI hasn't been added then return
            return

        # Loop over each volume
        roi = self.ivm.current_roi

        if roi is None or (not self.options['ShowOverlay']):
            self.imgwinb[0].setImage(np.zeros((1, 1)))
            self.imgwinb[1].setImage(np.zeros((1, 1)))
            self.imgwinb[2].setImage(np.zeros((1, 1)))
            return
        else:
            lut = roi.get_lut(self.roi_alpha)
            roi_levels = self.ivm.current_roi.range
            self.imgwinb[0].setImage(roi.data[:, :, self.ivm.cim_pos[2]],
                                   lut=lut,
                                   autoLevels=False,
                                   levels=roi_levels)
            self.imgwinb[1].setImage(roi.data[:, self.ivm.cim_pos[1], :],
                                   lut=lut,
                                   autoLevels=False,
                                   levels=roi_levels)
            self.imgwinb[2].setImage(roi.data[self.ivm.cim_pos[0], :, :],
                                   lut=lut,
                                   autoLevels=False,
                                   levels=roi_levels)

        n = 0
        if roi is not None and self.options['ShowOverlayContour']:
            # Get slice of ROI for each viewing window and convert to float
            # for isosurface routine
            slices = []
            slices.append(roi.data[:, :, self.ivm.cim_pos[2]])
            slices.append(roi.data[:, self.ivm.cim_pos[1], :])
            slices.append(roi.data[self.ivm.cim_pos[0], :, :])

            # Update data and level for existing contour items, and create new ones
            # if we need them
            n_conts = len(self.cont[0])
            create_new = False
            for val in roi.regions:
                pencol = roi.get_pencol(val)
                if val != 0:
                    if n == n_conts:
                        create_new = True

                    for i in range(3):
                        if create_new:
                            self.cont[i].append(pg.IsocurveItem())
                            self.view[i].addItem(self.cont[i][n])

                        d = self._iso_prepare(slices[i], val)
                        self.cont[i][n].setData(d)
                        self.cont[i][n].setLevel(1)
                        self.cont[i][n].setPen(pg.mkPen(pencol, width=self.options['roi_outline_width']))

                    n += 1

        # Set data to None for any existing contour items that we are not using
        # right now FIXME should we delete these?
        for i in range(3):
            for idx in range(n, len(self.cont[i])):
                self.cont[i][idx].setData(None)

    @QtCore.Slot(bool)
    def current_roi_changed(self, roi):
        # Initialises viewer if it hasn't been initialised before
        if self.imgwinb[0] is None:
            self.imgwinb[0] = pg.ImageItem(border='k')
            self.imgwinb[1] = pg.ImageItem(border='k')
            self.imgwinb[2] = pg.ImageItem(border='k')

            self.view[0].addItem(self.imgwinb[0])
            self.view[1].addItem(self.imgwinb[1])
            self.view[2].addItem(self.imgwinb[2])

        self._update_view()

    def set_roi_view(self, shade, contour):
        """
        Set the view mode for the ROI
        """
        self.options['ShowOverlay'] = shade
        self.options['ShowOverlayContour'] = contour
        self._update_view()

    @QtCore.Slot(int)
    def roi_alpha_changed(self, alpha):
        """
        Set the ROI transparency
        """
        self.roi_alpha = alpha
        self._update_view()

class ImageViewColorOverlay(ImageViewOverlay):
    """
    This class adds the ability to have a 3D color image overlay
    of the medical image

    Interactions should include:
    1) Show / hide
    2) Alpha
    3) colormap

    Inherits from ImageViewOverlay
    - this is the image view class that allows a ROI to be set
    """
    def __init__(self, ivm):
        """
        Updating viewer to include second image layer
        """
        super(ImageViewColorOverlay, self).__init__()

        self.ivm = ivm
        self.ivm.sig_current_overlay.connect(self.current_overlay_changed)
        self.ivm.sig_current_roi.connect(self.current_roi_changed)
        self.ivm.sig_main_volume.connect(self.main_volume_changed)

        # Image windows
        self.imgwinc = [None, None, None]

        # overlay data
        self.ovreg = None

        # Histogram, which controls colour map and levels
        self.h2 = MultiImageHistogramWidget(fillHistogram=False)
        self.h2.setBackground(background=None)
        self.h2.setGradientName("jet")

        self.grid1.addWidget(self.h2, 1, 2)

        # Viewing options as a dictionary
        self.options['ShowColorOverlay'] = True
        self.options['UseROI'] = False

    def init_viewer(self):
        """
        Initialises viewer if it hasn't been initialised before
        """
        if self.imgwinc[0] is None:
            self.imgwinc[0] = pg.ImageItem(border='k')
            self.imgwinc[1] = pg.ImageItem(border='k')
            self.imgwinc[2] = pg.ImageItem(border='k')
            self.view[0].addItem(self.imgwinc[0])
            self.view[1].addItem(self.imgwinc[1])
            self.view[2].addItem(self.imgwinc[2])

            self.h2.addImageItem(self.imgwinc[0])
            self.h2.addImageItem(self.imgwinc[1])
            self.h2.addImageItem(self.imgwinc[2])

    def _overlay_changed(self):
        """
        Processes overlay for visualisation on viewer
        """
        ov = self.ivm.current_overlay
        if (self.ivm.current_roi is not None) and (self.options['UseROI'] == 1):
            self.ovreg = ov.data_roi
        elif ov is not None:
            self.ovreg = ov.data
        else:
            self.ovreg = None

        if self.ovreg is not None:
            self.h2.setSourceData(self.ovreg)
        self.init_viewer()
        self._update_view()

    def _update_view(self):
        """
        Updates the viewing windows
        """
        super(ImageViewColorOverlay, self)._update_view()

        if self.imgwinc[0] is None:
            # If an overlay hasn't been added then return
            return

        if self.ivm.current_overlay is None or self.ovreg is None or self.options['ShowColorOverlay'] == 0:
            self.imgwinc[0].setImage(np.zeros((1, 1)), autoLevels=False)
            self.imgwinc[1].setImage(np.zeros((1, 1)), autoLevels=False)
            self.imgwinc[2].setImage(np.zeros((1, 1)), autoLevels=False)

        elif self.ivm.current_overlay.ndims == 4:
            if self.ivm.current_overlay.shape[3] == 3:
                # RGB or RGBA image
                self.imgwinc[0].setImage(np.squeeze(self.ovreg[:, :, self.ivm.cim_pos[2], :]), autoLevels=False)
                self.imgwinc[1].setImage(np.squeeze(self.ovreg[:, self.ivm.cim_pos[1], :, :]), autoLevels=False)
                self.imgwinc[2].setImage(np.squeeze(self.ovreg[self.ivm.cim_pos[0], :, :, :]), autoLevels=False)
            else:
                # Timeseries
                self.imgwinc[0].setImage(np.squeeze(self.ovreg[:, :, self.ivm.cim_pos[2], self.ivm.cim_pos[3]]), autoLevels=False)
                self.imgwinc[1].setImage(np.squeeze(self.ovreg[:, self.ivm.cim_pos[1], :, self.ivm.cim_pos[3]]), autoLevels=False)
                self.imgwinc[2].setImage(np.squeeze(self.ovreg[self.ivm.cim_pos[0], :, :, self.ivm.cim_pos[3]]), autoLevels=False)
        else:
            self.imgwinc[0].setImage(self.ovreg[:, :, self.ivm.cim_pos[2]], autoLevels=False)
            self.imgwinc[1].setImage(self.ovreg[:, self.ivm.cim_pos[1], :], autoLevels=False)
            self.imgwinc[2].setImage(self.ovreg[self.ivm.cim_pos[0], :, :], autoLevels=False)

    def set_overlay_view(self, view=True, roiOnly=False):
        """
        Change the view mode of the overlay
        """
        self.options['ShowColorOverlay'] = view
        self.options['UseROI'] = roiOnly
        self._overlay_changed()

    @QtCore.Slot(int)
    def overlay_alpha_changed(self, alpha):
        """
        Set the overlay transparency
        """
        self.h2.setAlpha(alpha)

    @QtCore.Slot(bool)
    def current_overlay_changed(self, ov):
        """
        Update the overlay data
        """
        self._overlay_changed()

    #@QtCore.Slot(bool)
    #def save_overlay(self, state):
    #    """
    #    Save the edited annotation back to the volume management
    #    """
    #    if state:
    #        self.ivm.add_overlay(Overlay('annotation', data=self.ovreg))
    #
    # @QtCore.Slot(int)
    # def enable_drawing(self, color1=1):
    #
    #     """
    #     Allow drawing on annotation in all three views
    #     """
    #
    #     if color1 != -1:
    #
    #         # start drawing with 3x3 brush
    #         kern = np.array([[color1]])
    #         self.imgwinc[0].setDrawKernel(kern, mask=None, center=(1, 1), mode='set')
    #         self.imgwinc[1].setDrawKernel(kern, mask=None, center=(1, 1), mode='set')
    #         self.imgwinc[2].setDrawKernel(kern, mask=None, center=(1, 1), mode='set')
    #
    #         self.view[0].setAspectLocked(True)
    #         self.view[1].setAspectLocked(True)
    #         self.view[2].setAspectLocked(True)
    #
    #     else:
    #
    #         self.imgwinc[0].setDrawKernel(kernel=None)
    #         self.imgwinc[1].setDrawKernel(kernel=None)
    #         self.imgwinc[2].setDrawKernel(kernel=None)
    #
    #         self.view[0].setAspectLocked(False)
    #         self.view[1].setAspectLocked(False)
    #         self.view[2].setAspectLocked(False)
    #
    #         # Save overlay to annotation when stopped annotating
    #         self.save_overlay(True)





