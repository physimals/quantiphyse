#!/usr/bin/env python
from __future__ import division, unicode_literals, absolute_import, print_function

import matplotlib
matplotlib.use('Qt4Agg')
matplotlib.rcParams['backend.qt4'] = 'PySide'

import sys
from PySide import QtCore, QtGui


# my libs
from libs.ImageView import ImageViewLayout
from libs.AnalysisWidgets import SECurve, SECurve2

#TODO Need some sort of volume management object...
#TODO Need map overlay function


class MainWidge1(QtGui.QWidget):
    """
    Main widget where most of the control should happen
    """

    def __init__(self):
        super(MainWidge1, self).__init__()

        #loading ImageView
        self.ivl1 = ImageViewLayout()
        self.sw1 = SECurve()
        self.sw2 = SECurve2()

        #Connecting widget signals
        #1) Plotting data on mouse image click
        self.ivl1.sig_mouse.connect(self.sw1.sig_mouse)

        # InitUI
        #Sliders
        self.sld1 = QtGui.QSlider(QtCore.Qt.Horizontal, self)
        self.sld1.setFocusPolicy(QtCore.Qt.NoFocus)
        self.sld2 = QtGui.QSlider(QtCore.Qt.Horizontal, self)
        self.sld2.setFocusPolicy(QtCore.Qt.NoFocus)
        self.sld3 = QtGui.QSlider(QtCore.Qt.Horizontal, self)
        self.sld3.setFocusPolicy(QtCore.Qt.NoFocus)
        self.sld4 = QtGui.QSlider(QtCore.Qt.Horizontal, self)
        self.sld4.setFocusPolicy(QtCore.Qt.NoFocus)
        self.update_slider_range()

        #connect sliders to ivl1
        self.sld1.valueChanged[int].connect(self.ivl1.slider_connect1)
        self.sld2.valueChanged[int].connect(self.ivl1.slider_connect2)
        self.sld3.valueChanged[int].connect(self.ivl1.slider_connect3)
        self.sld4.valueChanged[int].connect(self.ivl1.slider_connect4)

        self.testbutton = QtGui.QPushButton("Test ok")

        # Tabbed Widget
        self.qtab1 = QtGui.QTabWidget()
        self.qtab1.setTabsClosable(True)
        self.qtab1.setMovable(True)
        self.qtab1.addTab(self.sw1, "Voxel analysis")
        self.qtab1.addTab(self.sw2, "Test 2")
        #signal
        self.qtab1.tabCloseRequested.connect(self.on_tab_close)

        #Layout
        grid = QtGui.QGridLayout()
        grid.setSpacing(10)
      
        # connect to ivl1
        grid.addWidget(self.ivl1, 0, 0, 1, 3)
        grid.addWidget(QtGui.QLabel('Axial'), 1, 0)
        grid.addWidget(self.sld1, 1, 1)
        grid.addWidget(QtGui.QLabel('Sagittal'), 2, 0)
        grid.addWidget(self.sld2, 2, 1)
        grid.addWidget(QtGui.QLabel('Coronal'), 3, 0)
        grid.addWidget(self.sld3, 3, 1)
        grid.addWidget(QtGui.QLabel('Time'), 4, 0)
        grid.addWidget(self.sld4, 4, 1)
        grid.addWidget(self.qtab1, 0, 3, 5, 1)
        #define the proportion of the space each column takes
        grid.setColumnStretch(1, 3)
        grid.setColumnStretch(2, 3)
        grid.setColumnStretch(3, 4)
        #grid.setColumnMinimumHeight()

        # horizontal widgets
        self.setLayout(grid)

    # update slider range
    def update_slider_range(self):
        #set slider range
        self.sld1.setRange(0, self.ivl1.img_dims[2]-1)
        self.sld2.setRange(0, self.ivl1.img_dims[1]-1)
        self.sld3.setRange(0, self.ivl1.img_dims[0]-1)

        if len(self.ivl1.img_dims) == 4:
            self.sld4.setRange(0, self.ivl1.img_dims[3]-1)
        else:
            self.sld4.setRange(0, 0)

    # Mouse clicked on widget
    def mousePressEvent(self, event):
        self.ivl1.mouse_click_connect(event)
        #update slider positions
        self.sld1.setValue(self.ivl1.cim_pos[2])
        self.sld2.setValue(self.ivl1.cim_pos[1])
        self.sld3.setValue(self.ivl1.cim_pos[0])

    # Handles closing of tabs
    def on_tab_close(self, value):
        print("closing tab...(well testing it anyway) ", value)
        self.qtab1.removeTab(value)

        #TODO delete object if tab closed? Create object if menu item clicked?

    #
    def show_se(self):
        index = self.qtab1.addTab(self.sw1, "Voxel analysis")
        print(index)
        self.qtab1.setCurrentIndex(index)


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
        self.setGeometry(100, 100, 1000, 500)
        self.setCentralWidget(self.mw1)

        self.menu_ui()
        self.show()

    def menu_ui(self):

        #File --> Load Image
        load_action = QtGui.QAction(QtGui.QIcon('icons/layers.svg'), '&Load Image Volume', self)
        load_action.setShortcut('Ctrl+L')
        load_action.setStatusTip('Load a 3d or 4d dceMRI image')
        load_action.triggered.connect(self.show_dialog)

        #File --> Settings
        #TODO

        #File --> Exit
        exit_action = QtGui.QAction('&Exit', self)
        exit_action.setShortcut('Ctrl+Q')
        exit_action.setStatusTip('Exit Application')
        exit_action.triggered.connect(self.close)

        # Widgets --> SE curve
        se_action = QtGui.QAction('&SEcuve', self)
        se_action.setStatusTip('Plot SE of a voxel')
        se_action.triggered.connect(self.mw1.show_se)

        #Help -- > Online help
        help_action = QtGui.QAction('&Online Help', self)
        help_action.setStatusTip('See online help file')

        menubar = self.menuBar()
        file_menu = menubar.addMenu('&File')
        overlayMenu = menubar.addMenu('&Overlay')
        widget_menu = menubar.addMenu('&Widgets')
        help_menu = menubar.addMenu('&Help')

        file_menu.addAction(load_action)
        file_menu.addAction(exit_action)

        widget_menu.addAction(se_action)

        help_menu.addAction(help_action)

        self.toolbar = self.addToolBar('Load Image')
        self.toolbar.addAction(load_action)

        # extra info displayed in the status bar
        self.statusBar()

    def show_dialog(self):
        """
        Dialog for loading a file
        """
        fname, _ = QtGui.QFileDialog.getOpenFileName(self, 'Open file', '/home')
        self.mw1.ivl1.load_image(fname)
        self.mw1.update_slider_range()
        print(fname)


def main():
    app = QtGui.QApplication(sys.argv)
    ex = MainWin1()
    sys.exit(app.exec_())


if __name__ == '__main__':
    main()




