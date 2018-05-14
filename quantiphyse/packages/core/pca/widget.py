"""
Quantiphyse - Widgets for PCA reduction

Copyright (c) 2013-2018 University of Oxford
"""

from PySide import QtGui

from quantiphyse.gui.widgets import QpWidget, TitleWidget, OverlayCombo, RoiCombo, NumericOption
from quantiphyse.gui.plot import Plot
from quantiphyse.utils import sf

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

        self.plot = Plot(qpo=None, parent=self, title="PCA modes")

        self.variance_model = QtGui.QStandardItemModel()
        variance_table = QtGui.QTableView()
        variance_table.verticalHeader().hide()
        variance_table.setModel(self.variance_model)

        tabs = QtGui.QTabWidget()
        tabs.addTab(self.plot, "PCA modes")
        tabs.addTab(variance_table, "Explained variance")
        tabs.setCurrentWidget(self.plot)
        vbox.addWidget(tabs)

        vbox.addStretch(1)

        self._data_changed()  
    
    def _data_changed(self):
        self.output_name.setText("%s_pca" % self.data_combo.currentText())
        self.run_btn.setEnabled(self.data_combo.currentText() in self.ivm.data)

    def batch_options(self):
        roi = self.roi_combo.currentText()
        if roi == "<none>": 
            roi = None
        return "PCA", {"data" : self.data_combo.currentText(),
                       "roi" : roi,
                       "n-components" : self.n_comp.value(),
                       "output-name" : self.output_name.text()}

    def run(self):
        process = PcaProcess(self.ivm)
        process.run(self.batch_options()[1])
        self._update_plot(process)
        self._update_table(process)

    def _update_plot(self, process):
        self.plot.clear()
        for idx, mode in enumerate(process.pca_modes):
            self.plot.add_line(name="Mode %i" % (idx+1), values=mode)
        self.plot.add_line(name="Mean", values=process.mean, line_col=(255, 0, 0), line_width=3.0)

    def _update_table(self, process):
        self.variance_model.clear()
        self.variance_model.setHorizontalHeaderItem(0, QtGui.QStandardItem("PCA mode"))
        self.variance_model.setHorizontalHeaderItem(1, QtGui.QStandardItem("Variance explained"))
        self.variance_model.setHorizontalHeaderItem(2, QtGui.QStandardItem("Cumulative"))
        
        cumulative = 0
        for idx, variance in enumerate(process.explained_variance):
            cumulative += variance
            self.variance_model.setItem(idx, 0, QtGui.QStandardItem("Mode %i" % (idx+1)))
            self.variance_model.setItem(idx, 1, QtGui.QStandardItem(sf(variance)))
            self.variance_model.setItem(idx, 2, QtGui.QStandardItem(sf(cumulative)))
