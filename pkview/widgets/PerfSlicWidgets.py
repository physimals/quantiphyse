from PySide import QtGui
import numpy as np
import skimage.segmentation as seg

from ..QtInherit.widgets import HelpButton, BatchButton, OverlayCombo, RoiCombo
from ..analysis.sv import SupervoxelsProcess
from ..analysis.misc import MeanValuesProcess
from . import PkWidget

CITE = """
<i>Irving et al (2017)
"maskSLIC: Regional Superpixel Generation with Application to Local Pathology Characterisation in Medical Images"
https://arxiv.org/abs/1606.09518v2</i>
"""

class NumericOption:
    def __init__(self, text, grid, ypos, minval=0, maxval=100, default=0, step=1, intonly=False):
        self.label = QtGui.QLabel(text)
        if intonly:
            self.spin = QtGui.QSpinBox()
        else:
            self.spin = QtGui.QDoubleSpinBox()

        self.spin.setMinimum(minval)
        self.spin.setMaximum(maxval)
        self.spin.setValue(default)
        self.spin.setSingleStep(step)
        grid.addWidget(self.label, ypos, 0)
        grid.addWidget(self.spin, ypos, 1)

class PerfSlicWidget(PkWidget):
    """
    Generates supervoxels using SLIC method
    """
    def __init__(self, **kwargs):
        super(PerfSlicWidget, self).__init__(name="Super Voxels", icon="sv", desc="Generate supervoxel clusters", **kwargs)
        
    def init_ui(self):
        layout = QtGui.QVBoxLayout()
        self.setLayout(layout)

        hbox = QtGui.QHBoxLayout()
        hbox.addWidget(QtGui.QLabel('<font size="5">Supervoxel Generation</font>'))
        hbox.addStretch(1)
        hbox.addWidget(BatchButton(self))
        hbox.addWidget(HelpButton(self, "sv"))
        layout.addLayout(hbox)
        
        cite = QtGui.QLabel(CITE)
        cite.setWordWrap(True)
        layout.addWidget(cite)
        layout.addWidget(QtGui.QLabel(""))

        hbox = QtGui.QHBoxLayout()
        optbox = QtGui.QGroupBox()
        optbox.setTitle("Options")
        grid = QtGui.QGridLayout()
        optbox.setLayout(grid)
        
        grid.addWidget(QtGui.QLabel("Data"), 0, 0)
        self.ovl = OverlayCombo(self.ivm)
        self.ovl.currentIndexChanged.connect(self.ovl_changed)
        grid.addWidget(self.ovl, 0, 1)
        grid.addWidget(QtGui.QLabel("ROI"), 1, 0)
        self.roi = RoiCombo(self.ivm)
        grid.addWidget(self.roi, 1, 1)

        self.n_comp = NumericOption("Number of components", grid, 2, minval=1, maxval=3, default=3, intonly=True)
        self.compactness = NumericOption("Compactness", grid, 3, minval=0.01, maxval=1, step=0.05, default=0.1, intonly=False)
        self.sigma = NumericOption("Smoothing", grid, 4, minval=0, maxval=5, step=0.1, default=1, intonly=False)
        self.n_supervoxels = NumericOption("Number of supervoxels", grid, 5, minval=2, maxval=1000, default=20, intonly=True)

        grid.addWidget(QtGui.QLabel("Output name"), 6, 0)
        self.output_name = QtGui.QLineEdit("supervoxels")
        grid.addWidget(self.output_name, 6, 1)

        btn = QtGui.QPushButton('Generate', self)
        btn.clicked.connect(self.generate)
        grid.addWidget(btn, 7, 0)
        hbox.addWidget(optbox)
        hbox.addStretch(1)
        layout.addLayout(hbox)

        layout.addStretch(1)

    def ovl_changed(self, idx):
        name = self.ovl.currentText()
        if name:
            ovl = self.ivm.overlays[name]
            self.n_comp.label.setEnabled(ovl.ndim == 4)
            self.n_comp.spin.setEnabled(ovl.ndim == 4)

    def batch_options(self):
        options = {"data" : self.ovl.currentText(),
                   "roi" : self.roi.currentText(),
                   "n-components" : self.n_comp.spin.value(),
                   "compactness" : self.compactness.spin.value(),
                   "sigma" : self.sigma.spin.value(),
                   "n-supervoxels" :  self.n_supervoxels.spin.value(),
                   "output-name" :  self.output_name.text() }
        return "Supervoxels", options

    def generate(self):
        process = SupervoxelsProcess(self.ivm, sync=True)
        process.run(self.batch_options()[1])
        if process.status != SupervoxelsProcess.SUCCEEDED:
            QtGui.QMessageBox.warning(None, "Process error", "Supervoxels process failed to run:\n\n" + str(process.output),
                                      QtGui.QMessageBox.Close)

class MeanValuesWidget(PkWidget):
    """
    Convert an overlay + multi-level ROI into mean values overlay
    """
    def __init__(self, **kwargs):
        super(MeanValuesWidget, self).__init__(name="Mean Values", icon="meanvals", desc="Generate mean values overlays", **kwargs)

        layout = QtGui.QVBoxLayout()

        hbox = QtGui.QHBoxLayout()
        hbox.addWidget(QtGui.QLabel('<font size="5">Generate Mean Values Overlay</font>'))
        hbox.addStretch(1)
        hbox.addWidget(HelpButton(self, "mean_values"))
        layout.addLayout(hbox)
        
        desc = QtGui.QLabel("This widget will convert the current overlay into a "
                            "new overlay in which each ROI region contains the mean "
                            "value for that region.\n\nThis is generally only useful for "
                            "multi-level ROIs such as clusters or supervoxels")
        desc.setWordWrap(True)
        layout.addWidget(desc)

        hbox = QtGui.QHBoxLayout()
        gbox = QtGui.QGroupBox()
        gbox.setTitle("Options")
        grid = QtGui.QGridLayout()
        gbox.setLayout(grid)
        
        grid.addWidget(QtGui.QLabel("Data"), 0, 0)
        self.ovl = OverlayCombo(self.ivm)
        self.ovl.currentIndexChanged.connect(self.ovl_changed)
        grid.addWidget(self.ovl, 0, 1)
        grid.addWidget(QtGui.QLabel("ROI regions"), 1, 0)
        self.roi = RoiCombo(self.ivm)
        grid.addWidget(self.roi, 1, 1)
        grid.addWidget(QtGui.QLabel("Output name"), 2, 0)
        self.output_name = QtGui.QLineEdit()
        grid.addWidget(self.output_name, 2, 1)

        btn = QtGui.QPushButton('Generate', self)
        btn.clicked.connect(self.generate)
        grid.addWidget(btn, 2, 0)
        hbox.addWidget(gbox)
        hbox.addStretch(1)
        layout.addLayout(hbox)
        layout.addStretch(1)
        self.setLayout(layout)

    def ovl_changed(self):
        name = self.ovl.currentText()
        if name:
            self.output_name.setText(name + "_means")

    def batch_options(self):
        options = {"roi" : self.roi.currentText(),
                   "data" : self.ovl.currentText(),
                   "output-name" :  self.output_name.text() }
        return "MeanValues", options

    def generate(self):
        options = self.batch_options()[1]

        if not options["data"]:
            QtGui.QMessageBox.warning(self, "No data selected", "Load data to generate mean values from", QtGui.QMessageBox.Close)
            return
        if not options["roi"]:
            QtGui.QMessageBox.warning(self, "No ROI selected", "Load an ROI for mean value regions", QtGui.QMessageBox.Close)
            return
        
        process = MeanValuesProcess(self.ivm)
        process.run(options)
        if process.status != SupervoxelsProcess.SUCCEEDED:
            QtGui.QMessageBox.warning(None, "Process error", "MeanValues process failed to run:\n\n" + str(process.output),
                                      QtGui.QMessageBox.Close)



