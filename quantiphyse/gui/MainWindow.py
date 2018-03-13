"""
Quantiphyse - Main application window

Copyright (c) 2013-2018 University of Oxford
"""

from __future__ import division, unicode_literals, print_function, absolute_import

import sys
import os
import requests

import numpy as np

from PySide import QtCore, QtGui
import pyqtgraph.console

from .ViewOptions import ViewOptions
from .Register import RegisterDialog
from .ImageView import ImageView

from ..gui.widgets import FingerTabBarWidget, FingerTabWidget
from ..volumes.io import load, save
from ..volumes.volume_management import ImageVolumeManagement
from ..utils import get_icon, get_local_file, get_version, get_plugins, local_file_from_drop_url
from ..utils.exceptions import QpException

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

class MainWindow(QtGui.QMainWindow):
    """
    Main application window

    Initializes volume management object and main view widget.
    Loads optional widgets
    Builds menus
    Requests registration if required
    Loads data from command line options
    """

    def __init__(self, load_data=None, load_roi=None):
        super(MainWindow, self).__init__()
        
        self.ivm = ImageVolumeManagement()
        self.view_options_dlg = ViewOptions(self, self.ivm)
        self.ivl = ImageView(self.ivm, self.view_options_dlg)

        # Load style sheet
        stFile = get_local_file("resources/darkorange.stylesheet")
        with open(stFile, "r") as fs:
            self.setStyleSheet(fs.read())

        # Default dir to load files from is the user's home dir
        self.default_directory = os.path.expanduser("~")

        # Widgets 
        self.widget_groups = {}
        self.current_widget = None

        widgets = get_plugins("widgets")
        for wclass in widgets:
            w = wclass(ivm=self.ivm, ivl=self.ivl, opts=self.view_options_dlg)
            if w.group not in self.widget_groups:
                self.widget_groups[w.group] = []
            self.widget_groups[w.group].append(w)

        for group, widgets in self.widget_groups.items():
            widgets.sort(key=lambda x: x.position)

        # Initialize menu and tabs
        self.init_menu()
        self.init_tabs()
        
        # Main layout - image view to left, tabs to right
        main_widget = QtGui.QWidget()
        hbox = QtGui.QHBoxLayout()
        splitter = QtGui.QSplitter(QtCore.Qt.Horizontal)
        splitter.addWidget(self.ivl)
        splitter.addWidget(self.tab_widget)
        splitter.setStretchFactor(0, 4)
        splitter.setStretchFactor(1, 1)
        hbox.addWidget(splitter)
        main_widget.setLayout(hbox)
        self.setCentralWidget(main_widget)
        
        # General properties of main window
        self.setWindowTitle("Quantiphyse %s" % get_version())
        self.setWindowIcon(QtGui.QIcon(get_icon("main_icon.png")))
        self.resize(1000, 700)
        self.setUnifiedTitleAndToolBarOnMac(True)
        self.setAcceptDrops(True)
        self.show()

        settings = QtCore.QSettings()
        reg = settings.value("registered", 0)
        #reg = 0
        if not reg:
            try:
                dlg = RegisterDialog(self)
                res = dlg.exec_()
                if res:
                    dlg.send_register_email(dlg.name_edit.text(), dlg.inst_edit.text(), dlg.email_edit.text())
                    settings.setValue("registered", 1)
                else:
                    self.close()
                    QtCore.QCoreApplication.quit()
            except:
                # On failure, allow program to continue but do not mark user as registered
                pass

        # autoload any files that have been passed from the command line
        if load_data is not None: self.load_data(fname=load_data, ftype="DATA")
        if load_roi is not None: self.load_data(fname=load_roi, ftype="ROI")

    def init_tabs(self):
        self.tab_widget = FingerTabWidget(self)

        # Add widgets flagged to appear by default
        for w in self.widget_groups["DEFAULT"]:
            index = self.tab_widget.addTab(w, w.icon, w.tabname)
            w.init_ui()
            w.visible = True
            w.index = index
        self.tab_widget.currentChanged.connect(self.select_tab)
        self.select_tab(0)

    def show_widget(self):
        # For some reason a closure did not work here - get the widget to show from the event sender
        w = self.sender().widget
        if not w.visible:
            index = self.tab_widget.addTab(w, w.icon, w.tabname)
            w.init_ui()
            w.visible = True
            w.index = index
        self.tab_widget.setCurrentIndex(w.index)

    def select_tab(self, idx):
        if self.current_widget is not None:
            self.current_widget.deactivate()
        self.current_widget = self.tab_widget.widget(idx)
        self.current_widget.activate()
        
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

        # Advanced --> Python Console
        console_action = QtGui.QAction(QtGui.QIcon(get_icon("console")), '&Console', self)
        console_action.setStatusTip('Run a console for advanced interaction')
        console_action.triggered.connect(self.show_console)
        
        # Advanced --> Install Packages
        #install_action = QtGui.QAction(QtGui.QIcon(get_icon("package")), '&Install Packages', self)
        #install_action.setStatusTip('Install additional packages')
        #install_action.triggered.connect(self.install_packages)

        menubar = self.menuBar()
        file_menu = menubar.addMenu('&File')
        widget_menu = menubar.addMenu('&Widgets')
        advanced_menu = menubar.addMenu('&Advanced')
        help_menu = menubar.addMenu('&Help')

        file_menu.addAction(load_action)
        file_menu.addAction(load_roi_action)
        file_menu.addAction(save_ovreg_action)
        file_menu.addAction(save_roi_action)
        file_menu.addAction(clear_action)
        file_menu.addAction(exit_action)

        widget_submenus = {"" : widget_menu}
        for group in sorted(self.widget_groups.keys()):
            if group != "DEFAULT":
                if group not in widget_submenus:
                    widget_submenus[group] = widget_menu.addMenu(group)
                    
                for w in self.widget_groups[group]:
                    action = QtGui.QAction(w.icon, '&%s' % w.name, self)
                    action.setStatusTip(w.description)
                    action.widget = w
                    action.triggered.connect(self.show_widget)
                    widget_submenus[group].addAction(action)

        help_menu.addAction(help_action)
        help_menu.addAction(about_action)

        advanced_menu.addAction(console_action)
        #advanced_menu.addAction(install_action)

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
                fnames.append(local_file_from_drop_url(url))
            self.raise_()
            self.activateWindow()
            for fname in fnames:
                self.load_data(fname)
        else:
            e.ignore()

    def show_help(self):
        """ Provide a clickable link to help files """
        QtGui.QDesktopServices.openUrl(QtCore.QUrl("http://quantiphyse.readthedocs.io/en/latest/", QtCore.QUrl.TolerantMode))

    def show_about(self):
        text = """
        <h1 align="center">Quantiphyse %s</h1>
        <p align="center">Formerly 'PkView'</p>
        <h2 align="center">Contributers</h2>
        <p align="center">Martin Craig (current maintainer)</p>
        <p align="center">Benjamin Irving (original author)</p>
        <p align="center">Michael Chappell</p>
        <p align="center">Paula Croal</p>
        """ % get_version()
        QtGui.QMessageBox.about(self, "Quantiphyse", text)

    #def install_packages(self):
    #    raise QpException("Package installation not implemented yet")

    def show_console(self):
        """
        Creates a pop up console that allows interaction with the GUI and data
        Uses:
        pyqtgraph.console
        """
        # Places that the console has access to
        namespace = {'np': np, 'ivm': self.ivm, 'self': self}
        for name, ovl in self.ivm.data.items():
            namespace[name] = ovl.std()
        for name, roi in self.ivm.rois.items():
            namespace[name] = roi.std()

        text = (
            """
            ****** Quantiphyse Console ******

            This is a python console that allows interaction with the GUI data and running of scripts.

            Libraries already imported
              np: Numpy

            Access to data
              ivm: Access to all the stored image data

            """)
        self.con1 = pyqtgraph.console.ConsoleWidget(namespace=namespace, text=text)
        self.con1.setWindowTitle('Quantiphyse Console')
        self.con1.setGeometry(QtCore.QRect(100, 100, 600, 600))
        self.con1.show()

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
            warning = "Interpreted data as multiple 2D volumes although file contained 3D spatial data"
            msgBox = QtGui.QMessageBox()
            msgBox.setText("Warning: There were problems loading this data:\n  - %s" % warning)
            msgBox.setInformativeText("Add data anyway?")
            msgBox.setStandardButtons(QtGui.QMessageBox.Ok | QtGui.QMessageBox.Cancel)
            msgBox.setDefaultButton(QtGui.QMessageBox.Ok)
            if msgBox.exec_() != QtGui.QMessageBox.Ok: return
            data.set_2dt()
        
        # Check for inappropriate ROI data
        if ftype == "ROI" and np.max(data.std()) > ROI_MAXVAL_WARN:
            msgBox = QtGui.QMessageBox()
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
