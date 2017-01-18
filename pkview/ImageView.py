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
        self.gradient.loadPreset(name)

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

    def __init__(self):
        super(ImageViewLayout, self).__init__()

        # volume management for the images
        self.ivm = None

        #ViewerOptions
        self.options = {}

        # Automatically adjust threshold for each view
        # If false then use the same threshold for the entire volume
        self.options['view_thresh'] = False
        self.options['show_crosshairs'] = True

        #empty array for arrows
        self.pts1 = []
        self.sizeScaling = False

        self.win1 = pg.GraphicsView()
        self.win2 = pg.GraphicsView()
        self.win3 = pg.GraphicsView()
        #self.winhist = pg.GraphicsView()

        self.view1 = pg.ViewBox(name="view1", border=pg.mkPen((0, 0, 255), width=3.0))
        self.view1.setAspectLocked(True)
        self.imgwin1 = ImageMed(border='k')
        self.view1.addItem(self.imgwin1)

        self.view2 = pg.ViewBox(name="view2", border=pg.mkPen((0, 0, 255), width=3.0))
        self.view2.setAspectLocked(True)
        self.imgwin2 = ImageMed(border='k')
        self.view2.addItem(self.imgwin2)

        self.view3 = pg.ViewBox(name="view3", border=pg.mkPen((0, 0, 255), width=3.0))
        self.view3.setAspectLocked(True)
        self.imgwin3 = ImageMed(border='k')
        self.view3.addItem(self.imgwin3)

        # Adding a histogram LUT
        self.h1 = MultiImageHistogramWidget(fillHistogram=False)
        self.h1.addImageItem(self.imgwin1)
        self.h1.addImageItem(self.imgwin2)
        self.h1.addImageItem(self.imgwin3)

        self.vline1 = pg.InfiniteLine(angle=90, movable=False)
        self.vline1.setPen(pg.mkPen((0, 255, 0), width=1.0, style=QtCore.Qt.DashLine))
        self.hline1 = pg.InfiniteLine(angle=0, movable=False)
        self.hline1.setPen(pg.mkPen((0, 255, 0), width=1.0, style=QtCore.Qt.DashLine))
        self.vline1.setVisible(False)
        self.hline1.setVisible(False)
        self.view1.addItem(self.vline1, ignoreBounds=True)
        self.view1.addItem(self.hline1, ignoreBounds=True)

        self.vline2 = pg.InfiniteLine(angle=90, movable=False)
        self.vline2.setPen(pg.mkPen((0, 255, 0), width=1.0, style=QtCore.Qt.DashLine))
        self.hline2 = pg.InfiniteLine(angle=0, movable=False)
        self.hline2.setPen(pg.mkPen((0, 255, 0), width=1.0, style=QtCore.Qt.DashLine))
        self.vline2.setVisible(False)
        self.hline2.setVisible(False)
        self.view2.addItem(self.vline2, ignoreBounds=True)
        self.view2.addItem(self.hline2, ignoreBounds=True)

        self.vline3 = pg.InfiniteLine(angle=90, movable=False)
        self.vline3.setPen(pg.mkPen((0, 255, 0), width=1.0, style=QtCore.Qt.DashLine))
        self.hline3 = pg.InfiniteLine(angle=0, movable=False)
        self.hline3.setPen(pg.mkPen((0, 255, 0), width=1.0, style=QtCore.Qt.DashLine))
        self.vline3.setVisible(False)
        self.hline3.setVisible(False)
        self.view3.addItem(self.vline3, ignoreBounds=True)
        self.view3.addItem(self.hline3, ignoreBounds=True)

        # Setting the background color of the various views to be black
        self.view1.setBackgroundColor([0, 0, 0])
        self.view2.setBackgroundColor([0, 0, 0])
        self.view3.setBackgroundColor([0, 0, 0])

        # Connecting scroll wheel to stepping through the volume
        self.imgwin1.sig_mouse_wheel.connect(self.step_axis1)
        self.imgwin2.sig_mouse_wheel.connect(self.step_axis2)
        self.imgwin3.sig_mouse_wheel.connect(self.step_axis3)

        self.win1.setCentralItem(self.view1)
        self.win2.setCentralItem(self.view2)
        self.win3.setCentralItem(self.view3)
        self.h1.setBackground(background=None)
        #self.winhist.setCentralItem(self.h1)

        self.grid1 = QtGui.QGridLayout()

        self.grid1.addWidget(self.win1, 0, 0,)
        self.grid1.addWidget(self.win2, 0, 1)
        self.grid1.addWidget(self.win3, 1, 0)
        self.grid1.addWidget(self.h1, 0, 2)

        self.grid1.setColumnStretch(0, 3)
        self.grid1.setColumnStretch(1, 3)
        self.grid1.setColumnStretch(2, 1)
        self.grid1.setRowStretch(0, 1)
        self.grid1.setRowStretch(1, 1)

        self.setLayout(self.grid1)

        self.imgwin1.sig_click.connect(self._mouse_pos_view1)
        self.imgwin2.sig_click.connect(self._mouse_pos_view2)
        self.imgwin3.sig_click.connect(self._mouse_pos_view3)

        self.imgwin1.sig_doubleClick.connect(self.expand_view1)
        self.imgwin2.sig_doubleClick.connect(self.expand_view2)
        self.imgwin3.sig_doubleClick.connect(self.expand_view3)

        self.roisel = pg.PolyLineROI([])
        self.roipts = []
        self.roi_lasso = 0

    def expand_view1(self):
        if self.win2.isVisible():
            self.win2.setVisible(False)
            self.win3.setVisible(False)
            self.grid1.addWidget(self.win1, 0, 0, 2, 2)
        else:
            self.grid1.addWidget(self.win1, 0, 0)
            self.grid1.addWidget(self.win2, 0, 1)
            self.grid1.addWidget(self.win3, 1, 0)
            self.win2.setVisible(True)
            self.win3.setVisible(True)

    def expand_view2(self):
        if self.win1.isVisible():
            self.win1.setVisible(False)
            self.win3.setVisible(False)
            self.grid1.addWidget(self.win2, 0, 0, 2, 2)
        else:
            self.grid1.addWidget(self.win1, 0, 0)
            self.grid1.addWidget(self.win2, 0, 1)
            self.grid1.addWidget(self.win3, 1, 0)
            self.win1.setVisible(True)
            self.win3.setVisible(True)

    def expand_view3(self):
        if self.win2.isVisible():
            self.win2.setVisible(False)
            self.win1.setVisible(False)
            self.grid1.addWidget(self.win3, 0, 0, 2, 2)
        else:
            self.grid1.addWidget(self.win1, 0, 0)
            self.grid1.addWidget(self.win2, 0, 1)
            self.grid1.addWidget(self.win3, 1, 0)
            self.win2.setVisible(True)
            self.win1.setVisible(True)

    def start_roi_lasso(self):
        self.roipts = []
        self.roi_lasso = -1

    def stop_roi_lasso(self, ovname):
        ovl = self.ivm.overlay_all[ovname]
        ret = None
        view = None
        if self.roi_lasso == 1:
            data = ovl[:, :, self.ivm.cim_pos[2]]
            ret = self.roisel.getArrayRegion(data, self.imgwin1)
            view = self.view1
        elif self.roi_lasso == 2:
            data = ovl[:, self.ivm.cim_pos[1], :]
            ret = self.roisel.getArrayRegion(data, self.imgwin2)
            view = self.view2
        elif self.roi_lasso == 3:
            data = ovl[self.ivm.cim_pos[0], :, :]
            ret = self.roisel.getArrayRegion(data, self.imgwin3)
            view = self.view3
        self.roi_lasso = 0
        if view:
            self.roisel.clearPoints()
            view.removeItem(self.roisel)
        return ret

    def add_image_management(self, image_vol_management):
        """
        Adding image management
        """
        self.ivm = image_vol_management
        self.ivm.set_cmap_roi(self.roilut)

    def load_image(self):
        self.view1.setVisible(True)
        self.view2.setVisible(True)
        self.view3.setVisible(True)

        # update view
        self.h1.setSourceData(self.ivm.image)
        self._update_view()

    @QtCore.Slot()
    def _mouse_pos_view1(self, event):
        """
        Capture mouse click events from window 1
        """

        mspt0 = event.pos().x()
        mspt1 = event.pos().y()
        self.ivm.cim_pos[0] = round(mspt0)
        self.ivm.cim_pos[1] = round(mspt1)

        if self.roi_lasso == -1:
            self.view1.addItem(self.roisel)
            self.roi_lasso = 1

        if self.roi_lasso == 1:
            self.roipts.append([mspt0, mspt1])
            self.roisel.setPoints(self.roipts)

        self.sig_mouse_scroll.emit(1)
        self.sig_mouse_click.emit(1)
        self._update_view()

    @QtCore.Slot()
    def _mouse_pos_view2(self, event):
        """
        Capture mouse click events from window 2
        """
        mspt0 = event.pos().x()
        mspt1 = event.pos().y()
        self.ivm.cim_pos[0] = round(mspt0)
        self.ivm.cim_pos[2] = round(mspt1)

        if self.roi_lasso == -1:
            self.view2.addItem(self.roisel)
            self.roi_lasso = 2

        if self.roi_lasso == 2:
            self.roipts.append([mspt0, mspt1])
            self.roisel.setPoints(self.roipts)

        self.sig_mouse_scroll.emit(1)
        self.sig_mouse_click.emit(1)
        self._update_view()

    @QtCore.Slot()
    def _mouse_pos_view3(self, event):
        """
        Capture mouse click events from window 3
        """
        mspt0 = event.pos().x()
        mspt1 = event.pos().y()
        self.ivm.cim_pos[1] = round(mspt0)
        self.ivm.cim_pos[2] = round(mspt1)

        if self.roi_lasso == -1:
            self.view3.addItem(self.roisel)
            self.roi_lasso = 3

        if self.roi_lasso == 3:
            self.roipts.append([mspt0, mspt1])
            self.roisel.setPoints(self.roipts)

        self.sig_mouse_scroll.emit(1)
        self.sig_mouse_click.emit(1)
        self._update_view()

    def __update_crosshairs(self):
        """
        update cross hair positions based on cim_pos

        """

        self.vline1.setPos(self.ivm.cim_pos[0])
        self.hline1.setPos(self.ivm.cim_pos[1])

        #
        self.vline2.setPos(self.ivm.cim_pos[0])
        self.hline2.setPos(self.ivm.cim_pos[2])

        #
        self.vline3.setPos(self.ivm.cim_pos[1])
        self.hline3.setPos(self.ivm.cim_pos[2])

        if self.options["show_crosshairs"]:
            self.vline1.setVisible(True)
            self.hline1.setVisible(True)
            self.vline2.setVisible(True)
            self.hline2.setVisible(True)
            self.vline3.setVisible(True)
            self.hline3.setVisible(True)
        else:
            self.vline1.setVisible(False)
            self.hline1.setVisible(False)
            self.vline2.setVisible(False)
            self.hline2.setVisible(False)
            self.vline3.setVisible(False)
            self.hline3.setVisible(False)

    def _update_view(self):
        """
        Update the image viewer to account for the new position
        """
        if self.ivm.image is None:
            return

        if len(self.ivm.img_dims) == 3:

            self.imgwin1.setImage(self.ivm.image[:, :, self.ivm.cim_pos[2]], autoLevels=False)
            self.imgwin2.setImage(self.ivm.image[:, self.ivm.cim_pos[1], :], autoLevels=False)
            self.imgwin3.setImage(self.ivm.image[self.ivm.cim_pos[0], :, :], autoLevels=False)

        elif len(self.ivm.img_dims) == 4:

            self.imgwin1.setImage(self.ivm.image[:, :, self.ivm.cim_pos[2], self.ivm.cim_pos[3]], autoLevels=False)
            self.imgwin2.setImage(self.ivm.image[:, self.ivm.cim_pos[1], :, self.ivm.cim_pos[3]], autoLevels=False)
            self.imgwin3.setImage(self.ivm.image[self.ivm.cim_pos[0], :, :, self.ivm.cim_pos[3]], autoLevels=False)

        else:

            print("Image does not have 3 or 4 dimensions")

        self.__update_crosshairs()

        #if not self.options['view_thresh']:
        #    self.ivm.img_range = self.h1.getLevels()
        #    self.imgwin1.setLevels(self.ivm.img_range)
        #    self.imgwin2.setLevels(self.ivm.img_range)
        #    self.imgwin3.setLevels(self.ivm.img_range)

    # Set the 3D position of the cross hairs
    @QtCore.Slot(int)
    def set_temporal_position(self, value):

        # Set 3D coordinates of the image
        self.ivm.cim_pos[3] = value

        # Update the view
        self._update_view()

    @QtCore.Slot(int)
    def step_axis3(self, value):
        """
        Stepping through the axis when the scroll wheel is triggered
        """

        if self.ivm.cim_pos[0]+value >= self.ivm.img_dims[0]:
            return

        if self.ivm.cim_pos[0]+value < 0:
            return

        self.ivm.cim_pos[0] += value
        self._update_view()
        # signal that the mouse is scrolling
        self.sig_mouse_scroll.emit(1)

    @QtCore.Slot(int)
    def step_axis2(self, value):
        """
        Stepping through the axis when the scroll wheel is triggered
        """
        if self.ivm.cim_pos[1]+value >= self.ivm.img_dims[1]:
            return

        if self.ivm.cim_pos[1]+value < 0:
            return

        self.ivm.cim_pos[1] += value
        self._update_view()
        # signal that the mouse is scrolling
        self.sig_mouse_scroll.emit(1)

    @QtCore.Slot(int)
    def step_axis1(self, value):
        """
        Stepping through the axis when the scroll wheel is triggered
        """

        if self.ivm.cim_pos[2]+value >= self.ivm.img_dims[2]:
            return

        if self.ivm.cim_pos[2]+value < 0:
            return

        self.ivm.cim_pos[2] += value
        self._update_view()
        # signal that the mouse is scrolling
        self.sig_mouse_scroll.emit(1)

    # Create an image from one of the windows
    @QtCore.Slot(int, str)
    def capture_view_as_image(self, window, outputfile):
        """
        Export an image based
        """

        # exporting image using pyqtgraph
        if window == 1:
            expimg = self.imgwin1
        elif window == 2:
            expimg = self.imgwin2
        elif window == 3:
            expimg = self.imgwin3
        else:
            expimg = self.imgwin1m
            print("Warning: Window choice does not exist. Using window 1")

        exporter = ImageExporter(expimg)
        exporter.parameters()['width'] = 2000
        exporter.export(str(outputfile))

    # Slots for sliders and mouse
    @QtCore.Slot(int)
    def slider_connect1(self, value):

        if self.ivm.cim_pos[2] == value:
            # don't do any updating if the values are the same
            return

        self.ivm.cim_pos[2] = value
        self._update_view()

    @QtCore.Slot(int)
    def slider_connect2(self, value):

        if self.ivm.cim_pos[1] == value:
            # don't do any updating if the values are the same
            return

        self.ivm.cim_pos[1] = value
        self._update_view()

    @QtCore.Slot(int)
    def slider_connect3(self, value):

        if self.ivm.cim_pos[0] == value:
            # don't do any updating if the values are the same
            return

        self.ivm.cim_pos[0] = value
        self._update_view()

    @QtCore.Slot(int)
    def slider_connect4(self, value):

        if self.ivm.cim_pos[3] == value:
            # don't do any updating if the values are the same
            return

        self.ivm.cim_pos[3] = value
        self._update_view()

    @QtCore.Slot()
    def set_arrow_color(self, c):
        None

    @QtCore.Slot()
    def add_arrow_current_pos(self, pen1=(255, 0, 0)):
        """
        Place an arrow at the current position
        """

        aa = pg.ArrowItem(pen=pen1, brush=pen1)
        self.pts1.append(aa)
        self.pts1[-1].setPos(self.ivm.cim_pos[0], self.ivm.cim_pos[1])
        self.view1.addItem(self.pts1[-1])

    @QtCore.Slot()
    def set_current_arrow(self):
        #TODO
        None

    @QtCore.Slot()
    def remove_all_arrows(self):
        """
        Remove all the arrows that have been places
        """
        for ii in range(len(self.pts1)):
            self.view1.removeItem(self.pts1[ii])

        self.pts1 = []

    def set_size_scaling(self, state):
        """
        toggles whether voxel scaling is used
        """
        self.sizeScaling = state
        if self.sizeScaling:
            self.view1.setAspectLocked(True, ratio=(self.ivm.voxel_size[0] / self.ivm.voxel_size[1]))
            self.view2.setAspectLocked(True, ratio=(self.ivm.voxel_size[0] / self.ivm.voxel_size[2]))
            self.view3.setAspectLocked(True, ratio=(self.ivm.voxel_size[1] / self.ivm.voxel_size[2]))
        else:
            self.view1.setAspectLocked(True, ratio=1)
            self.view2.setAspectLocked(True, ratio=1)
            self.view3.setAspectLocked(True, ratio=1)

        self._update_view()


class ImageViewOverlay(ImageViewLayout):
    """
    Adds the ability to view the ROI as a transparent overlay
    """

    def __init__(self):
        # Updating viewer to include second image layer
        super(ImageViewOverlay, self).__init__()

        # ROI Image windows
        self.imgwin1b = None
        self.imgwin2b = None
        self.imgwin3b = None

        # Contours
        self.cont1 = []
        self.cont2 = []
        self.cont3 = []

        # Viewing options as a dictionary
        self.options['ShowOverlay'] = True
        self.options['ShowOverlayContour'] = False
        self.options['roi_outline_width'] = 3.0

        # ROI pens
        self.roipen = [pg.mkPen((255, 0, 0), width=self.options['roi_outline_width']),
                       pg.mkPen((0, 255, 0), width=self.options['roi_outline_width']),
                       pg.mkPen((0, 0, 255), width=self.options['roi_outline_width'])]

        # Setting up ROI viewing parameters
        pos = np.array([0.0, 1.0])
        # color = np.array([[0, 0, 0, 0], [255, 0, 0, 90]], dtype=np.ubyte)
        # map1 = pg.ColorMap(pos, color)

        # ROI lut
        # TODO set the colormap
        self.set_roi_colormap_matplotlib()
        # self.roilut = map1.getLookupTable(0.0, 1.0, 256)

    def set_roi_colormap_matplotlib(self):

        """
        Use default colormaps from matplotlib.

        First value out of the 255 range is set to be transparent. This needs to maybe be defined in a slightly better
        way to avoid scaling issue.
        """
        cmap1 = getattr(cm, 'jet')

        lut = [[int(255*rgb1) for rgb1 in cmap1(ii)[:3]] for ii in xrange(256)]
        self.roilut = np.array(lut, dtype=np.ubyte)

        # add transparency
        alpha1 = np.ones((self.roilut.shape[0], 1))
        alpha1 *= 150
        alpha1[0] = 0
        # alpha1[1] = 0
        # alpha1[2] = 0
        self.roilut = np.hstack((self.roilut, alpha1))

    def load_roi(self):
        """

        Adds ROI overlay to viewer

        Notes:
        This currently supports both a single overlay (with multiple labels)

        """

        if self.ivm.image.shape[0] == 1:
            print("Please load an image first")
            return

        if self.imgwin1b is None:

            # Initialises viewer if it hasn't been initialised before
            self.imgwin1b = pg.ImageItem(border='k')
            self.imgwin2b = pg.ImageItem(border='k')
            self.imgwin3b = pg.ImageItem(border='k')

            self.view1.addItem(self.imgwin1b)
            self.view2.addItem(self.imgwin2b)
            self.view3.addItem(self.imgwin3b)

        self.roi_levels = [self.ivm.roi.min(), self.ivm.roi.max()]
        self._update_view()

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

        if len(self.ivm.rois) == 0:
            # If an overlay hasn't been added then return
            return

        # Loop over each volume

        if (self.ivm.roi_dims is None) or (not self.options['ShowOverlay']):
            self.imgwin1b.setImage(np.zeros((1, 1)))
            self.imgwin2b.setImage(np.zeros((1, 1)))
            self.imgwin3b.setImage(np.zeros((1, 1)))

        else:
            self.imgwin1b.setImage(self.ivm.roi[:, :, self.ivm.cim_pos[2]],
                                       lut=self.roilut,
                                       autoLevels=False,
                                       levels=self.roi_levels)
            self.imgwin2b.setImage(self.ivm.roi[:, self.ivm.cim_pos[1], :],
                                       lut=self.roilut,
                                       autoLevels=False,
                                       levels=self.roi_levels)
            self.imgwin3b.setImage(self.ivm.roi[self.ivm.cim_pos[0], :, :],
                                       lut=self.roilut,
                                       autoLevels=False,
                                       levels=self.roi_levels)

        n = 0
        if self.options['ShowOverlayContour']:
            # Get slice of ROI for each viewing window and convert to float
            # for isosurface routine
            i1 = self.ivm.roi[:, :, self.ivm.cim_pos[2]]
            i2 = self.ivm.roi[:, self.ivm.cim_pos[1], :]
            i3 = self.ivm.roi[self.ivm.cim_pos[0], :, :]

            # Update data and level for existing contour items, and create new ones
            # if we need them
            n_conts = len(self.cont1)
            create_new = False
            for val in np.unique(self.ivm.roi):
                lutval = (255*float(val))/self.ivm.roi.max()
                if val != 0:
                    if n == n_conts:
                        create_new = True

                    if create_new:
                        self.cont1.append(pg.IsocurveItem())
                        self.cont2.append(pg.IsocurveItem())
                        self.cont3.append(pg.IsocurveItem())
                        self.view1.addItem(self.cont1[n])
                        self.view2.addItem(self.cont2[n])
                        self.view3.addItem(self.cont3[n])

                    d = self._iso_prepare(i1, val)
                    self.cont1[n].setData(d)
                    self.cont1[n].setLevel(1)
                    self.cont1[n].setPen(pg.mkPen(self.roilut[lutval][:3], width=self.options['roi_outline_width']))
                    d = self._iso_prepare(i2, val)
                    self.cont2[n].setData(d)
                    self.cont2[n].setLevel(1)
                    self.cont2[n].setPen(pg.mkPen(self.roilut[lutval][:3], width=self.options['roi_outline_width']))
                    d = self._iso_prepare(i3, val)
                    self.cont3[n].setData(d)
                    self.cont3[n].setLevel(1)
                    self.cont3[n].setPen(pg.mkPen(self.roilut[lutval][:3], width=self.options['roi_outline_width']))
                    n += 1

        # Set data to None for any existing contour items that we are not using
        # right now FIXME should we delete these?
        for idx in range(n, len(self.cont1)):
            self.cont1[idx].setData(None)
            self.cont2[idx].setData(None)
            self.cont3[idx].setData(None)

    def set_roi_view(self, shade, contour):
        self.options['ShowOverlay'] = shade
        self.options['ShowOverlayContour'] = contour
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

    def __init__(self):
        # Updating viewer to include second image layer
        super(ImageViewColorOverlay, self).__init__()

        # Image windows
        self.imgwin1c = None
        self.imgwin2c = None
        self.imgwin3c = None

        # ROI image
        self.ovreg = None

        # Histogram
        self.h2 = MultiImageHistogramWidget(fillHistogram=False)
        self.h2.setBackground(background=None)
        self.h2.setGradientName("spectrum")
        self.grid1.addWidget(self.h2, 1, 2)

        # Viewing options as a dictionary
        self.options['ShowColorOverlay'] = 1
        self.options['ColorMap'] = 'jet'  # default. Can choose any matplotlib colormap
        self.options['UseROI'] = 0

    def load_ovreg(self):
        """
        Adds overlay to image viewer
        """
        if self.ivm.image.shape[0] == 1:
            print("Please load an image first")
            return

        self._process_overlay()

        if self.imgwin1c is None:
            # Initialises viewer if it hasn't been initialised before
            self.imgwin1c = pg.ImageItem(border='k')
            self.imgwin2c = pg.ImageItem(border='k')
            self.imgwin3c = pg.ImageItem(border='k')
            self.view1.addItem(self.imgwin1c)
            self.view2.addItem(self.imgwin2c)
            self.view3.addItem(self.imgwin3c)

            self.h2.addImageItem(self.imgwin1c)
            self.h2.addImageItem(self.imgwin2c)
            self.h2.addImageItem(self.imgwin3c)

        self._update_view()

    def _process_overlay(self, set_range=False):
        """
        Processes overlay for visualisation on viewer
        """
        if self.ivm.ovreg_dims == 4:
            print('RGB or RGBa array')
            # TODO currently a place holder
            self.ov_range = [0, 1]
        elif (self.ivm.roi is not None) and (self.options['UseROI'] == 1):
            self.ovreg = self.ivm.overlay_roi
            if not set_range:
                self.ov_range = self.ivm.ov_range_roi
        else:
            self.ovreg = self.ivm.overlay
            if not set_range:
                self.ov_range = self.ivm.ov_range

        self.h2.setSourceData(self.ovreg)

    def _update_view(self):
        """
        Updates the viewing windows
        """
        super(ImageViewColorOverlay, self)._update_view()

        if self.imgwin1c is None:
            # If an overlay hasn't been added then return
            return

        if (self.ivm.ovreg_dims is None) or (self.options['ShowColorOverlay'] == 0):

            self.imgwin1c.setImage(np.zeros((1, 1)), autoLevels=False)
            self.imgwin2c.setImage(np.zeros((1, 1)), autoLevels=False)
            self.imgwin3c.setImage(np.zeros((1, 1)), autoLevels=False)

        elif len(self.ivm.ovreg_dims) == 4:
            # RGB or RGBA image

            self.imgwin1c.setImage(np.squeeze(self.ovreg[:, :, self.ivm.cim_pos[2], :]), autoLevels=False)
            self.imgwin2c.setImage(np.squeeze(self.ovreg[:, self.ivm.cim_pos[1], :, :]), autoLevels=False)
            self.imgwin3c.setImage(np.squeeze(self.ovreg[self.ivm.cim_pos[0], :, :, :]), autoLevels=False)

        else:

            self.imgwin1c.setImage(self.ovreg[:, :, self.ivm.cim_pos[2]], autoLevels=False)
            self.imgwin2c.setImage(self.ovreg[:, self.ivm.cim_pos[1], :], autoLevels=False)
            self.imgwin3c.setImage(self.ovreg[self.ivm.cim_pos[0], :, :], autoLevels=False)

    def set_overlay_view(self, view=True, roiOnly=False):
        """
        Slot to show or hide overlay
        """
        self.options['ShowColorOverlay'] = view
        self.options['UseROI'] = roiOnly

        self._process_overlay()
        self._update_view()

    # Slot to change overlay transparency
    @QtCore.Slot(int)
    def set_overlay_alpha(self, alpha):
        """
        Set the transparency
        """
        self.h2.setAlpha(alpha)

    @QtCore.Slot(bool)
    def update_overlay(self, x):
        """
        Update any changes to the overlay and view
        """
        if x == 1:
            self.load_ovreg()
            
    @QtCore.Slot(bool)
    def update_roi(self, x):
        """
        Update any changes to the overlay and view
        """
        if x == 1:
            self.load_roi()

    @QtCore.Slot(bool)
    def save_overlay(self, state):
        """
        Save the edited annotation back to the volume management
        """
        if state:
            self.ivm.set_overlay('annotation', self.ovreg)

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
    #         self.imgwin1c.setDrawKernel(kern, mask=None, center=(1, 1), mode='set')
    #         self.imgwin2c.setDrawKernel(kern, mask=None, center=(1, 1), mode='set')
    #         self.imgwin3c.setDrawKernel(kern, mask=None, center=(1, 1), mode='set')
    #
    #         self.view1.setAspectLocked(True)
    #         self.view2.setAspectLocked(True)
    #         self.view3.setAspectLocked(True)
    #
    #     else:
    #
    #         self.imgwin1c.setDrawKernel(kernel=None)
    #         self.imgwin2c.setDrawKernel(kernel=None)
    #         self.imgwin3c.setDrawKernel(kernel=None)
    #
    #         self.view1.setAspectLocked(False)
    #         self.view2.setAspectLocked(False)
    #         self.view3.setAspectLocked(False)
    #
    #         # Save overlay to annotation when stopped annotating
    #         self.save_overlay(True)





