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
        self.update_slider_range()

        #connect sliders to ivl1
        self.sld1.valueChanged[int].connect(self.ivl1.slider_connect1)
        self.sld2.valueChanged[int].connect(self.ivl1.slider_connect2)

        self.testbutton = QtGui.QPushButton("Test ok")

        # Tabbed Widget
        self.qtab1 = QtGui.QTabWidget()
        self.qtab1.setTabsClosable(True)
        self.qtab1.addTab(self.sw1, "Voxel analysis")
        self.qtab1.addTab(self.sw2, "Test 2")
        #signal
        self.qtab1.tabCloseRequested.connect(self.on_tab_close)

        #Layout
        hbox = QtGui.QHBoxLayout()
        vbox = QtGui.QVBoxLayout()

        # connect to ivl1
        vbox.addWidget(self.ivl1)
        vbox.addWidget(self.sld1)
        vbox.addWidget(self.sld2)

        # horizontal widgets
        hbox.addLayout(vbox)
        hbox.addWidget(self.qtab1)
        self.setLayout(hbox)

    # update slider range
    def update_slider_range(self):
        self.sld1.setRange(0, self.ivl1.img_dims[2])
        self.sld2.setRange(0, self.ivl1.img_dims[1])

    # Mouse clicked on widget
    def mousePressEvent(self, event):
        self.ivl1.mouse_click_connect(event)
        self.sld1.setValue(self.ivl1.cim_pos[2])
        self.sld2.setValue(self.ivl1.cim_pos[1])

    def on_tab_close(self, value):
        print("closing tab...(well testing it anyway) ", value)
        self.qtab1.removeTab(value)


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
        widgetmenu = menubar.addMenu('&Widgets')

        file_menu.addAction(load_action)
        file_menu.addAction(exit_action)

        self.toolbar = self.addToolBar('Load Image')
        self.toolbar.addAction(load_action)

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




