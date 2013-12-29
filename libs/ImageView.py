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
        self.img = np.zeros([10, 10, 10])
        print(self.img.shape)

        #self.ivl1 = pg.ImageView()
        #self.ivl1 = ImageViewLayout()
        #print(self.ivl1.mousePressPos)
        #self.win2 = pg.GraphicsLayoutWidget()

        #Current image position and size
        self.img_dims = self.img.shape
        self.cim_pos = [0, 0, 0]

        ##initialise layout
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

        self.view3 = self.addViewBox(name="view3")
        self.view3.setAspectLocked(True)
        self.imgwin3 = pg.ImageItem(border='k')
        self.view3.addItem(self.imgwin3)

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

        # update view
        self.__update_view()

    def __update_view(self):
        """
        Update the image viewer to account for the new position
        """

        self.imgwin1.setImage(self.img[:, :, self.cim_pos[2]])
        self.imgwin2.setImage(self.img[:, self.cim_pos[1], :])
        self.imgwin3.setImage(self.img[self.cim_pos[0], :, :])
        self.__update_crosshairs()

    # Slots for sliders and mouse
    @QtCore.Slot(int)
    def slider_connect1(self, value):
        self.cim_pos[2] = value
        self.__update_view()

    @QtCore.Slot(int)
    def slider_connect2(self, value):
        self.cim_pos[1] = value
        self.__update_view()

    @QtCore.Slot(int)
    def slider_connect3(self, value):
        self.cim_pos[0] = value
        self.__update_view()

    def mouse_click_connect(self, value):
        """
        On mouse click:
        1) get the current position on the image,
        2) update the view
        3) emit signal of current position data
        """
        self.__mouse_pos()
        self.__update_view()

        #Signal emit current enhancement curve
        vec_sig = self.img[self.cim_pos[0], :, self.cim_pos[2]]
        self.sig_mouse.emit(vec_sig)
