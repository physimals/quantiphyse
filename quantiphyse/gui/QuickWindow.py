"""
Quantiphyse - Quick cutodown version of the main application window

Copyright (c) 2013-2018 University of Oxford
"""

from __future__ import division, unicode_literals, print_function, absolute_import

import sys
import os

import numpy as np

from PySide import QtCore, QtGui

from .ViewOptions import ViewOptions
from .ImageView import ImageView

from ..volumes.io import load, save
from ..volumes.volume_management import ImageVolumeManagement
from ..utils import get_icon, get_local_file, get_version, local_file_from_drop_url
from ..utils.exceptions import QpException
from quantiphyse import __contrib__, __acknowledge__

# ROIs with values larger than this will trigger a warning
ROI_MAXVAL_WARN = 1000

class DragOptions(QtGui.QDialog):
    """
    Interface for dealing with drag and drop
    """

    def __init__(self, parent, fname, ivm, ftype=None, force_t_option=False, default_main=False):
        super(DragOptions, self).__init__(parent)
        self.setWindowTitle("Load Data")
        self.ivm = ivm

        layout = QtGui.QVBoxLayout()

        grid = QtGui.QGridLayout()
        grid.addWidget(QtGui.QLabel("Name:"), 1, 0)
        self.name_combo = QtGui.QComboBox()
        def_name = self.ivm.suggest_name(os.path.split(fname)[1].split(".", 1)[0])
        for name in [def_name, 'MRI', 'T10', 'Ktrans', 'kep', 've', 'vp', 'model_curves']:
            self.name_combo.addItem(name)
        self.name_combo.setEditable(True)
        grid.addWidget(self.name_combo, 1, 1)
        layout.addLayout(grid)
        hbox = QtGui.QHBoxLayout()
        if ftype is None:
            btn = QtGui.QPushButton("Data")
            btn.clicked.connect(self.clicked("DATA"))
            hbox.addWidget(btn)
            btn = QtGui.QPushButton("ROI")
            btn.clicked.connect(self.clicked("ROI"))
            hbox.addWidget(btn)
        else:
            btn = QtGui.QPushButton("Ok")
            btn.clicked.connect(self.clicked(ftype.upper()))
            hbox.addWidget(btn)
        btn = QtGui.QPushButton("Cancel")
        btn.clicked.connect(self.reject)
        hbox.addWidget(btn)
        layout.addLayout(hbox)
        
        hbox = QtGui.QHBoxLayout()
        self.adv_cb = QtGui.QCheckBox("Advanced Options")
        self.adv_cb.stateChanged.connect(self._adv_changed)
        hbox.addWidget(self.adv_cb)
        layout.addLayout(hbox)

        self.adv_pane = QtGui.QWidget()
        vbox = QtGui.QVBoxLayout()
        self.adv_pane.setLayout(vbox)

        grid = QtGui.QGridLayout()
        self.main_cb = QtGui.QCheckBox("Set as main data")
        self.main_cb.setChecked(default_main)
        self.make_main = default_main
        grid.addWidget(self.main_cb, 0, 0)

        self.force_t_cb = QtGui.QCheckBox("Treat as 2D multi-volume")
        self.force_t_cb.setVisible(force_t_option)
        grid.addWidget(self.force_t_cb, 1, 0)
        
        grid.setColumnStretch(2, 1)
        vbox.addLayout(grid)
        
        self.adv_pane.setVisible(False)
        layout.addWidget(self.adv_pane)

        self.setLayout(layout)
        self.type = ""
        self.name = ""
        self.force_t = False

    def _adv_changed(self, state):
        self.adv_pane.setVisible(state)

    def clicked(self, ret):
        def cb():
            self.type = ret
            self.force_t = self.force_t_cb.isChecked()
            self.make_main = self.main_cb.isChecked()
            self.name = self.name_combo.currentText()
            if self.name in self.ivm.data or self.name in self.ivm.rois:
                btn = QtGui.QMessageBox.warning(self, "Name already exists",
                    "Data already exists with this name - overwrite?",
                    QtGui.QMessageBox.Ok | QtGui.QMessageBox.Cancel)
                if btn == QtGui.QMessageBox.Ok:
                    self.accept()
            else:
                self.accept()
        return cb

    @staticmethod
    def getImageChoice(parent, fname, ivm, ftype=None, force_t_option=False, make_main=False):
        dialog = DragOptions(parent, fname, ivm, ftype=ftype, force_t_option=force_t_option, default_main=make_main)
        result = dialog.exec_()
        return dialog.type, dialog.name, result == QtGui.QDialog.Accepted, dialog.force_t, dialog.make_main

class QuickWindow(QtGui.QMainWindow):
    """
    Main application window

    Initializes volume management object and main view widget.
    Loads optional widgets
    Builds menus
    Requests registration if required
    Loads data from command line options
    """

    def __init__(self, load_data=None, load_roi=None):
        super(QuickWindow, self).__init__()
        
        self.ivm = ImageVolumeManagement()
        self.view_options_dlg = ViewOptions(self, self.ivm)
        self.ivl = ImageView(self.ivm, self.view_options_dlg)

        # Load style sheet
        stFile = get_local_file("resources/darkorange.stylesheet")
        with open(stFile, "r") as fs:
            self.setStyleSheet(fs.read())

        # Default dir to load files from is the user's home dir
        self.default_directory = os.path.expanduser("~")

        # Initialize menu
        self.init_menu()
        
        # Main layout
        main_widget = QtGui.QWidget()
        hbox = QtGui.QHBoxLayout()
        hbox.addWidget(self.ivl)
        main_widget.setLayout(hbox)
        self.setCentralWidget(main_widget)
        
        # General properties of main window
        self.setWindowTitle("Quantiphyse %s" % get_version())
        self.setWindowIcon(QtGui.QIcon(get_icon("main_icon.png")))
        self.resize(700, 500)
        self.setUnifiedTitleAndToolBarOnMac(True)
        self.setAcceptDrops(True)
        self.show()

        # autoload any files that have been passed from the command line
        if load_data is not None: self.load_data(fname=load_data, ftype="DATA")
        if load_roi is not None: self.load_data(fname=load_roi, ftype="ROI")

    def init_menu(self):
        """
        Set up the main window menus
        """
        
        # File --> Load Data
        load_action = QtGui.QAction(QtGui.QIcon(get_icon("picture")), '&Load Data', self)
        load_action.setShortcut('Ctrl+L')
        load_action.setStatusTip('Load a 3d or 4d image')
        load_action.triggered.connect(self.load_vol)

        # File --> Load ROI
        load_roi_action = QtGui.QAction(QtGui.QIcon(get_icon("pencil")), '&Load ROI', self)
        load_roi_action.setStatusTip('Load binary ROI')
        load_roi_action.triggered.connect(self.load_roi)

        # File --> Save Data
        save_ovreg_action = QtGui.QAction(QtGui.QIcon.fromTheme("document-save"), '&Save current data', self)
        save_ovreg_action.setStatusTip('Save current data as a NIFTI file')
        save_ovreg_action.triggered.connect(self.save_data)
        save_ovreg_action.setShortcut('Ctrl+S')

        # File --> Save ROI
        save_roi_action = QtGui.QAction(QtGui.QIcon.fromTheme("document-save"), '&Save current ROI', self)
        save_roi_action.setStatusTip('Save current ROI as a NIFTI file')
        save_roi_action.triggered.connect(self.save_roi)

        # File --> Clear all
        clear_action = QtGui.QAction(QtGui.QIcon.fromTheme("clear"), '&Clear all data', self)
        clear_action.setStatusTip('Remove all data from the viewer')
        clear_action.triggered.connect(self.clear)

        # File --> Exit
        exit_action = QtGui.QAction(QtGui.QIcon.fromTheme("application-exit"), '&Exit', self)
        exit_action.setShortcut('Ctrl+Q')
        exit_action.setStatusTip('Exit Application')
        exit_action.triggered.connect(self.close)

        # About
        about_action = QtGui.QAction(QtGui.QIcon.fromTheme("help-about"), '&About', self)
        about_action.setStatusTip('About Quantiphyse')
        about_action.triggered.connect(self.show_about)

        # Help -- > Online help
        help_action = QtGui.QAction(QtGui.QIcon.fromTheme("help-contents"), '&Online Help', self)
        help_action.setStatusTip('See online help file')
        help_action.triggered.connect(self.show_help)

        menubar = self.menuBar()
        file_menu = menubar.addMenu('&File')
        help_menu = menubar.addMenu('&Help')

        file_menu.addAction(load_action)
        file_menu.addAction(load_roi_action)
        file_menu.addAction(save_ovreg_action)
        file_menu.addAction(save_roi_action)
        file_menu.addAction(clear_action)
        file_menu.addAction(exit_action)

        help_menu.addAction(help_action)
        help_menu.addAction(about_action)

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
        Called when a file or files are dropped on to the interface
        """
        if e.mimeData().hasUrls:
            e.setDropAction(QtCore.Qt.CopyAction)
            e.accept()
            fnames = []
            for url in e.mimeData().urls():
                names.append(local_file_from_drop_url(url))
            self.raise_()
            self.activateWindow()
            for fname in fnames:
                self.load_data(fname)
        else:
            e.ignore()

    def show_help(self):
        """ Provide a clickable link to help files """
        QtGui.QDesktopServices.openUrl(QtCore.QUrl("http://quantiphyse.readthedocs.io/en/v0.4/", QtCore.QUrl.TolerantMode))

    def show_about(self):
        text = """
        <h1 align="center">Quantiphyse %s</h1>
        <p align="center">Formerly 'PkView'</p>
        <h2 align="center">Contributers</h2>""" % get_version()
        for author, role in __contrib__.items():
            if role != "":
                text += "<p align='center'>%s(%s)</p>" % (author, role)
            else:
                text += "<p align='center'>%s</p>" % author
        for ack, role in __acknowledge__.items():
            text += "<p align='center'>%s</p>" % ack

        QtGui.QMessageBox.about(self, "Quantiphyse", text)

    def load_data(self, fname=None, name=None, ftype=None):
        """
        Load data into the IVM from a file (which may already be known)
        """
        if fname is None:
            fname, _ = QtGui.QFileDialog.getOpenFileName(self, 'Open file', self.default_directory)
            if not fname: return
        self.default_directory = os.path.dirname(fname)

        # Data is not loaded at this point, however basic metadata is so we can tailor the
        # options we offer
        data = load(fname)

        # FIXME not doing this because a lot of ROIs seem to come in as float data? 
        #if ftype is None and issubclass(dtype.type, np.floating):
        #    # Floating point is assumed to be data (not ROI)
        #    print(dtype)
        #    ftype = "DATA"

        # If we have apparently 3d data then we have the 'advanced' option of treating the
        # third dimension as time - some broken NIFTI files require this.
        force_t_option = (data.nvols == 1 and data.rawgrid.shape[2] > 1)
        force_t = False
                
        make_main = (self.ivm.main is None) or (self.ivm.main.nvols == 1 and data.nvols > 1)
        ftype, name, ok, force_t_dialog, make_main = DragOptions.getImageChoice(self, fname, self.ivm, force_t_option=force_t_option, make_main=make_main)
        if not ok: return
        data.name = name
        if force_t_option: force_t = force_t_dialog
        
        # If we had to do anything evil to make data fit, warn and give user the chance to back out
        warnings = []
        if force_t:
            msgBox = QtGui.QMessageBox(self)
            msgBox.setText("3D data was interpreted as multiple 2D volumes")
            msgBox.setStandardButtons(QtGui.QMessageBox.Ok | QtGui.QMessageBox.Cancel)
            msgBox.setDefaultButton(QtGui.QMessageBox.Ok)
            if msgBox.exec_() != QtGui.QMessageBox.Ok: return
            data.set_2dt()
        
        # Check for inappropriate ROI data
        if ftype == "ROI" and np.max(data.std()) > ROI_MAXVAL_WARN:
            msgBox = QtGui.QMessageBox(self)
            warntxt = "\n  -".join(warnings)
            msgBox.setText("Warning: ROI contains values larger than %i" % ROI_MAXVAL_WARN)
            msgBox.setInformativeText("Are you sure this is an ROI file?")
            msgBox.setStandardButtons(QtGui.QMessageBox.Yes | QtGui.QMessageBox.Cancel)
            msgBox.setDefaultButton(QtGui.QMessageBox.Cancel)
            if msgBox.exec_() != QtGui.QMessageBox.Yes: return

        if ftype == "DATA": 
            self.ivm.add_data(data, make_current=True, make_main=make_main)
        else:
            self.ivm.add_roi(data, make_current=True)

    def save_data(self):
        """
        Dialog for saving an data as a nifti file
        """
        if self.ivm.current_data is None:
            QtGui.QMessageBox.warning(self, "No data", "No current data to save", QtGui.QMessageBox.Close)
        else:
            fname, _ = QtGui.QFileDialog.getSaveFileName(self, 'Save file', dir=self.default_directory, filter="NIFTI files (*.nii *.nii.gz)")
            if fname != '':
                save(self.ivm.current_data, fname, self.ivm.save_grid)
            else: # Cancelled
                pass

    def save_roi(self):
        """
        Dialog for saving an ROI as a nifti file
        """
        if self.ivm.current_roi is None:
            QtGui.QMessageBox.warning(self, "No ROI", "No current ROI to save", QtGui.QMessageBox.Close)
        else:
            fname, _ = QtGui.QFileDialog.getSaveFileName(self, 'Save file', dir=self.default_directory, filter="NIFTI files (*.nii *.nii.gz)")
            if fname != '':
                save(self.ivm.current_roi, fname, self.ivm.save_grid)
            else: # Cancelled
                pass

    def clear(self):
         # Check for inappropriate ROI data
        if len(self.ivm.data) != 0:
            msgBox = QtGui.QMessageBox()
            msgBox.setText("Clear all data")
            msgBox.setInformativeText("Are you sure you want to clear all data?")
            msgBox.setStandardButtons(QtGui.QMessageBox.Yes | QtGui.QMessageBox.Cancel)
            msgBox.setDefaultButton(QtGui.QMessageBox.Cancel)
            if msgBox.exec_() != QtGui.QMessageBox.Yes: return
        self.ivm.reset()

    def load_vol(self):
        self.load_data(ftype="DATA")

    def load_roi(self):
        self.load_data(ftype="ROI")
