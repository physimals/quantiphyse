"""

Author: Benjamin Irving (benjamin.irv@gmail.com)
Copyright (c) 2013-2015 University of Oxford, Benjamin Irving

"""

from __future__ import division, unicode_literals, absolute_import, print_function

import matplotlib
matplotlib.use('Qt4Agg')
matplotlib.rcParams['backend.qt4'] = 'PySide'
#from matplotlib.backends.backend_qt4agg import FigureCanvasQTAgg as FigureCanvas
#import matplotlib.pyplot as plt

from matplotlib import cm
from PySide import QtCore
import warnings
import numpy as np

import pyqtgraph as pg
from pyqtgraph.exporters.ImageExporter import ImageExporter
# setting defaults for the library


class ImageMed(pg.ImageItem, object):
    """
    Subclassing ImageItem in order to change the wheeEvent action
    """

    sig_mouse_wheel = QtCore.Signal(int)

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


class ImageViewLayout(pg.GraphicsLayoutWidget, object):
    """
    Re-implementing graphics layout class to include mouse press event.
    This defines the 3D image interaction with the cross hairs,
    provides slots to connect sliders and controls 3D/4D image view updates

    Signals:
            self.sig_mouse
    """

    # Signals (moving out of init means that the signal is shared by
    # each instance. Just how Qt appears to be set up)
    #signalling a mouse click
    sig_mouse = QtCore.Signal(np.ndarray)

    # Signals when the mouse is scrolling
    sig_mouse_scroll = QtCore.Signal(bool)

    #File dropped
    sig_dropped = QtCore.Signal(str)

    def __init__(self):
        super(ImageViewLayout, self).__init__()

        # Access the underlying central widget in the GraphicsLayoutWidget
        # https://github.com/robertsj/poropy/blob/master/pyqtgraph/widgets/GraphicsLayoutWidget.py
        self.ci.setBorder(pg.mkPen((220, 220, 220), width=2.0))

        # volume management for the images
        self.ivm = None

        #ViewerOptions
        self.options = {}

        # Automatically adjust threshold for each view
        # If false then use the same threshold for the entire volume
        self.options['view_thresh'] = False
        self.options['show_crosshairs'] = False

        #empty array for arrows
        self.pts1 = []

        self.view1 = self.addViewBox(name="view1", row=1, col=0, colspan=2, rowspan=1,
                                     border=pg.mkPen((0, 0, 255), width=3.0))
        self.view1.setAspectLocked(True)
        self.imgwin1 = ImageMed(border='k')
        self.view1.addItem(self.imgwin1)
        self.view2 = self.addViewBox(name="view2", row=1, col=2,  colspan=2, rowspan=1,
                                     border=pg.mkPen((0, 0, 255), width=3.0))
        self.view2.setAspectLocked(True)
        self.imgwin2 = ImageMed(border='k')
        self.view2.addItem(self.imgwin2)

        # Adding a histogram LUT
        self.h1 = pg.HistogramLUTItem(fillHistogram=False)
        self.addItem(self.h1, row=1, col=4)
        self.h1.setImageItem(self.imgwin1)

        self.view3 = self.addViewBox(name="view3", row=3, col=0, colspan=2, rowspan=1,
                                     border=pg.mkPen((0, 0, 255), width=3.0))
        self.view3.setAspectLocked(True)
        self.imgwin3 = ImageMed(border='k')
        self.view3.addItem(self.imgwin3)

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

        self.ci.layout.setColumnStretchFactor(0, 4)
        self.ci.layout.setColumnStretchFactor(1, 4)
        self.ci.layout.setColumnStretchFactor(2, 4)
        self.ci.layout.setColumnStretchFactor(3, 4)
        self.ci.layout.setColumnStretchFactor(4, 1)
        self.ci.layout.setColumnMaximumWidth(4, 100)

        # Setting the background color of the various views to be black
        self.view1.setBackgroundColor([0, 0, 0])
        self.view2.setBackgroundColor([0, 0, 0])
        self.view3.setBackgroundColor([0, 0, 0])

        # Connecting scroll wheel to stepping through the volume
        self.imgwin1.sig_mouse_wheel.connect(self.step_axis1)
        self.imgwin2.sig_mouse_wheel.connect(self.step_axis2)
        self.imgwin3.sig_mouse_wheel.connect(self.step_axis3)

    def dragEnterEvent(self, e):
        if e.mimeData().hasUrls:
            e.accept()
        else:
            e.ignore()

    def dragMoveEvent(self, e):
        if e.mimeData().hasUrls:
            e.accept()
        else:
            e.ignore()

    def dropEvent(self, e):
        """
        Drop files directly onto the widget

        File locations are stored in fname
        :param e:
        :return:
        """
        if e.mimeData().hasUrls:
            e.setDropAction(QtCore.Qt.CopyAction)
            e.accept()
            fname = []
            for url in e.mimeData().urls():
                fname.append(str(url.toLocalFile()))
            print(fname)
            # Signal that a file has been dropped
            self.sig_dropped.emit(fname[0])

        else:
            e.ignore()

    def add_image_management(self, image_vol_management):
        """
        Adding image management
        """
        self.ivm = image_vol_management

    def load_image(self):

        # update view
        self.h1.setLevels(self.ivm.img_range[0], self.ivm.img_range[1])
        self._update_view()

    def _mouse_pos(self):

        """
        Capture positions of the 3 views on mouse press and update cim_pos
        """

        ishp = self.ivm.get_image_shape()

        if ishp is None:
            return

        # Check if in View1
        if self.view1.sceneBoundingRect().contains(self.lastMousePos):
            print("Image position 1:", self.imgwin1.mapFromScene(self.lastMousePos))
            mouse_point = self.imgwin1.mapFromScene(self.lastMousePos)
            mspt0 = mouse_point.x()
            mspt1 = mouse_point.y()
            if (round(mspt0) < ishp[0]) and (round(mspt1) < ishp[1]):
                self.ivm.cim_pos[0] = round(mspt0)
                self.ivm.cim_pos[1] = round(mspt1)
            else:
                warnings.warn('Out of bounds')

        # Check if in View 2
        elif self.view2.sceneBoundingRect().contains(self.lastMousePos):
            print("Image position 2:", self.imgwin2.mapFromScene(self.lastMousePos))
            mouse_point = self.imgwin2.mapFromScene(self.lastMousePos)
            mspt0 = mouse_point.x()
            mspt1 = mouse_point.y()
            if (round(mspt0) < ishp[0]) and (round(mspt1) < ishp[2]):
                self.ivm.cim_pos[0] = round(mspt0)
                self.ivm.cim_pos[2] = round(mspt1)
            else:
                warnings.warn('Out of bounds')

        # Check if in view 3
        elif self.view3.sceneBoundingRect().contains(self.lastMousePos):
            print("Image position 3:", self.imgwin3.mapFromScene(self.lastMousePos))
            mouse_point = self.imgwin3.mapFromScene(self.lastMousePos)
            mspt0 = mouse_point.x()
            mspt1 = mouse_point.y()
            if (round(mspt0) < ishp[1]) and (round(mspt1) < ishp[2]):
                self.ivm.cim_pos[1] = round(mspt0)
                self.ivm.cim_pos[2] = round(mspt1)
            else:
                warnings.warn('Out of bounds')

        #self.ivm.cim_pos[self.ivm.cim_pos > ishp] = ishp[self.ivm.cim_pos > ishp]

        # stops it going below zeros
        self.ivm.cim_pos[0] *= (self.ivm.cim_pos[0] > 0)
        self.ivm.cim_pos[1] *= (self.ivm.cim_pos[1] > 0)
        self.ivm.cim_pos[2] *= (self.ivm.cim_pos[2] > 0)

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

            self.imgwin1.setImage(self.ivm.image[:, :, self.ivm.cim_pos[2]])
            self.imgwin2.setImage(self.ivm.image[:, self.ivm.cim_pos[1], :])
            self.imgwin3.setImage(self.ivm.image[self.ivm.cim_pos[0], :, :])

        elif len(self.ivm.img_dims) == 4:

            self.imgwin1.setImage(self.ivm.image[:, :, self.ivm.cim_pos[2], self.ivm.cim_pos[3]])
            self.imgwin2.setImage(self.ivm.image[:, self.ivm.cim_pos[1], :, self.ivm.cim_pos[3]])
            self.imgwin3.setImage(self.ivm.image[self.ivm.cim_pos[0], :, :, self.ivm.cim_pos[3]])

        else:

            print("Image does not have 3 or 4 dimensions")

        self.__update_crosshairs()

        if not self.options['view_thresh']:
            self.ivm.img_range = self.h1.getLevels()
            self.imgwin1.setLevels(self.ivm.img_range)
            self.imgwin2.setLevels(self.ivm.img_range)
            self.imgwin3.setLevels(self.ivm.img_range)

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

    @QtCore.Slot(int)
    def mouse_click_connect(self, event):
        """
        On mouse click:
        1) get the current position on the image,
        2) update the view
        3) emit signal of current position data
        """

        if self.ivm.image is None:
            return

        self._mouse_pos()
        self._update_view()

        #Signal emit current enhancement curve to widget
        if len(self.ivm.img_dims) == 3:
            print("3D image so just calculating cross image profile")
            vec_sig = self.ivm.image[self.ivm.cim_pos[0], :, self.ivm.cim_pos[2]]
        elif len(self.ivm.img_dims) == 4:
            vec_sig = self.ivm.image[self.ivm.cim_pos[0], self.ivm.cim_pos[1], self.ivm.cim_pos[2], :]
        else:
            vec_sig = None
            print("Image is not 3D or 4D")

        self.sig_mouse.emit(vec_sig)

        #self.add_arrow_current_pos()

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

    @QtCore.Slot()
    def toggle_dimscale(self, state):
        #toggles whether voxel scaling is used

        if state == QtCore.Qt.Checked:
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
        self.imgwin1b = []
        self.imgwin2b = []
        self.imgwin3b = []

        # Contour
        self.cont1 = []
        self.cont2 = []
        self.cont3 = []

        # Viewing options as a dictionary
        self.options['ShowOverlay'] = 0
        self.options['ShowOverlayContour'] = False
        self.options['roi_outline_width'] = 3.0

        # ROI pens
        self.roipen = [pg.mkPen((255, 0, 0), width=self.options['roi_outline_width']),
                       pg.mkPen((0, 255, 0), width=self.options['roi_outline_width']),
                       pg.mkPen((0, 0, 255), width=self.options['roi_outline_width'])]

        # Setting up ROI viewing parameters
        pos = np.array([0.0, 1.0])
        color = np.array([[0, 0, 0, 0], [255, 0, 0, 90]], dtype=np.ubyte)
        map1 = pg.ColorMap(pos, color)
        self.roilut = map1.getLookupTable(0.0, 1.0, 256)

    def load_roi(self):
        """
        Adds roi to viewer
        """

        if self.ivm.image.shape[0] == 1:
            print("Please load an image first")
            return

        # Initialises viewer if it hasn't been initialised before
        self.imgwin1b.append(pg.ImageItem(border='k'))
        self.imgwin2b.append(pg.ImageItem(border='k'))
        self.imgwin3b.append(pg.ImageItem(border='k'))
        self.view1.addItem(self.imgwin1b[self.ivm.num_roi-1])
        self.view2.addItem(self.imgwin2b[self.ivm.num_roi-1])
        self.view3.addItem(self.imgwin3b[self.ivm.num_roi-1])

        self.cont1.append(pg.IsocurveItem(level=1.0, pen=self.roipen[self.ivm.num_roi-1]))
        self.cont2.append(pg.IsocurveItem(level=1.0, pen=self.roipen[self.ivm.num_roi-1]))
        self.cont3.append(pg.IsocurveItem(level=1.0, pen=self.roipen[self.ivm.num_roi-1]))
        self.view1.addItem(self.cont1[self.ivm.num_roi-1])
        self.view2.addItem(self.cont2[self.ivm.num_roi-1])
        self.view3.addItem(self.cont3[self.ivm.num_roi-1])

        self._update_view()

    def _update_view(self):
        super(ImageViewOverlay, self)._update_view()

        if self.ivm.num_roi == 0:
            #If an overlay hasn't been added then return
            return

        #Loop over each volume
        for ii in range(self.ivm.num_roi):

            if (self.ivm.roi_dims is None) or (self.options['ShowOverlay'] == 0):
                self.imgwin1b[ii].setImage(np.zeros((1, 1)))
                self.imgwin2b[ii].setImage(np.zeros((1, 1)))
                self.imgwin3b[ii].setImage(np.zeros((1, 1)))

            else:
                self.imgwin1b[ii].setImage(self.ivm.roi_all[ii][:, :, self.ivm.cim_pos[2]], lut=self.roilut)
                self.imgwin2b[ii].setImage(self.ivm.roi_all[ii][:, self.ivm.cim_pos[1], :], lut=self.roilut)
                self.imgwin3b[ii].setImage(self.ivm.roi_all[ii][self.ivm.cim_pos[0], :, :], lut=self.roilut)

            if self.options['ShowOverlayContour']:
                self.cont1[ii].setData(self.ivm.roi_all[ii][:, :, self.ivm.cim_pos[2]])
                self.cont2[ii].setData(self.ivm.roi_all[ii][:, self.ivm.cim_pos[1], :])
                self.cont3[ii].setData(self.ivm.roi_all[ii][self.ivm.cim_pos[0], :, :])
            else:
                self.cont1[ii].setData(None)
                self.cont2[ii].setData(None)
                self.cont3[ii].setData(None)

    # Slot to toggle whether the overlay is seen or not
    @QtCore.Slot()
    def toggle_roi_view(self, state):

        if state == QtCore.Qt.Checked:
            self.options['ShowOverlay'] = 1
        else:
            self.options['ShowOverlay'] = 0
        self._update_view()

    @QtCore.Slot()
    def toggle_roi_contour(self, state):

        if state == QtCore.Qt.Checked:
            self.options['ShowOverlayContour'] = True
        else:
            self.options['ShowOverlayContour'] = False
        self._update_view()


class ImageViewColorOverlay(ImageViewOverlay):
    """
    This class adds the ability to have a 3D color image overlay
    of the medical image

    Interactions should include:
    1) Show / hide
    2) Alpha
    3) colormap (future)

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
        self.h2 = None
        self.axcol = None

        # Viewing options as a dictionary
        self.options['ShowColorOverlay'] = 1
        self.options['ColorMap'] = 'jet'  # default. Can choose any matplotlib colormap
        self.options['UseROI'] = 1

        # Initialise the colormap
        self.ovreg_lut = None

        # self.set_default_colormap_manual()
        self.ov_range = [0.0, 1.0]

        self.l2 = self.addLayout(row=3, col=4, colspan=1, rowspan=1)
        self.view4 = self.l2.addViewBox(lockAspect=False, enableMouse=False, enableMenu=False)

    def load_ovreg(self):
        """
        Adds overlay to image viewer
        """

        # Initilise lut colormap
        self.set_default_colormap_matplotlib()

        if self.ivm.image.shape[0] == 1:
            print("Please load an image first")
            return

        self._process_overlay()
        self._create_colorbar()

        if self.imgwin1c is None:
            # Initialises viewer if it hasn't been initialised before
            self.imgwin1c = pg.ImageItem(border='k')
            self.imgwin2c = pg.ImageItem(border='k')
            self.imgwin3c = pg.ImageItem(border='k')
            self.view1.addItem(self.imgwin1c)
            self.view2.addItem(self.imgwin2c)
            self.view3.addItem(self.imgwin3c)

            self.imgcolbar1 = pg.ImageItem(border='k')
            self.view4.addItem(self.imgcolbar1)
            self.axcol = pg.AxisItem('right')
            self.l2.addItem(self.axcol)

        if len(self.ivm.ovreg_dims) < 4:
            self.imgcolbar1.setImage(self.colbar1, lut=self.ovreg_lut)

        self.view4.setXRange(0, 100, padding=0)
        self.view4.setYRange(0, 1000, padding=0)
        self.axcol.setRange(self.ov_range[0], self.ov_range[1])

        if len(self.ivm.ovreg_dims) < 4:
            self.imgwin1c.setLevels(self.ov_range)
            self.imgwin2c.setLevels(self.ov_range)
            self.imgwin3c.setLevels(self.ov_range)

        self._update_view()

    def _create_colorbar(self):
        c1 = np.linspace(self.ov_range[0], self.ov_range[1], 1000)
        c1 = np.expand_dims(c1, axis=0)
        self.colbar1 = np.tile(c1, (100, 1))

    def _process_overlay(self):
        """
        Processes overlay for visualisation on viewer
        """

        self.ovreg = np.copy(self.ivm.overlay)

        # Convert to numpy double
        self.ovreg = np.array(self.ovreg, dtype=np.double)

        if self.ivm.ovreg_dims == 4:

            print('RGB or RGBa array')
            #TODO currently a place holder
            self.ov_range = [0, 1]

        elif (self.ivm.roi is not None) and (self.options['UseROI'] == 1):

            # Scale ROI
            subreg1 = self.ovreg[np.array(self.ivm.roi, dtype=bool)]
            self.ov_range_orig = [np.min(subreg1), np.max(subreg1)]

            # Regions that are not part of the ROI
            self.ovreg[np.logical_not(self.ivm.roi)] = -0.01 * (self.ov_range_orig[1] - self.ov_range_orig[0]) + self.ov_range_orig[0]

            # ov_range using the -1 values as well to properly scale the data
            self.ov_range = [self.ovreg.min(), self.ovreg.max()]

        else:
            self.ov_range = [self.ovreg.min(), self.ovreg.max()]

    def _update_view(self):

        """
        Updates the viewing windows
        """

        super(ImageViewColorOverlay, self)._update_view()

        if self.imgwin1c is None:
            # If an overlay hasn't been added then return
            return

        if (self.ivm.ovreg_dims is None) or (self.options['ShowColorOverlay'] == 0):

            self.imgwin1c.setImage(np.zeros((1, 1)))
            self.imgwin2c.setImage(np.zeros((1, 1)))
            self.imgwin3c.setImage(np.zeros((1, 1)))

            self.imgwin1c.setLevels(self.ov_range)
            self.imgwin2c.setLevels(self.ov_range)
            self.imgwin3c.setLevels(self.ov_range)

        elif len(self.ivm.ovreg_dims) == 4:
            # RGB or RGBA image

            self.imgwin1c.setImage(np.squeeze(self.ovreg[:, :, self.ivm.cim_pos[2], :]))
            self.imgwin2c.setImage(np.squeeze(self.ovreg[:, self.ivm.cim_pos[1], :, :]))
            self.imgwin3c.setImage(np.squeeze(self.ovreg[self.ivm.cim_pos[0], :, :, :]))

        else:

            self.imgwin1c.setImage(self.ovreg[:, :, self.ivm.cim_pos[2]], lut=self.ovreg_lut)
            self.imgwin2c.setImage(self.ovreg[:, self.ivm.cim_pos[1], :], lut=self.ovreg_lut)
            self.imgwin3c.setImage(self.ovreg[self.ivm.cim_pos[0], :, :], lut=self.ovreg_lut)

            self.imgwin1c.setLevels(self.ov_range)
            self.imgwin2c.setLevels(self.ov_range)
            self.imgwin3c.setLevels(self.ov_range)

        # print(np.max(self.ovreg[1:-1, 1:-1, 1:-1]))

    # Slot to toggle whether the overlay is seen or not
    @QtCore.Slot()
    def toggle_roi_lim(self, state):

        """
        Slot to limit overlay to ROI
        """

        if state == QtCore.Qt.Checked:
            self.options['UseROI'] = 1
        else:
            self.options['UseROI'] = 0

        self._process_overlay()
        self._update_view()

    @QtCore.Slot()
    def toggle_ovreg_view(self, state):
        """
        Slot to show or hide overlay
        """

        if state == QtCore.Qt.Checked:
            self.options['ShowColorOverlay'] = 1
        else:
            self.options['ShowColorOverlay'] = 0

        self._update_view()

    # Slot to change overlay transparency
    @QtCore.Slot(int)
    def set_overlay_alpha(self, state):

        """
        Set the transparency
        """

        if len(self.ivm.ovreg_dims) < 4:

            # Changing colormap
            self.ovreg_lut[:, 3] = state
            self.ovreg_lut[0, 3] = 0

            self.imgwin1c.setLookupTable(self.ovreg_lut)
            self.imgwin2c.setLookupTable(self.ovreg_lut)
            self.imgwin3c.setLookupTable(self.ovreg_lut)
            self.imgcolbar1.setLookupTable(self.ovreg_lut)

        else:
            print("Can't set transparency because RGB")

    @QtCore.Slot()
    def set_overlay_range(self, state):
        """
        Set the range of the overlay map
        """
        #TODO
        None

    @QtCore.Slot(bool)
    def update_overlay(self, x):
        """
        Update any changes to the overlay and view
        """
        if x == 1:
            self.load_ovreg()

    @QtCore.Slot(str)
    def set_colormap(self, text):
        """
        Choose a colormap for the overlay
        """

        #TODO change the functionality to use the builtin HistogramLUTItem colormaps
        # Subclass HistogramLUTIT tem to signal changes in the colormap etc

        self.options['ColorMap'] = text

        # update colormap
        self.set_default_colormap_matplotlib()

        if self.ivm.image is not None and len(self.ivm.ovreg_dims) < 4:
                # set colormap
                self.imgwin1c.setLookupTable(self.ovreg_lut)
                self.imgwin2c.setLookupTable(self.ovreg_lut)
                self.imgwin3c.setLookupTable(self.ovreg_lut)
                self.imgcolbar1.setLookupTable(self.ovreg_lut)

        else:
            print("Can't update colormap on image because RGB or not loaded")

    def set_default_colormap_matplotlib(self):

        """
        Use default colormaps from matplotlib.

        First value out of the 255 range is set to be transparent. This needs to maybe be defined in a slightly better
        way to avoid scaling issue.
        """

        cmap1 = getattr(cm, self.options['ColorMap'])

        lut = [[int(255*rgb1) for rgb1 in cmap1(ii)[:3]] for ii in xrange(256)]
        self.ovreg_lut = np.array(lut, dtype=np.ubyte)

        # add transparency
        alpha1 = np.ones((self.ovreg_lut.shape[0], 1))
        alpha1 *= 255
        alpha1[0] = 0
        # alpha1[1] = 0
        # alpha1[2] = 0
        self.ovreg_lut = np.hstack((self.ovreg_lut, alpha1))

        # Save the lut to the volume management system for easy transfer between widgets
        self.ivm.set_cmap(self.ovreg_lut)

    def set_default_colormap_manual(self):
        """
        Manually create a colormap
        """

        # Setting up overlay region viewing parameters
        ovreg_color = np.array([[0, 0, 255, 255], [0, 255, 0, 255], [255, 255, 0, 255], [255, 0, 0, 255]],
                               dtype=np.ubyte)
        ovreg_pos = np.array([0.0, 0.33, 0.66, 1.0])
        map1 = pg.ColorMap(ovreg_pos, ovreg_color)

        self.ovreg_lut = map1.getLookupTable(0, 1.0, 1000)
        self.ovreg_lut[0, 3] = 0

        # Save the lut to the volume management system for easy transfer between widgets
        self.ivm.set_cmap(self.ovreg_lut)

    @QtCore.Slot(int)
    def enable_drawing(self, color1=1):

        """
        Allow drawing on annotation in all three views
        """

        if color1 != -1:

            # start drawing with 3x3 brush
            kern = np.array([[color1]])
            self.imgwin1c.setDrawKernel(kern, mask=None, center=(1, 1), mode='set')
            self.imgwin2c.setDrawKernel(kern, mask=None, center=(1, 1), mode='set')
            self.imgwin3c.setDrawKernel(kern, mask=None, center=(1, 1), mode='set')

            self.view1.setAspectLocked(True)
            self.view2.setAspectLocked(True)
            self.view3.setAspectLocked(True)

        else:

            self.imgwin1c.setDrawKernel(kernel=None)
            self.imgwin2c.setDrawKernel(kernel=None)
            self.imgwin3c.setDrawKernel(kernel=None)

            self.view1.setAspectLocked(False)
            self.view2.setAspectLocked(False)
            self.view3.setAspectLocked(False)

            # Save overlay to annotation when stopped annotating
            self.save_overlay(True)

    @QtCore.Slot(bool)
    def save_overlay(self, state):
        """
        Save the edited annotation back to the volume management
        """
        if state:
            self.ivm.set_overlay('annotation', self.ovreg)



