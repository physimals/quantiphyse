"""
Quantiphyse - Widgets for data registration and motion correction

Copyright (c) 2013-2018 University of Oxford
"""

import os.path
import re
import numpy as np

from PySide import QtGui

from quantiphyse.gui.widgets import QpWidget, HelpButton, RoiCombo, OverlayCombo, TitleWidget
from quantiphyse.gui.dialogs import TextViewerDialog

from quantiphyse.processes import Process

from quantiphyse.utils import debug, get_plugins, QpException

from .process import RegProcess, MocoProcess
    
class RegWidget(QpWidget):
    """
    Generic registration / motion correction widget 
    """
    def __init__(self, **kwargs):
        super(RegWidget, self).__init__(name="Registration", icon="reg", 
                                        desc="Registration and Motion Correction", 
                                        group="Processing", **kwargs)
        self.reg_methods = [c() for c in get_plugins("reg-methods")]

    def init_ui(self):
        layout = QtGui.QVBoxLayout()
        self.setLayout(layout)

        title = TitleWidget(self, title="Registration and Motion Correction", help="reg")
        layout.addWidget(title)

        if len(self.reg_methods) == 0:
            layout.addWidget(QtGui.QLabel("No registration methods found"))
            layout.addStretch(1)
            return

        hbox = QtGui.QHBoxLayout()
        gbox = QtGui.QGroupBox()
        gbox.setTitle("General Options")
        grid = QtGui.QGridLayout()

        grid.addWidget(QtGui.QLabel("Mode"), 0, 0)
        self.mode_combo = QtGui.QComboBox()
        self.mode_combo.addItem("Registration")
        self.mode_combo.addItem("Motion Correction")
        self.mode_combo.setCurrentIndex(0)
        self.mode_combo.currentIndexChanged.connect(self.mode_changed)
        grid.addWidget(self.mode_combo, 0, 1)

        grid.addWidget(QtGui.QLabel("Method"), 1, 0)
        self.method_combo = QtGui.QComboBox()
        for method in self.reg_methods:
            self.method_combo.addItem(method.name, method)
        self.method_combo.currentIndexChanged.connect(self.method_changed)
        self.method_combo.setCurrentIndex(self.method_combo.findText(self.reg_methods[0].name))
        grid.addWidget(self.method_combo, 1, 1)

        self.refdata_label = QtGui.QLabel("Reference data")
        grid.addWidget(self.refdata_label, 2, 0)
        self.refdata = QtGui.QComboBox()
        self.refdata.currentIndexChanged.connect(self.refdata_changed)
        grid.addWidget(self.refdata, 2, 1)
        
        self.refvol_label =QtGui.QLabel("Reference volume")
        grid.addWidget(self.refvol_label, 3, 0)
        self.refvol = QtGui.QComboBox()
        self.refvol.addItem("Middle volume")
        self.refvol.addItem("Mean volume")
        self.refvol.addItem("Specified volume")
        self.refvol.currentIndexChanged.connect(self.refvol_changed)
        grid.addWidget(self.refvol, 3, 1)

        self.refidx_label = QtGui.QLabel("Index of reference volume")
        self.refidx_label.setVisible(False)
        grid.addWidget(self.refidx_label, 4, 0)
        self.refidx = QtGui.QSpinBox()
        self.refidx.setMinimum(0)
        self.refidx.setVisible(False)
        grid.addWidget(self.refidx, 4, 1)

        self.regdata_label = QtGui.QLabel("Registration data")
        grid.addWidget(self.regdata_label, 5, 0)
        self.regdata = QtGui.QComboBox()
        self.regdata.currentIndexChanged.connect(self.regdata_changed)
        grid.addWidget(self.regdata, 5, 1)
        
        self.warproi_label = QtGui.QLabel("Linked ROI")
        grid.addWidget(self.warproi_label, 6, 0)
        self.warproi = RoiCombo(self.ivm, none_option=True)
        grid.addWidget(self.warproi, 6, 1)
        
        grid.addWidget(QtGui.QLabel("Replace data"), 7, 0)
        self.replace_cb = QtGui.QCheckBox()
        self.replace_cb.stateChanged.connect(self.replace_changed)
        grid.addWidget(self.replace_cb, 7, 1)
        
        self.name_label = QtGui.QLabel("New data name")
        grid.addWidget(self.name_label, 8, 0)
        self.name_edit = QtGui.QLineEdit()
        grid.addWidget(self.name_edit, 8, 1)

        gbox.setLayout(grid)
        hbox.addWidget(gbox)
        hbox.addStretch(1)
        layout.addLayout(hbox)

        # Create the options boxes for reg methods - only one visible at a time!
        self.opt_boxes = {}
        for method in self.reg_methods:
            hbox = QtGui.QHBoxLayout()
            opt_box = QtGui.QGroupBox()
            opt_box.setTitle(method.name.upper())
            opt_box.setLayout(method.interface())
            hbox.addWidget(opt_box)
            opt_box.setVisible(False)
            layout.addLayout(hbox)
            self.opt_boxes[method.name] = opt_box

        hbox = QtGui.QHBoxLayout()
        self.runBtn = QtGui.QPushButton('Run', self)
        self.runBtn.clicked.connect(self.run)
        hbox.addWidget(self.runBtn)
        self.progress = QtGui.QProgressBar(self)
        self.progress.setStatusTip('Be patient. Progress is only updated in chunks')
        hbox.addWidget(self.progress)
        self.logBtn = QtGui.QPushButton('View log', self)
        self.logBtn.clicked.connect(self.view_log)
        self.logBtn.setEnabled(False)
        hbox.addWidget(self.logBtn)
        layout.addLayout(hbox)

        layout.addStretch(1)

        self.mode = 0
        self.method_changed(0)

    def activate(self):
        if len(self.reg_methods) > 0:
            self.ivm.sig_main_data.connect(self.main_data_changed)
            self.ivm.sig_all_data.connect(self.data_changed)
            self.update()

    def deactivate(self):
        if len(self.reg_methods) > 0:
            self.ivm.sig_main_data.disconnect(self.main_data_changed)
            self.ivm.sig_all_data.disconnect(self.data_changed)

    def data_changed(self, ovls):
        self.update()

    def main_data_changed(self, vol):
        self.update()

    def method_changed(self, idx):
        if idx >= 0:
            self.method = self.method_combo.itemData(idx)
            for name, box in self.opt_boxes.items():
                box.setVisible(name == self.method.name)
        else:
            self.method = None

    def mode_changed(self, idx):
        self.mode = idx
        if self.mode == 0:
            self.refdata_label.setText("Reference Data")
        else:
            self.refdata_label.setText("Moving Data")

        self.regdata_label.setVisible(self.mode == 0)
        self.regdata.setVisible(self.mode == 0)
        self.update() # Need to remove 3D data when doing Moco

    def refdata_changed(self, idx):
        if idx >= 0:
            vol = self.ivm.data[self.refdata.currentText()]
            self.refvol_label.setVisible(vol.nvols > 1)
            self.refvol.setVisible(vol.nvols > 1)
            if vol.nvols > 1:
                self.refidx.setMaximum(vol.nvols-1)
                self.refidx.setValue(int(vol.nvols/2))
            self.refvol_changed(self.refvol.currentIndex())
            if self.mode == 1: # MoCo
                self.name_edit.setText("%s_reg" % vol.name)

    def regdata_changed(self, idx):
        if idx >= 0 and self.mode == 0:
            self.name_edit.setText("%s_reg" % self.ivm.data[self.regdata.currentText()].name)

    def refvol_changed(self, idx):
        self.refidx.setVisible(self.refvol.isVisible() and (idx == 2))
        self.refidx_label.setVisible(self.refvol.isVisible() and (idx == 2))

    def replace_changed(self):
        self.name_label.setVisible(not self.replace_cb.isChecked())
        self.name_edit.setVisible(not self.replace_cb.isChecked())

    def update(self):
        currentRef = self.refdata.currentText()
        currentReg = self.regdata.currentText()
        self.refdata.clear()
        self.regdata.clear()
            
        for ovl in self.ivm.data.values():
            if self.mode == 0 or ovl.nvols > 1: self.refdata.addItem(ovl.name)
            if ovl.nvols == 1: self.regdata.addItem(ovl.name)

        idx = self.refdata.findText(currentRef)
        self.refdata.setCurrentIndex(max(0, idx))
        idx = self.regdata.findText(currentReg)
        self.regdata.setCurrentIndex(max(0, idx))

    def batch_options(self):
        if self.method is None:
            raise QpException("No registration method has been chosen")

        refdata = self.ivm.data.get(self.refdata.currentText(), None)
        if refdata is None: raise QpException("Reference data not found: '%s'" % self.refdata.currentText())

        options = self.method.options()
        options["method"] = self.method.name
        options["output-name"] = self.name_edit.text()
        
        if refdata.nvols > 1:
            refvol = self.refvol.currentIndex()
            if refvol == 0:
                options["ref-vol"] = "median"
            elif refvol == 1:
                options["ref-vol"] = "mean"
            elif refvol == 2:
                options["ref-vol"] = self.refidx.value()
        
        if self.mode_combo.currentIndex() == 0:
            proc_name = "Reg"
            options["ref"] = self.refdata.currentText()
            options["reg"] = self.regdata.currentText()
            if self.warproi.currentText() != "<none>":
                options["warp-roi"] = self.warproi.currentText()
        else:
            proc_name = "MoCo"
            options["reg"] = self.refdata.currentText()
        return proc_name, options
        
    def run(self):
        options = self.batch_options()[1]
        process = RegProcess(self.ivm)
        self.progress.setValue(0)
        self.runBtn.setEnabled(False)
        self.logBtn.setEnabled(False)
        process.sig_progress.connect(self.progress_cb)
        process.sig_finished.connect(self.finished_cb)
        process.execute(options)

    def finished_cb(self, status, log, exception):   
        self.log = log
        if status != Process.SUCCEEDED:
            QtGui.QMessageBox.warning(self, "Registration error", "Registration failed to run:\n\n" + str(exception),
                                      QtGui.QMessageBox.Close)

        self.runBtn.setEnabled(True)
        self.logBtn.setEnabled(status == Process.SUCCEEDED)

    def progress_cb(self, complete):
        self.progress.setValue(100*complete)

    def view_log(self):
        self.logview = TextViewerDialog(self, title="Registration Log", text=self.log)
        self.logview.show()
        self.logview.raise_()
 
QP_WIDGETS = [RegWidget]
QP_PROCESSES = [RegProcess, MocoProcess]
