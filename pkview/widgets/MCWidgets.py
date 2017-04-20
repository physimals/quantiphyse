import os.path
import re
import numpy as np

from PySide import QtGui

from pkview.analysis.mcflirt import mcflirt
from pkview.volumes.volume_management import Overlay
from pkview.widgets import PkWidget

# MCflirt options!
"""
       << "        -out, -o <outfile>               (default is infile_mcf)\n"
       << "        -cost {mutualinfo,woods,corratio,normcorr,normmi,leastsquares}        (default is normcorr)\n"
       << "        -bins <number of histogram bins>   (default is "
       << no_bins << ")\n"
       << "        -dof  <number of transform dofs>   (default is "
       << dof << ")\n"
       << "        -refvol <number of reference volume> (default is no_vols/2)- registers to (n+1)th volume in series\n"
       << "        -reffile, -r <filename>            use a separate 3d image file as the target for registration (overrides refvol option)\n"
       << "        -scaling <num>                             (6.0 is default)\n"
       << "        -smooth <num>                      (1.0 is default - controls smoothing in cost function)\n"
       << "        -rotation <num>                    specify scaling factor for rotation optimization tolerances\n"
       << "        -verbose <num>                     (0 is least and default)\n"
       << "        -stages <number of search levels>  (default is "
       << no_stages << " - specify 4 for final sinc interpolation)\n"
       << "        -fov <num>                         (default is 20mm - specify size of field of view when padding 2d volume)\n"
       << "        -2d                                Force padding of volume\n"
       << "        -sinc_final                        (applies final transformations using sinc interpolation)\n"
       << "        -spline_final                      (applies final transformations using spline interpolation)\n"
       << "        -nn_final                          (applies final transformations using Nearest Neighbour interpolation)\n"
       << "        -init <filename>                   (initial transform matrix to apply to all vols)\n"
       << "        -gdt                               (run search on gradient images)\n"
       << "        -meanvol                           register timeseries to mean volume (overrides refvol and reffile options)\n"
       << "        -stats                             produce variance and std. dev. images\n"
       << "        -mats                              save transformation matricies in subdirectory outfilename.mat\n"
       << "        -plots                             save transformation parameters in file outputfilename.par\n"
       << "        -report                            report progress to screen\n"
       << "        -help\n";
"""

class MCFlirtWidget(PkWidget):
    """
    Run MCFLIRT motion correction on an input volume
    """
    def __init__(self, **kwargs):
        super(MCFlirtWidget, self).__init__(name="MCFLIRT", icon="mcflirt", desc="MCFLIRT motion correction", **kwargs)

        self.ivm.sig_main_volume.connect(self.main_vol_changed)

        self.cost_models = {"Mutual information" : "mutualinfo",
                            "Woods" : "woods",
                            "Correlation ratio" : "corratio",
                            "Normalized correlation" : "normcorr",
                            "Normalized mutual information" : "normmi",
                            "Least squares" : "leastsquares"}

        layout = QtGui.QVBoxLayout()
        self.setLayout(layout)

        layout.addWidget(QtGui.QLabel("<font size=5>MCFlirt motion correction</font>"))

        hbox = QtGui.QHBoxLayout()
        gbox = QtGui.QGroupBox()
        gbox.setTitle("Options")
        grid = QtGui.QGridLayout()

        grid.addWidget(QtGui.QLabel("Cost model"), 0, 0)
        self.cost_combo = QtGui.QComboBox()
        for name, opt in self.cost_models.items():
            self.cost_combo.addItem(name, opt)
        self.cost_combo.setCurrentIndex(self.cost_combo.findData("normcorr"))
        grid.addWidget(self.cost_combo, 0, 1)

        grid.addWidget(QtGui.QLabel("Reference volume"), 1, 0)
        self.ref = QtGui.QComboBox()
        self.ref.addItem("Middle volume")
        self.ref.addItem("Mean volume")
        self.ref.addItem("Specified volume")
        self.ref.currentIndexChanged.connect(self.ref_changed)
        grid.addWidget(self.ref, 1, 1)

        self.refvol_label = QtGui.QLabel("Time index of reference volume")
        self.refvol_label.setVisible(False)
        grid.addWidget(self.refvol_label, 2, 0)
        self.refvol = QtGui.QSpinBox()
        self.refvol.setMinimum(0)
        self.refvol.setVisible(False)
        grid.addWidget(self.refvol, 2, 1)

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

        gbox.setLayout(grid)
        hbox.addWidget(gbox)
        hbox.addStretch(1)
        layout.addLayout(hbox)

        hbox = QtGui.QHBoxLayout()
        self.run = QtGui.QPushButton('Run MCFlirt', self)
        self.run.clicked.connect(self.run_mcflirt)
        hbox.addWidget(self.run)
        hbox.addStretch(1)
        layout.addLayout(hbox)

        layout.addStretch(1)

    def main_vol_changed(self, vol):
        if vol is not None and len(vol.shape) == 4:
            self.refvol.setMaximum(vol.shape[3]-1)
            self.refvol.setValue(int(vol.shape[3]/2))

    def ref_changed(self, idx):
        self.refvol.setVisible(idx == 2)
        self.refvol_label.setVisible(idx == 2)

    def run_mcflirt(self):
        if self.ivm.vol is None:
            QtGui.QMessageBox.warning(self, "No volume", "Load a volume before running motion correction", QtGui.QMessageBox.Close)
            return

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

        ref = self.ref.currentIndex()
        if ref == 1:
            opts["meanvol"] = ""
        elif ref == 2:
            opts["refvol"] = self.refvol.value()

        for key, value in opts.items():
            print(key, value)

        corvol = mcflirt(self.ivm.vol.data, self.ivm.vol.voxel_sizes, **opts)
        self.ivm.add_overlay(Overlay(name="Motion corrected", data=corvol), make_current=True)
