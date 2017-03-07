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

if sys.platform.startswith("darwin"):
    from Cocoa import NSURL

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
from .widgets.T10Widgets import T10Widget
from .widgets.PerfSlicWidgets import MeanValuesWidget
from .widgets.PerfSlicWidgets import PerfSlicWidget
from .widgets.FabberWidgets import FabberWidget, fabber_batch
from .widgets.MCWidgets import MCFlirtWidget
from .widgets.ExperimentalWidgets import ImageExportWidget
from .widgets.OverviewWidgets import OverviewWidget
from .volumes.volume_management import Volume, Overlay, Roi, ImageVolumeManagement
from .analysis.overlay_analysis import OverlayAnalyis
from .QtInherit.FingerTabs import FingerTabBarWidget, FingerTabWidget
from .widgets.ExampleWidgets import ExampleWidget1

from .utils.cmd_pkmodel import pkbatch
from .utils.cmd_perfslic import perfslic
from .utils.cmd_t10 import t10_preclinical, t10
from .utils.cmd_mcflirt import mcflirt_batch

from .utils import set_local_file_path, get_icon

op_sys = platform.system()

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

    def __init__(self):
        super(MainWindowWidget, self).__init__()

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
        self.wid["SigEn"] = [SECurve(), 'voxel', 'Voxel analysis']
        self.wid["SigEn"][0].add_image_management(self.ivm)
        self.wid["SigEn"][0].add_image_view(self.ivl1)

        # Pharmaview is not initialised by default
        self.wid["PView"] = [None, 'a', 'b']

        # Color overlay widget
        self.wid["ColOv"] = [ColorOverlay1(), 'a', 'b']
        self.wid["ColOv"][0].add_analysis(self.ia)
        self.wid["ColOv"][0].add_image_management(self.ivm)
        self.wid["ColOv"][0].add_image_view(self.ivl1)

        # Pharmacokinetic modelling widget
        self.wid["PAna"] = [PharmaWidget(), 'a', 'b']
        self.wid["PAna"][0].add_image_management(self.ivm)

        # T10 widget - not visible by default
        self.wid["T10"] = [T10Widget(), 'a', 'b']
        self.wid["T10"][0].add_image_management(self.ivm)

        # Supervoxels widget - not visible by default
        self.wid["sv"] = [PerfSlicWidget(), 'a', 'b']
        self.wid["sv"][0].add_image_management(self.ivm)
        self.wid["sv"][0].add_image_view(self.ivl1)

        # Fabber modelling widget
        self.wid["Fab"] = [FabberWidget(), 'a', 'b']
        self.wid["Fab"][0].add_image_management(self.ivm)

        # Mean value overlay widget
        self.wid["meanvals"] = [MeanValuesWidget(), 'a', 'b']
        self.wid["meanvals"][0].add_image_management(self.ivm)

        # MCFlirt widget
        self.wid["mcflirt"] = [MCFlirtWidget(), 'a', 'b']
        self.wid["mcflirt"][0].add_image_management(self.ivm)

        # Gif creation widget
        self.wid["ImExp"] = [ImageExportWidget(), 'a', 'b']
        self.wid["ImExp"][0].add_image_management(self.ivm)

        # Clustering widget
        self.wid["Clus"] = [CurveClusteringWidget(), 'a', 'b']
        self.wid["Clus"][0].add_image_management(self.ivm)

        # Clustering widget
        self.wid["ClusOv"] = [OvCurveClusteringWidget(), 'a', 'b']
        self.wid["ClusOv"][0].add_image_management(self.ivm)

        self.wid["Overview"] = [OverviewWidget(), 'a', 'b']
        self.wid["Overview"][0].add_image_management(self.ivm)

        # Random Walker
        # self.sw_rw = None

        # Connect image export widget
        self.wid["ImExp"][0].sig_set_temp.connect(self.ivl1.set_time_pos)
        self.wid["ImExp"][0].sig_cap_image.connect(self.ivl1.capture_view_as_image)

        self.initTabs()

        # Choosing supervoxels for ROI
        self.ivl1.sig_mouse_click.connect(self.wid["sv"][0].sig_mouse_click)

        # InitUI
        # Sliders
        self.sld1 = QtGui.QSlider(QtCore.Qt.Horizontal, self)
        self.sld1.setFocusPolicy(QtCore.Qt.NoFocus)
        self.sld1.setMinimumWidth(100)
        self.sld2 = QtGui.QSlider(QtCore.Qt.Horizontal, self)
        self.sld2.setFocusPolicy(QtCore.Qt.NoFocus)
        self.sld2.setMinimumWidth(100)
        self.sld3 = QtGui.QSlider(QtCore.Qt.Horizontal, self)
        self.sld3.setFocusPolicy(QtCore.Qt.NoFocus)
        self.sld3.setMinimumWidth(100)
        self.sld4 = QtGui.QSlider(QtCore.Qt.Horizontal, self)
        self.sld4.setFocusPolicy(QtCore.Qt.NoFocus)
        self.sld4.setMinimumWidth(100)
        # self.update_slider_range()

        # connect sliders to ivl1
        self.sld1.valueChanged[int].connect(self.ivl1.set_space_pos(2))
        self.sld2.valueChanged[int].connect(self.ivl1.set_space_pos(1))
        self.sld3.valueChanged[int].connect(self.ivl1.set_space_pos(0))
        self.sld4.valueChanged[int].connect(self.ivl1.set_time_pos)

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
        grid = QtGui.QGridLayout()
        grid.addWidget(QtGui.QLabel("ROI"), 0, 0)
        self.roi_combo = QtGui.QComboBox()
        self.roi_combo.currentIndexChanged.connect(self.roi_changed)
        grid.addWidget(self.roi_combo, 0, 1)
        self.ivm.sig_current_roi.connect(self.update_current_roi)
        self.ivm.sig_all_rois.connect(self.update_rois)
        grid.addWidget(QtGui.QLabel("View"), 1, 0)
        self.roi_view_combo = QtGui.QComboBox()
        self.roi_view_combo.addItem("Shaded")
        self.roi_view_combo.addItem("Contour")
        self.roi_view_combo.addItem("Both")
        self.roi_view_combo.addItem("None")
        self.roi_view_combo.currentIndexChanged.connect(self.roi_view_changed)
        grid.addWidget(self.roi_view_combo, 1, 1)
        grid.addWidget(QtGui.QLabel("Alpha"), 2, 0)
        sld1 = QtGui.QSlider(QtCore.Qt.Horizontal, self)
        sld1.setFocusPolicy(QtCore.Qt.NoFocus)
        sld1.setRange(0, 255)
        sld1.setValue(150)
        sld1.valueChanged.connect(self.ivl1.roi_alpha_changed)
        grid.addWidget(sld1, 2, 1)
        grid.setRowStretch(3, 1)
        gBox.setLayout(grid)

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
        gBoxlay2.setColumnStretch(0, 0)
        gBoxlay2.setColumnStretch(1, 2)
        gBox2.setLayout(gBoxlay2)

        gBox3 = QtGui.QGroupBox("Overlay")
        grid = QtGui.QGridLayout()
        grid.addWidget(QtGui.QLabel("Overlay"), 0, 0)
        self.overlay_combo = QtGui.QComboBox()
        self.overlay_combo.currentIndexChanged.connect(self.overlay_changed)
        grid.addWidget(self.overlay_combo, 0, 1)
        self.ivm.sig_current_overlay.connect(self.update_current_overlay)
        self.ivm.sig_all_overlays.connect(self.update_overlays)
        grid.addWidget(QtGui.QLabel("View"), 1, 0)
        self.ov_view_combo = QtGui.QComboBox()
        self.ov_view_combo.addItem("All")
        self.ov_view_combo.addItem("Only in ROI")
        self.ov_view_combo.addItem("None")
        self.ov_view_combo.currentIndexChanged.connect(self.overlay_view_changed)
        grid.addWidget(self.ov_view_combo, 1, 1)
        grid.addWidget(QtGui.QLabel("Color map"), 2, 0)
        self.ov_cmap_combo = QtGui.QComboBox()
        self.ov_cmap_combo.addItem("jet")
        self.ov_cmap_combo.addItem("hot")
        self.ov_cmap_combo.addItem("gist_heat")
        self.ov_cmap_combo.addItem("flame")
        self.ov_cmap_combo.addItem("bipolar")
        self.ov_cmap_combo.addItem("spectrum")
        self.ov_cmap_combo.currentIndexChanged.connect(self.overlay_cmap_changed)
        grid.addWidget(self.ov_cmap_combo, 2, 1)

        grid.addWidget(QtGui.QLabel("Alpha"), 3, 0)
        sld1 = QtGui.QSlider(QtCore.Qt.Horizontal, self)
        sld1.setFocusPolicy(QtCore.Qt.NoFocus)
        sld1.setRange(0, 255)
        sld1.setValue(255)
        sld1.valueChanged.connect(self.ivl1.overlay_alpha_changed)
        grid.addWidget(sld1, 3, 1)
        grid.setRowStretch(4, 1)
        gBox3.setLayout(grid)

        # All buttons layout
        gBox_all = QtGui.QWidget()
        gBoxlay_all = QtGui.QHBoxLayout()
        vbox = QtGui.QVBoxLayout()
        self.voxel_scaling_btn = QtGui.QPushButton()
        self.voxel_scaling_btn.setCheckable(True)
        self.voxel_scaling_btn.toggled.connect(self.set_size_scaling)
        self.set_size_scaling(False)
        vbox.addWidget(self.voxel_scaling_btn)
        vbox.addStretch(1)
        gBoxlay_all.addLayout(vbox)
        gBoxlay_all.addWidget(gBox2)
        gBoxlay_all.addWidget(gBox)
        gBoxlay_all.addWidget(gBox3)
        gBoxlay_all.setStretch(1, 1)
        gBoxlay_all.setStretch(2, 1)
        gBoxlay_all.setStretch(3, 1)
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

    def set_size_scaling(self, state):
        if state:
            self.voxel_scaling_btn.setIcon(QtGui.QIcon(get_icon("voxel_scaling_off.png")))
            self.voxel_scaling_btn.setToolTip("Disable voxel size scaling")
        else:
            self.voxel_scaling_btn.setIcon(QtGui.QIcon(get_icon("voxel_scaling_on.png")))
            self.voxel_scaling_btn.setToolTip("Enable voxel size scaling")
        self.ivl1.set_size_scaling(state)

    def overlay_changed(self, idx):
        if idx >= 0:
            ov = self.overlay_combo.itemText(idx)
            self.ivm.set_current_overlay(ov, signal=True)

    def update_current_overlay(self, overlay):
        if overlay is None:
            self.roi_combo.setCurrentIndex(-1)
        else:
            idx = self.overlay_combo.findText(overlay.name)
            if idx != self.overlay_combo.currentIndex():
                try:
                    self.overlay_combo.blockSignals(True)
                    self.overlay_combo.setCurrentIndex(idx)
                finally:
                    self.overlay_combo.blockSignals(False)

    def update_overlays(self, overlays):
        try:
            self.overlay_combo.blockSignals(True)
            self.overlay_combo.clear()
            for ov in overlays:
                self.overlay_combo.addItem(ov)
        finally:
            self.overlay_combo.blockSignals(False)
        self.update_current_overlay(self.ivm.current_overlay)
        self.overlay_combo.updateGeometry()

    def roi_changed(self, idx):
        if idx >= 0:
            roi = self.roi_combo.itemText(idx)
            self.ivm.set_current_roi(roi, signal=True)

    def update_current_roi(self, roi):
        if roi is None:
            self.roi_combo.setCurrentIndex(-1)
        else:
            idx = self.roi_combo.findText(roi.name)
            if idx != self.roi_combo.currentIndex():
                try:
                    self.roi_combo.blockSignals(True)
                    self.roi_combo.setCurrentIndex(idx)
                finally:
                    self.roi_combo.blockSignals(False)

    def update_rois(self, rois):
        try:
            self.roi_combo.blockSignals(True)
            self.roi_combo.clear()
            for roi in rois:
                self.roi_combo.addItem(roi)
        finally:
            self.roi_combo.blockSignals(False)
        self.update_current_roi(self.ivm.current_roi)
        self.roi_combo.updateGeometry()

    def overlay_view_changed(self, idx):
        view = idx in (0, 1)
        roiOnly = (idx == 1)
        self.ivl1.set_overlay_view(view, roiOnly)

    def roi_view_changed(self, idx):
        shade = idx in (0, 2)
        contour = idx in (1, 2)
        self.ivl1.set_roi_view(shade, contour)

    def overlay_cmap_changed(self, idx):
        cmap = self.ov_cmap_combo.itemText(idx)
        self.ivl1.h2.setGradientName(cmap)

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
        self.qtab1.addTab(self.wid["SigEn"][0], QtGui.QIcon(get_icon("voxel")), "Voxel\n analysis")
        self.qtab1.addTab(self.wid["ColOv"][0], QtGui.QIcon(get_icon("edit")), "Overlay\n statistics")
        self.qtab1.addTab(self.wid["Clus"][0], QtGui.QIcon(get_icon("clustering")), "Curve\n cluster")
        self.qtab1.addTab(self.wid["ClusOv"][0], QtGui.QIcon(get_icon("clustering")), "Overlay\n cluster")

        # signal
        # self.qtab1.tabCloseRequested.connect(self.qtab1.removeTab)
        self.qtab1.setTabPosition(QtGui.QTabWidget.West)

    # update slider range
    def update_slider_range(self):
        # set slider range
        self.sld1.setRange(0, self.ivm.vol.shape[2]-1)
        self.sld2.setRange(0, self.ivm.vol.shape[1]-1)
        self.sld3.setRange(0, self.ivm.vol.shape[0]-1)

        if self.ivm.vol.ndims == 4:
            self.sld4.setRange(0, self.ivm.vol.shape[3]-1)
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
        index = self.qtab1.addTab(self.wid[wname][0], QtGui.QIcon(get_icon(self.wid[wname][1])), self.wid[wname][2])
        self.qtab1.setCurrentIndex(index)

    # Connect widget
    def show_se(self):
        index = self.qtab1.addTab(self.wid["SigEn"][0], QtGui.QIcon(get_icon("voxel")), "Voxel\nanalysis")
        self.qtab1.setCurrentIndex(index)

    # Connect widget
    def show_ic(self):
        index = self.qtab1.addTab(self.wid["ImExp"][0], QtGui.QIcon(get_icon("image_export")), "Image\nExport")
        self.qtab1.setCurrentIndex(index)

    def show_pk(self):
        index = self.qtab1.addTab(self.wid["PAna"][0], QtGui.QIcon(get_icon("pk")), "Pk")
        self.qtab1.setCurrentIndex(index)

    def show_t10(self):
        index = self.qtab1.addTab(self.wid["T10"][0], QtGui.QIcon(get_icon("t10")), "T10")
        self.qtab1.setCurrentIndex(index)

    def show_fab(self):
        index = self.qtab1.addTab(self.wid["Fab"][0], QtGui.QIcon(get_icon("fabber.svg")), "Fabber")
        self.qtab1.setCurrentIndex(index)

    def show_sv(self):
        index = self.qtab1.addTab(self.wid["sv"][0], QtGui.QIcon(get_icon("sv")), "Super\nvoxels")
        self.qtab1.setCurrentIndex(index)

    def show_meanvals(self):
        index = self.qtab1.addTab(self.wid["meanvals"][0], QtGui.QIcon(get_icon("meanvals")), "Mean\nvalues")
        self.qtab1.setCurrentIndex(index)

    def show_mcflirt(self):
        index = self.qtab1.addTab(self.wid["mcflirt"][0], QtGui.QIcon(get_icon("mcflirt")), "MCFlirt")
        self.qtab1.setCurrentIndex(index)

    def show_cc(self):
        index = self.qtab1.addTab(self.wid["Clus"][0], QtGui.QIcon(get_icon("clustering")),
                                  "Curve\n Cluster", )
        self.qtab1.setCurrentIndex(index)

    def show_pw(self):

        # Initialise if it is not already initialised
        if self.wid["PView"][0] is None:
            self.wid["PView"][0] = PharmaView()
            self.wid["PView"][0].add_image_management(self.ivm)
            self.ivl1.sig_mouse_click.connect(self.wid["PView"][0].sig_mouse)

        index = self.qtab1.addTab(self.wid["PView"][0], QtGui.QIcon(get_icon("curve_view")), "Pharma\n View")
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
        local_file_path = ""
        if hasattr(sys, 'frozen'):
            # if frozen
            print("Frozen executable")
            if hasattr(sys, '_MEIPASS'):
                print("Have _MEIPASS")
                local_file_path = sys._MEIPASS
            elif hasattr(sys, '_MEIPASS2'):
                print("Have _MEIPASS2")
                local_file_path = sys._MEIPASS2
            elif sys.frozen == 'macosx_app':
                local_file_path = os.getcwd() + '/pkview'
            else:
                local_file_path = os.path.dirname(sys.executable)
            os.environ["FABBERDIR"] = os.path.join(local_file_path, "fabber")

        # Running from a script
        else:
            local_file_path = os.path.dirname(__file__)

        # Use local working directory otherwise
        if local_file_path == "":
            print("Reverting to current directory as base")
            local_file_path = os.getcwd()

        # Print directory
        print("Local directory: ", local_file_path)
        set_local_file_path(local_file_path)

        # Load style sheet
        stFile = local_file_path + "/resources/darkorange.stylesheet"
        with open(stFile, "r") as fs:
            self.setStyleSheet(fs.read())

        # Load the main widget
        self.mw1 = MainWindowWidget()

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
        self.setWindowIcon(QtGui.QIcon(get_icon("main_icon.png")))

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
        load_action = QtGui.QAction(QtGui.QIcon(get_icon("picture")), '&Load Image Volume', self)
        load_action.setShortcut('Ctrl+L')
        load_action.setStatusTip('Load a 3d or 4d dceMRI image')
        load_action.triggered.connect(self.show_image_load_dialog)

        # File --> Load ROI
        load_roi_action = QtGui.QAction(QtGui.QIcon(get_icon("pencil")), '&Load ROI', self)
        load_roi_action.setStatusTip('Load binary ROI')
        load_roi_action.triggered.connect(self.show_roi_load_dialog)

        # File --> Load Overlay
        load_ovreg_action = QtGui.QAction(QtGui.QIcon(get_icon("edit")), '&Load Overlay', self)
        load_ovreg_action.setStatusTip('Load overlay')
        load_ovreg_action.triggered.connect(self.show_ovregsel_load_dialog)

        # File --> Save Overlay
        save_ovreg_action = QtGui.QAction(QtGui.QIcon.fromTheme("document-save"), '&Save Current Overlay', self)
        save_ovreg_action.setStatusTip('Save Current Overlay as a nifti file')
        save_ovreg_action.triggered.connect(self.show_ovreg_save_dialog)
        save_ovreg_action.setShortcut('Ctrl+S')

        # File --> Exit
        exit_action = QtGui.QAction(QtGui.QIcon.fromTheme("application-exit"), '&Exit', self)
        exit_action.setShortcut('Ctrl+Q')
        exit_action.setStatusTip('Exit Application')
        exit_action.triggered.connect(self.close)

        # Widgets --> Image export
        ic_action = QtGui.QAction(QtGui.QIcon(get_icon("image_export")), '&ImageExport', self)
        ic_action.setStatusTip('Export images from the GUI')
        ic_action.triggered.connect(self.mw1.show_ic)

        # Widgets --> Pharmacokinetics
        pk_action = QtGui.QAction(QtGui.QIcon(get_icon("pk")), '&Pharmacokinetics', self)
        pk_action.setStatusTip('Run pharmacokinetic analysis')
        pk_action.triggered.connect(self.mw1.show_pk)

        # Widgets --> T10
        t10_action = QtGui.QAction(QtGui.QIcon(get_icon("t10")), '&T10', self)
        t10_action.setStatusTip('T10 Map Generation')
        t10_action.triggered.connect(self.mw1.show_t10)

        # Widgets --> Supervoxels
        sv_action = QtGui.QAction(QtGui.QIcon(get_icon("sv")), '&Supervoxels', self)
        sv_action.setStatusTip('Supervoxel analysis')
        sv_action.triggered.connect(self.mw1.show_sv)

        # Widgets --> Supervoxels
        mv_action = QtGui.QAction(QtGui.QIcon(get_icon("meanvals")), '&Mean values overlay', self)
        mv_action.setStatusTip('Generate overlay of mean values within ROI regions')
        mv_action.triggered.connect(self.mw1.show_meanvals)

        # Widgets --> Fabber
        fab_action = QtGui.QAction(QtGui.QIcon(get_icon("fabber.svg")), '&Fabber', self)
        fab_action.setStatusTip('Run fabber model fitting')
        fab_action.triggered.connect(self.mw1.show_fab)

        # Widgets --> MCFlirt
        mcflirt_action = QtGui.QAction(QtGui.QIcon(get_icon("mcflirt")), '&MCFlirt', self)
        mcflirt_action.setStatusTip('MCFlirt motion correction')
        mcflirt_action.triggered.connect(self.mw1.show_mcflirt)

        # Widgets --> PharmaView
        pw_action = QtGui.QAction(QtGui.QIcon(get_icon("curve_view")), '&PharmCurveView', self)
        pw_action.setStatusTip('Compare the true signal enhancement to the predicted model enhancement')
        pw_action.triggered.connect(self.mw1.show_pw)

        # Widgets --> RandomWalker
        # rw_action = QtGui.QAction('&RandomWalker', self)
        # rw_action.setStatusTip('RandomWalker')
        # rw_action.triggered.connect(self.mw1.show_rw)

        # Widgets --> CurveClustering
        # cc_action = QtGui.QAction(QtGui.QIcon(get_icon("clustering")), '&CurveClustering', self)
        # cc_action.setStatusTip('Cluster curves in a ROI of interest')
        # cc_action.triggered.connect(self.mw1.show_cc)

        # Wigets --> Create Annotation
        # annot_ovreg_action = QtGui.QAction(QtGui.QIcon(get_icon("edit")), '&Enable Annotation', self)
        # annot_ovreg_action.setStatusTip('Enable Annotation of the GUI')
        # annot_ovreg_action.setCheckable(True)
        # annot_ovreg_action.toggled.connect(self.show_annot_load_dialog)

        # Help -- > Online help
        help_action = QtGui.QAction(QtGui.QIcon.fromTheme("help-contents"), '&Online Help', self)
        help_action.setStatusTip('See online help file')
        help_action.triggered.connect(self.click_link)

        # Advanced --> Python Console
        console_action = QtGui.QAction(QtGui.QIcon(get_icon("console")), '&Console', self)
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
        widget_menu.addAction(fab_action)
        widget_menu.addAction(pw_action)
        widget_menu.addAction(sv_action)
        widget_menu.addAction(mv_action)
        widget_menu.addAction(mcflirt_action)
        widget_menu.addAction(t10_action)
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
        QtGui.QDesktopServices.openUrl(QtCore.QUrl("http://pkview.readthedocs.io/en/latest/", QtCore.QUrl.TolerantMode))

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

            if self.mw1.ivm.vol is not None:
                # Checking if data already exists
                msgBox = QtGui.QMessageBox()
                msgBox.setText("A volume has already been loaded")
                msgBox.setInformativeText("Do you want to clear all data and load this new volume?")
                msgBox.setStandardButtons(QtGui.QMessageBox.Ok | QtGui.QMessageBox.Cancel)
                msgBox.setDefaultButton(QtGui.QMessageBox.Ok)

                ret = msgBox.exec_()

                if ret == QtGui.QMessageBox.Ok:
                    print("Clearing data")
                    self.mw1.ivm.init(reset=True)
                else:
                    return

            self.default_directory = get_dir(fname)
            self.mw1.ivm.set_main_volume(Volume("main", fname=fname))
            print("Image dimensions: ", self.mw1.ivm.vol.shape)
            print("Voxel size: ", self.mw1.ivm.vol.voxel_sizes)
            print("Image range: ", self.mw1.ivm.vol.range)
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
            name = os.path.split(fname)[1].split(".", 1)[0]
            self.mw1.ivm.add_roi(Roi(name, fname=fname), make_current=True)
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
                # Make default type the filename (without extension) if not specified
                ftype = os.path.split(fname)[1].split(".", 1)[0]
                ftype, ok = QtGui.QInputDialog.getItem(self, 'Overlay type', 'Type of overlay loaded:',
                                                       [ftype, 'T10', 'Ktrans', 'kep', 've', 'vp', 'model_curves',
                                                        'annotation'])

            if ok:
                self.default_directory = get_dir(fname)
                self.mw1.ivm.add_overlay(Overlay(ftype, fname=fname), make_current=True)
        else:
            print('Warning: No file selected')

    def show_ovreg_save_dialog(self):
        """
        Dialog for saving an overlay as a nifti file

        """
        if self.mw1.ivm.current_overlay is None:
            QtGui.QMessageBox.warning(self, "No overlay", "No current overlay to save", QtGui.QMessageBox.Close)
            return

        fname, _ = QtGui.QFileDialog.getSaveFileName(self, 'Save file', dir=self.default_directory, filter="*.nii")

        if fname != '':
            # self.default_directory = get_dir(fname)
            self.mw1.ivm.current_overlay.save_nifti(fname)
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
            self.show_ovregsel_load_dialog(fname)

        # Loading main image
        elif ftype == 'DCE':
            if self.mw1.ivm.vol is not None:

                # Checking if data already exists
                msgBox = QtGui.QMessageBox()
                msgBox.setText("A volume has already been loaded")
                msgBox.setInformativeText("Do you want to clear all data and load this new volume?")
                msgBox.setStandardButtons(QtGui.QMessageBox.Ok | QtGui.QMessageBox.Cancel)
                msgBox.setDefaultButton(QtGui.QMessageBox.Ok)

                ret = msgBox.exec_()

                if ret == QtGui.QMessageBox.Ok:
                    print("Clearing data")
                    self.mw1.ivm.init(reset=True)
                else:
                    return

            self.mw1.ivm.set_main_volume(Volume("main", fname=fname))
            print("Image dimensions: ", self.mw1.ivm.vol.shape)
            print("Voxel size: ", self.mw1.ivm.vol.voxel_sizes)
            print("Image range: ", self.mw1.ivm.vol.range)
            self.mw1.update_slider_range()

        # Loading ROI
        elif ftype == 'ROI':
            name = os.path.split(fname)[1].split(".", 1)[0]
            self.mw1.ivm.add_roi(Roi(name, fname=fname), make_current=True)

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
    parser.add_argument('--slicbatch', help='Run batch SLIC supervoxel processing from a yaml file', default=None, type=str)
    parser.add_argument('--T10batch', help='Run batch T10 processing from a yaml file', default=None, type=str)
    parser.add_argument('--PKbatch', help='Run batch PK processing from a yaml file', default=None, type=str)
    parser.add_argument('--fabberbatch', help='Run batch Fabber processing from a yaml file', default=None, type=str)
    parser.add_argument('--mcflirtbatch', help='Run batch MCFLIRT processing from a yaml file', default=None, type=str)
    parser.add_argument('--image', help='DCE-MRI nifti file location', default=None, type=str)
    parser.add_argument('--roi', help='ROI nifti file location', default=None, type=str)
    parser.add_argument('--overlay', help='Overlay nifti file location', default=None, type=str)
    parser.add_argument('--overlaytype', help='Type of overlay', default=None, type=str)
    args = parser.parse_args()

    print(pg.systemInfo())

    # Check whether any batch processing arguments have been called

    if (args.T10batch is not None):
        # Run T10 batch processing from a yaml file
        t10(args.T10batch)

    elif (args.T10afibatch is not None):
        # Run T10 and afi batch processing from a yaml file
        t10_preclinical(args.T10afibatch)

    elif (args.slicbatch is not None):
        perfslic(args.slicbatch)

    elif (args.PKbatch is not None):
        pkbatch(args.PKbatch)

    elif (args.mcflirtbatch is not None):
        mcflirt_batch(args.mcflirtbatch)

    elif (args.fabberbatch is not None):

        fabber_batch(args.fabberbatch)

    else:
        # Initialise main GUI

        # OSx specific Changes
        if op_sys == 'Darwin':
            from Foundation import NSURL
            QtGui.QApplication.setGraphicsSystem('native')

        # Initialise the PKView application
        app = QtGui.QApplication(sys.argv)
        app.setStyle('plastique')  # windows, motif, cde, plastique, windowsxp, macintosh
        # app.setGraphicsSystem('native')  ## work around a variety of bugs in the native graphics system

        # Pass arguments from the terminal (if any) into the main application
        ex = WindowAndDecorators(args.image, args.roi, args.overlay, args.overlaytype)
        sys.exit(app.exec_())

if __name__ == '__main__':
    main()
