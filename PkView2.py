#!/usr/bin/env python

"""
Benjamin Irving

"""

from __future__ import division, unicode_literals, absolute_import, print_function

#import matplotlib
#matplotlib.use('Qt4Agg')
#matplotlib.rcParams['backend.qt4'] = 'PySide'

import sys
import os
from PySide import QtCore, QtGui
import argparse
import pyqtgraph as pg
import pyqtgraph.console
import numpy as np

# My libs
from libs.ImageView import ImageViewColorOverlay
from libs.AnalysisWidgets import SECurve, ColorOverlay1
from libs.ClusteringWidgets import CurveClusteringWidget
from libs.PharmaWidgets import PharmaWidget, PharmaView
from libs.ExperimentalWidgets import ImageExportWidget
from analysis.volume_management import ImageVolumeManagement
from analysis.overlay_analysis import OverlayAnalyis

"""
class DragAction(QtGui.QAction):

    def __init__(self, icon, text, parent):
        super(DragAction, self).__init__(icon, text, parent)

        self.setAcceptDrops(True)

    def dragEnterEvent(self, e):

        if e.mimData().hasFormat('text/plain'):
            e.accept()
        else:
            e.ignore()

    def dropEvent(self, e):

        #TODO currently just testing for the main image
        self.mw1.ivm.load_image(e)
        self.mw1.ivl1.load_image()
        self.mw1.update_slider_range()
"""


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

    def __init__(self, local_file_path):
        super(MainWidge1, self).__init__()

        self.local_file_path = local_file_path

        # get the default color
        color1 = self.palette().color(QtGui.QPalette.Background)
        colorvec = [color1.red(), color1.green(), color1.blue()]
        # set the default color for pg
        pg.setConfigOption('background', [242, 241, 240])
        pg.setConfigOption('foreground', 'k')

        # Loading data management object
        self.ivm = ImageVolumeManagement()

        # Loading image analysis
        self.ia = OverlayAnalyis()
        self.ia.add_image_management(self.ivm)

        #loading ImageView
        self.ivl1 = ImageViewColorOverlay()
        self.ivl1.add_image_management(self.ivm)

        # Loading widgets
        self.sw1 = SECurve(self.local_file_path)

        #Pharmaview is not initialised by default
        self.sw5 = None

        # Color overlay widget
        self.sw2 = ColorOverlay1()
        self.sw2.add_analysis(self.ia)
        self.sw2.add_image_management(self.ivm)

        # Pharmacokinetic modelling widget
        self.sw3 = PharmaWidget()
        self.sw3.add_image_management(self.ivm)

        # Gif creation widget
        self.sw4 = ImageExportWidget()
        self.sw4.add_image_management(self.ivm)

        # Clustering widget
        self.sw_cc = CurveClusteringWidget()
        self.sw_cc.add_image_management(self.ivm)

        # Connect widgets
        #Connect colormap choice, alpha
        self.sw2.sig_choose_cmap.connect(self.ivl1.set_colormap)
        self.sw2.sig_set_alpha.connect(self.ivl1.set_overlay_alpha)

        #Connecting toggle buttons
        self.sw2.cb1.stateChanged.connect(self.ivl1.toggle_ovreg_view)
        self.sw2.cb2.stateChanged.connect(self.ivl1.toggle_roi_lim)

        self.sw2.sig_emit_reset.connect(self.ivl1.update_overlay)

        self.sw3.sig_emit_reset.connect(self.ivl1.update_overlay)

        #Connect image export widget
        self.sw4.sig_set_temp.connect(self.ivl1.set_temporal_position)
        self.sw4.sig_cap_image.connect(self.ivl1.capture_view_as_image)

        #Connect reset from clustering widget
        self.sw_cc.sig_emit_reset.connect(self.ivl1.update_overlay)


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
        cb1.stateChanged.connect(self.ivl1.toggle_roi_view)
        #cb1.toggle()
        cb2 = QtGui.QCheckBox('Show ROI contour', self)
        cb2.toggle()
        cb2.stateChanged.connect(self.ivl1.toggle_roi_contour)
        cb3 = QtGui.QCheckBox('Use voxel size scaling', self)
        cb3.toggle()
        cb3.stateChanged.connect(self.ivl1.toggle_dimscale)

        # Tabbed Widget
        self.qtab1 = QtGui.QTabWidget()
        self.qtab1.setTabsClosable(True)
        self.qtab1.setMovable(True)
        #Widgets
        self.qtab1.addTab(self.sw1, QtGui.QIcon(self.local_file_path + '/icons/voxel.png'), "Voxel analysis")
        self.qtab1.addTab(self.sw2, QtGui.QIcon(self.local_file_path + '/icons/edit.png'), "Overlay options")
        #self.qtab1.addTab(self.sw3, "Pharmacokinetics")
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
        # Group box buttons
        gBox = QtGui.QGroupBox("Image and ROI options")
        gBoxlay = QtGui.QVBoxLayout()
        gBoxlay.addWidget(cb1)
        gBoxlay.addWidget(cb2)
        gBoxlay.addWidget(cb3)
        gBoxlay.addStretch(1)
        gBox.setLayout(gBoxlay)
        gBox.setStyleSheet("QGroupBox{border:2px solid gray;border-radius:5px;margin-top: 1ex;} "
                           "QGroupBox::title{subcontrol-origin: margin;subcontrol-position:top center;padding:0 3px;}")

        # Group box: sliders
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
        grid_box = QGroupBoxClick()
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

        self.ivl1.sig_mouse_scroll.connect(self.slider_scroll_mouse)

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

    @QtCore.Slot(bool)
    def slider_scroll_mouse(self, value):
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
        index = self.qtab1.addTab(self.sw1, QtGui.QIcon(self.local_file_path + '/icons/voxel.png'), "Voxel analysis")
        print(index)
        self.qtab1.setCurrentIndex(index)

    # Connect widget
    def show_ic(self):
        index = self.qtab1.addTab(self.sw4, "Image Export")
        print(index)
        self.qtab1.setCurrentIndex(index)

    def show_pk(self):
        index = self.qtab1.addTab(self.sw3, "Pharmacokinetics")
        self.qtab1.setCurrentIndex(index)

    def show_cc(self):
        index = self.qtab1.addTab(self.sw_cc, QtGui.QIcon(self.local_file_path + '/icons/clustering.png'),
                                  "CurveClustering", )
        self.qtab1.setCurrentIndex(index)

    def show_pw(self):

        # Initialise if it is not already initialised
        if self.sw5 is None:
            self.sw5 = PharmaView()
            self.sw5.add_image_management(self.ivm)
            self.ivl1.sig_mouse.connect(self.sw5.sig_mouse)

        index = self.qtab1.addTab(self.sw5, "PharmaViewCompare")
        print(index)
        self.qtab1.setCurrentIndex(index)


class MainWin1(QtGui.QMainWindow):
    """
    Overall window framework
    Only purpose is to put the menu, menu bar etc decorations around the main window
    Also initialises the open file menus
    """
    def __init__(self, image_dir_in=None, roi_dir_in=None, overlay_dir_in=None):
        super(MainWin1, self).__init__()

        # Patch for if file is frozen
        if hasattr(sys, 'frozen'):
            # if frozen
            self.local_file_path = os.path.dirname(sys.executable)
        else:
            self.local_file_path = os.path.dirname(__file__)

        if self.local_file_path == "":
            print("Reverting to current directory as base")
            self.local_file_path = os.getcwd()

        #Load the main widget
        self.mw1 = MainWidge1(self.local_file_path)

        self.toolbar = None
        self.default_directory ='/home'

        # Directories for the three main files
        self.image_dir_in = image_dir_in
        self.roi_dir_in = roi_dir_in
        self.overlay_dir_in = overlay_dir_in



        #initialise the whole UI
        self.init_ui()

        #autoload any files that have been passed from the command line
        self.auto_load_files()

    def init_ui(self):
        self.setGeometry(100, 100, 1000, 500)
        self.setCentralWidget(self.mw1)
        self.setWindowTitle("PkViewer")
        self.setWindowIcon(QtGui.QIcon(self.local_file_path + '/icons/main_icon.png'))

        self.menu_ui()
        self.show()

    def menu_ui(self):

        #File --> Load Image
        load_action = QtGui.QAction(QtGui.QIcon(self.local_file_path + '/icons/picture.png'), '&Load Image Volume', self)
        load_action.setShortcut('Ctrl+L')
        load_action.setStatusTip('Load a 3d or 4d dceMRI image')
        load_action.triggered.connect(self.show_image_load_dialog)

        #File --> Load ROI
        load_roi_action = QtGui.QAction(QtGui.QIcon(self.local_file_path + '/icons/pencil.png'), '&Load ROI', self)
        load_roi_action.setStatusTip('Load binary ROI')
        load_roi_action.triggered.connect(self.show_roi_load_dialog)

        #File --> Load Overlay
        load_ovreg_action = QtGui.QAction(QtGui.QIcon(self.local_file_path + '/icons/edit.png'), '&Load Overlay', self)
        load_ovreg_action.setStatusTip('Load overlay')
        load_ovreg_action.triggered.connect(self.show_ovreg_load_dialog)

        #File --> Load Overlay Select
        load_ovregsel_action = QtGui.QAction(QtGui.QIcon(self.local_file_path + '/icons/edit.png'),
                                             '&Load Overlay Select', self)
        load_ovregsel_action.setStatusTip('Load specific type of overlay')
        load_ovregsel_action.triggered.connect(self.show_ovregsel_load_dialog)

        #File --> Settings
        #TODO

        #File --> Exit
        exit_action = QtGui.QAction('&Exit', self)
        exit_action.setShortcut('Ctrl+Q')
        exit_action.setStatusTip('Exit Application')
        exit_action.triggered.connect(self.close)

        # Widgets --> SE curve
        se_action = QtGui.QAction(QtGui.QIcon(self.local_file_path + '/icons/voxel.png'), '&SEcuve', self)
        se_action.setStatusTip('Plot SE of a voxel')
        se_action.triggered.connect(self.mw1.show_se)

        # Widgets --> Image export
        ic_action = QtGui.QAction('&ImageExport', self)
        ic_action.setStatusTip('Export images from the GUI')
        ic_action.triggered.connect(self.mw1.show_ic)

        #Widgets --> Pharmacokinetics
        pk_action = QtGui.QAction('&Pharmacokinetics', self)
        pk_action.setStatusTip('Run pharmacokinetic analysis')
        pk_action.triggered.connect(self.mw1.show_pk)

        # Widgets --> PharmaView
        pw_action = QtGui.QAction('&PharmCurveView', self)
        pw_action.setStatusTip('Compare the true signal enhancement to the predicted model enhancement')
        pw_action.triggered.connect(self.mw1.show_pw)

        # Widgets --> CurveClustering
        cc_action = QtGui.QAction(QtGui.QIcon(self.local_file_path + '/icons/clustering.png'), '&CurveClustering', self)
        cc_action.setStatusTip('Cluster curves in a ROI of interest')
        cc_action.triggered.connect(self.mw1.show_cc)

        #Help -- > Online help
        help_action = QtGui.QAction('&Online Help', self)
        help_action.setStatusTip('See online help file')
        help_action.triggered.connect(self.click_link)

        # Advanced --> Python Console
        console_action = QtGui.QAction('&Console', self)
        console_action.setStatusTip('Run a console for advanced interaction')
        console_action.triggered.connect(self.show_console)

        menubar = self.menuBar()
        file_menu = menubar.addMenu('&File')
        widget_menu = menubar.addMenu('&Widgets')
        advanced_menu = menubar.addMenu('&Advanced')
        help_menu = menubar.addMenu('&Help')

        file_menu.addAction(load_action)
        file_menu.addAction(load_roi_action)
        file_menu.addAction(load_ovreg_action)
        file_menu.addAction(load_ovregsel_action)
        file_menu.addAction(exit_action)

        widget_menu.addAction(se_action)
        widget_menu.addAction(ic_action)
        widget_menu.addAction(pk_action)
        widget_menu.addAction(pw_action)
        widget_menu.addAction(cc_action)

        help_menu.addAction(help_action)

        advanced_menu.addAction(console_action)

        #Toolbar
        self.toolbar = self.addToolBar('Load Image')
        self.toolbar.addAction(load_action)
        self.toolbar.addAction(load_roi_action)
        self.toolbar.addAction(load_ovreg_action)

        # extra info displayed in the status bar
        self.statusBar()

    def click_link(self):
        QtGui.QDesktopServices.openUrl(QtCore.QUrl("https://github.com/benjaminirving/PkView_help_files", QtCore.QUrl.TolerantMode))

    def show_console(self):
        """

        Creates a pop up console that allows interaction with the GUI and data
        Uses:
        pyqtgraph.console

        """

        # Places that the console has access to
        namespace = {'pg': pg, 'np': np, 'mw1': self.mw1, 'ivm': self.mw1.ivm, 'self': self}
        text = (
            """
            ****** PkView Console ******

            This is a python console that allows interaction with the GUI data and running of scripts.

            Libraries already imported
            np: Numpy

            Access to data
            mw1: Access to the main window
            ivm: Access to all the stored image data

            """)
        self.con1 = pg.console.ConsoleWidget(namespace=namespace, text=text)
        self.con1.setWindowTitle('pyqtgraph example: ConsoleWidget')
        self.con1.setGeometry(QtCore.QRect(100, 100, 600, 600))
        self.con1.show()

    def show_image_load_dialog(self, fname=None):
        """
        Dialog for loading a file
        @fname: allows a file name to be passed in automatically
        """


        if fname is None:
            # Show file select widget
            fname, _ = QtGui.QFileDialog.getOpenFileName(self, 'Open file', self.default_directory)

        # check if file is returned
        if fname != '':

            if self.mw1.ivm.image_file1 is not None:
                # Checking if data already exists
                msgBox = QtGui.QMessageBox()
                msgBox.setText("A volume has already been loaded")
                msgBox.setInformativeText("Do you want to clear all data and load this new volume?")
                msgBox.setStandardButtons(QtGui.QMessageBox.Ok | QtGui.QMessageBox.Cancel)
                msgBox.setDefaultButton(QtGui.QMessageBox.Ok)

                ret = msgBox.exec_()

                if ret == QtGui.QMessageBox.Ok:
                    print("Clearing data")
                    self.mw1.ivm.init()
                else:
                    return

            self.default_directory = self.get_dir(fname)
            self.mw1.ivm.load_image(fname)
            self.mw1.ivl1.load_image()
            self.mw1.update_slider_range()
        else:
            print('Warning: No file selected')

    def show_roi_load_dialog(self, fname=None):
        """
        Dialog for loading a file
        @fname: allows a file name to be passed in automatically
        """
        if fname is None:
            # Show file select widget
            fname, _ = QtGui.QFileDialog.getOpenFileName(self, 'Open file', self.default_directory)

        #check if file is returned
        if fname != '':
            self.default_directory = self.get_dir(fname)
            self.mw1.ivm.load_roi(fname)
            self.mw1.ivl1.load_roi()
        else:
            print('Warning: No file selected')

    def show_ovreg_load_dialog(self, fname=None):
        """
        Dialog for loading a file
        @fname: allows a file name to be passed in automatically
        """
        if fname is None:
            #Show file select widget
            fname, _ = QtGui.QFileDialog.getOpenFileName(self, 'Open file', self.default_directory)

        #check if file is returned
        if fname != '':
            self.default_directory = self.get_dir(fname)
            self.mw1.ivm.load_ovreg(fname)
            self.mw1.ivl1.load_ovreg()
        else:
            print('Warning: No file selected')

    def show_ovregsel_load_dialog(self, fname=None, ftype=None):
        """
        Dialog for loading an overlay and specifying the type of overlay
        @fname: allows a file name to be passed in automatically
        @ftype: allows overlay type to be passed automatically
        """
        if fname is None:
            # Show file select widget
            fname, _ = QtGui.QFileDialog.getOpenFileName(self, 'Open file', self.default_directory)

        if ftype is None:
            ftype, ok = QtGui.QInputDialog.getItem(self, 'Overlay type', 'Type of overlay loaded:',
                                                   ['T10', 'Ktrans', 'kep', 've', 'vp', 'model_curves'])

        # check if file is returned
        if fname != '':
            self.default_directory = self.get_dir(fname)
            self.mw1.ivm.load_ovreg(fname, ftype)
            if ftype != 'estimated':
                self.mw1.ivl1.load_ovreg()
        else:
            print('Warning: No file selected')

    def auto_load_files(self):
        """
        Check to see if any input directories have been passed for auto loading and loads those images
        """

        if self.image_dir_in is not None:
            self.show_image_load_dialog(fname=self.image_dir_in)
        if self.roi_dir_in is not None:
            self.show_roi_load_dialog(fname=self.roi_dir_in)
        if self.overlay_dir_in is not None:
            self.show_ovreg_load_dialog(fname=self.overlay_dir_in)

    @staticmethod
    def get_dir(str1):
        ind1 = str1.rfind('/')
        dir1 = str1[:ind1]
        return dir1


if __name__ == '__main__':
    """
    Run the application
    """

    # Parse input arguments to pass info to GUI
    parser = argparse.ArgumentParser()
    parser.add_argument('--image', help='DCE-MRI nifti file location', default=None, type=str)
    parser.add_argument('--roi', help='ROI nifti file location', default=None, type=str)
    parser.add_argument('--overlay', help='Overlay nifti file location', default=None, type=str)
    args = parser.parse_args()


    app = QtGui.QApplication(sys.argv)
    ex = MainWin1(args.image, args.roi, args.overlay)
    sys.exit(app.exec_())




