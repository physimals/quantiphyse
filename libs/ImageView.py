from __future__ import division, unicode_literals, absolute_import, print_function

import matplotlib
matplotlib.use('Qt4Agg')
matplotlib.rcParams['backend.qt4'] = 'PySide'
#from matplotlib.backends.backend_qt4agg import FigureCanvasQTAgg as FigureCanvas
#import matplotlib.pyplot as plt
from matplotlib import cm

from PySide import QtCore

import nibabel as nib
import numpy as np

import pyqtgraph as pg
# setting defaults for the library
pg.setConfigOption('background', 'w')
pg.setConfigOption('foreground', 'k')


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
    sig_mouse = QtCore.Signal(np.ndarray)

    def __init__(self):
        super(ImageViewLayout, self).__init__()

        ## Initialise parameters
        self.file1 = None
        self.img = np.zeros((1, 1, 1))

        #Current image position and size
        self.img_dims = self.img.shape
        self.cim_pos = [0, 0, 0, 0]

        #ViewerOptions
        self.options = {}
        self.options['one_view'] = False

        #For creating screenshots. single large window

        #arrows
        self.pts1 = []

        ##initialise layout (3 view boxes each containing an image item)
        self.addLabel('Axial')

        if not self.options['one_view']:
            self.addLabel('Sagittal')
            self.nextRow()
        else:
            axwin = pg.GraphicsLayoutWidget()
            self.view2 = axwin.addViewBox(name="view2")
            self.view3 = axwin.addViewBox(name="view3")

        self.view1 = self.addViewBox(name="view1")
        self.view1.setAspectLocked(True)
        self.imgwin1 = pg.ImageItem(border='k')
        self.view1.addItem(self.imgwin1)
        if not self.options['one_view']:
            self.view2 = self.addViewBox(name="view2")
        self.view2.setAspectLocked(True)
        self.imgwin2 = pg.ImageItem(border='k')
        self.view2.addItem(self.imgwin2)

        #set a new row in the graphics layout widget
        if not self.options['one_view']:
            self.nextRow()
            self.addLabel('Coronal')
            self.nextRow()
            self.view3 = self.addViewBox(name="view3")
        self.view3.setAspectLocked(True)
        self.imgwin3 = pg.ImageItem(border='k')
        self.view3.addItem(self.imgwin3)

        #Cross hairs added to each viewbox

        self.vline1 = pg.InfiniteLine(angle=90, movable=False)
        self.hline1 = pg.InfiniteLine(angle=0, movable=False)
        self.vline1.setVisible(False)
        self.hline1.setVisible(False)
        self.view1.addItem(self.vline1, ignoreBounds=True)
        self.view1.addItem(self.hline1, ignoreBounds=True)

        self.vline2 = pg.InfiniteLine(angle=90, movable=False)
        self.hline2 = pg.InfiniteLine(angle=0, movable=False)
        self.vline2.setVisible(False)
        self.hline2.setVisible(False)
        self.view2.addItem(self.vline2, ignoreBounds=True)
        self.view2.addItem(self.hline2, ignoreBounds=True)

        self.vline3 = pg.InfiniteLine(angle=90, movable=False)
        self.hline3 = pg.InfiniteLine(angle=0, movable=False)
        self.vline3.setVisible(False)
        self.hline3.setVisible(False)
        self.view3.addItem(self.vline3, ignoreBounds=True)
        self.view3.addItem(self.hline3, ignoreBounds=True)
        #self.scene().sigMouseMoved.connect(self.mouseMoved)
        #self.scene().sigMouseReleased.connect()

        #Voxel size initialisation
        self.voxel_size = [1.0, 1.0, 1.0]
        # Range of image
        self.img_range = [0, 1]

    def load_image(self, file1):
        """
        Loading nifti image

        self.img: variable storing numpy volume
        self.img_dims: dimensions of the image

        """

        self.file1 = file1
        img = nib.load(self.file1)
        self.img = img.get_data()
        self.img_dims = self.img.shape

        h1 = img.get_affine()
        self.voxel_size = [np.abs(h1[0, 0]), np.abs(h1[1, 1]), np.abs(h1[2, 2])]

        self.img_range = [self.img.min(), self.img.max()]

        print("Image dimensions: ", self.img_dims)
        print("Voxel size: ", self.voxel_size)
        print("Image range: ", self.img_range)

        # update view
        self._update_view()

    def __mouse_pos(self):
        """
        Capture positions of the 3 views on mouse press and update cim_pos
        """
        # existing stuff
        #super(ImageViewLayout, self).mousePressEvent(event)
        #print(self.lastMousePos)

        if self.view1.sceneBoundingRect().contains(self.lastMousePos):
            print("Image position 1:", self.imgwin1.mapFromScene(self.lastMousePos))
            mouse_point = self.imgwin1.mapFromScene(self.lastMousePos)
            self.cim_pos[0] = mouse_point.x()
            self.cim_pos[1] = mouse_point.y()
            print(self.cim_pos)

        elif self.view2.sceneBoundingRect().contains(self.lastMousePos):
            print("Image position 2:", self.imgwin2.mapFromScene(self.lastMousePos))
            mouse_point = self.imgwin2.mapFromScene(self.lastMousePos)
            self.cim_pos[0] = mouse_point.x()
            self.cim_pos[2] = mouse_point.y()
            print(self.cim_pos)

        elif self.view3.sceneBoundingRect().contains(self.lastMousePos):
            print("Image position 3:", self.imgwin3.mapFromScene(self.lastMousePos))
            mouse_point = self.imgwin3.mapFromScene(self.lastMousePos)
            self.cim_pos[1] = mouse_point.x()
            self.cim_pos[2] = mouse_point.y()
            print(self.cim_pos)

    def __update_crosshairs(self):
        """
        update cross hair positions based on cim_pos

        """

        self.vline1.setPos(self.cim_pos[0])
        self.hline1.setPos(self.cim_pos[1])
        self.vline1.setVisible(True)
        self.hline1.setVisible(True)
        #
        self.vline2.setPos(self.cim_pos[0])
        self.hline2.setPos(self.cim_pos[2])
        self.vline2.setVisible(True)
        self.hline2.setVisible(True)
        #
        self.vline3.setPos(self.cim_pos[1])
        self.hline3.setPos(self.cim_pos[2])
        self.vline3.setVisible(True)
        self.hline3.setVisible(True)

    def _update_view(self):
        """
        Update the image viewer to account for the new position
        """

        if len(self.img_dims) == 3:
            self.imgwin1.setImage(self.img[:, :, self.cim_pos[2]])
            self.imgwin2.setImage(self.img[:, self.cim_pos[1], :])
            self.imgwin3.setImage(self.img[self.cim_pos[0], :, :])

        elif len(self.img_dims) == 4:

            self.imgwin1.setImage(self.img[:, :, self.cim_pos[2], self.cim_pos[3]])
            self.imgwin2.setImage(self.img[:, self.cim_pos[1], :, self.cim_pos[3]])
            self.imgwin3.setImage(self.img[self.cim_pos[0], :, :, self.cim_pos[3]])
        else:
            print("Image does not have 3 or 4 dimensions")

        self.__update_crosshairs()
        self.imgwin1.setLevels(self.img_range)
        self.imgwin2.setLevels(self.img_range)
        self.imgwin3.setLevels(self.img_range)


    # Slots for sliders and mouse
    @QtCore.Slot(int)
    def slider_connect1(self, value):
        self.cim_pos[2] = value
        self._update_view()

    @QtCore.Slot(int)
    def slider_connect2(self, value):
        self.cim_pos[1] = value
        self._update_view()

    @QtCore.Slot(int)
    def slider_connect3(self, value):
        self.cim_pos[0] = value
        self._update_view()

    @QtCore.Slot(int)
    def slider_connect4(self, value):
        self.cim_pos[3] = value
        self._update_view()

    @QtCore.Slot(int)
    def mouse_click_connect(self, value):
        """
        On mouse click:
        1) get the current position on the image,
        2) update the view
        3) emit signal of current position data
        """
        self.__mouse_pos()
        self._update_view()

        #Signal emit current enhancement curve
        if len(self.img_dims) == 3: 
            print("3D image so just calculating cross image profile")
            vec_sig = self.img[self.cim_pos[0], :, self.cim_pos[2]]
        elif len(self.img_dims) == 4:
            vec_sig = self.img[self.cim_pos[0], self.cim_pos[1], self.cim_pos[2], :]
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
        self.pts1[-1].setPos(self.cim_pos[0], self.cim_pos[1])
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
            self.view1.setAspectLocked(True, ratio=(self.voxel_size[0] / self.voxel_size[1]))
            self.view2.setAspectLocked(True, ratio=(self.voxel_size[0] / self.voxel_size[2]))
            self.view3.setAspectLocked(True, ratio=(self.voxel_size[1] / self.voxel_size[2]))
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

        # Number of ROIs
        self.num_roi = 0

        # ROI Image windows
        self.imgwin1b = []
        self.imgwin2b = []
        self.imgwin3b = []


        # Contour
        self.cont1 = []
        self.cont2 = []
        self.cont3 = []

        # ROI image
        self.roi = None
        self.roi_all = []  # All rois
        self.roi_dims = None
        self.roi_file1 = None

        # Viewing options as a dictionary
        self.options['ShowOverlay'] = 1
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

    def load_roi(self, file1):
        """
        Loads and checks roi image
        Initialise viewing windows
        """

        if self.img.shape[0] == 1:
            print("Please load an image first")
            return

        #Setting ROI data
        self.roi_file1 = file1
        roi = nib.load(self.roi_file1)
        self.roi = roi.get_data()
        self.roi_all.append(self.roi)
        self.roi_dims = self.roi.shape

        if (self.roi_dims != self.img_dims[:3]) or (len(self.roi_dims) > 3):
            print("First 3 Dimensions of the ROI must be the same as the image, "
                  "and ROI must be 3D")
            self.roi = None
            self.roi_dims = None

        else:
            self.num_roi += 1

        # Initialises viewer if it hasn't been initialised before
        self.imgwin1b.append(pg.ImageItem(border='k'))
        self.imgwin2b.append(pg.ImageItem(border='k'))
        self.imgwin3b.append(pg.ImageItem(border='k'))
        self.view1.addItem(self.imgwin1b[self.num_roi-1])
        self.view2.addItem(self.imgwin2b[self.num_roi-1])
        self.view3.addItem(self.imgwin3b[self.num_roi-1])

        self.cont1.append(pg.IsocurveItem(level=1.0, pen=self.roipen[self.num_roi-1]))
        self.cont2.append(pg.IsocurveItem(level=1.0, pen=self.roipen[self.num_roi-1]))
        self.cont3.append(pg.IsocurveItem(level=1.0, pen=self.roipen[self.num_roi-1]))
        self.view1.addItem(self.cont1[self.num_roi-1])
        self.view2.addItem(self.cont2[self.num_roi-1])
        self.view3.addItem(self.cont3[self.num_roi-1])

        self._update_view()

    def _update_view(self):
        super(ImageViewOverlay, self)._update_view()

        if self.num_roi == 0:
            #If an overlay hasn't been added then return
            return

        #Loop over each volume
        for ii in range(self.num_roi):

            if (self.roi_dims is None) or (self.options['ShowOverlay'] == 0):
                self.imgwin1b[ii].setImage(np.zeros((1, 1)))
                self.imgwin2b[ii].setImage(np.zeros((1, 1)))
                self.imgwin3b[ii].setImage(np.zeros((1, 1)))

            else:
                self.imgwin1b[ii].setImage(self.roi_all[ii][:, :, self.cim_pos[2]], lut=self.roilut)
                self.imgwin2b[ii].setImage(self.roi_all[ii][:, self.cim_pos[1], :], lut=self.roilut)
                self.imgwin3b[ii].setImage(self.roi_all[ii][self.cim_pos[0], :, :], lut=self.roilut)

            if self.options['ShowOverlayContour']:
                self.cont1[ii].setData(self.roi_all[ii][:, :, self.cim_pos[2]])
                self.cont2[ii].setData(self.roi_all[ii][:, self.cim_pos[1], :])
                self.cont3[ii].setData(self.roi_all[ii][self.cim_pos[0], :, :])
            else:
                self.cont1[ii].setData(None)
                self.cont2[ii].setData(None)
                self.cont3[ii].setData(None)

    #Slot to toggle whether the overlay is seen or not
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
        self.ovreg_dims = None
        self.ovreg_file1 = None

        # Viewing options as a dictionary
        self.options['ShowColorOverlay'] = 1
        self.options['ColorMap'] = 'jet' # default. Can choose any matplotlib colormap
        self.options['UseROI'] = 1

        #Initialise the colormap
        self.ovreg_lut = None
        self.set_default_colormap_matplotlib()
        #self.set_default_colormap_manual()
        self.ov_range = [0.0, 1.0]

    def load_ovreg(self, file1):
        """
        Loads and checks Overlay region image
        """

        #TODO Might be cleaner to do this checking in the loading function
        if self.img.shape[0] == 1:
            print("Please load an image first")
            return

        #Setting Overlay region data
        self.ovreg_file1 = file1
        ovreg = nib.load(self.ovreg_file1)
        self.ovreg_in = ovreg.get_data()

        self._process_overlay()

        if (self.ovreg_dims != self.img_dims[:3]) or (len(self.ovreg_dims) > 3):
            print("First 3 Dimensions of the overlay region must be the same as the image, "
                  "and overlay region must be 3D")
            self.ovreg = None
            self.ovreg_dims = None

        if self.imgwin1c is None:
            # Initialises viewer if it hasn't been initialised before
            self.imgwin1c = pg.ImageItem(border='k')
            self.imgwin2c = pg.ImageItem(border='k')
            self.imgwin3c = pg.ImageItem(border='k')
            self.view1.addItem(self.imgwin1c)
            self.view2.addItem(self.imgwin2c)
            self.view3.addItem(self.imgwin3c)


        self.imgwin1c.setLevels(self.ov_range)
        self.imgwin2c.setLevels(self.ov_range)
        self.imgwin3c.setLevels(self.ov_range)

        self._update_view()

    def _process_overlay(self):

        self.ovreg = np.copy(self.ovreg_in)
        self.ovreg_dims = self.ovreg.shape
        # Convert to numpy double
        self.ovreg = np.array(self.ovreg, dtype=np.double)

        if (self.roi is not None) and (self.options['UseROI'] == 1):

            #Scale ROI
            subreg1 = self.ovreg[np.array(self.roi, dtype=bool)]
            self.ovreg = self.ovreg - np.min(subreg1)
            self.ovreg = self.ovreg / np.max(subreg1 - np.min(subreg1))

            #Set transparency around ROI
            self.ovreg[np.logical_not(self.roi)] = -0.01

            self.ov_range = [self.ovreg.min(), self.ovreg.max()]

        else:
            #Normalisation
            self.ovreg = self.ovreg - np.min(self.ovreg)
            self.ovreg = self.ovreg / np.max(self.ovreg)

            self.ov_range = [self.ovreg.min(), self.ovreg.max()]


    def _update_view(self):
        super(ImageViewColorOverlay, self)._update_view()

        if self.imgwin1c is None:
            #If an overlay hasn't been added then return
            return

        if (self.ovreg_dims is None) or (self.options['ShowColorOverlay'] == 0):
            self.imgwin1c.setImage(np.zeros((1, 1)))
            self.imgwin2c.setImage(np.zeros((1, 1)))
            self.imgwin3c.setImage(np.zeros((1, 1)))
        else:
            self.imgwin1c.setImage(self.ovreg[:, :, self.cim_pos[2]], lut=self.ovreg_lut)
            self.imgwin2c.setImage(self.ovreg[:, self.cim_pos[1], :], lut=self.ovreg_lut)
            self.imgwin3c.setImage(self.ovreg[self.cim_pos[0], :, :], lut=self.ovreg_lut)


        self.imgwin1c.setLevels(self.ov_range)
        self.imgwin2c.setLevels(self.ov_range)
        self.imgwin3c.setLevels(self.ov_range)

    #Slot to toggle whether the overlay is seen or not
    @QtCore.Slot()
    def toggle_roi_lim(self, state):

        """
        Show or hide overlay
        """

        if state == QtCore.Qt.Checked:
            self.options['UseROI'] = 1
        else:
            self.options['UseROI'] = 0

        self._process_overlay()
        self._update_view()

    @QtCore.Slot()
    def toggle_ovreg_view(self, state):

        if state == QtCore.Qt.Checked:
            self.options['ShowColorOverlay'] = 1
        else:
            self.options['ShowColorOverlay'] = 0

        self._update_view()

    #Slot to change overlay transparency
    @QtCore.Slot(int)
    def set_overlay_alpha(self, state):
        """
        Set the transparency
        """

        # Changing colormap
        self.ovreg_lut[:, 3] = state
        self.ovreg_lut[0, 3] = 0

        self.imgwin1c.setLookupTable(self.ovreg_lut)
        self.imgwin2c.setLookupTable(self.ovreg_lut)
        self.imgwin3c.setLookupTable(self.ovreg_lut)
        #self._update_view()

    @QtCore.Slot()
    def set_overlay_range(self, state):
        """
        Set the range of the overlay map
        """
        None

    @QtCore.Slot(str)
    def set_colormap(self, text):
        """
        Choose a colormap
        """
        self.options['ColorMap'] = text

        # update colormap
        self.set_default_colormap_matplotlib()

        # set colormap
        self.imgwin1c.setLookupTable(self.ovreg_lut)
        self.imgwin2c.setLookupTable(self.ovreg_lut)
        self.imgwin3c.setLookupTable(self.ovreg_lut)
        #self._update_view()



    def set_default_colormap_matplotlib(self):

        """
        Use default colormaps from matplotlib.

        First value out of the 255 range is set to be transparent. This needs to maybe be defined in a slightly better
        way to avoid scaling issue.
        """

        cmap1 = getattr(cm, self.options['ColorMap'])

        lut = [[int(255*rgb1) for rgb1 in cmap1(ii)[:3]] for ii in xrange(256)]
        self.ovreg_lut = np.array(lut, dtype=np.ubyte)

        alpha1 = np.ones((self.ovreg_lut.shape[0], 1))
        alpha1 *= 255
        alpha1[0] = 0
        self.ovreg_lut = np.hstack((self.ovreg_lut, alpha1))

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







