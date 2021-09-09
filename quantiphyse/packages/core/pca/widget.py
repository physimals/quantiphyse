"""
Quantiphyse - Widgets for PCA reduction

Copyright (c) 2013-2020 University of Oxford

Licensed under the Apache License, Version 2.0 (the "License");
you may not use this file except in compliance with the License.
You may obtain a copy of the License at

    http://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and
limitations under the License.
"""
import numpy as np
from PySide2 import QtGui, QtCore, QtWidgets

from quantiphyse.gui.widgets import QpWidget, TitleWidget, RunWidget
from quantiphyse.gui.options import OptionBox, DataOption, NumericOption, OutputNameOption
from quantiphyse.gui.plot import Plot
from quantiphyse.utils import sf

class PcaWidget(QpWidget):
    """
    PCA widget
    """
    def __init__(self, **kwargs):
        super(PcaWidget, self).__init__(name="PCA", icon="pca",
                                        desc="PCA reduction", group="Processing", **kwargs)
        
    def init_ui(self):
        vbox = QtWidgets.QVBoxLayout()
        self.setLayout(vbox)

        title = TitleWidget(self, title="PCA reduction", subtitle="Principal Component Analysis for 4D data")
        vbox.addWidget(title)

        self._options = OptionBox("Options")
        self._options.add("Data", DataOption(self.ivm, include_3d=False), key="data")
        self._options.add("ROI", DataOption(self.ivm, data=False, rois=True), key="roi")
        self._options.add("Number of components", NumericOption(minval=1, intonly=True, default=4), key="n-components")
        self._options.add("Output name", OutputNameOption(src_data=self._options.option("data"), suffix="_pca"), key="output-name")
        self._options.option("data").sig_changed.connect(self._data_changed)
        vbox.addWidget(self._options)

        self._run = RunWidget(self)
        self._run.sig_postrun.connect(self._postrun)
        vbox.addWidget(self._run)

        self.plot = Plot(qpo=None, parent=self, title="PCA modes")

        self.variance_model = QtGui.QStandardItemModel()
        variance_table = QtWidgets.QTableView()
        variance_table.verticalHeader().hide()
        variance_table.setModel(self.variance_model)

        tabs = QtWidgets.QTabWidget()
        tabs.addTab(self.plot, "PCA modes")
        tabs.addTab(variance_table, "Explained variance")
        tabs.setCurrentWidget(self.plot)
        vbox.addWidget(tabs)

        vbox.addStretch(1)
        self._data_changed()  
    
    def processes(self):
        return {"PCA" : self._options.values()}
        
    def _data_changed(self):
        self._run.setEnabled(self._options.option("data").value in self.ivm.data)

    def _postrun(self):
        self._update_plot()
        self._update_table()

    def _update_plot(self):
        self.plot.clear()
        extra = self.ivm.extras.get(self._options.option("output-name").value + "_modes", None)
        if extra is not None:
            arr = np.array(extra.arr)
            for idx in range(arr.shape[1]-1):
                self.plot.add_line(arr[:, idx], name="Mode %i" % idx)
            self.plot.add_line(arr[:, -1], name="Mean", line_col=(255, 0, 0), line_width=3.0)

    def _update_table(self):
        self.variance_model.clear()
        extra = self.ivm.extras.get(self._options.option("output-name").value + "_variance", None)
        if extra is not None:
            self.debug(str(extra))
            for idx, header in enumerate(extra.col_headers):
                self.variance_model.setHorizontalHeaderItem(idx, QtGui.QStandardItem(header))
           
            for idx, variance in enumerate(extra.arr):
                self.variance_model.setItem(idx, 0, QtGui.QStandardItem(str(variance[0])))
                self.variance_model.setItem(idx, 1, QtGui.QStandardItem(sf(variance[1])))
                self.variance_model.setItem(idx, 2, QtGui.QStandardItem(sf(variance[2])))
