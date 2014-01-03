from __future__ import division, unicode_literals, absolute_import, print_function

import matplotlib
matplotlib.use('Qt4Agg')
matplotlib.rcParams['backend.qt4'] = 'PySide'
#from matplotlib.backends.backend_qt4agg import FigureCanvasQTAgg as FigureCanvas
#import matplotlib.pyplot as plt

from PySide import QtGui, QtCore

import nibabel as nib
import numpy as np

import pyqtgraph as pg
# setting defaults for the library
pg.setConfigOption('background', 'w')
pg.setConfigOption('foreground', 'k')


class ImageViewLayout(pg.GraphicsLayoutWidget):
    """
    Re-implementing graphics layout class to include mouse press event.
    This defines the 3D image interaction with the cross hairs,
    provides slots to connect sliders and controls 3D image view updates

    Adding 4D view

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

        ##initialise layout (3 view boxes each containing an image item)
        self.addLabel('Axial')
        self.addLabel('Sagittal')
        self.nextRow()
        self.view1 = self.addViewBox(name="view1")
        self.view1.setAspectLocked(True)
        self.imgwin1 = pg.ImageItem(border='k')
        self.view1.addItem(self.imgwin1)
        self.view2 = self.addViewBox(name="view2")
        self.view2.setAspectLocked(True)
        self.imgwin2 = pg.ImageItem(border='k')
        self.view2.addItem(self.imgwin2)

        #set a new row in the graphics layout widget
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

    #def mouseMoved(self, pos):
    #    print("Image position:", self.imgwin1.mapFromScene(pos))

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

        print(self.img_dims)

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

        self.sig_mouse.emit(vec_sig)


class ImageViewOverlay(ImageViewLayout):
    """
    Adds the ability to view the ROI as a transparent overlay
    """

    def __init__(self):
        # Updating viewer to include second image layer
        super(ImageViewOverlay, self).__init__()
        self.imgwin1b = pg.ImageItem(border='k')
        self.imgwin2b = pg.ImageItem(border='k')
        self.imgwin3b = pg.ImageItem(border='k')
        self.view1.addItem(self.imgwin1b)
        self.view2.addItem(self.imgwin2b)
        self.view3.addItem(self.imgwin3b)

        # ROI image
        self.roi = None
        self.roi_dims = None
        self.roi_file1 = None

        # Viewing options as a dictionary
        self.options['ShowOverlay'] = 1

        # Setting up ROI viewing parameters
        pos = np.array([0.0, 1.0])
        color = np.array([[0, 0, 0, 0], [255, 0, 0, 90]], dtype=np.ubyte)
        map1 = pg.ColorMap(pos, color)
        self.roilut = map1.getLookupTable(0.0, 1.0, 256)

    def load_roi(self, file1):
        """
        Loads and checks roi image
        """
        #TODO Might be cleaner to do this checking in the loading function

        if self.img.shape[0] == 1:
            print("Please load an image first")
            return

        self.roi_file1 = file1
        roi = nib.load(self.roi_file1)
        self.roi = roi.get_data()
        self.roi_dims = self.roi.shape

        if (self.roi_dims != self.img_dims[:3]) or (len(self.roi_dims) > 3):
            print("First 3 Dimensions of the ROI must be the same as the image, "
                  "and ROI must be 3D")
            self.roi = None
            self.roi_dims = None

        self._update_view()

    def _update_view(self):
        super(ImageViewOverlay, self)._update_view()

        if (self.roi_dims is None) or (self.options['ShowOverlay'] == 0):
            self.imgwin1b.setImage(np.zeros((1, 1)))
            self.imgwin2b.setImage(np.zeros((1, 1)))
            self.imgwin3b.setImage(np.zeros((1, 1)))
        else:
            self.imgwin1b.setImage(self.roi[:, :, self.cim_pos[2]], lut=self.roilut)
            self.imgwin2b.setImage(self.roi[:, self.cim_pos[1], :], lut=self.roilut)
            self.imgwin3b.setImage(self.roi[self.cim_pos[0], :, :], lut=self.roilut)

    @QtCore.Slot()
    def toggle_roi_view(self, state):

        if state == QtCore.Qt.Checked:
            self.options['ShowOverlay'] = 1
        else:
            self.options['ShowOverlay'] = 0
        self._update_view()



        '''
        ################ testing colormaps, LUTs and ROIs
        print("Testing colormap, LUT and alpha ROIs")

        pos = np.array([-1.0, 0.0, 0.5, 1.0])
        color = np.array([[0, 0, 0, 0], [0, 0, 255, 255], [0, 255, 0, 255], [255, 0, 0, 255]], dtype=np.ubyte)
        map1 = pg.ColorMap(pos, color)
        lut = map1.getLookupTable(-1.0, 1.0, 256)
        img_test = self.img[:, self.cim_pos[1], :]
        img_test = img_test - img_test.min()
        img_test = img_test / img_test.max()
        print(img_test.max())
        print(img_test.min())
        print(img_test.mean())
        img_test[img_test < 0.5] = -1
        self.imgwin1b.setImage(img_test, lut=lut)
        #################
        '''