"""
Quantiphyse - Widget for data clustering using the Supervoxel method

Copyright (c) 2013-2018 University of Oxford
"""

from PySide import QtGui

from quantiphyse.gui.widgets import QpWidget, TitleWidget, Citation, OverlayCombo, RoiCombo, NumericOption

from .process import SupervoxelsProcess, MeanValuesProcess

CITE_TITLE = "maskSLIC: Regional Superpixel Generation with Application to Local Pathology Characterisation in Medical Images"
CITE_AUTHOR = "Benjamin Irving"
CITE_JOURNAL = "https://arxiv.org/abs/1606.09518v2 (2017)"

class PerfSlicWidget(QpWidget):
    """
    Generates supervoxels using SLIC method
    """
    def __init__(self, **kwargs):
        super(PerfSlicWidget, self).__init__(name="Super Voxels", icon="sv", 
                                             desc="Generate supervoxel clusters", 
                                             group="Clustering", **kwargs)
        
    def init_ui(self):
        layout = QtGui.QVBoxLayout()
        self.setLayout(layout)

        title = TitleWidget(self, "Supervoxel Generation", help="sv")
        layout.addWidget(title)
        
        cite = Citation(CITE_TITLE, CITE_AUTHOR, CITE_JOURNAL)
        layout.addWidget(cite)

        hbox = QtGui.QHBoxLayout()
        optbox = QtGui.QGroupBox()
        optbox.setTitle("Options")
        grid = QtGui.QGridLayout()
        optbox.setLayout(grid)
        
        grid.addWidget(QtGui.QLabel("Data"), 0, 0)
        self.ovl = OverlayCombo(self.ivm)
        self.ovl.currentIndexChanged.connect(self._data_changed)
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

        self.gen_btn = QtGui.QPushButton('Generate', self)
        self.gen_btn.clicked.connect(self._generate)
        grid.addWidget(self.gen_btn, 7, 0)
        hbox.addWidget(optbox)
        hbox.addStretch(1)
        layout.addLayout(hbox)

        layout.addStretch(1)

    def _data_changed(self, _):
        name = self.ovl.currentText()
        if name:
            ovl = self.ivm.data[name]
            self.n_comp.label.setVisible(ovl.nvols > 1)
            self.n_comp.spin.setVisible(ovl.nvols > 1)

    def batch_options(self):
        options = {
            "data" : self.ovl.currentText(),
            "roi" : self.roi.currentText(),
            "n-components" : self.n_comp.spin.value(),
            "compactness" : self.compactness.spin.value(),
            "sigma" : self.sigma.spin.value(),
            "n-supervoxels" :  self.n_supervoxels.spin.value(),
            "output-name" :  self.output_name.text() 
        }
        return "Supervoxels", options

    def _generate(self):
        process = SupervoxelsProcess(self.ivm, sync=True)
        process.run(self.batch_options()[1])
        
class MeanValuesWidget(QpWidget):
    """
    Convert a data + multi-level ROI into mean values data set
    """
    def __init__(self, **kwargs):
        super(MeanValuesWidget, self).__init__(name="Mean in ROI", icon="meanvals", 
                                               desc="Replace data with its mean value within each ROI region", 
                                               group="ROIs", **kwargs)

        layout = QtGui.QVBoxLayout()

        title = TitleWidget(self, "Generate Mean Values Data", help="mean_values")
        layout.addWidget(title)
        
        desc = QtGui.QLabel("This widget will convert the current data set into a "
                            "new data set in which each ROI region contains the mean "
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
        self.ovl.currentIndexChanged.connect(self._data_changed)
        grid.addWidget(self.ovl, 0, 1)
        grid.addWidget(QtGui.QLabel("ROI regions"), 1, 0)
        self.roi = RoiCombo(self.ivm)
        grid.addWidget(self.roi, 1, 1)
        grid.addWidget(QtGui.QLabel("Output name"), 2, 0)
        self.output_name = QtGui.QLineEdit()
        grid.addWidget(self.output_name, 2, 1)

        btn = QtGui.QPushButton('Generate', self)
        btn.clicked.connect(self._generate)
        grid.addWidget(btn, 2, 0)
        hbox.addWidget(gbox)
        hbox.addStretch(1)
        layout.addLayout(hbox)
        layout.addStretch(1)
        self.setLayout(layout)

    def _data_changed(self):
        name = self.ovl.currentText()
        if name:
            self.output_name.setText(name + "_means")

    def batch_options(self):
        options = {
            "roi" : self.roi.currentText(),
            "data" : self.ovl.currentText(),
            "output-name" :  self.output_name.text()
        }
        return "MeanValues", options

    def _generate(self):
        options = self.batch_options()[1]

        if not options["data"]:
            QtGui.QMessageBox.warning(self, "No data selected", "Load data to generate mean values from", QtGui.QMessageBox.Close)
            return
        if not options["roi"]:
            QtGui.QMessageBox.warning(self, "No ROI selected", "Load an ROI for mean value regions", QtGui.QMessageBox.Close)
            return
        
        process = MeanValuesProcess(self.ivm)
        process.run(options)
