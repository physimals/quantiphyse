"""
Quantiphyse - Main application window

Copyright (c) 2013-2018 University of Oxford
"""

from __future__ import division, unicode_literals, print_function, absolute_import

import os

import numpy as np

try:
    from PySide import QtGui, QtCore, QtGui as QtWidgets
except ImportError:
    from PySide2 import QtGui, QtCore, QtWidgets

import pyqtgraph.console

from quantiphyse.data import load, save, ImageVolumeManagement
from quantiphyse.utils import set_default_save_dir, default_save_dir, get_icon, get_local_file, get_version, get_plugins, local_file_from_drop_url, show_help
from quantiphyse import __contrib__, __acknowledge__

from .widgets import FingerTabWidget
from .viewer.viewer import Viewer

class DragOptions(QtGui.QDialog):
    """
    Interface for dealing with drag and drop
    """

    def __init__(self, parent, fname, ivm, force_t_option=False, default_main=False, possible_roi=True):
        super(DragOptions, self).__init__(parent)
        self.setWindowTitle("Load Data")
        self.ivm = ivm
        self.force_t = False
        self.make_main = default_main
        self.type = ""
        self.name = ""

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
        if possible_roi:
            btn = QtGui.QPushButton("ROI")
            btn.clicked.connect(self._roi)
            hbox.addWidget(btn)
        btn = QtGui.QPushButton("Data")
        btn.setDefault(True)
        btn.clicked.connect(self._data)
        hbox.addWidget(btn)
        btn = QtGui.QPushButton("Cancel")
        btn.clicked.connect(self.reject)
        hbox.addWidget(btn)
        layout.addLayout(hbox)
        
        self.main_cb = QtGui.QCheckBox("Set as main data")
        self.main_cb.setChecked(default_main)
        layout.addWidget(self.main_cb)
        
        self.force_t_cb = QtGui.QCheckBox("Treat as 2D multi-volume")
        if force_t_option:
            # Currently only one possible advanced option so hide it when this is not required
            hbox = QtGui.QHBoxLayout()
            self.adv_cb = QtGui.QCheckBox("Advanced Options")
            self.adv_cb.stateChanged.connect(self._adv_changed)
            hbox.addWidget(self.adv_cb)
            layout.addLayout(hbox)

            self.adv_pane = QtGui.QWidget()
            vbox = QtGui.QVBoxLayout()
            self.adv_pane.setLayout(vbox)

            grid = QtGui.QGridLayout()
            grid.setColumnStretch(2, 1)

            self.force_t_cb = QtGui.QCheckBox("Treat as 2D multi-volume")
            #self.force_t_cb.setVisible(force_t_option)
            grid.addWidget(self.force_t_cb, 0, 0)
            
            vbox.addLayout(grid)
            
            self.adv_pane.setVisible(False)
            layout.addWidget(self.adv_pane)

        self.setLayout(layout)

    def _adv_changed(self, state):
        self.adv_pane.setVisible(state)

    def _data(self):
        self.type = "data"
        self._accepted()

    def _roi(self):
        self.type = "roi"
        self._accepted()

    def _accepted(self):
        self.force_t = self.force_t_cb.isChecked()
        self.make_main = self.main_cb.isChecked()
        self.name = self.name_combo.currentText()
        if self.name in self.ivm.data:
            btn = QtGui.QMessageBox.warning(self, "Name already exists",
                                            "Data already exists with this name - overwrite?",
                                            QtGui.QMessageBox.Ok | QtGui.QMessageBox.Cancel)
            if btn == QtGui.QMessageBox.Ok:
                self.accept()
        else:
            self.accept()

class MainWindow(QtGui.QMainWindow):
    """
    Main application window

    Initializes volume management object and main view widget.
    Loads optional widgets
    Builds menus
    Requests registration if required
    Loads data from command line options
    """

    def __init__(self, load_data=None, widgets=True):
        super(MainWindow, self).__init__()
        
        self.ivm = ImageVolumeManagement()
        self.ivl = Viewer(self.ivm)

        # Load style sheet
        stylesheet = get_local_file("resources/darkorange.stylesheet")
        with open(stylesheet, "r") as stylesheet_file:
            self.setStyleSheet(stylesheet_file.read())

        # Default dir to load files from is the user's home dir
        set_default_save_dir(os.path.expanduser("~"))

        # Widgets 
        self.widget_groups = {}
        self.current_widget = None

        # Main layout - image view to left, tabs to right
        main_widget = QtGui.QWidget()
        self.setCentralWidget(main_widget)
        hbox = QtGui.QHBoxLayout()
        main_widget.setLayout(hbox)

        splitter = QtGui.QSplitter(QtCore.Qt.Horizontal)
        splitter.addWidget(self.ivl)
        splitter.setStretchFactor(0, 4)
        hbox.addWidget(splitter)
        
        if widgets:
            default_size = (1000, 700)
            widgets = get_plugins("widgets")
            for wclass in widgets:
                w = wclass(ivm=self.ivm, ivl=self.ivl)
                if w.group not in self.widget_groups:
                    self.widget_groups[w.group] = []
                self.widget_groups[w.group].append(w)

            for _, widgets in self.widget_groups.items():
                widgets.sort(key=lambda x: x.position)

            self._init_tabs()
            splitter.addWidget(self.tab_widget)
            splitter.setStretchFactor(1, 1)
        else:
            default_size = (700, 700)

        self.init_menu()
        
        # General properties of main window
        self.setWindowTitle("Quantiphyse %s" % get_version())
        self.setWindowIcon(QtGui.QIcon(get_icon("main_icon.png")))
        self.resize(*default_size)
        self.setUnifiedTitleAndToolBarOnMac(True)
        self.setAcceptDrops(True)
        self.show()

        # Load any files from the command line
        if load_data:
            for fname in load_data:
                self.load_data(fname=fname)

    def _init_tabs(self):
        self.tab_widget = FingerTabWidget(self)

        # Add widgets flagged to appear by default
        for w in self.widget_groups.get("DEFAULT", []):
            index = self.tab_widget.addTab(w, w.icon, w.tabname)
            w.init_ui()
            w.visible = True
            w.inited = True
            w.index = index
        self.tab_widget.currentChanged.connect(self._tab_selected)
        self._tab_selected(0)

    def _show_widget(self):
        # For some reason a closure did not work here - get the widget to show from the event sender
        w = self.sender().widget
        if not w.visible:
            index = self.tab_widget.addTab(w, w.icon, w.tabname)
            if not w.inited:
                w.init_ui()
                w.inited = True
            w.visible = True
            w.index = index
        self.tab_widget.setCurrentIndex(w.index)

    def _tab_selected(self, idx):
        if self.current_widget is not None:
            self.current_widget.deactivate()
        self.current_widget = self.tab_widget.widget(idx)
        if self.current_widget is not None:
            self.current_widget.activate()
        
    def init_menu(self):
        """
        Set up the main window menus
        """
        
        # File --> Load Data
        load_action = QtGui.QAction(QtGui.QIcon(get_icon("picture")), '&Load Data', self)
        load_action.setShortcut('Ctrl+L')
        load_action.setStatusTip('Load a 3d or 4d image or ROI')
        load_action.triggered.connect(self.load_data_interactive)

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
        clear_action.triggered.connect(self._clear)

        # File --> Exit
        exit_action = QtGui.QAction(QtGui.QIcon.fromTheme("application-exit"), '&Exit', self)
        exit_action.setShortcut('Ctrl+Q')
        exit_action.setStatusTip('Exit Application')
        exit_action.triggered.connect(self.close)

        # About
        about_action = QtGui.QAction(QtGui.QIcon.fromTheme("help-about"), '&About', self)
        about_action.setStatusTip('About Quantiphyse')
        about_action.triggered.connect(self._show_about)

        # Help -- > Online help
        help_action = QtGui.QAction(QtGui.QIcon.fromTheme("help-contents"), '&Online Help', self)
        help_action.setStatusTip('See online help file')
        help_action.triggered.connect(self._show_help)

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
        file_menu.addAction(save_ovreg_action)
        file_menu.addAction(save_roi_action)
        file_menu.addAction(clear_action)
        file_menu.addAction(exit_action)

        widget_submenus = {"" : widget_menu}
        default_widget_groups = ["Visualisation", "Processing", "Clustering", "ROIs", "Utilities"]
        for group in default_widget_groups:
            widget_submenus[group] = widget_menu.addMenu(group)

        for group in sorted(self.widget_groups.keys()):
            if group != "DEFAULT":
                if group not in widget_submenus:
                    widget_submenus[group] = widget_menu.addMenu(group)
                    
                for w in self.widget_groups[group]:
                    action = QtGui.QAction(w.icon, '&%s' % w.name, self)
                    action.setStatusTip(w.description)
                    action.widget = w
                    action.triggered.connect(self._show_widget)
                    widget_submenus[group].addAction(action)

        help_menu.addAction(help_action)
        help_menu.addAction(about_action)

        advanced_menu.addAction(console_action)
        #advanced_menu.addAction(install_action)

        # extra info displayed in the status bar
        self.statusBar()

    def dragEnterEvent(self, drag_data):
        """
        Called when a drag object enters the interface
        """
        if drag_data.mimeData().hasUrls:
            drag_data.accept()
        else:
            drag_data.ignore()

    def dragMoveEvent(self, drag_data):
        """
        Called when a drag object is moved over the interface
        """
        if drag_data.mimeData().hasUrls:
            drag_data.accept()
        else:
            drag_data.ignore()

    def dropEvent(self, drag_data):
        """
        Called when a file or files are dropped on to the interface
        """
        if drag_data.mimeData().hasUrls:
            drag_data.setDropAction(QtCore.Qt.CopyAction)
            drag_data.accept()
            fnames = []
            for url in drag_data.mimeData().urls():
                fnames.append(local_file_from_drop_url(url))
            self.raise_()
            self.activateWindow()
            for fname in fnames:
                self.load_data_interactive(fname)
        else:
            drag_data.ignore()

    def _show_help(self):
        """ Provide a clickable link to help files """
        show_help()

    def _show_about(self):
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
            namespace[name] = ovl.raw()

        text = (
            """
            ****** Quantiphyse Console ******

            This is a python console that allows interaction with the GUI data and running of scripts.

            Libraries already imported
              np: Numpy

            Access to data
              ivm: Access to all the stored image data

            """)
        console = pyqtgraph.console.ConsoleWidget(namespace=namespace, text=text)
        console.setWindowTitle('Quantiphyse Console')
        console.setGeometry(QtCore.QRect(100, 100, 600, 600))
        console.show()

    def load_data_interactive(self, fname=None, name=None):
        """
        Load data into the IVM from a file (which may already be known)
        """
        if fname is None:
            fname, _ = QtGui.QFileDialog.getOpenFileName(self, 'Open file', default_save_dir())
            if not fname: return
        set_default_save_dir(os.path.dirname(fname))

        # Data is not loaded at this point, however basic metadata is so we can tailor the
        # options we offer
        data = load(fname)

        # If we have apparently 3d data then we have the 'advanced' option of treating the
        # third dimension as time - some broken NIFTI files require this.
        force_t_option = (data.nvols == 1 and data.grid.shape[2] > 1)
        force_t = False
                
        options = DragOptions(self, fname, self.ivm, force_t_option=force_t_option, 
                              default_main=self.ivm.main is None, possible_roi=(data.nvols ==1))
        if not options.exec_(): return
        
        data.name = options.name
        data.roi = options.type == "roi"
        if force_t_option: force_t = options.force_t
        
        # If we had to do anything evil to make data fit, warn and give user the chance to back out
        if force_t:
            msg_box = QtGui.QMessageBox(self)
            msg_box.setText("3D data was interpreted as multiple 2D volumes")
            msg_box.setStandardButtons(QtGui.QMessageBox.Ok | QtGui.QMessageBox.Cancel)
            msg_box.setDefaultButton(QtGui.QMessageBox.Ok)
            if msg_box.exec_() != QtGui.QMessageBox.Ok: return
            data.set_2dt()
        
        self.ivm.add(data, make_main=options.make_main, make_current=not options.make_main)

    def load_data(self, fname):
        """
        Load data non-interactively. The data will not be flagged as an ROI but the user
        can change that later if they want. Any finer control and you need to use interactive
        loading.
        """
        qpdata = load(fname)
        name = self.ivm.suggest_name(os.path.split(fname)[1].split(".", 1)[0])
        qpdata.name = name
        self.ivm.add(qpdata)

    def save_data(self):
        """
        Dialog for saving an data as a nifti file
        """
        if self.ivm.current_data is None:
            QtGui.QMessageBox.warning(self, "No data", "No current data to save", QtGui.QMessageBox.Close)
        else:
            if hasattr(self.ivm.current_data, "fname") and self.ivm.current_data.fname is not None:
                fname = self.ivm.current_data.fname
            else:
                fname = os.path.join(default_save_dir(), self.ivm.current_data.name + ".nii")

            fname, _ = QtGui.QFileDialog.getSaveFileName(self, 'Save file', dir=fname,
                                                         filter="NIFTI files (*.nii *.nii.gz)")
            if fname != '':
                save(self.ivm.current_data, fname)
            else: # Cancelled
                pass

    def save_roi(self):
        """
        Dialog for saving an ROI as a nifti file
        """
        if self.ivm.current_roi is None:
            QtGui.QMessageBox.warning(self, "No ROI", "No current ROI to save", QtGui.QMessageBox.Close)
        else:
            if hasattr(self.ivm.current_roi, "fname") and self.ivm.current_roi.fname is not None:
                fname = self.ivm.current_roi.fname
            else:
                fname = os.path.join(default_save_dir(), self.ivm.current_roi.name + ".nii")
            fname, _ = QtGui.QFileDialog.getSaveFileName(self, 'Save file', dir=fname,
                                                         filter="NIFTI files (*.nii *.nii.gz)")
            if fname != '':
                save(self.ivm.current_roi, fname)
            else: # Cancelled
                pass

    def _clear(self):
        if self.ivm.data:
            ret = QtGui.QMessageBox.warning(self, "Clear all data", "Are you sure you want to clear all data?",
                                            QtGui.QMessageBox.Yes | QtGui.QMessageBox.Cancel, QtGui.QMessageBox.Cancel)
            if ret == QtGui.QMessageBox.Yes:
                self.ivm.reset()
