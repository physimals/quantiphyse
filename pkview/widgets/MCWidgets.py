import os.path
import re
import numpy as np

from PySide import QtGui

from pkview.QtInherit import HelpButton
from pkview.QtInherit.dialogs import LogViewerDialog
from pkview.analysis import Process
from pkview.analysis.reg import RegProcess, McflirtProcess
from pkview.widgets import PkWidget

class McflirtInterface:
    def __init__(self):
        self.cost_models = {"Mutual information" : "mutualinfo",
                            "Woods" : "woods",
                            "Correlation ratio" : "corratio",
                            "Normalized correlation" : "normcorr",
                            "Normalized mutual information" : "normmi",
                            "Least squares" : "leastsquares"}
                            
        grid = QtGui.QGridLayout()

        grid.addWidget(QtGui.QLabel("Cost model"), 0, 0)
        self.cost_combo = QtGui.QComboBox()
        for name, opt in self.cost_models.items():
            self.cost_combo.addItem(name, opt)
        self.cost_combo.setCurrentIndex(self.cost_combo.findData("normcorr"))
        grid.addWidget(self.cost_combo, 0, 1)

        grid.addWidget(QtGui.QLabel("Number of search stages"), 3, 0)
        self.stages = QtGui.QComboBox()
        for i in range(1, 5):
            self.stages.addItem(str(i), i)
        self.stages.setCurrentIndex(2)
        grid.addWidget(self.stages, 3, 1)

        self.final_label = QtGui.QLabel("Final stage interpolation")
        grid.addWidget(self.final_label, 4, 0)
        self.final = QtGui.QComboBox()
        self.final.addItem("None", "")
        self.final.addItem("Sinc", "sinc_final")
        self.final.addItem("Spline", "spline_final")
        self.final.addItem("Nearest neighbour", "nn_final")
        grid.addWidget(self.final, 4, 1)

        grid.addWidget(QtGui.QLabel("Field of view (mm)"), 5, 0)
        self.fov = QtGui.QSpinBox()
        self.fov.setValue(20)
        self.fov.setMinimum(1)
        self.fov.setMaximum(100)
        grid.addWidget(self.fov, 5, 1)

        grid.addWidget(QtGui.QLabel("Number of bins"), 6, 0)
        self.num_bins = QtGui.QSpinBox()
        self.num_bins.setMinimum(1)
        self.num_bins.setMaximum(1000)
        self.num_bins.setValue(256)
        grid.addWidget(self.num_bins, 6, 1)

        grid.addWidget(QtGui.QLabel("Number of transform degrees of freedom"), 7, 0)
        self.num_dofs = QtGui.QSpinBox()
        self.num_dofs.setMinimum(6)
        self.num_dofs.setMaximum(12)
        self.num_dofs.setValue(6)
        grid.addWidget(self.num_dofs, 7, 1)

        grid.addWidget(QtGui.QLabel("Scaling"), 8, 0)
        self.scaling = QtGui.QDoubleSpinBox()
        self.scaling.setValue(6.0)
        self.scaling.setMinimum(0.1)
        self.scaling.setMaximum(10.0)
        self.scaling.setSingleStep(0.1)
        grid.addWidget(self.scaling, 8, 1)

        grid.addWidget(QtGui.QLabel("Smoothing in cost function"), 9, 0)
        self.smoothing = QtGui.QDoubleSpinBox()
        self.smoothing.setValue(1.0)
        self.smoothing.setMinimum(0.1)
        self.smoothing.setMaximum(10.0)
        self.smoothing.setSingleStep(0.1)
        grid.addWidget(self.smoothing, 9, 1)

        grid.addWidget(QtGui.QLabel("Scaling factor for rotation\noptimization tolerances"), 10, 0)
        self.rotation = QtGui.QDoubleSpinBox()
        self.rotation.setValue(1.0)
        self.rotation.setMinimum(0.1)
        self.rotation.setMaximum(10.0)
        self.rotation.setSingleStep(0.1)
        grid.addWidget(self.rotation, 10, 1)

        grid.addWidget(QtGui.QLabel("Search on gradient images"), 11, 0)
        self.gdt = QtGui.QCheckBox()
        grid.addWidget(self.gdt, 11, 1)

        self.options_layout = grid

    def getOptions(self):
        opts = {}
        opts["cost"] = self.cost_combo.itemData(self.cost_combo.currentIndex())
        opts["bins"] = self.num_bins.value()
        opts["dof"] = self.num_dofs.value()
        opts["scaling"] = self.scaling.value()
        opts["smooth"] = self.smoothing.value()
        opts["rotation"] = self.rotation.value()
        opts["stages"] = self.stages.itemData(self.stages.currentIndex())
        opts["fov"] = self.fov.value()
        if self.gdt.isChecked(): opts["gdt"] = ""

        final_interp = self.final.currentIndex()
        if final_interp != 0: opts[self.final.itemData(final_interp)] = ""

        for key, value in opts.items():
            print(key, value)
        return opts
        
class DeedsInterface:
    def __init__(self):
        grid = QtGui.QGridLayout()

        grid.addWidget(QtGui.QLabel("Regularisation parameter (alpha)"), 0, 0)
        self.alpha = QtGui.QDoubleSpinBox()
        self.alpha.setValue(2.0)
        self.alpha.setMinimum(0)
        self.alpha.setMaximum(10.0)
        self.alpha.setSingleStep(0.1)
        grid.addWidget(self.alpha, 0, 1)

        grid.addWidget(QtGui.QLabel("Num random samples per node"), 1, 0)
        self.randsamp = QtGui.QSpinBox()
        self.randsamp.setValue(50)
        self.randsamp.setMinimum(1)
        self.randsamp.setMaximum(100)
        grid.addWidget(self.randsamp, 1, 1)

        grid.addWidget(QtGui.QLabel("Number of levels"), 2, 0)
        self.levels = QtGui.QSpinBox()
        self.levels.setValue(5)
        self.levels.setMinimum(1)
        self.levels.setMaximum(10)
        grid.addWidget(self.levels, 2, 1)

        #grid.addWidget(QtGui.QLabel("Grid spacing for each level"), 3, 0)
        #self.spacing = QtGui.QLineEdit()
        #grid.addWidget(self.spacing, 3, 1)

        #grid.addWidget(QtGui.QLabel("Search radius for each level"),4, 0)
        #self.radius = QtGui.QLineEdit()
        #grid.addWidget(self.radius,4, 1)

        #grid.addWidget(QtGui.QLabel("Quantisation of search step size for each level"),5, 0)
        #self.radius = QtGui.QLineEdit()
        #grid.addWidget(self.radius,5, 1)

        #grid.addWidget(QtGui.QLabel("Use symmetric approach"),6, 0)
        #self.symm = QtGui.QCheckBox()
        #self.symm.setChecked(True)
        #grid.addWidget(self.symm,6, 1)

        self.options_layout = grid

    def getOptions(self):
        return {"alpha" : self.alpha.value(),
                "randsamp" : self.randsamp.value(),
                "levels" : self.levels.value()}
        
class RegWidget(PkWidget):
    """
    Generic registration / motion correction widget 
    """
    def __init__(self, **kwargs):
        super(RegWidget, self).__init__(name="Registration", icon="reg", desc="Registration and Motion Correction", **kwargs)

        self.ivm.sig_main_volume.connect(self.main_vol_changed)
        self.ivm.sig_all_overlays.connect(self.overlays_changed)

        self.reg_methods = {"DEEDS" : DeedsInterface(),
                            "MCFLIRT" : McflirtInterface()}

        layout = QtGui.QVBoxLayout()
        self.setLayout(layout)

        hbox = QtGui.QHBoxLayout()
        hbox.addWidget(QtGui.QLabel('<font size="5">Registration and Motion Correction</font>'))
        hbox.addStretch(1)
        hbox.addWidget(HelpButton(self, "reg"))
        layout.addLayout(hbox)

        hbox = QtGui.QHBoxLayout()
        
        hbox.addStretch(1)
        layout.addLayout(hbox)

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
        for name, impl in self.reg_methods.items():
            self.method_combo.addItem(name,impl)
        self.method_combo.currentIndexChanged.connect(self.method_changed)
        self.method_combo.setCurrentIndex(self.method_combo.findText("DEEDS"))
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
        
        grid.addWidget(QtGui.QLabel("Replace data"), 6, 0)
        self.replace_cb = QtGui.QCheckBox()
        self.replace_cb.stateChanged.connect(self.replace_changed)
        grid.addWidget(self.replace_cb, 6, 1)
        
        self.name_label = QtGui.QLabel("New data name")
        grid.addWidget(self.name_label, 7, 0)
        self.name_edit = QtGui.QLineEdit()
        grid.addWidget(self.name_edit, 7, 1)

        gbox.setLayout(grid)
        hbox.addWidget(gbox)
        hbox.addStretch(1)
        layout.addLayout(hbox)

        # Create the options boxes for reg methods - only one visible at a time!
        self.opt_boxes = {}
        for name, impl in self.reg_methods.items():
            hbox = QtGui.QHBoxLayout()
            opt_box = QtGui.QGroupBox()
            opt_box.setTitle("%s Options" % name)
            opt_box.setLayout(impl.options_layout)
            hbox.addWidget(opt_box)
            hbox.addStretch(1)
            opt_box.setVisible(False)
            layout.addLayout(hbox)
            self.opt_boxes[name] = opt_box

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

    def overlays_changed(self, ovls):
        self.update()

    def main_vol_changed(self, vol):
        self.update()

    def method_changed(self, idx):
        if idx >= 0:
            method_name = self.method_combo.currentText()
            self.method = self.reg_methods[method_name]
            for name, box in self.opt_boxes.items():
                box.setVisible(name == method_name)

    def mode_changed(self, idx):
        self.mode = idx
        if self.mode == 0:
            self.refdata_label.setText("Reference Data")
        else:
            self.refdata_label.setText("Moving Data")

        self.regdata_label.setVisible(self.mode == 0)
        self.regdata.setVisible(self.mode == 0)
        self.update() # Need to remove 3D overlays when doing Moco

    def refdata_changed(self, idx):
        if idx >= 0:
            vol = self.ivm.overlays[self.refdata.currentText()]
            self.refvol_label.setVisible(vol.ndim == 4)
            self.refvol.setVisible(vol.ndim == 4)
            if vol.ndim == 4:
                self.refidx.setMaximum(vol.shape[3]-1)
                self.refidx.setValue(int(vol.shape[3]/2))
            self.refvol_changed(self.refvol.currentIndex())
            if self.mode == 1: # MoCo
                self.name_edit.setText("%s_reg" % vol.name)

    def regdata_changed(self, idx):
        if idx >= 0 and self.mode == 0:
            self.name_edit.setText("%s_reg" % self.ivm.overlays[self.regdata.currentText()])

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
        vol = self.ivm.vol
        if vol is not None:
            self.refdata.addItem(vol.name)
            
        for ovl in self.ivm.overlays.values():
            if self.mode == 0 or ovl.ndim == 4: self.refdata.addItem(ovl.name)
            if ovl.ndim == 3: self.regdata.addItem(ovl.name)

        idx = self.refdata.findText(currentRef)
        self.refdata.setCurrentIndex(max(0, idx))
        idx = self.regdata.findText(currentReg)
        self.regdata.setCurrentIndex(max(0, idx))

    def run(self):
        options = self.method.getOptions()

        options["method"] = self.method_combo.currentText()
        options["output-name"] = self.name_edit.text()

        refdata = self.ivm.overlays[self.refdata.currentText()]
        if refdata.ndim == 4:
            refvol = self.refvol.currentIndex()
            if refvol == 0:
                options["ref-vol"] = "median"
            elif refvol == 1:
                options["ref-vol"] = "mean"
            elif refvol == 2:
                options["ref-vol"] = self.refidx.value()
        
        if self.mode_combo.currentIndex() == 0:
            options["ref"] = self.refdata.currentText()
            options["reg"] = self.regdata.currentText()
            process = RegProcess(self.ivm)
        else:
            options["reg"] = self.refdata.currentText()
            process = RegProcess(self.ivm)
        
        self.progress.setValue(0)
        self.runBtn.setEnabled(False)
        self.logBtn.setEnabled(False)
        process.sig_progress.connect(self.progress_cb)
        process.sig_finished.connect(self.finished_cb)
        process.run(options)

    def finished_cb(self, status, results, log):   
        self.log = log
        if status != Process.SUCCEEDED:
            QtGui.QMessageBox.warning(self, "Registration error", "Registration failed to run:\n\n" + str(results),
                                      QtGui.QMessageBox.Close)

        self.runBtn.setEnabled(True)
        self.logBtn.setEnabled(status == Process.SUCCEEDED)

    def progress_cb(self, complete):
        self.progress.setValue(100*complete)

    def view_log(self):
        self.logview = LogViewerDialog(self, title="Registration Log", log=self.log)
        self.logview.show()
        self.logview.raise_()
 