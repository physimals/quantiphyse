"""
Quantiphyse - Widgets for PCA reduction

Copyright (c) 2013-2018 University of Oxford
"""

from PySide import QtGui

from quantiphyse.gui.widgets import QpWidget, TitleWidget, OverlayCombo, RoiCombo, NumericOption

from .process import PcaProcess
    
class PcaWidget(QpWidget):
    """
    PCA widget
    """
    def __init__(self, **kwargs):
        super(PcaWidget, self).__init__(name="PCA", 
                                        desc="PCA reduction", group="Processing", **kwargs)
        
    def init_ui(self):
        vbox = QtGui.QVBoxLayout()
        self.setLayout(vbox)

        title = TitleWidget(self, title="PCA reduction", subtitle="Principal Component Analysis for 4D data")
        vbox.addWidget(title)

        hbox = QtGui.QHBoxLayout()
        gbox = QtGui.QGroupBox()
        gbox.setTitle("Options")
        grid = QtGui.QGridLayout()
        gbox.setLayout(grid)

        grid.addWidget(QtGui.QLabel("Data"), 0, 0)
        self.data_combo = OverlayCombo(self.ivm)
        self.data_combo.currentIndexChanged.connect(self._data_changed)
        grid.addWidget(self.data_combo, 0, 1)

        grid.addWidget(QtGui.QLabel("ROI"), 1, 0)
        self.roi_combo = RoiCombo(self.ivm, none_option=True)
        grid.addWidget(self.roi_combo, 1, 1)

        self.n_comp = NumericOption("Number of components", grid, ypos=2, 
                                    minval=1, intonly=True, default=4)

        grid.addWidget(QtGui.QLabel("Output name"), 3, 0)
        self.output_name = QtGui.QLineEdit()
        grid.addWidget(self.output_name, 3, 1)

        hbox.addWidget(gbox)
        hbox.addStretch(1)
        vbox.addLayout(hbox)

        hbox = QtGui.QHBoxLayout()
        self.run_btn = QtGui.QPushButton("Run")
        self.run_btn.clicked.connect(self.run)
        hbox.addWidget(self.run_btn)
        hbox.addStretch(1)
        vbox.addLayout(hbox)

        vbox.addStretch(1) 
        self._data_changed()  
    
    def _data_changed(self):
        self.output_name.setText("%s_pca" % self.data_combo.currentText())
        self.run_btn.setEnabled(self.data_combo.currentText() in self.ivm.data)

    def batch_options(self):
        return "PCA", {"data" : self.data_combo.currentText(),
                       "roi" : self.roi_combo.currentText(),
                       "n-components" : self.n_comp.value(),
                       "output-name" : self.output_name.text()}

    def run(self):
        process = PcaProcess(self.ivm)
        process.run(self.batch_options()[1])
