#!/usr/bin/env python

from __future__ import division, unicode_literals, absolute_import, print_function

import sys
import matplotlib

matplotlib.use('Qt4Agg')
matplotlib.rcParams['backend.qt4'] = 'PySide'
#from matplotlib.backends.backend_qt4agg import FigureCanvasQTAgg as FigureCanvas
#import matplotlib.pyplot as plt

from PySide import QtCore, QtGui

import pyqtgraph as pg
# setting defaults for the library
pg.setConfigOption('background', 'w')
pg.setConfigOption('foreground', 'k')

import nibabel as nib
import numpy as np


class ImageViewLayout(pg.GraphicsLayoutWidget):
    """
    Re-implementing graphics layout class to include mouse press event.
    This defines the 3D image interaction with the cross hairs
    """
    def __init__(self):
        super(ImageViewLayout, self).__init__()

        self.view1 = self.addViewBox(name="view1")
        self.view1.setAspectLocked(True)
        self.imgwin1 = pg.ImageItem(border='k')
        self.view1.addItem(self.imgwin1)
        self.view2 = self.addViewBox(name="view2")
        self.view2.setAspectLocked(True)
        self.imgwin2 = pg.ImageItem(border='k')
        self.view2.addItem(self.imgwin2)

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

        # Initial
        self.cim_pos = None

    #def mouseMoved(self, pos):
    #    print("Image position:", self.imgwin1.mapFromScene(pos))

    def mouse_pos(self, cim_pos):

        self.cim_pos = cim_pos

        """
        Capture positions of the 3 views on mouse press
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

        return self.cim_pos

    def update_crosshairs(self, cim_pos):
        self.cim_pos = cim_pos

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


class ImageView:
    """
    Controls the viewing of the image by interacting with the sliders in the main
    widget and passing on position data to ImageViewLayout
    """

    def __init__(self):

        self.file1 = None
        self.img = np.zeros([10, 10, 10])
        print(self.img.shape)

        #self.ivl1 = pg.ImageView()
        self.ivl1 = ImageViewLayout()
        #print(self.ivl1.mousePressPos)
        #self.win2 = pg.GraphicsLayoutWidget()

        #Current image position and size
        self.img_dims = self.img.shape
        self.cim_pos = [0, 0, 0]

    def load_image(self, file1):
        """
        Loading nifti image
        """

        self.file1 = file1
        img = nib.load(self.file1)
        self.img = img.get_data()
        self.img_dims = self.img.shape

        self.update_view()

    def update_view(self):

        self.ivl1.imgwin1.setImage(self.img[:, :, self.cim_pos[2]])
        self.ivl1.imgwin2.setImage(self.img[:, self.cim_pos[1], :])
        self.ivl1.imgwin3.setImage(self.img[self.cim_pos[0], :, :])

        self.ivl1.update_crosshairs(self.cim_pos)

    # Sliders
    def slider_connect1(self, value):
        self.cim_pos[2] = value
        self.update_view()

    def slider_connect2(self, value):
        self.cim_pos[1] = value
        self.update_view()

    def slider_connect3(self, value):
        self.cim_pos[0] = value
        self.update_view()

    def mouse_click_connect(self, value):
        self.cim_pos = self.ivl1.mouse_pos(self.cim_pos)
        self.update_view()


class MainWidge1(QtGui.QWidget):
    """
    Main widget where most of the control should happen
    """

    def __init__(self):
        super(MainWidge1, self).__init__()

        #loading ImageView
        self.im1 = ImageView()

        # InitUI
        # matplotlib central widget figure
        self.sld1 = QtGui.QSlider(QtCore.Qt.Horizontal, self)
        self.sld1.setFocusPolicy(QtCore.Qt.NoFocus)
        self.sld2 = QtGui.QSlider(QtCore.Qt.Horizontal, self)
        self.sld2.setFocusPolicy(QtCore.Qt.NoFocus)

        self.update_slider_range()

        hbox = QtGui.QVBoxLayout(self)

        #connect to im1
        self.sld1.valueChanged[int].connect(self.im1.slider_connect1)
        self.sld2.valueChanged[int].connect(self.im1.slider_connect2)

        # connect to im1
        hbox.addWidget(self.im1.ivl1)
        hbox.addWidget(self.sld1)
        #hbox.addWidget(self.im1.win2)
        hbox.addWidget(self.sld2)

    # update slider range
    def update_slider_range(self):
        self.sld1.setRange(0, self.im1.img_dims[2])
        self.sld2.setRange(0, self.im1.img_dims[1])

    # Mouse clicked on widget
    def mousePressEvent(self, event):
        self.im1.mouse_click_connect(event)
        self.sld1.setValue(self.im1.cim_pos[2])
        self.sld2.setValue(self.im1.cim_pos[1])


class MainWin1(QtGui.QMainWindow):
    """
    Really just used to add standard menu options etc.
    """
    def __init__(self):
        super(MainWin1, self).__init__()
        self.mw1 = MainWidge1()

        self.toolbar = None

        self.init_ui()

    def init_ui(self):
        self.setCentralWidget(self.mw1)
        self.setGeometry(300, 300, 1000, 500)

        self.menu_ui()
        self.show()

    def menu_ui(self):

        #File --> Load Image
        load_action = QtGui.QAction('&Load Image', self)
        load_action.setShortcut('Ctrl+L')
        load_action.setStatusTip('Load a 3d or 4d dceMRI image')
        load_action.triggered.connect(self.show_dialog)

        #File --> Exit
        exit_action = QtGui.QAction('&Exit', self)
        exit_action.setShortcut('Ctrl+Q')
        exit_action.setStatusTip('Exit Application')
        exit_action.triggered.connect(self.close)

        menubar = self.menuBar()
        file_menu = menubar.addMenu('&File')
        overlayMenu = menubar.addMenu('&Overlay')

        file_menu.addAction(load_action)
        file_menu.addAction(exit_action)

        self.toolbar = self.addToolBar('Load Image')
        self.toolbar.addAction(load_action)


    def show_dialog(self):
        """
        Dialog for loading a file
        """
        fname, _ = QtGui.QFileDialog.getOpenFileName(self, 'Open file', '/home')
        self.mw1.im1.load_image(fname)
        self.mw1.update_slider_range()
        print(fname)


def main():
    app = QtGui.QApplication(sys.argv)
    ex = MainWin1()
    sys.exit(app.exec_())


if __name__ == '__main__':
    main()




