import os.path
import re
import numpy as np

from PySide import QtGui

from pkview.analysis.mcflirt import mcflirt
from pkview.volumes.volume_management import Overlay

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

class MCFlirtWidget(QtGui.QWidget):
    """
    Run MCFLIRT motion correction on an input volume
    """
    def __init__(self):
        super(MCFlirtWidget, self).__init__()

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
        grid.addWidget(self.cost_combo, 0, 1)

        grid.addWidget(QtGui.QLabel("Number of bins"), 1, 0)
        self.num_bins = QtGui.QLineEdit("256")
        grid.addWidget(self.num_bins, 1, 1)

        grid.addWidget(QtGui.QLabel("Number of transform dofs"), 2, 0)
        self.num_dofs = QtGui.QLineEdit("6")
        grid.addWidget(self.num_dofs, 2, 1)

        grid.addWidget(QtGui.QLabel("Number of reference volume"), 4, 0)
        self.refvol = QtGui.QLineEdit("0")
        grid.addWidget(self.refvol, 4, 1)

        grid.addWidget(QtGui.QLabel("Scaling"), 5, 0)
        self.scaling = QtGui.QLineEdit("6")
        grid.addWidget(self.scaling, 5, 1)

        grid.addWidget(QtGui.QLabel("Smoothing in cost function"), 6, 0)
        self.smoothing = QtGui.QLineEdit("1")
        grid.addWidget(self.smoothing, 6, 1)

        grid.addWidget(QtGui.QLabel("Scaling factor for rotation\noptimization tolerances"), 7, 0)
        self.rotation = QtGui.QLineEdit("1")
        grid.addWidget(self.rotation, 7, 1)

        grid.addWidget(QtGui.QLabel("Number of search stages"), 8, 0)
        self.stages = QtGui.QLineEdit("3")
        grid.addWidget(self.stages, 8, 1)

        grid.addWidget(QtGui.QLabel("Field of view (mm)"), 9, 0)
        self.fov = QtGui.QLineEdit("20")
        grid.addWidget(self.fov, 9, 1)

        grid.addWidget(QtGui.QLabel("Sinc interpolation"), 10, 0)
        self.sinc = QtGui.QCheckBox()
        grid.addWidget(self.sinc, 10, 1)

        grid.addWidget(QtGui.QLabel("Spline interpolation"), 11, 0)
        self.spline = QtGui.QCheckBox()
        grid.addWidget(self.spline, 11, 1)

        grid.addWidget(QtGui.QLabel("Nearest-neighbour interpolation"), 12, 0)
        self.nn = QtGui.QCheckBox()
        grid.addWidget(self.nn, 12, 1)

        grid.addWidget(QtGui.QLabel("Search on gradient images"), 13, 0)
        self.gdt = QtGui.QCheckBox()
        grid.addWidget(self.gdt, 13, 1)

        grid.addWidget(QtGui.QLabel("Register to mean volume"), 14, 0)
        self.meanvol = QtGui.QCheckBox()
        grid.addWidget(self.meanvol, 14, 1)

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

    def add_image_management(self, image_vol_management):
        """
        Adding image management
        """
        self.ivm = image_vol_management
        self.ivm.sig_main_volume.connect(self.main_vol_changed)

    def main_vol_changed(self, vol):
        self.refvol.setText(str(int(vol.shape[3]/2)))

    def run_mcflirt(self):
        if self.ivm.vol is None:
            QtGui.QMessageBox.warning(self, "No volume", "Load a volume before running motion correction", QtGui.QMessageBox.Close)
            return

        opts = {}
        opts["cost"] = self.cost_combo.itemData(self.cost_combo.currentIndex())
        opts["bins"] = self.num_bins.text()
        opts["dof"] = self.num_dofs.text()
        opts["refvol"] = self.refvol.text()
        opts["scaling"] = self.scaling.text()
        opts["smooth"] = self.smoothing.text()
        opts["rotation"] = self.rotation.text()
        opts["stages"] = self.stages.text()
        opts["fov"] = self.fov.text()
        if self.sinc.isChecked(): opts["sinc_final"] = ""
        if self.spline.isChecked(): opts["spline_final"] = ""
        if self.nn.isChecked(): opts["nn_final"] = ""
        if self.gdt.isChecked(): opts["gdt"] = ""
        if self.meanvol.isChecked(): opts["meanvol"] = ""

        for key, value in opts.items():
            print(key, value)

        corvol = mcflirt(self.ivm.vol.data, self.ivm.vol.voxel_sizes, **opts)
        self.ivm.add_overlay(Overlay(name="Motion corrected", data=corvol), make_current=True)