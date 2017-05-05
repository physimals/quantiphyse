"""
Author: Benjamin Irving (benjamin.irv@gmail.com)
Copyright (c) 2013-2015 University of Oxford, Benjamin Irving
"""

from __future__ import division, unicode_literals, print_function, absolute_import

import sys
import os
import platform
import argparse
import traceback
import requests
import warnings

from PySide import QtCore, QtGui
import pyqtgraph as pg
import pyqtgraph.console
import numpy as np

if sys.platform.startswith("darwin"):
    from Cocoa import NSURL

from pkview.QtInherit.dialogs import error_dialog

# required to use resources in theme. Check if 2 or 3.
if (sys.version_info > (3, 0)):
    from pkview.resources import resource_py2
else:
    from pkview.resources import resource_py3

from .QtInherit.FingerTabs import FingerTabBarWidget, FingerTabWidget

# My widgets
from ._version import __version__
from .ImageView import ImageView
from .widgets.AnalysisWidgets import SECurve, ColorOverlay1, RoiAnalysisWidget
from .widgets.ClusteringWidgets import CurveClusteringWidget
from .widgets.OvClusteringWidgets import OvCurveClusteringWidget
from .widgets.PharmaWidgets import PharmaWidget, PharmaView
from .widgets.T10Widgets import T10Widget
from .widgets.PerfSlicWidgets import MeanValuesWidget
from .widgets.PerfSlicWidgets import PerfSlicWidget
from .widgets.fabber import FabberWidget
from .widgets.MCWidgets import RegWidget
from .widgets.ExperimentalWidgets import ImageExportWidget
from .widgets.OverviewWidgets import OverviewWidget
from .volumes.volume_management import Volume, Overlay, Roi, ImageVolumeManagement
from .widgets.ExampleWidgets import ExampleWidget1

from .utils.batch import run_batch
from .utils import set_local_file_path, get_icon, get_local_file

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

    def __init__(self, parent, fname, ftype=None):
        super(DragOptions, self).__init__(parent)
        self.setWindowTitle("Load Data")

        layout = QtGui.QVBoxLayout()

        grid = QtGui.QGridLayout()
        grid.addWidget(QtGui.QLabel("File:"), 0, 0)
        grid.addWidget(QtGui.QLabel(fname), 0, 1)
        grid.addWidget(QtGui.QLabel("Name:"), 1, 0)
        self.name_combo = QtGui.QComboBox()
        def_name = os.path.split(fname)[1].split(".", 1)[0]
        for name in [def_name, 'MRI', 'T10', 'Ktrans', 'kep', 've', 'vp', 'model_curves', 'annotation']:
            self.name_combo.addItem(name)
        self.name_combo.setEditable(True)
        grid.addWidget(self.name_combo)
        layout.addLayout(grid)

        hbox = QtGui.QHBoxLayout()
        if ftype is None:
            btn = QtGui.QPushButton("Main data")
            btn.clicked.connect(self.clicked("MAIN"))
            hbox.addWidget(btn)
            btn = QtGui.QPushButton("ROI")
            btn.clicked.connect(self.clicked("ROI"))
            hbox.addWidget(btn)
            btn = QtGui.QPushButton("Overlay")
            btn.clicked.connect(self.clicked("OVERLAY"))
            hbox.addWidget(btn)
        else:
            btn = QtGui.QPushButton("Ok")
            btn.clicked.connect(self.clicked(ftype.upper()))
            hbox.addWidget(btn)
        btn = QtGui.QPushButton("Cancel")
        btn.clicked.connect(self.reject)
        hbox.addWidget(btn)
        layout.addLayout(hbox)

        self.setLayout(layout)
        self.but = ""
        self.name = ""

    def clicked(self, ret):
        def cb():
            self.but = ret
            self.name = self.name_combo.currentText()
            self.accept()
        return cb

    @staticmethod
    def getImageChoice(parent, fname, ftype=None):

        dialog = DragOptions(parent, fname, ftype)
        result = dialog.exec_()
        return dialog.but, dialog.name, result == QtGui.QDialog.Accepted

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
        lic_file = open(get_local_file("../licence.md"), "r")
        try:
            for line in lic_file:
                edit.append(line)
        finally:
            lic_file.close()
        edit.moveCursor (QtGui.QTextCursor.Start)
        edit.ensureCursorVisible()
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
        self.ivm.sig_main_volume.connect(self.vol_changed)

        # Options
        self.size_scaling = 0
        self.orientation = 0
        self.t_type = "Volume"
        self.t_unit = ""
        self.t_scale_type = 0
        self.t_res = 1.0
        self.t_scale = []
        self.display_order = 0

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
        if self.ivm.vol is not None and self.ivm.vol.ndim == 4 and \
           (self.t_scale_type == 0 or self.ivm.vol.shape[3] != len(self.t_scale)):
            self.t_scale = [i*self.t_res for i in range(self.ivm.vol.shape[3])]

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

class MainWindowWidget(QtGui.QWidget):
    """
    Main widget where most of the control should happen

    """
    def __init__(self):
        super(MainWindowWidget, self).__init__()

        # Create objects for volume and view management
        self.ivm = ImageVolumeManagement()
        self.view_options_dlg = ViewOptions(self, self.ivm)
        self.ivl = ImageView(self.ivm, self.view_options_dlg)
        self.ivl.sig_mouse_scroll.connect(self.slider_scroll_mouse)

        # ~~~~~~~~~~~~ Widgets ~~~~~~~~~~~~~~~~~~~~
        self.widgets = []

        # Signal Enhancement
        self.add_widget(OverviewWidget, default=True) 
        self.add_widget(SECurve, default=True)
        self.add_widget(PharmaView) 
        self.add_widget(ColorOverlay1, default=True) 
        self.add_widget(RoiAnalysisWidget) 
        self.add_widget(PharmaWidget) 
        self.add_widget(T10Widget) 
        self.add_widget(PerfSlicWidget) 
        self.add_widget(FabberWidget) 
        self.add_widget(MeanValuesWidget) 
        self.add_widget(RegWidget) 
        self.add_widget(ImageExportWidget) 
        self.add_widget(CurveClusteringWidget, default=True) 
        self.add_widget(OvCurveClusteringWidget, default=True) 
        
        self.initTabs()

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

        # connect sliders to ivl
        self.sld1.valueChanged[int].connect(self.ivl.set_space_pos(2))
        self.sld2.valueChanged[int].connect(self.ivl.set_space_pos(0))
        self.sld3.valueChanged[int].connect(self.ivl.set_space_pos(1))
        self.sld4.valueChanged[int].connect(self.ivl.set_time_pos)

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
        sld1.valueChanged.connect(self.ivl.roi_alpha_changed)
        grid.addWidget(sld1, 2, 1)
        grid.setRowStretch(3, 1)
        gBox.setLayout(grid)

        # Group box: sliders
        gBox2 = QtGui.QGroupBox("Navigation")
        gBoxlay2 = QtGui.QGridLayout()
        gBoxlay2.addWidget(QtGui.QLabel('Axial'), 0, 0)
        gBoxlay2.addWidget(self.sld1, 0, 1)
        gBoxlay2.addWidget(lab_p1, 0, 2)
        gBoxlay2.addWidget(QtGui.QLabel('Coronal'), 1, 0)
        gBoxlay2.addWidget(self.sld2, 1, 1)
        gBoxlay2.addWidget(lab_p2, 1, 2)
        gBoxlay2.addWidget(QtGui.QLabel('Sagittal'), 2, 0)
        gBoxlay2.addWidget(self.sld3, 2, 1)
        gBoxlay2.addWidget(lab_p3, 2, 2)
        gBoxlay2.addWidget(QtGui.QLabel('Volume'), 3, 0)
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
        sld1.valueChanged.connect(self.ivl.overlay_alpha_changed)
        grid.addWidget(sld1, 3, 1)
        grid.setRowStretch(4, 1)
        gBox3.setLayout(grid)

        # Navigation controls layout
        gBox_all = QtGui.QWidget()
        gBoxlay_all = QtGui.QHBoxLayout()
        gBoxlay_all.addWidget(gBox2)
        gBoxlay_all.addWidget(gBox)
        gBoxlay_all.addWidget(gBox3)
        
        # Data summary bar
        hbox = QtGui.QHBoxLayout()
        
        self.vol_name = QtGui.QLineEdit()
        p = self.vol_name.sizePolicy()
        p.setHorizontalPolicy(QtGui.QSizePolicy.Expanding)
        self.vol_name.setSizePolicy(p)
        hbox.addWidget(self.vol_name)
        hbox.setStretchFactor(self.vol_name, 1)
        self.vol_data = QtGui.QLineEdit()
        self.vol_data.setFixedWidth(60)
        hbox.addWidget(self.vol_data)
        self.roi_region = QtGui.QLineEdit()
        self.roi_region.setFixedWidth(30)
        hbox.addWidget(self.roi_region)
        self.ov_data = QtGui.QLineEdit()
        self.ov_data.setFixedWidth(60)
        hbox.addWidget(self.ov_data)
        self.view_options_btn = QtGui.QPushButton()
        self.view_options_btn.setIcon(QtGui.QIcon(get_icon("options.png")))
        self.view_options_btn.setFixedSize(24, 24)
        self.view_options_btn.clicked.connect(self.view_options)
        hbox.addWidget(self.view_options_btn)

        vbox = QtGui.QVBoxLayout()
        vbox.addLayout(hbox)
        vbox.addLayout(gBoxlay_all)  
        gBox_all.setLayout(vbox)  

        # Viewing window layout + buttons
        # Add a horizontal splitter between image viewer and buttons below
        #grid_box = QtGui.QWidget()
        # grid_box.sig_click.connect(self.mpe)
        #grid = QtGui.QVBoxLayout()
        splitter2 = QtGui.QSplitter(QtCore.Qt.Vertical)
        splitter2.addWidget(self.ivl)
        splitter2.addWidget(gBox_all)
        splitter2.setStretchFactor(0, 5)
        splitter2.setStretchFactor(1, 1)
        #grid.addWidget(splitter2)
        #grid_box.setLayout(grid)

        # Add a vertical splitter between main view and tabs
        hbox = QtGui.QHBoxLayout(self)
        splitter1 = QtGui.QSplitter(QtCore.Qt.Horizontal)
        splitter1.addWidget(splitter2)
        splitter1.addWidget(self.qtab1)
        splitter1.setStretchFactor(0, 4)
        splitter1.setStretchFactor(1, 1)
        hbox.addWidget(splitter1)

        # horizontal widgets
        self.setLayout(hbox)

    def add_widget(self, w, **kwargs):
	    self.widgets.append(w(ivm=self.ivm, ivl=self.ivl, opts=self.view_options_dlg, **kwargs))

    def view_options(self):
        self.view_options_dlg.show()
        self.view_options_dlg.raise_()
        
    def overlay_changed(self, idx):
        if idx >= 0:
            ov = self.overlay_combo.itemText(idx)
            self.ivm.set_current_overlay(ov, signal=True)

    def update_current_overlay(self, overlay):
        if overlay is None:
            self.overlay_combo.setCurrentIndex(-1)
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
        self.ivl.set_overlay_view(view, roiOnly)

    def roi_view_changed(self, idx):
        shade = idx in (0, 2)
        contour = idx in (1, 2)
        self.ivl.set_roi_view(shade, contour)

    def overlay_cmap_changed(self, idx):
        cmap = self.ov_cmap_combo.itemText(idx)
        self.ivl.h2.setGradientName(cmap)

    def initTabs(self):
        """
        Initialise the tab widget
        """
        self.qtab1 = FingerTabWidget(self)

        # Add widgets flagged to appear by default
        for idx, w in enumerate(self.widgets):
            if w.default:
                index = self.qtab1.addTab(w, w.icon, w.tabname)
                w.init()
                w.activate()
                w.visible = True
                w.index = index
                
    def update_slider_range(self):
        try:
            self.sld1.blockSignals(True)
            self.sld2.blockSignals(True)
            self.sld3.blockSignals(True)
            self.sld4.blockSignals(True)
            self.sld1.setRange(0, self.ivm.vol.shape[2]-1)
            self.sld2.setRange(0, self.ivm.vol.shape[0]-1)
            self.sld3.setRange(0, self.ivm.vol.shape[1]-1)

            if self.ivm.vol.ndim == 4:
                self.sld4.setRange(0, self.ivm.vol.shape[3]-1)
            else:
                self.sld4.setRange(0, 0)
        finally:
            self.sld1.blockSignals(False)
            self.sld2.blockSignals(False)
            self.sld3.blockSignals(False)
            self.sld4.blockSignals(False)

    @QtCore.Slot(bool)
    def slider_scroll_mouse(self, value=None):
        # update slider positions
        self.sld1.setValue(self.ivm.cim_pos[2])
        self.sld2.setValue(self.ivm.cim_pos[0])
        self.sld3.setValue(self.ivm.cim_pos[1])
        if self.ivm.vol.ndim == 4:
            self.sld4.setValue(self.ivm.cim_pos[3])
        else:
            self.sld4.setValue(0)
        if self.ivm.vol is not None: 
            self.vol_data.setText(self.ivm.vol.value_str(self.ivm.cim_pos))
        if self.ivm.current_roi is not None: 
            self.roi_region.setText(self.ivm.current_roi.value_str(self.ivm.cim_pos))
        if self.ivm.current_overlay is not None: 
            self.ov_data.setText(self.ivm.current_overlay.value_str(self.ivm.cim_pos))
            
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
                local_file_path = sys._MEIPASS
            elif hasattr(sys, '_MEIPASS2'):
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

        self.show()

        settings = QtCore.QSettings()
        reg = settings.value("registered", 0)
        if not reg:
            dlg = RegisterDialog(self)
            res = dlg.exec_()
            if res:
                settings.setValue("registered", 1)
                send_register_email(dlg.name_edit.text(), dlg.inst_edit.text(), dlg.email_edit.text())
            else:
                self.close()
                QtCore.QCoreApplication.quit()

    def init_ui(self):
        """
        Called during init. Sets the size and title of the overall GUI
        :return:
        """
        self.resize(1000, 700)
        self.setCentralWidget(self.mw1)
        self.setWindowTitle("Quantiphyse %s" % __version__)
        self.setWindowIcon(QtGui.QIcon(get_icon("main_icon.png")))
        self.menu_ui()

        # OSx specific enhancments
        self.setUnifiedTitleAndToolBarOnMac(True)

    def show_widget(self):
        w = self.sender().widget
        if not w.visible:
            index = self.mw1.qtab1.addTab(w, w.icon, w.tabname)
            w.init()
            w.activate()
            w.visible = True
            w.index = index
        self.mw1.qtab1.setCurrentIndex(w.index)

    def menu_ui(self):
        """
        Set up the file menu system and the toolbar at the top
        :return:
        """
        
        # File --> Load Image
        load_action = QtGui.QAction(QtGui.QIcon(get_icon("picture")), '&Load Image Volume', self)
        load_action.setShortcut('Ctrl+L')
        load_action.setStatusTip('Load a 3d or 4d image')
        load_action.triggered.connect(self.load_volume)

        # File --> Load ROI
        load_roi_action = QtGui.QAction(QtGui.QIcon(get_icon("pencil")), '&Load ROI', self)
        load_roi_action.setStatusTip('Load binary ROI')
        load_roi_action.triggered.connect(self.load_roi)

        # File --> Load Overlay
        load_ovreg_action = QtGui.QAction(QtGui.QIcon(get_icon("edit")), '&Load Overlay', self)
        load_ovreg_action.setStatusTip('Load overlay')
        load_ovreg_action.triggered.connect(self.load_overlay)

        # File --> Save Overlay
        save_ovreg_action = QtGui.QAction(QtGui.QIcon.fromTheme("document-save"), '&Save Current Overlay', self)
        save_ovreg_action.setStatusTip('Save Current Overlay as a nifti file')
        save_ovreg_action.triggered.connect(self.save_overlay)
        save_ovreg_action.setShortcut('Ctrl+S')

        # File --> Exit
        exit_action = QtGui.QAction(QtGui.QIcon.fromTheme("application-exit"), '&Exit', self)
        exit_action.setShortcut('Ctrl+Q')
        exit_action.setStatusTip('Exit Application')
        exit_action.triggered.connect(self.close)

        # About
        about_action = QtGui.QAction(QtGui.QIcon.fromTheme("help-about"), '&About', self)
        about_action.setStatusTip('About Quantiphyse')
        about_action.triggered.connect(self.about)

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
        widget_menu = menubar.addMenu('&Widgets')
        advanced_menu = menubar.addMenu('&Advanced')
        help_menu = menubar.addMenu('&Help')

        file_menu.addAction(load_action)
        file_menu.addAction(load_roi_action)
        file_menu.addAction(load_ovreg_action)
        file_menu.addAction(save_ovreg_action)
        file_menu.addAction(exit_action)

        for w in self.mw1.widgets:
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
            for name in fname:
                # Signal that a file has been dropped
                self.sig_dropped.emit(name)
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
    def about(self):
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
            ****** Quantiphyse Console ******

            This is a python console that allows interaction with the GUI data and running of scripts.

            Libraries already imported
            np: Numpy

            Access to data
            mw1: Access to the main window
            ivm: Access to all the stored image data

            """)
        self.con1 = pg.console.ConsoleWidget(namespace=namespace, text=text)
        self.con1.setWindowTitle('Quantiphyse Console')
        self.con1.setGeometry(QtCore.QRect(100, 100, 600, 600))
        self.con1.show()

    # Dialogs

    def load_volume(self, fname=None):
        """
        Dialog for loading a file
        @fname: allows a file name to be passed in automatically
        """
        if fname is None:
            fname, _ = QtGui.QFileDialog.getOpenFileName(self, 'Open file', self.default_directory)

        if fname != '':
            self.load_main(fname)

    # def show_annot_load_dialog(self, checked):
    #     """
    #     Annotation dialog
    #     """
    #
    #     if checked:
    #         self.mw1.ivm.set_blank_annotation()
    #         self.mw1.ivl.load_ovreg()
    #         self.mw1.ivl.enable_drawing(color1=1)
    #     else:
    #         self.mw1.ivl.enable_drawing(color1=-1)

    def load_roi(self, fname=None, name=None):
        """
        Dialog for loading a file
        @fname: allows a file name to be passed in automatically
        """
        if fname is None:
            fname, _ = QtGui.QFileDialog.getOpenFileName(self, 'Open file', self.default_directory)
            if not fname: return

        if name is None:
            name = os.path.split(fname)[1].split(".", 1)[0]
        
        self.default_directory = get_dir(fname)
        
        try:
            self.mw1.ivm.add_roi(Roi(name, fname=fname), make_current=True)
        except:
            # Try again, ignoring file transformation
            if self.mw1.ivm.vol:
                print("Failed shape check, try again with volume affine")
                self.mw1.ivm.add_roi(Roi(name, fname=fname, affine=self.mw1.ivm.vol.affine), make_current=True)
            else:
                raise

    def load_overlay(self, fname=None, name=None):
        """
        Dialog for loading an overlay and specifying the type of overlay
        @fname: allows a file name to be passed in automatically
        @name: allows overlay name to be passed automatically
        """
        if fname is None:
            fname, _ = QtGui.QFileDialog.getOpenFileName(self, 'Open file', self.default_directory)
            if not fname: return

        if name is None:
            ftype, name, ok = DragOptions.getImageChoice(self, fname, ftype="OVERLAY")
            if not ok: return

        self.default_directory = get_dir(fname)
        
        try:
            self.mw1.ivm.add_overlay(Overlay(name, fname=fname), make_current=True)
        except:
            # Try again, ignoring file transformation
            if self.mw1.ivm.vol:
                print("Failed shape check, try again with volume affine")
                self.mw1.ivm.add_overlay(Overlay(name, fname=fname, affine=self.mw1.ivm.vol.affine), make_current=True)
            else:
                raise

    def save_overlay(self):
        """
        Dialog for saving an overlay as a nifti file
        """
        if self.mw1.ivm.current_overlay is None:
            QtGui.QMessageBox.warning(self, "No overlay", "No current overlay to save", QtGui.QMessageBox.Close)
        else:
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
        """
        self.raise_()
        self.activateWindow()
        ftype, name, ok = DragOptions.getImageChoice(self, fname)
        if not ok: return

        # Remember load directory
        self.default_directory = get_dir(fname)

        if ftype == 'MAIN':
            self.load_main(fname)
        elif ftype == 'OVERLAY':
            self.load_overlay(fname, name)
        elif ftype == 'ROI':
            self.load_roi(fname, name)

    def load_main(self, fname):
        vol = Volume(os.path.basename(fname), fname=fname)
        ndim = vol.ndim
        if vol.ndim == 2:
            multi = False
            ndim = 3
        if vol.ndim == 3:
            # 3D volume loaded - is it 2d + time or static 3d?
            msgBox = QtGui.QMessageBox()
            msgBox.setText("3D volume loaded")
            msgBox.setInformativeText("Choose image type")
            msgBox.addButton("Single 3D volume", QtGui.QMessageBox.NoRole)
            msgBox.addButton("Multiple 2D volumes", QtGui.QMessageBox.YesRole)
            msgBox.setDefaultButton(QtGui.QMessageBox.Yes)
            ret = msgBox.exec_()
            if ret == QtGui.QDialog.Accepted:
                ndim = 4
        elif vol.ndim != 4:
            error_dialog("Quantiphyse supports 2D and 3D volumes with one optional additional dimension only", "Error")
            return

        vol.force_ndim(ndim, multi=(ndim == 4))
        
        try:
            self.mw1.ivm.check_shape(vol.shape)
        except:
            # Data already exists and shape is not consistent
            msgBox = QtGui.QMessageBox()
            msgBox.setText("A different shaped volume has already been loaded")
            msgBox.setInformativeText("Do you want to clear all data and load this new volume?")
            msgBox.setStandardButtons(QtGui.QMessageBox.Ok | QtGui.QMessageBox.Cancel)
            msgBox.setDefaultButton(QtGui.QMessageBox.Ok)
            ret = msgBox.exec_()
        
            if ret == QtGui.QMessageBox.Ok:
                self.mw1.ivm.reset()
            else:
                return

        self.mw1.ivm.add_overlay(vol, make_main=True)
        print("Image dimensions: ", self.mw1.ivm.shape)
        print("Voxel size: ", self.mw1.ivm.voxel_sizes)
        print("Image range: ", self.mw1.ivm.vol.range)
        self.mw1.vol_name.setText(fname)
        self.mw1.update_slider_range()
        self.mw1.slider_scroll_mouse()

    def auto_load_files(self):
        """
        Check to see if any input directories have been passed from the terminal for auto loading and loads those images
        """

        if self.image_dir_in is not None:
            self.load_volume(fname=self.image_dir_in)
        if self.roi_dir_in is not None:
            self.load_roi(fname=self.roi_dir_in)
        if self.overlay_dir_in is not None:
            self.load_overlay(fname=self.overlay_dir_in, name=self.overlay_type_in)

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

    # current_folder = args_in.pop(0)

    # Parse input arguments to pass info to GUI
    parser = argparse.ArgumentParser()
    parser.add_argument('--image', help='main image nifti file location', default=None, type=str)
    parser.add_argument('--roi', help='ROI nifti file location', default=None, type=str)
    parser.add_argument('--overlay', help='Overlay nifti file location', default=None, type=str)
    parser.add_argument('--overlaytype', help='Type of overlay', default=None, type=str)
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
        # Initialise the application
        app = QtGui.QApplication(sys.argv)
        QtCore.QCoreApplication.setOrganizationName("ibme-qubic")
        QtCore.QCoreApplication.setOrganizationDomain("eng.ox.ac.uk")
        QtCore.QCoreApplication.setApplicationName("Quantiphyse")
        # Initialise main GUI
        sys.excepthook = my_catch_exceptions

        # OSx specific Changes
        if op_sys == 'Darwin':
            from Foundation import NSURL
            QtGui.QApplication.setGraphicsSystem('native')

        app.setStyle('plastique')  # windows, motif, cde, plastique, windowsxp, macintosh

        # Pass arguments from the terminal (if any) into the main application
        ex = WindowAndDecorators(args.image, args.roi, args.overlay, args.overlaytype)

        sys.exit(app.exec_())

if __name__ == '__main__':
    main()
