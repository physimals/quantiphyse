#!/usr/bin/env python

"""
Benjamin Irving

"""

#TODO 1) Drag and drop file volumes into a volume window

from __future__ import division, unicode_literals, absolute_import, print_function

import matplotlib
matplotlib.use('Qt4Agg')
matplotlib.rcParams['backend.qt4'] = 'PySide'

import sys
import os
from PySide import QtCore, QtGui

# My libs
from libs.ImageView import ImageViewColorOverlay
from libs.AnalysisWidgets import SECurve, ColorOverlay1, PharmaWidget
from analysis.volume_management import ImageVolumeManagement
from analysis.overlay_analysis import OverlayAnalyis


class QGroupBoxClick(QtGui.QGroupBox):

    """
    Subclassing QGroupBox to detect clicks and signal click
    """

    sig_click = QtCore.Signal(int)

    # Mouse clicked on widget
    def mousePressEvent(self, event):
        self.sig_click.emit(1)


class MainWidge1(QtGui.QWidget):

    """
    Main widget where most of the control should happen

    """

    def __init__(self):
        super(MainWidge1, self).__init__()

        # Loading data management object
        self.ivm = ImageVolumeManagement()

        # Loading image analysis
        self.ia = OverlayAnalyis()
        self.ia.add_image_management(self.ivm)

        #loading ImageView
        self.ivl1 = ImageViewColorOverlay()
        self.ivl1.add_image_management(self.ivm)

        # Loading widgets
        self.sw1 = SECurve()

        self.sw2 = ColorOverlay1()
        self.sw2.add_analysis(self.ia)
        self.sw2.add_image_management(self.ivm)

        self.sw3 = PharmaWidget()

        # Connect widgets
        #Connect colormap choice, alpha
        self.sw2.sig_choose_cmap.connect(self.ivl1.set_colormap)
        self.sw2.sig_set_alpha.connect(self.ivl1.set_overlay_alpha)
        self.sw2.cb1.stateChanged.connect(self.ivl1.toggle_ovreg_view)
        self.sw2.cb2.stateChanged.connect(self.ivl1.toggle_roi_lim)

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

        #CheckBox
        cb1 = QtGui.QCheckBox('Show ROI', self)
        cb1.toggle()
        cb1.stateChanged.connect(self.ivl1.toggle_roi_view)
        cb2 = QtGui.QCheckBox('Show ROI contour', self)
        cb2.stateChanged.connect(self.ivl1.toggle_roi_contour)
        cb3 = QtGui.QCheckBox('Use voxel size scaling', self)
        cb3.stateChanged.connect(self.ivl1.toggle_dimscale)

        # Tabbed Widget
        self.qtab1 = QtGui.QTabWidget()
        self.qtab1.setTabsClosable(True)
        self.qtab1.setMovable(True)
        #Widgets
        self.qtab1.addTab(self.sw1, "Voxel analysis")
        self.qtab1.addTab(self.sw2, "Color overlay")
        self.qtab1.addTab(self.sw3, "Pharmacokinetics")
        #signal
        self.qtab1.tabCloseRequested.connect(self.on_tab_close)

        #Position Label and connect to slider
        lab_p1 = QtGui.QLabel('0')
        self.sld1.valueChanged[int].connect(lab_p1.setNum)
        lab_p2 = QtGui.QLabel('0')
        self.sld2.valueChanged[int].connect(lab_p2.setNum)
        lab_p3 = QtGui.QLabel('0')
        self.sld3.valueChanged[int].connect(lab_p3.setNum)
        lab_p4 = QtGui.QLabel('0')
        self.sld4.valueChanged[int].connect(lab_p4.setNum)

        #Layout
        # Box of buttons
        gBox = QtGui.QGroupBox("Image and ROI options")
        gBoxlay = QtGui.QVBoxLayout()
        gBoxlay.addWidget(cb1)
        gBoxlay.addWidget(cb2)
        gBoxlay.addWidget(cb3)
        gBoxlay.addStretch(1)
        gBox.setLayout(gBoxlay)
        gBox.setStyleSheet("QGroupBox{border:2px solid gray;border-radius:5px;margin-top: 1ex;} "
                           "QGroupBox::title{subcontrol-origin: margin;subcontrol-position:top center;padding:0 3px;}")

        # Slider layout
        gBox2 = QtGui.QGroupBox("Navigation Sliders")
        gBoxlay2 = QtGui.QGridLayout()
        gBoxlay2.addWidget(QtGui.QLabel('Axial'), 0, 0)
        gBoxlay2.addWidget(self.sld1, 0, 1)
        gBoxlay2.addWidget(lab_p1, 0, 2)
        gBoxlay2.addWidget(QtGui.QLabel('Sagittal'), 1, 0)
        gBoxlay2.addWidget(self.sld2, 1, 1)
        gBoxlay2.addWidget(lab_p2, 1, 2)
        gBoxlay2.addWidget(QtGui.QLabel('Coronal'), 2, 0)
        gBoxlay2.addWidget(self.sld3, 2, 1)
        gBoxlay2.addWidget(lab_p3, 2, 2)
        gBoxlay2.addWidget(QtGui.QLabel('Time'), 3, 0)
        gBoxlay2.addWidget(self.sld4, 3, 1)
        gBoxlay2.addWidget(lab_p4, 3, 2)
        gBoxlay2.setColumnStretch(0, 0)
        gBoxlay2.setColumnStretch(1, 2)

        gBox2.setLayout(gBoxlay2)
        gBox2.setStyleSheet("QGroupBox{border:2px solid gray;border-radius:5px;margin-top: 1ex;} "
                            "QGroupBox::title{subcontrol-origin: margin;subcontrol-position:top center;padding:0 3px;}")

        # All buttons layout
        gBox_all = QtGui.QGroupBox()
        gBoxlay_all = QtGui.QHBoxLayout()
        gBoxlay_all.addWidget(gBox2)
        gBoxlay_all.addStretch(1)
        gBoxlay_all.addWidget(gBox)
        gBoxlay_all.setStretch(0, 2)
        gBoxlay_all.setStretch(2, 1)
        gBox_all.setLayout(gBoxlay_all)

        # Viewing window layout + buttons
        # Add a horizontal splitter between image viewer and buttons below
        grid_box = QGroupBoxClick("Viewer")
        grid_box.sig_click.connect(self.mpe)
        grid = QtGui.QVBoxLayout()
        splitter2 = QtGui.QSplitter(QtCore.Qt.Vertical)
        splitter2.addWidget(self.ivl1)
        splitter2.addWidget(gBox_all)
        splitter2.setStretchFactor(0, 3)
        splitter2.setStretchFactor(1, 1)
        grid.addWidget(splitter2)
        grid_box.setLayout(grid)

        # Add a vertical splitter between main view and tabs
        hbox = QtGui.QHBoxLayout(self)
        splitter1 = QtGui.QSplitter(QtCore.Qt.Horizontal)
        splitter1.addWidget(grid_box)
        splitter1.addWidget(self.qtab1)
        splitter1.setStretchFactor(0, 2)
        splitter1.setStretchFactor(1, 1)
        hbox.addWidget(splitter1)

        # horizontal widgets
        self.setLayout(hbox)

        # Signals to connect widget
        self.sw1.sig_add_pnt.connect(self.ivl1.add_arrow_current_pos)
        self.sw1.sig_clear_pnt.connect(self.ivl1.remove_all_arrows)

    # update slider range
    def update_slider_range(self):
        #set slider range
        self.sld1.setRange(0, self.ivm.img_dims[2]-1)
        self.sld2.setRange(0, self.ivm.img_dims[1]-1)
        self.sld3.setRange(0, self.ivm.img_dims[0]-1)

        if len(self.ivm.img_dims) == 4:
            self.sld4.setRange(0, self.ivm.img_dims[3]-1)
        else:
            self.sld4.setRange(0, 0)

    # Mouse clicked on widget
    @QtCore.Slot(int)
    def mpe(self, event):
        """
        Provides a pathway to updating mouse points
        """

        #trigger update of image
        self.ivl1.mouse_click_connect(event)

        #update slider positions
        self.sld1.setValue(self.ivm.cim_pos[2])
        self.sld2.setValue(self.ivm.cim_pos[1])
        self.sld3.setValue(self.ivm.cim_pos[0])

    # Handles closing of tabs
    def on_tab_close(self, value):
        self.qtab1.removeTab(value)

        #TODO delete object if tab closed? Create object if menu item clicked?

    # Connect widget
    def show_se(self):
        index = self.qtab1.addTab(self.sw1, "Voxel analysis")
        print(index)
        self.qtab1.setCurrentIndex(index)


class MainWin1(QtGui.QMainWindow):
    """
    Overall window framework
    Only purpose is to put the menu, menu bar etc decorations around the main window
    Also initialises the open file menus
    """
    def __init__(self):
        super(MainWin1, self).__init__()
        self.mw1 = MainWidge1()

        self.toolbar = None
        self.default_directory ='/home'

        # Patch for if file is frozen
        if hasattr(sys, 'frozen'):
            # if frozen
            self.local_file_path = os.path.dirname(sys.executable)
        else:
            self.local_file_path = os.path.dirname(__file__)
            #self.local_file_path = os.getcwd()

        self.init_ui()

    def init_ui(self):
        self.setGeometry(100, 100, 1000, 500)
        self.setCentralWidget(self.mw1)
        self.setWindowTitle("PkViewer")
        self.setWindowIcon(QtGui.QIcon(self.local_file_path + '/icons/main_icon.png'))

        self.menu_ui()
        self.show()

    def menu_ui(self):

        #File --> Load Image
        load_action = QtGui.QAction(QtGui.QIcon(self.local_file_path + '/icons/picture.svg'), '&Load Image Volume', self)
        load_action.setShortcut('Ctrl+L')
        load_action.setStatusTip('Load a 3d or 4d dceMRI image')
        load_action.triggered.connect(self.show_image_load_dialog)

        #File --> Load ROI
        load_roi_action = QtGui.QAction(QtGui.QIcon(self.local_file_path + '/icons/pencil.svg'), '&Load ROI', self)
        load_roi_action.setStatusTip('Load binary ROI')
        load_roi_action.triggered.connect(self.show_roi_load_dialog)

        #File --> Load Overlay
        load_ovreg_action = QtGui.QAction(QtGui.QIcon(self.local_file_path + '/icons/edit.svg'), '&Load Overlay', self)
        load_ovreg_action.setStatusTip('Load color overlay')
        load_ovreg_action.triggered.connect(self.show_ovreg_load_dialog)

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
        overlayMenu = menubar.addMenu('&Analysis')
        widget_menu = menubar.addMenu('&Widgets')
        help_menu = menubar.addMenu('&Help')

        file_menu.addAction(load_action)
        file_menu.addAction(load_roi_action)
        file_menu.addAction(load_ovreg_action)
        file_menu.addAction(exit_action)

        widget_menu.addAction(se_action)

        help_menu.addAction(help_action)

        #Toolbar
        self.toolbar = self.addToolBar('Load Image')
        self.toolbar.addAction(load_action)
        self.toolbar.addAction(load_roi_action)
        self.toolbar.addAction(load_ovreg_action)

        # extra info displayed in the status bar
        self.statusBar()

    def show_image_load_dialog(self):
        """
        Dialog for loading a file
        """
        fname, _ = QtGui.QFileDialog.getOpenFileName(self, 'Open file', self.default_directory)
        self.default_directory = self.get_dir(fname)

        #check if file is returned
        if fname != '':
            self.mw1.ivm.load_image(fname)
            self.mw1.ivl1.load_image()
            self.mw1.update_slider_range()
        else:
            print('Warning: No file selected')

    def show_roi_load_dialog(self):
        """
        Dialog for loading a file
        """
        fname, _ = QtGui.QFileDialog.getOpenFileName(self, 'Open file', self.default_directory)
        self.default_directory = self.get_dir(fname)

        #check if file is returned
        if fname != '':
            self.mw1.ivm.load_roi(fname)
            self.mw1.ivl1.load_roi()
        else:
            print('Warning: No file selected')

    def show_ovreg_load_dialog(self):
        """
        Dialog for loading a file
        """
        fname, _ = QtGui.QFileDialog.getOpenFileName(self, 'Open file', self.default_directory)
        self.default_directory = self.get_dir(fname)

        #check if file is returned
        if fname != '':
            self.mw1.ivm.load_ovreg(fname)
            self.mw1.ivl1.load_ovreg()
        else:
            print('Warning: No file selected')

    @staticmethod
    def get_dir(str1):
        ind1 = str1.rfind('/')
        dir1 = str1[:ind1]
        return dir1


#~ Main application
def main():
    """
    Run the application
    """
    app = QtGui.QApplication(sys.argv)
    ex = MainWin1()
    sys.exit(app.exec_())


if __name__ == '__main__':
    main()




