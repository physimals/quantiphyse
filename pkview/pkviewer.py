"""

Author: Benjamin Irving (benjamin.irv@gmail.com)
Copyright (c) 2013-2015 University of Oxford, Benjamin Irving

"""

from __future__ import division, unicode_literals, print_function, absolute_import

import sys
import os
import platform
import argparse

from PySide import QtCore, QtGui
import pyqtgraph as pg
import pyqtgraph.console
import numpy as np

import warnings

# required to use resources in theme. Check if 2 or 3.
if (sys.version_info > (3, 0)):
    from pkview.resources import resource_py2
else:
    from pkview.resources import resource_py3


# My widgets
from pkview.ImageView import ImageViewColorOverlay
from .widgets.AnalysisWidgets import SECurve, ColorOverlay1
from .widgets.ClusteringWidgets import CurveClusteringWidget
from .widgets.OvClusteringWidgets import OvCurveClusteringWidget
from .widgets.PharmaWidgets import PharmaWidget, PharmaView
#from .widgets.FabberWidgets import FabberWidget
#from .widgets.T10Widgets import T10Widget
from .widgets.ExperimentalWidgets import ImageExportWidget
from .widgets.OverviewWidgets import OverviewWidget
from .volumes.volume_management import ImageVolumeManagement
from .analysis.overlay_analysis import OverlayAnalyis
from .QtInherit.FingerTabs import FingerTabBarWidget, FingerTabWidget

op_sys = platform.system()
# OSx specific Changes
if op_sys == 'Darwin':
    from Foundation import NSURL
    QtGui.QApplication.setGraphicsSystem('native')

# Linux specific changes
# None currently

# Windows specific changes
from .utils.cmd_pkmodel import pkbatch
if op_sys != 'Windows':
    from .utils.cmd_t10 import t10_preclinical, t10


def get_dir(str1):
    """
    Parse a file name to extract just the directory
    :param str1:
    :return:
    """
    ind1 = str1.rfind('/')
    dir1 = str1[:ind1]
    return dir1


class DragOptions(QtGui.QDialog):
    """
    Interface for dealing with drag and drop
    """

    def __init__(self, parent=None):
        super(DragOptions, self).__init__(parent)
        self.setWindowTitle("Image Type")

        self.button1 = QtGui.QPushButton("DCE")
        self.button2 = QtGui.QPushButton("ROI")
        self.button3 = QtGui.QPushButton("OVERLAY")

        layout = QtGui.QHBoxLayout()
        layout.addWidget(self.button1)
        layout.addWidget(self.button2)
        layout.addWidget(self.button3)

        self.setLayout(layout)

        self.but = 0

        self.button1.clicked.connect(self.b1)
        self.button2.clicked.connect(self.b2)
        self.button3.clicked.connect(self.b3)

    def b1(self):
        self.but = "DCE"
        self.accept()

    def b2(self):
        self.but = "ROI"
        self.accept()

    def b3(self):
        self.but = "OVERLAY"
        self.accept()

    @staticmethod
    def getImageChoice(parent=None):

        dialog = DragOptions(parent)
        result = dialog.exec_()
        return dialog.but, result == QtGui.QDialog.Accepted


class MainWindowWidget(QtGui.QWidget):

    """
    Main widget where most of the control should happen

    """

    def __init__(self, local_file_path):
        super(MainWindowWidget, self).__init__()

        self.local_file_path = local_file_path

        # Loading data management object
        self.ivm = ImageVolumeManagement()

        # Loading image analysis

        self.ia = OverlayAnalyis()
        self.ia.add_image_management(self.ivm)

        # loading ImageView
        self.ivl1 = ImageViewColorOverlay()
        self.ivl1.add_image_management(self.ivm)
        self.ivl1.sig_mouse_scroll.connect(self.slider_scroll_mouse)

        # ~~~~~~~~~~~~ Widgets ~~~~~~~~~~~~~~~~~~~~
        self.wid = {}

        # Signal Enhancement
        self.wid["SigEn"] = [SECurve(self.local_file_path), '/icons/voxel.svg', 'Voxel analysis']
        self.wid["SigEn"][0].add_image_management(self.ivm)
        # Signals to connect widget
        self.wid["SigEn"][0].sig_add_pnt.connect(self.ivl1.add_arrow_current_pos)
        self.wid["SigEn"][0].sig_clear_pnt.connect(self.ivl1.remove_all_arrows)

        # Pharmaview is not initialised by default
        self.wid["PView"] = [None, 'a', 'b']

        # Color overlay widget
        self.wid["ColOv"] = [ColorOverlay1(self.local_file_path), 'a', 'b']
        self.wid["ColOv"][0].add_analysis(self.ia)
        self.wid["ColOv"][0].add_image_management(self.ivm)

        # Pharmacokinetic modelling widget
        self.wid["PAna"] = [PharmaWidget(), 'a', 'b']
        self.wid["PAna"][0].add_image_management(self.ivm)

        # Fabber modelling widget
        #self.wid["Fab"] = [FabberWidget(), 'a', 'b']
        #self.wid["Fab"][0].add_image_management(self.ivm)

        # T10 widget
        #self.wid["T10"] = [T10Widget(), 'a', 'b']
        #self.wid["T10"][0].add_image_management(self.ivm)

        # Gif creation widget
        self.wid["ImExp"] = [ImageExportWidget(), 'a', 'b']
        self.wid["ImExp"][0].add_image_management(self.ivm)

        # Clustering widget
        self.wid["Clus"] = [CurveClusteringWidget(self.local_file_path), 'a', 'b']
        self.wid["Clus"][0].add_image_management(self.ivm)

        # Clustering widget
        self.wid["ClusOv"] = [OvCurveClusteringWidget(self.local_file_path), 'a', 'b']
        self.wid["ClusOv"][0].add_image_management(self.ivm)

        self.wid["Overview"] = [OverviewWidget(self.local_file_path), 'a', 'b']
        self.wid["Overview"][0].add_image_management(self.ivm)

        # Random Walker
        # self.sw_rw = None

        # Connect widgets
        # Connect colormap choice, alpha and colormap range
        self.wid["ColOv"][0].sig_emit_reset.connect(self.ivl1.update_overlay)

        self.wid["PAna"][0].sig_emit_reset.connect(self.ivl1.update_overlay)

        #self.wid["Fab"][0].sig_emit_reset.connect(self.ivl1.update_overlay)

        self.wid["Overview"][0].l1.sig_emit_reset.connect(self.ivl1.update_overlay)
        self.wid["Overview"][0].l2.sig_emit_reset.connect(self.ivl1.update_roi)

        # Connect image export widget
        self.wid["ImExp"][0].sig_set_temp.connect(self.ivl1.set_temporal_position)
        self.wid["ImExp"][0].sig_cap_image.connect(self.ivl1.capture_view_as_image)

        # Connect reset from clustering widget
        self.wid["Clus"][0].sig_emit_reset.connect(self.ivl1.update_roi)
        self.wid["Clus"][0].add_image_management(self.ivm)

        self.initTabs()

        # Connecting widget signals
        # 1) Plotting data on mouse image click
        self.ivl1.sig_mouse_click.connect(self.wid["SigEn"][0].sig_mouse)

        # InitUI
        # Sliders
        self.sld1 = QtGui.QSlider(QtCore.Qt.Horizontal, self)
        self.sld1.setFocusPolicy(QtCore.Qt.NoFocus)
        self.sld2 = QtGui.QSlider(QtCore.Qt.Horizontal, self)
        self.sld2.setFocusPolicy(QtCore.Qt.NoFocus)
        self.sld3 = QtGui.QSlider(QtCore.Qt.Horizontal, self)
        self.sld3.setFocusPolicy(QtCore.Qt.NoFocus)
        self.sld4 = QtGui.QSlider(QtCore.Qt.Horizontal, self)
        self.sld4.setFocusPolicy(QtCore.Qt.NoFocus)
        # self.update_slider_range()

        # connect sliders to ivl1
        self.sld1.valueChanged[int].connect(self.ivl1.slider_connect1)
        self.sld2.valueChanged[int].connect(self.ivl1.slider_connect2)
        self.sld3.valueChanged[int].connect(self.ivl1.slider_connect3)
        self.sld4.valueChanged[int].connect(self.ivl1.slider_connect4)

        # CheckBox
        cb1 = QtGui.QCheckBox('Show ROI', self)
        cb1.stateChanged.connect(self.ivl1.toggle_roi_view)
        cb1.toggle()
        cb2 = QtGui.QCheckBox('Show ROI contour', self)
        cb2.stateChanged.connect(self.ivl1.toggle_roi_contour)
        cb3 = QtGui.QCheckBox('Use voxel size scaling', self)
        cb3.stateChanged.connect(self.ivl1.toggle_dimscale)

        # Position Label and connect to slider
        lab_p1 = QtGui.QLabel('0')
        self.sld1.valueChanged[int].connect(lab_p1.setNum)
        lab_p2 = QtGui.QLabel('0')
        self.sld2.valueChanged[int].connect(lab_p2.setNum)
        lab_p3 = QtGui.QLabel('0')
        self.sld3.valueChanged[int].connect(lab_p3.setNum)
        lab_p4 = QtGui.QLabel('0')
        self.sld4.valueChanged[int].connect(lab_p4.setNum)

        # Layout
        # Group box buttons
        gBox = QtGui.QGroupBox("ROI")
        gBoxlay = QtGui.QVBoxLayout()
        gBoxlay.addWidget(cb1)
        gBoxlay.addWidget(cb2)
        gBoxlay.addStretch(1)
        gBox.setLayout(gBoxlay)

        # Group box: sliders
        gBox2 = QtGui.QGroupBox("Navigation")
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
        gBoxlay2.addWidget(cb3, 4, 0, 1, 2)
        gBoxlay2.setColumnStretch(0, 0)
        gBoxlay2.setColumnStretch(1, 2)
        gBox2.setLayout(gBoxlay2)

        gBox3 = QtGui.QGroupBox("Overlay")
        grid = QtGui.QGridLayout()
        grid.addWidget(QtGui.QLabel("View"), 0, 0)
        self.ov_view_combo = QtGui.QComboBox()
        self.ov_view_combo.addItem("All")
        self.ov_view_combo.addItem("Only in ROI")
        self.ov_view_combo.addItem("None")
        self.ov_view_combo.currentIndexChanged.connect(self.ov_view_changed)
        grid.addWidget(self.ov_view_combo, 0, 1)
        grid.addWidget(QtGui.QLabel("Transparency"), 1, 0)
        sld1 = QtGui.QSlider(QtCore.Qt.Horizontal, self)
        sld1.setFocusPolicy(QtCore.Qt.NoFocus)
        sld1.setRange(0, 255)
        sld1.setValue(255)
        sld1.valueChanged.connect(self.ivl1.set_overlay_alpha)
        grid.addWidget(sld1, 1, 1)
        grid.setRowStretch(2, 1)
        gBox3.setLayout(grid)

        # All buttons layout
        gBox_all = QtGui.QWidget()
        gBoxlay_all = QtGui.QHBoxLayout()
        gBoxlay_all.addWidget(gBox2)
        gBoxlay_all.addWidget(gBox)
        gBoxlay_all.addWidget(gBox3)
        #gBoxlay_all.setStretch(0, 2)
        #gBoxlay_all.setStretch(2, 1)
        gBox_all.setLayout(gBoxlay_all)

        # Viewing window layout + buttons
        # Add a horizontal splitter between image viewer and buttons below
        grid_box = QtGui.QGroupBox()
        # grid_box.sig_click.connect(self.mpe)
        grid = QtGui.QVBoxLayout()
        splitter2 = QtGui.QSplitter(QtCore.Qt.Vertical)
        splitter2.addWidget(self.ivl1)
        splitter2.addWidget(gBox_all)
        splitter2.setStretchFactor(0, 5)
        splitter2.setStretchFactor(1, 1)
        grid.addWidget(splitter2)
        grid_box.setLayout(grid)

        # Add a vertical splitter between main view and tabs
        hbox = QtGui.QHBoxLayout(self)
        splitter1 = QtGui.QSplitter(QtCore.Qt.Horizontal)
        splitter1.addWidget(grid_box)
        splitter1.addWidget(self.qtab1)
        splitter1.setStretchFactor(0, 4)
        splitter1.setStretchFactor(1, 1)
        hbox.addWidget(splitter1)

        # horizontal widgets
        self.setLayout(hbox)

    def ov_view_changed(self, idx):
        print(idx)
        view = idx in (0, 1)
        roiOnly = (idx == 1)
        self.ivl1.set_overlay_view(view, roiOnly)

    def initTabs(self):

        """
        Initialise the tab widget

        Returns:

        """

        # Tabbed Widget
        self.qtab1 = QtGui.QTabWidget()
        # add finger tabs
        self.qtab1.setTabBar(FingerTabBarWidget(width=100, height=50))

        self.qtab1.setTabsClosable(False)
        self.qtab1.setMovable(False)
        # Set the icon size of the tabs
        self.qtab1.setIconSize(QtCore.QSize(16, 16))

        # Widgets added to tabs on the right hand side
        self.qtab1.addTab(self.wid["Overview"][0], "Volumes")
        self.qtab1.addTab(self.wid["SigEn"][0], QtGui.QIcon(self.local_file_path + '/icons/voxel.svg'), "Voxel\n analysis")
        self.qtab1.addTab(self.wid["ColOv"][0], QtGui.QIcon(self.local_file_path + '/icons/edit.svg'), "Overlay\n statistics")
        self.qtab1.addTab(self.wid["Clus"][0], QtGui.QIcon(self.local_file_path + '/icons/clustering.svg'), "Curve\n cluster")
        self.qtab1.addTab(self.wid["ClusOv"][0], QtGui.QIcon(self.local_file_path + '/icons/clustering.svg'), "Overlay\n cluster")
        #self.qtab1.addTab(self.wid["T10"][0], QtGui.QIcon(self.local_file_path + '/icons/pk.svg'), "T10")

        # signal
        # self.qtab1.tabCloseRequested.connect(self.qtab1.removeTab)
        self.qtab1.setTabPosition(QtGui.QTabWidget.West)

    # update slider range
    def update_slider_range(self):
        # set slider range
        self.sld1.setRange(0, self.ivm.img_dims[2]-1)
        self.sld2.setRange(0, self.ivm.img_dims[1]-1)
        self.sld3.setRange(0, self.ivm.img_dims[0]-1)

        if len(self.ivm.img_dims) == 4:
            self.sld4.setRange(0, self.ivm.img_dims[3]-1)
        else:
            self.sld4.setRange(0, 0)

    @QtCore.Slot(bool)
    def slider_scroll_mouse(self, value):
        # update slider positions
        self.sld1.setValue(self.ivm.cim_pos[2])
        self.sld2.setValue(self.ivm.cim_pos[1])
        self.sld3.setValue(self.ivm.cim_pos[0])

    # Connect to a widget
    def show_widget(self, wname):
        index = self.qtab1.addTab(self.wid[wname][0], QtGui.QIcon(self.local_file_path + self.wid[wname][1]), self.wid[wname][2])
        self.qtab1.setCurrentIndex(index)

    # Connect widget
    def show_se(self):
        index = self.qtab1.addTab(self.wid["SigEn"][0], QtGui.QIcon(self.local_file_path + '/icons/voxel.svg'), "Voxel analysis")
        self.qtab1.setCurrentIndex(index)

    # Connect widget
    def show_ic(self):
        index = self.qtab1.addTab(self.wid["ImExp"][0], "Image Export")
        self.qtab1.setCurrentIndex(index)

    def show_pk(self):
        index = self.qtab1.addTab(self.wid["PAna"][0], QtGui.QIcon(self.local_file_path + '/icons/pk.svg'), "Pk")
        self.qtab1.setCurrentIndex(index)
    
    #def show_fab(self):
    #    index = self.qtab1.addTab(self.wid["Fab"][0], QtGui.QIcon(self.local_file_path + '/icons/pk.svg'), "Fabber")
    #    self.qtab1.setCurrentIndex(index)

    #def show_t10(self):
    #    index = self.qtab1.addTab(self.wid["T10"][0], QtGui.QIcon(self.local_file_path + '/icons/pk.svg'), "T10")
    #    self.qtab1.setCurrentIndex(index)

    def show_cc(self):
        index = self.qtab1.addTab(self.wid["Clus"][0], QtGui.QIcon(self.local_file_path + '/icons/clustering.svg'),
                                  "Curve\n Cluster", )
        self.qtab1.setCurrentIndex(index)

    def show_pw(self):

        # Initialise if it is not already initialised
        if self.wid["PView"][0] is None:
            self.wid["PView"][0] = PharmaView()
            self.wid["PView"][0].add_image_management(self.ivm)
            self.ivl1.sig_mouse_click.connect(self.wid["PView"][0].sig_mouse)

        index = self.qtab1.addTab(self.wid["PView"][0], "Pharma\n View")
        print(index)
        self.qtab1.setCurrentIndex(index)


class WindowAndDecorators(QtGui.QMainWindow):

    """
    Overall window framework

    Steps:
    1) Loads the main widget (mw1) - this is where all the interesting stuff happens
    2) Accepts any input directories that are passed from the terminal
    3) Initialises the GUI, menus, and toolbar
    3) Loads any files that are passed from the terminal

    """

    #File dropped
    sig_dropped = QtCore.Signal(str)

    def __init__(self, image_dir_in=None, roi_dir_in=None, overlay_dir_in=None, overlay_type_in=None):

        super(WindowAndDecorators, self).__init__()

        self.setAcceptDrops(True)

        # Patch for if file is frozen (packaged apps)
        if hasattr(sys, 'frozen'):
            # if frozen
            print(sys.frozen)
            if sys.frozen == 'macosx_app':
                self.local_file_path = os.getcwd() + '/pkview'
            else:
                self.local_file_path = os.path.dirname(sys.executable)

        # Running from a script
        else:
            self.local_file_path = os.path.dirname(__file__)

        # Use local working directory otherwise
        if self.local_file_path == "":
            print("Reverting to current directory as base")
            self.local_file_path = os.getcwd()

        # Print directory
        print("Local directory: ", self.local_file_path)

        # Load style sheet
        stFile = self.local_file_path + "/resources/darkorange.stylesheet"
        with open(stFile, "r") as fs:
            self.setStyleSheet(fs.read())

        # Load the main widget
        self.mw1 = MainWindowWidget(self.local_file_path)

        self.toolbar = None
        self.default_directory ='/home'

        # Directories for the three main files
        self.image_dir_in = image_dir_in
        self.roi_dir_in = roi_dir_in
        self.overlay_dir_in = overlay_dir_in
        self.overlay_type_in = overlay_type_in

        # initialise the whole UI
        self.init_ui()

        # autoload any files that have been passed from the command line
        self.auto_load_files()

        self.sig_dropped.connect(self.drag_drop_dialog)

    def init_ui(self):
        """
        Called during init. Sets the size and title of the overall GUI
        :return:
        """
        self.setGeometry(100, 100, 1000, 500)
        self.setCentralWidget(self.mw1)
        self.setWindowTitle("PkViewer - Benjamin Irving")
        self.setWindowIcon(QtGui.QIcon(self.local_file_path + '/icons/main_icon.png'))

        self.menu_ui()
        self.show()

        # OSx specific enhancments
        self.setUnifiedTitleAndToolBarOnMac(True)

    def menu_ui(self):
        """
        Set up the file menu system and the toolbar at the top
        :return:
        """

        # File --> Load Image
        load_action = QtGui.QAction(QtGui.QIcon(self.local_file_path + '/icons/picture.svg'), '&Load Image Volume', self)
        load_action.setShortcut('Ctrl+L')
        load_action.setStatusTip('Load a 3d or 4d dceMRI image')
        load_action.triggered.connect(self.show_image_load_dialog)

        # File --> Load ROI
        load_roi_action = QtGui.QAction(QtGui.QIcon(self.local_file_path + '/icons/pencil.svg'), '&Load ROI', self)
        load_roi_action.setStatusTip('Load binary ROI')
        load_roi_action.triggered.connect(self.show_roi_load_dialog)

        # File --> Load Overlay
        load_ovreg_action = QtGui.QAction(QtGui.QIcon(self.local_file_path + '/icons/edit.svg'), '&Load Overlay', self)
        load_ovreg_action.setStatusTip('Load overlay')
        load_ovreg_action.triggered.connect(self.show_ovregsel_load_dialog)

        # File --> Save Overlay
        save_ovreg_action = QtGui.QAction('&Save Current Overlay', self)
        save_ovreg_action.setStatusTip('Save Current Overlay as a nifti file')
        save_ovreg_action.triggered.connect(self.show_ovreg_save_dialog)
        save_ovreg_action.setShortcut('Ctrl+S')

        # File --> Exit
        exit_action = QtGui.QAction('&Exit', self)
        exit_action.setShortcut('Ctrl+Q')
        exit_action.setStatusTip('Exit Application')
        exit_action.triggered.connect(self.close)

        # Widgets --> Image export
        ic_action = QtGui.QAction('&ImageExport', self)
        ic_action.setStatusTip('Export images from the GUI')
        ic_action.triggered.connect(self.mw1.show_ic)

        # Widgets --> Pharmacokinetics
        pk_action = QtGui.QAction(QtGui.QIcon(self.local_file_path + '/icons/pk.svg'), '&Pharmacokinetics', self)
        pk_action.setStatusTip('Run pharmacokinetic analysis')
        pk_action.triggered.connect(self.mw1.show_pk)

        # Widgets --> Fabber
        #fab_action = QtGui.QAction(QtGui.QIcon(self.local_file_path + '/icons/pk.svg'), '&Fabber', self)
        #fab_action.setStatusTip('Run fabber model fitting')
        #fab_action.triggered.connect(self.mw1.show_fab)

        # Widgets --> PharmaView
        pw_action = QtGui.QAction('&PharmCurveView', self)
        pw_action.setStatusTip('Compare the true signal enhancement to the predicted model enhancement')
        pw_action.triggered.connect(self.mw1.show_pw)

        # Widgets --> RandomWalker
        # rw_action = QtGui.QAction('&RandomWalker', self)
        # rw_action.setStatusTip('RandomWalker')
        # rw_action.triggered.connect(self.mw1.show_rw)

        # Widgets --> CurveClustering
        # cc_action = QtGui.QAction(QtGui.QIcon(self.local_file_path + '/icons/clustering.svg'), '&CurveClustering', self)
        # cc_action.setStatusTip('Cluster curves in a ROI of interest')
        # cc_action.triggered.connect(self.mw1.show_cc)

        # Wigets --> Create Annotation
        # annot_ovreg_action = QtGui.QAction(QtGui.QIcon(self.local_file_path + '/icons/edit.svg'), '&Enable Annotation', self)
        # annot_ovreg_action.setStatusTip('Enable Annotation of the GUI')
        # annot_ovreg_action.setCheckable(True)
        # annot_ovreg_action.toggled.connect(self.show_annot_load_dialog)

        # Help -- > Online help
        help_action = QtGui.QAction('&Online Help', self)
        help_action.setStatusTip('See online help file')
        help_action.triggered.connect(self.click_link)

        # Advanced --> Python Console
        console_action = QtGui.QAction('&Console', self)
        console_action.setStatusTip('Run a console for advanced interaction')
        console_action.triggered.connect(self.show_console)

        menubar = self.menuBar()
        file_menu = menubar.addMenu('&File')
        widget_menu = menubar.addMenu('&Additional Widgets')
        advanced_menu = menubar.addMenu('&Advanced')
        help_menu = menubar.addMenu('&Help')

        file_menu.addAction(load_action)
        file_menu.addAction(load_roi_action)
        file_menu.addAction(load_ovreg_action)
        # file_menu.addAction(load_ovregsel_action)
        file_menu.addAction(save_ovreg_action)
        file_menu.addAction(exit_action)

        widget_menu.addAction(ic_action)
        widget_menu.addAction(pk_action)
        #widget_menu.addAction(fab_action)
        widget_menu.addAction(pw_action)
        # widget_menu.addAction(rw_action)
        # widget_menu.addAction(annot_ovreg_action)


        help_menu.addAction(help_action)

        advanced_menu.addAction(console_action)

        # Toolbar
        # self.toolbar = self.addToolBar('Load Image')
        # self.setIconSize(QtCore.QSize(20, 20))
        # self.toolbar.addAction(load_action)
        # self.toolbar.addAction(load_roi_action)
        # self.toolbar.addAction(load_ovreg_action)

        # extra info displayed in the status bar
        self.statusBar()

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
                if op_sys == 'Darwin':
                    # OSx specific changes to allow drag and drop
                    filep = str(NSURL.URLWithString_(str(url.toString())).filePathURL().path())
                    fname.append(filep)
                else:
                    fname.append(str(url.toLocalFile()))
                print(fname)
            # Signal that a file has been dropped
            self.sig_dropped.emit(fname[0])

        else:
            e.ignore()

    @QtCore.Slot()
    def click_link(self):
        """
        Provide a clickable link to help files

        :return:
        """
        QtGui.QDesktopServices.openUrl(QtCore.QUrl("https://github.com/benjaminirving/PkView_help_files", QtCore.QUrl.TolerantMode))

    @QtCore.Slot()
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

    # Dialogs

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

            self.default_directory = get_dir(fname)
            self.mw1.ivm.load_image(fname)
            self.mw1.ivl1.load_image()
            self.mw1.update_slider_range()
        else:
            print('Warning: No file selected')

    # def show_annot_load_dialog(self, checked):
    #     """
    #     Annotation dialog
    #     """
    #
    #     if checked:
    #         self.mw1.ivm.set_blank_annotation()
    #         self.mw1.ivl1.load_ovreg()
    #         self.mw1.ivl1.enable_drawing(color1=1)
    #     else:
    #         self.mw1.ivl1.enable_drawing(color1=-1)

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
            self.default_directory = get_dir(fname)
            self.mw1.ivm.load_roi(fname)
            self.mw1.ivl1.load_roi()
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

        # check if file is returned
        if fname != '':

            if ftype is None:
                ftype, ok = QtGui.QInputDialog.getItem(self, 'Overlay type', 'Type of overlay loaded:',
                                                       ['loaded', 'T10', 'Ktrans', 'kep', 've', 'vp', 'model_curves',
                                                        'annotation'])

            self.default_directory = get_dir(fname)
            self.mw1.ivm.load_ovreg(fname, ftype)
            if ftype != 'estimated':
                self.mw1.ivl1.load_ovreg()
        else:
            print('Warning: No file selected')

    def show_ovreg_save_dialog(self):
        """
        Dialog for saving an overlay as a nifti file

        """

        fname, _ = QtGui.QFileDialog.getSaveFileName(self, 'Save file', dir=self.default_directory, filter="*.nii")

        # check if file is returned
        if fname != '':

            # self.default_directory = get_dir(fname)
            self.mw1.ivm.save_ovreg(fname, 'current')
        else:
            print('Warning: No file selected')

    @QtCore.Slot(str)
    def drag_drop_dialog(self, fname):
        """
        Dialog for loading an overlay and specifying the type of overlay
        @fname: allows a file name to be passed in automatically
        """

        ftype, ok = DragOptions.getImageChoice(self)

        if not ok:
            return

        self.default_directory = get_dir(fname)

        # Loading overlays
        if ftype != 'DCE' and ftype != 'ROI':

            ftype2, ok = QtGui.QInputDialog.getItem(self, 'Overlay type', 'Type of overlay loaded:',
                                                    ['loaded', 'T10', 'Ktrans', 'kep', 've', 'vp',
                                                     'model_curves', 'annotation'])
            self.mw1.ivm.load_ovreg(fname, ftype2)
            if ftype != 'estimation':
                self.mw1.ivl1.load_ovreg()

        # Loading main image
        elif ftype == 'DCE':
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

            self.mw1.ivm.load_image(fname)
            self.mw1.ivl1.load_image()
            self.mw1.update_slider_range()

        # Loading ROI
        elif ftype == 'ROI':
            self.mw1.ivm.load_roi(fname)
            self.mw1.ivl1.load_roi()

    def auto_load_files(self):
        """
        Check to see if any input directories have been passed from the terminal for auto loading and loads those images
        """

        if self.image_dir_in is not None:
            self.show_image_load_dialog(fname=self.image_dir_in)
        if self.roi_dir_in is not None:
            self.show_roi_load_dialog(fname=self.roi_dir_in)
        if self.overlay_dir_in is not None:
            self.show_ovregsel_load_dialog(fname=self.overlay_dir_in, ftype=self.overlay_type_in)


def main():

    """
    Parse any input arguments and run the application
    """

    # current_folder = args_in.pop(0)

    # Parse input arguments to pass info to GUI
    parser = argparse.ArgumentParser()
    parser.add_argument('--T10afibatch', help='Run batch T10 processing from a yaml file', default=None, type=str)
    parser.add_argument('--T10batch', help='Run batch T10 processing from a yaml file', default=None, type=str)
    parser.add_argument('--PKbatch', help='Run batch PK processing from a yaml file', default=None, type=str)
    parser.add_argument('--image', help='DCE-MRI nifti file location', default=None, type=str)
    parser.add_argument('--roi', help='ROI nifti file location', default=None, type=str)
    parser.add_argument('--overlay', help='Overlay nifti file location', default=None, type=str)
    parser.add_argument('--overlaytype', help='Type of overlay', default=None, type=str)
    args = parser.parse_args()

    print(pg.systemInfo())

    # Check whether any batch processing arguments have been called

    if (args.PKbatch is None) and (args.T10batch is None) and (args.T10afibatch is None):
        # Initialise main GUI

        # Initialise the PKView application
        app = QtGui.QApplication(sys.argv)
        app.setStyle('plastique')  # windows, motif, cde, plastique, windowsxp, macintosh
        # app.setGraphicsSystem('native')  ## work around a variety of bugs in the native graphics system

        # Pass arguments from the terminal (if any) into the main application
        ex = WindowAndDecorators(args.image, args.roi, args.overlay, args.overlaytype)
        sys.exit(app.exec_())

    elif (args.T10batch is not None):
        # Run T10 batch processing from a yaml file
        if op_sys == 'Windows':
            warnings.warn('Windows is not supported for T10 mapping')

        t10(args.T10batch)

    elif (args.T10afibatch is not None):
        if op_sys == 'Windows':
            warnings.warn('Windows is not supported for T10 mapping')
        # Run T10 and afi batch processing from a yaml file
        t10_preclinical(args.T10afibatch)

    else:
        # Run pk modelling from a yaml file.
        pkbatch(args.PKbatch)

if __name__ == '__main__':
    main()

