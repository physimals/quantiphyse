"""
Quantiphyse - Widgets for data smoothing

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

from PySide2 import QtGui, QtCore, QtWidgets

from quantiphyse.gui.widgets import QpWidget, TitleWidget, OverlayCombo, NumericOption
from quantiphyse.utils import QpException

from .process import SmoothingProcess
    
class SmoothingWidget(QpWidget):
    """
    Gaussian smoothing widget
    """
    def __init__(self, **kwargs):
        super(SmoothingWidget, self).__init__(name="Smoothing", icon="smooth.png", 
                                              desc="Gaussian smoothing", group="Processing", **kwargs)
        
    def init_ui(self):
        vbox = QtWidgets.QVBoxLayout()
        self.setLayout(vbox)

        title = TitleWidget(self, title="Data Smoothing", subtitle="Smooth data using a Gaussian kernel", help="smoothing")
        vbox.addWidget(title)

        hbox = QtWidgets.QHBoxLayout()
        gbox = QtWidgets.QGroupBox()
        gbox.setTitle("Options")
        grid = QtWidgets.QGridLayout()
        gbox.setLayout(grid)

        grid.addWidget(QtWidgets.QLabel("Data to smooth"), 0, 0)
        self.data_combo = OverlayCombo(self.ivm)
        self.data_combo.currentIndexChanged.connect(self.data_changed)
        grid.addWidget(self.data_combo, 0, 1)
        self.sigma = NumericOption("Sigma (mm)", grid, xpos=0, ypos=1, minval=0, step=0.1, default=1.0)
        grid.addWidget(QtWidgets.QLabel("Output name"), 2, 0)
        self.output_name = QtWidgets.QLineEdit()
        grid.addWidget(self.output_name, 2, 1)

        hbox.addWidget(gbox)
        hbox.addStretch(1)
        vbox.addLayout(hbox)

        hbox = QtWidgets.QHBoxLayout()
        self.run_btn = QtWidgets.QPushButton("Run")
        self.run_btn.clicked.connect(self.run)
        hbox.addWidget(self.run_btn)
        hbox.addStretch(1)
        vbox.addLayout(hbox)

        vbox.addStretch(1) 
        self.data_changed()  
    
    def data_changed(self):
        self.output_name.setText("%s_smoothed" % self.data_combo.currentText())
        self.run_btn.setEnabled(self.data_combo.currentText() in self.ivm.data)

    def batch_options(self):
        return "Smooth", {"data" : self.data_combo.currentText(),
                          "sigma" : self.sigma.spin.value(),
                          "output-name" : self.output_name.text()}

    def run(self):
        process = SmoothingProcess(self.ivm)
        process.run(self.batch_options()[1])
