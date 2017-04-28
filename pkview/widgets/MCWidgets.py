import os.path
import re
import numpy as np

from PySide import QtGui

from pkview.QtInherit.dialogs import LogViewerDialog
from pkview.analysis import Process
from pkview.analysis.reg import MocoProcess, RegProcess, McflirtProcess
from pkview.volumes.volume_management import Volume, Overlay
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
        super(RegWidget, self).__init__(name="Registration", icon="mcflirt", desc="Registration and Motion Correction", **kwargs)

        self.ivm.sig_main_volume.connect(self.main_vol_changed)

        self.reg_methods = {"DEEDS" : DeedsInterface(),
                            "MCFLIRT" : McflirtInterface()}

        layout = QtGui.QVBoxLayout()
        self.setLayout(layout)

        layout.addWidget(QtGui.QLabel("<font size=5>Registration and Motion Correction</font>"))

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
        self.method_combo.setCurrentIndex(self.method_combo.findText("DEEDS"))
        self.method_combo.currentIndexChanged.connect(self.method_changed)
        grid.addWidget(self.method_combo, 1, 1)

        self.refdata_label = QtGui.QLabel("Reference data")
        grid.addWidget(self.refdata_label, 2, 0)
        self.refdata = QtGui.QComboBox()
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
        grid.addWidget(self.regdata, 5, 1)
        
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

        self.set_method("DEEDS")

    def main_vol_changed(self, vol):
        self.update_refdata()

    def method_changed(self, idx):
        if idx >= 0:
            self.set_method(self.method_combo.currentText())

    def mode_changed(self, idx):
        if idx == 0:
            self.refdata_label.setText("Reference Data")
        else:
            self.refdata_label.setText("Moving Data")

        self.regdata_label.setVisible(idx == 0)
        self.regdata.setVisible(idx == 0)

    def update_refdata(self):
        self.refdata.clear()
        vol = self.ivm.vol
        if vol is not None:
            self.refdata.addItem(vol.name, vol)
            self.refdata_changed(0)

    def update_regdata(self):
        self.regdata.clear()
        vol = self.ivm.vol
        if vol is not None:
            self.regdata.addItem(vol.name, vol)

    def set_method(self, method_name):
        self.method = self.reg_methods[method_name]
        for name, box in self.opt_boxes.items():
            box.setVisible(name == method_name)

    def refdata_changed(self, idx):
        if idx >= 0:
            vol = self.refdata.itemData(idx)
            self.refvol_label.setVisible(vol.ndims == 4)
            self.refvol.setVisible(vol.ndims == 4)
            if vol.ndims == 4:
                self.refidx.setMaximum(vol.shape[3]-1)
                self.refidx.setValue(int(vol.shape[3]/2))
                self.refvol_changed(self.refvol.currentIndex())

    def refvol_changed(self, idx):
        self.refidx.setVisible(self.refvol.isVisible() and (idx == 2))
        self.refidx_label.setVisible(self.refvol.isVisible() and (idx == 2))

    def run(self):
        options = self.method.getOptions()

        # FIXME just using main volume for now
        #refvol = self.refdata.itemData(self.refdata.currentIndex())
        options["method"] = self.method_combo.currentText()
        if self.ivm.vol.ndims == 4:
            refvol = self.refvol.currentIndex()
            if refvol == 0:
                options["ref-vol"] = "median"
            elif refvol == 1:
                options["ref-vol"] = "mean"
            elif refvol == 2:
                options["ref-vol"] = self.refidx.value()
        
        if self.mode_combo.currentIndex() == 0:
            raise RuntimeError("Registration not implemented yet")
        elif options["method"] == "MCFLIRT":
            # MCFLIRT requires a different approach (because it's MOCO only, not general reg)
            options.pop("method")
            process = McflirtProcess(self.ivm)
        else:
            process = MocoProcess(self.ivm)
        
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
 