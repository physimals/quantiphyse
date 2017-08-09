"""
Author: Benjamin Irving (benjamin.irv@gmail.com), Martin Craig (martin.craig@eng.ox.ac.uk)
Copyright (c) 2013-2017 University of Oxford
"""

from __future__ import division, unicode_literals, print_function, absolute_import

import sys
import os
import os.path
import platform
import argparse
import traceback
import requests
import warnings
import signal

from PySide import QtCore, QtGui
import pyqtgraph as pg
import pyqtgraph.console
import numpy as np

if sys.platform.startswith("darwin"):
    from Cocoa import NSURL

from .QtInherit.dialogs import error_dialog

# required to use resources in theme. Check if 2 or 3.
if (sys.version_info > (3, 0)):
    from .resources import resource_py2
else:
    from .resources import resource_py3

from ._version import __version__

from .QtInherit.FingerTabs import FingerTabBarWidget, FingerTabWidget

from .volumes.io import load, save
from .volumes.volume_management import ImageVolumeManagement

from .utils.batch import run_batch
from .utils import set_local_file_path, get_icon, get_local_file

from .ImageView import ImageView

from .widgets.OverviewWidgets import OverviewWidget
from .widgets.AnalysisWidgets import SECurve, OverlayStatistics, RoiAnalysisWidget, SimpleMathsWidget
from .widgets.ClusteringWidgets import CurveClusteringWidget
from .widgets.OvClusteringWidgets import OvCurveClusteringWidget
#from .widgets.PharmaWidgets import PharmaWidget, ModelCurves
#from .widgets.T10Widgets import T10Widget
#from .widgets.PerfSlicWidgets import MeanValuesWidget
from .widgets.PerfSlicWidgets import PerfSlicWidget
#from .widgets.fabber import FabberWidget, CESTWidget, ASLWidget
from .widgets.MCWidgets import RegWidget
##from .widgets.ExperimentalWidgets import ImageExportWidget
#from .widgets.RoiBuilderWidget import RoiBuilderWidget

op_sys = platform.system()

# ROIs with values larger than this will trigger a warning
ROI_MAXVAL_WARN = 1000

class DragOptions(QtGui.QDialog):
    """
    Interface for dealing with drag and drop
    """

    def __init__(self, parent, fname, ivm, ftype=None, force_t_option=False):
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
        self.force_t_cb = QtGui.QCheckBox("Treat as 2D multi-volume")
        self.force_t_cb.setVisible(force_t_option)
        hbox.addWidget(self.force_t_cb, 2, 0)
        hbox.addStretch()
        layout.addLayout(hbox)
        
        self.setLayout(layout)
        self.type = ""
        self.name = ""
        self.force_t = False

    def clicked(self, ret):
        def cb():
            self.type = ret
            self.force_t = self.force_t_cb.isChecked()
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
    def getImageChoice(parent, fname, ivm, ftype=None, force_t_option=False):
        dialog = DragOptions(parent, fname, ivm, ftype=ftype, force_t_option=force_t_option)
        result = dialog.exec_()
        return dialog.type, dialog.name, result == QtGui.QDialog.Accepted, dialog.force_t

def send_register_email(name, inst, email):
    """
    Send registration email
    
    Note that this email service has been set only to send to the specified recipient
    so this cannot be used to spam anybody else!
    """
    return requests.post(
        "https://api.mailgun.net/v3/sandboxd8aca8efc95348609a6d63f0c651f4d2.mailgun.org/messages",
        auth=("api", "key-c0be61e997b71c2d0c43fa8aeb706a5c"),
        data={"from": "Quantiphyse <postmaster@sandboxd8aca8efc95348609a6d63f0c651f4d2.mailgun.org>",
              "to": "Martin Craig <martin.craig@eng.ox.ac.uk>",
              "subject": "Quantiphyse Registration",
              "text": "Name: %s\nInstitution: %s\nEmail: %s\n" % (name, inst, email)})

class RegisterDialog(QtGui.QDialog):
    """
    Dialog box which asks a first-time user to send a registration email
    """
    def __init__(self, parent=None, scale=[]):
        QtGui.QDialog.__init__(self, parent)
        
        layout = QtGui.QVBoxLayout()

        hbox = QtGui.QHBoxLayout()
        pixmap = QtGui.QPixmap(get_icon("quantiphyse_75.png"))
        lpic = QtGui.QLabel(self)
        lpic.setPixmap(pixmap)
        hbox.addWidget(lpic)
        hbox.addStretch(1)
        layout.addLayout(hbox)

        layout.addWidget(QtGui.QLabel(""))

        hbox = QtGui.QHBoxLayout()
        hbox.addStretch(1)
        hbox.addWidget(QtGui.QLabel("\n<font size=5>Welcome to Quantiphyse %s</font>" % __version__))
        hbox.addStretch(1)
        layout.addLayout(hbox)

        l = QtGui.QLabel("\nPlease register as a user. We will not send any unsolicited communications, this is just to help us know where the software is being used")
        l.setWordWrap(True)
        layout.addWidget(l)

        grid = QtGui.QGridLayout()
        grid.addWidget(QtGui.QLabel("Name"), 0, 0)
        self.name_edit = QtGui.QLineEdit()
        grid.addWidget(self.name_edit, 0, 1)
        grid.addWidget(QtGui.QLabel("Institution"), 0, 2)
        self.inst_edit = QtGui.QLineEdit()
        grid.addWidget(self.inst_edit, 0, 3)
        grid.addWidget(QtGui.QLabel("Email"), 1, 0)
        self.email_edit = QtGui.QLineEdit()
        grid.addWidget(self.email_edit, 1, 1, 1, 3)
        layout.addLayout(grid)

        layout.addWidget(QtGui.QLabel("<font size=5>\nLicense Agreement</font>"))
        edit = QtGui.QTextEdit()
        # FIXME
        #lic_file = open(get_local_file("../licence.md"), "r")
        #try:
        #    for line in lic_file:
        #        edit.append(line)
        #finally:
        #    lic_file.close()
        #edit.moveCursor (QtGui.QTextCursor.Start)
        #edit.ensureCursorVisible()
        layout.addWidget(edit)

        l = QtGui.QLabel("""The Software is distributed "AS IS" under this Licence solely for non-commercial use. If you are interested in using the Software commercially, please contact the technology transfer company of the University, to negotiate a licence. Contact details are: enquiries@innovation.ox.ac.uk""")
        l.setWordWrap(True)
        layout.addWidget(l)

        self.agree_cb = QtGui.QCheckBox("I agree to abide by the terms of the Quantiphyse license")
        self.agree_cb.stateChanged.connect(self.agree_changed)
        layout.addWidget(self.agree_cb)
        
        self.buttonBox = QtGui.QDialogButtonBox(QtGui.QDialogButtonBox.Ok|QtGui.QDialogButtonBox.Cancel)
        self.buttonBox.accepted.connect(self.accept)
        self.buttonBox.rejected.connect(self.reject)
        self.buttonBox.button(QtGui.QDialogButtonBox.Ok).setEnabled(False)
        layout.addWidget(self.buttonBox)

        self.setLayout(layout)
        self.setFixedSize(600, 600)

    def agree_changed(self, state):
        self.buttonBox.button(QtGui.QDialogButtonBox.Ok).setEnabled(state)

class ScaleEditDialog(QtGui.QDialog):
    """
    Dialog used by the view options to allow the user to edit the 
    scale of the 4th volume dimension
    """
    def __init__(self, parent=None, scale=[]):
        QtGui.QDialog.__init__(self, parent)
        
        vbox = QtGui.QVBoxLayout()
        label = QtGui.QLabel('<font size="5">Edit Scale</font>')
        vbox.addWidget(label)

        #paste_action = QtGui.QAction("Paste", self, triggered=self.paste)
        #paste_action.setShortcut(QtGui.QKeySequence.Paste)
        #paste_action.triggered.connect(self.paste)
        #self.menu = QtGui.QMenu(self.table)
        #self.menu.addAction(self.paste_action)
        #self.menu.exec_(QtGui.QCursor.pos())

        self.table = QtGui.QTableWidget()
        self.table.setRowCount(len(scale))
        self.table.setColumnCount(1)
        self.table.setHorizontalHeaderItem(0, QtGui.QTableWidgetItem("Scale position"))
        self.table.itemChanged.connect(self.changed)
        vbox.addWidget(self.table)

        self.buttonBox = QtGui.QDialogButtonBox(QtGui.QDialogButtonBox.Ok|QtGui.QDialogButtonBox.Cancel)
        self.buttonBox.accepted.connect(self.accept)
        self.buttonBox.rejected.connect(self.reject)
        vbox.addWidget(self.buttonBox)

        self.setLayout(vbox)

        self.set_scale(scale)
        shortcut = QtGui.QShortcut(QtGui.QKeySequence.Paste, self.table)
        shortcut.activated.connect(self.paste)

    def paste(self):
        clipboard = QtGui.QApplication.clipboard()
        text = clipboard.text()
        scale = text.strip().split(",")
        if len(scale) != self.table.rowCount():
            scale = text.strip().split()
        if len(scale) != self.table.rowCount():
            scale = text.strip().split("\t")
        if len(scale) == self.table.rowCount():
            try:
                self.set_scale([float(v) for v in scale])
            except:
                pass

    def changed(self):
        try:
            self.get_scale()
            self.buttonBox.button(QtGui.QDialogButtonBox.Ok).setEnabled(True)
        except:
            self.buttonBox.button(QtGui.QDialogButtonBox.Ok).setEnabled(False)

    def set_scale(self, scale):
        for r, v in enumerate(scale):
            self.table.setVerticalHeaderItem(r, QtGui.QTableWidgetItem("Volume %i" % r))
            self.table.setItem(r, 0, QtGui.QTableWidgetItem(str(v)))

    def get_scale(self):
        scale = []
        for r in range(self.table.rowCount()):
            scale.append(float(self.table.item(r, 0).text()))
        return scale

class ViewOptions(QtGui.QDialog):
    """
    This class is both a dialog to edit viewing options, but also
    the storage for the option values. For now this is convenient,
    however it will probably be necessary to separate the two 
    as the options become more extensive
    """
    SCALE_VOXELS = 0
    ISOTROPIC = 1

    RADIOLOGICAL = 0
    NEUROLOGICAL = 1
    
    OVERLAY_ON_TOP = 0
    ROI_ON_TOP = 1

    sig_options_changed = QtCore.Signal(object)

    def __init__(self, parent, ivm):
        super(ViewOptions, self).__init__(parent)
        self.setWindowTitle("View Options")
        #self.setFixedSize(300, 300)

        self.ivm = ivm
        self.ivm.sig_main_data.connect(self.vol_changed)

        # Options
        self.size_scaling = self.SCALE_VOXELS
        self.orientation = self.RADIOLOGICAL
        self.t_type = "Volume"
        self.t_unit = ""
        self.t_scale_type = 0
        self.t_res = 1.0
        self.t_scale = []
        self.display_order = self.ROI_ON_TOP

        grid = QtGui.QGridLayout()
        label = QtGui.QLabel('<font size="5">View Options</font>')
        grid.addWidget(label, 0, 0)

        grid.addWidget(QtGui.QLabel("Voxel size scaling"), 1, 0)
        c = QtGui.QComboBox()
        c.addItem("Use main volume dimensions")
        c.addItem("Display as isotropic")
        c.setCurrentIndex(self.size_scaling)
        c.currentIndexChanged.connect(self.voxel_scaling_changed)
        grid.addWidget(c, 1, 1)

        grid.addWidget(QtGui.QLabel("Orientation"), 2, 0)
        c = QtGui.QComboBox()
        c.addItem("Radiological (Right is Left)")
        c.addItem("Neurological (Left is Left)")
        c.setCurrentIndex(self.orientation)
        c.currentIndexChanged.connect(self.orientation_changed)
        grid.addWidget(c, 2, 1)

        grid.addWidget(QtGui.QLabel("4D Type"), 3, 0)
        self.t_type_edit = QtGui.QLineEdit(self.t_type)
        self.t_type_edit.editingFinished.connect(self.t_type_changed)
        grid.addWidget(self.t_type_edit, 3, 1)
        
        grid.addWidget(QtGui.QLabel("4D Unit"), 4, 0)
        self.t_unit_edit = QtGui.QLineEdit(self.t_unit)
        self.t_unit_edit.editingFinished.connect(self.t_unit_changed)
        grid.addWidget(self.t_unit_edit, 4, 1)
        
        grid.addWidget(QtGui.QLabel("4D Scale"), 5, 0)
        hbox = QtGui.QHBoxLayout()
        self.t_combo = QtGui.QComboBox()
        self.t_combo.addItem("Fixed resolution")
        self.t_combo.addItem("Labelled")
        self.t_combo.setCurrentIndex(self.t_scale_type)
        self.t_combo.currentIndexChanged.connect(self.t_combo_changed)
        hbox.addWidget(self.t_combo)

        self.t_res_edit = QtGui.QLineEdit(str(self.t_res))
        self.t_res_edit.editingFinished.connect(self.t_res_changed)
        hbox.addWidget(self.t_res_edit)

        self.t_btn = QtGui.QPushButton("Edit")
        self.t_btn.setVisible(False)
        self.t_btn.clicked.connect(self.edit_scale)
        hbox.addWidget(self.t_btn)
        grid.addLayout(hbox, 5, 1)

        grid.addWidget(QtGui.QLabel("Display order"), 6, 0)
        c = QtGui.QComboBox()
        c.addItem("Overlay on top")
        c.addItem("ROI on top")
        c.setCurrentIndex(self.display_order)
        c.currentIndexChanged.connect(self.zorder_changed)
        grid.addWidget(c, 6, 1)

        grid.setRowStretch(7, 1)
        self.setLayout(grid)

    def vol_changed(self, vol):
        """ 
        Do not signal 'options changed', even thought scale points may be updated. 
        The user has not changed any options, and widgets should update themselves 
        to the new volume by connecting to the volume changed signal
        """
        self.update_scale()

    def update_scale(self):
        """
        Update the list of scale points if we have a 4D volume. Always do this if
        we have a uniform scale, if not only do it if the number of points has
        changed (as a starting point for customisation)
        """
        if self.ivm.main is not None and self.ivm.main.ndim == 4 and \
           (self.t_scale_type == 0 or self.ivm.main.nvols != len(self.t_scale)):
            self.t_scale = [i*self.t_res for i in range(self.ivm.main.nvols)]

    def orientation_changed(self, idx):
        self.orientation = idx
        self.sig_options_changed.emit(self)

    def zorder_changed(self, idx):
        self.display_order = idx
        self.sig_options_changed.emit(self)

    def edit_scale(self):
        dlg = ScaleEditDialog(self, self.t_scale)
        if dlg.exec_():
            self.t_scale = dlg.get_scale()
        self.sig_options_changed.emit(self)

    def voxel_scaling_changed(self, idx):
        self.size_scaling = idx
        self.sig_options_changed.emit(self)

    def t_unit_changed(self):
        self.t_unit = self.t_unit_edit.text()
        self.sig_options_changed.emit(self)

    def t_type_changed(self):
        self.t_type = self.t_type_edit.text()
        self.sig_options_changed.emit(self)

    def t_res_changed(self):
        try:
            self.t_res = float(self.t_res_edit.text())
            self.update_scale()
            self.sig_options_changed.emit(self)
        except:
            traceback.print_exc()
            
    def t_combo_changed(self, idx):
        self.t_scale_type = idx
        self.t_btn.setVisible(idx == 1)
        self.t_res_edit.setVisible(idx == 0)
        self.update_scale()
        self.sig_options_changed.emit(self)

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
        self.widgets = []
        self.current_widget = None
        self.add_widget(OverviewWidget, default=True) 
        self.add_widget(SECurve, default=True)
        #self.add_widget(ModelCurves) 
        self.add_widget(OverlayStatistics, default=True) 
        self.add_widget(RoiAnalysisWidget) 
        self.add_widget(SimpleMathsWidget) 
        #self.add_widget(PharmaWidget) 
        #self.add_widget(T10Widget) 
        self.add_widget(PerfSlicWidget) 
        #self.add_widget(FabberWidget) 
        #self.add_widget(CESTWidget) 
        #self.add_widget(ASLWidget) 
        #self.add_widget(MeanValuesWidget) 
        self.add_widget(RegWidget) 
        ##self.add_widget(ImageExportWidget) 
        self.add_widget(CurveClusteringWidget, default=True) 
        self.add_widget(OvCurveClusteringWidget, default=True) 
        #self.add_widget(RoiBuilderWidget)
        
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
        self.setWindowTitle("Quantiphyse %s" % __version__)
        self.setWindowIcon(QtGui.QIcon(get_icon("main_icon.png")))
        self.resize(1000, 700)
        self.setUnifiedTitleAndToolBarOnMac(True)
        self.setAcceptDrops(True)
        self.show()

        settings = QtCore.QSettings()
        reg = settings.value("registered", 0)
        #reg = 0
        if not reg:
            dlg = RegisterDialog(self)
            res = dlg.exec_()
            if res:
                settings.setValue("registered", 1)
                send_register_email(dlg.name_edit.text(), dlg.inst_edit.text(), dlg.email_edit.text())
            else:
                self.close()
                QtCore.QCoreApplication.quit()

        # autoload any files that have been passed from the command line
        if load_data is not None: self.load_data(fname=load_data, ftype="DATA")
        if load_roi is not None: self.load_data(fname=load_roi, ftype="ROI")

    def init_tabs(self):
        self.tab_widget = FingerTabWidget(self)

        # Add widgets flagged to appear by default
        for idx, w in enumerate(self.widgets):
            if w.default:
                index = self.tab_widget.addTab(w, w.icon, w.tabname)
                w.init_ui()
                w.visible = True
                w.index = index
        self.tab_widget.currentChanged.connect(self.select_tab)
        self.select_tab(0)

    def add_widget(self, w, **kwargs):
	    self.widgets.append(w(ivm=self.ivm, ivl=self.ivl, opts=self.view_options_dlg, **kwargs))

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

        # File --> Save Overlay
        save_ovreg_action = QtGui.QAction(QtGui.QIcon.fromTheme("document-save"), '&Save current Overlay', self)
        save_ovreg_action.setStatusTip('Save current Overlay as a NIFTI file')
        save_ovreg_action.triggered.connect(self.save_data)
        save_ovreg_action.setShortcut('Ctrl+S')

        # File --> Save ROI
        save_roi_action = QtGui.QAction(QtGui.QIcon.fromTheme("document-save"), '&Save current ROI', self)
        save_roi_action.setStatusTip('Save current ROI as a NIFTI file')
        save_roi_action.triggered.connect(self.save_roi)

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

        menubar = self.menuBar()
        file_menu = menubar.addMenu('&File')
        widget_menu = menubar.addMenu('&Widgets')
        advanced_menu = menubar.addMenu('&Advanced')
        help_menu = menubar.addMenu('&Help')

        file_menu.addAction(load_action)
        file_menu.addAction(load_roi_action)
        file_menu.addAction(save_ovreg_action)
        file_menu.addAction(save_roi_action)
        file_menu.addAction(exit_action)

        for w in self.widgets:
            if not w.default:
                action = QtGui.QAction(w.icon, '&%s' % w.name, self)
                action.setStatusTip(w.description)
                action.widget = w
                action.triggered.connect(self.show_widget)
                widget_menu.addAction(action)

        help_menu.addAction(help_action)
        help_menu.addAction(about_action)

        advanced_menu.addAction(console_action)

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
                if op_sys == 'Darwin':
                    # OSx specific changes to allow drag and drop
                    filep = str(NSURL.URLWithString_(str(url.toString())).filePathURL().path())
                    fnames.append(filep)
                else:
                    fnames.append(str(url.toLocalFile()))
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
        <p align="center">Created by Benjamin Irving</p>
        <h2 align="center">Contributors</h2>
        <p align="center">Benjamin Irving</p>
        <p align="center">Martin Craig</p>
        <p align="center">Michael Chappell</p>
        """ % __version__
        QtGui.QMessageBox.about(self, "Quantiphyse", text)

    def show_console(self):
        """
        Creates a pop up console that allows interaction with the GUI and data
        Uses:
        pyqtgraph.console
        """
        # Places that the console has access to
        namespace = {'np': np, 'ivm': self.ivm, 'self': self}
        for name, ovl in self.ivm.data.items():
            namespace[name] = ovl
        for name, roi in self.ivm.rois.items():
            namespace[name] = roi

        text = (
            """
            ****** Quantiphyse Console ******

            This is a python console that allows interaction with the GUI data and running of scripts.

            Libraries already imported
              np: Numpy

            Access to data
              ivm: Access to all the stored image data

            """)
        self.con1 = pg.console.ConsoleWidget(namespace=namespace, text=text)
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

        # Get metadata for file - shape and data type so we can assess fit
        data = load(fname)

        # FIXME not doing this because a lot of ROIs seem to come in as float data? 
        #if ftype is None and issubclass(dtype.type, np.floating):
        #    # Floating point is assumed to be data (not ROI)
        #    print(dtype)
        #    ftype = "DATA"

        force_t_option = (data.ndim == 3)
        force_t = False
                
        ftype, name, ok, force_t_dialog = DragOptions.getImageChoice(self, fname, self.ivm, force_t_option=force_t_option)
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
            data.force_t()
        
        # Check for inappropriate ROI data
        if ftype == "ROI" and np.max(data.raw) > ROI_MAXVAL_WARN:
            msgBox = QtGui.QMessageBox()
            warntxt = "\n  -".join(warnings)
            msgBox.setText("Warning: ROI contains values larger than %i" % ROI_MAXVAL_WARN)
            msgBox.setInformativeText("Are you sure this is an ROI file?")
            msgBox.setStandardButtons(QtGui.QMessageBox.Yes | QtGui.QMessageBox.Cancel)
            msgBox.setDefaultButton(QtGui.QMessageBox.Cancel)
            if msgBox.exec_() != QtGui.QMessageBox.Yes: return

        if ftype == "DATA": 
            self.ivm.add_data(data, make_current=True)
        else:
            self.ivm.add_roi(data, make_current=True)

    def save_data(self):
        """
        Dialog for saving an data as a nifti file
        """
        if self.ivm.current_data is None:
            QtGui.QMessageBox.warning(self, "No data", "No current data to save", QtGui.QMessageBox.Close)
        else:
            fname, _ = QtGui.QFileDialog.getSaveFileName(self, 'Save file', dir=self.default_directory, filter="*.nii")
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
            fname, _ = QtGui.QFileDialog.getSaveFileName(self, 'Save file', dir=self.default_directory, filter="*.nii")
            if fname != '':
                save(self.ivm.current_roi, fname)
            else: # Cancelled
                pass

    def load_vol(self):
        self.load_data(ftype="DATA")

    def load_roi(self):
        self.load_data(ftype="ROI")

def my_catch_exceptions(type, value, tb):
    error_dialog(str(value), title="Error", detail=traceback.format_exception(type, value, tb))
        
"""
def get_run_batch(script):
    def run():
        print ("ok")
        run_batch(script)
    return run

import threading

class BatchThread(QtCore.QThread):

    def __init__(self, script):
        super(BatchThread, self).__init__()
        self.script = script

    def run(self):
        run_batch(self.script)
"""

def main():
    """
    Parse any input arguments and run the application
    """

    # Parse input arguments to pass info to GUI
    parser = argparse.ArgumentParser()
    parser.add_argument('--data', help='Load data file', default=None, type=str)
    parser.add_argument('--roi', help='Load ROI file', default=None, type=str)
    parser.add_argument('--batch', help='Run batch file', default=None, type=str)
    args = parser.parse_args()
    print(pg.systemInfo())

    # Check whether any batch processing arguments have been called
    if (args.batch is not None):
        #app = QtCore.QCoreApplication(sys.argv)
        #timer = threading.Timer(1, get_run_batch(args.batch))
        #timer.daemon = True
        #timer.start()
        #QtCore.QTimer.singleShot(0, get_run_batch(args.batch))
        #t = BatchThread(args.batch)
        #t.start()
        run_batch(args.batch)
        #sys.exit(app.exec_())
    else:
        app = QtGui.QApplication(sys.argv)
        QtCore.QCoreApplication.setOrganizationName("ibme-qubic")
        QtCore.QCoreApplication.setOrganizationDomain("eng.ox.ac.uk")
        QtCore.QCoreApplication.setApplicationName("Quantiphyse")
        sys.excepthook = my_catch_exceptions
        # Handle CTRL-C correctly
        signal.signal(signal.SIGINT, signal.SIG_DFL)

        # Set the local file path, used for finding icons, etc
        local_file_path = ""
        if hasattr(sys, 'frozen'):
            # File is frozen (packaged apps)
            print("Frozen executable")
            if hasattr(sys, '_MEIPASS'):
                local_file_path = sys._MEIPASS
            elif hasattr(sys, '_MEIPASS2'):
                local_file_path = sys._MEIPASS2
            elif sys.frozen == 'macosx_app':
                local_file_path = os.getcwd() + '/quantiphyse'
            else:
                local_file_path = os.path.dirname(sys.executable)
            os.environ["FABBERDIR"] = os.path.join(local_file_path, "fabber")
        else:
            # Running from a script
            local_file_path = os.path.dirname(__file__)
            
        if local_file_path == "":
            # Use local working directory otherwise
            warnings.warn("Reverting to current directory as local path")
            local_file_path = os.getcwd()

        print("Local directory: ", local_file_path)
        set_local_file_path(local_file_path)

        # OS specific changes
        if op_sys == 'Darwin':
            from Foundation import NSURL
            QtGui.QApplication.setGraphicsSystem('native')

        # Create window and start main loop
        app.setStyle('plastique') # windows, motif, cde, plastique, windowsxp, macintosh
        ex = MainWindow(load_data=args.data, load_roi=args.roi)
        sys.exit(app.exec_())

if __name__ == '__main__':
    main()
