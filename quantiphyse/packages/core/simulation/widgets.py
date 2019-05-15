"""
Quantiphyse - Widgets for data simulation

Copyright (c) 2013-2018 University of Oxford
"""
try:
    from PySide import QtGui, QtCore, QtGui as QtWidgets
except ImportError:
    from PySide2 import QtGui, QtCore, QtWidgets
  
from quantiphyse.gui.options import OptionBox, NumericOption, DataOption, OutputNameOption
from quantiphyse.gui.widgets import QpWidget, TitleWidget

from .processes import AddNoiseProcess, SimMotionProcess
    
class AddNoiseWidget(QpWidget):
    """
    Add noise to data
    """
    def __init__(self, **kwargs):
        super(AddNoiseWidget, self).__init__(name="Add noise", icon="noise", 
                                             desc="Add random noise to a data set", 
                                             group="Simulation", **kwargs)

    def init_ui(self):
        vbox = QtGui.QVBoxLayout()
        self.setLayout(vbox)

        title = TitleWidget(self, title="Add Noise", help="noise")
        vbox.addWidget(title)

        self.option_box = OptionBox("Options")
        data = self.option_box.add("Data set", DataOption(self.ivm), key="data")
        self.option_box.add("Gaussian standard deviation", NumericOption(minval=0, maxval=100, default=50), key="std")
        self.option_box.add("Output name", OutputNameOption(src_data=data, suffix="_noisy"), key="output-name")
        vbox.addWidget(self.option_box)

        run_btn = QtGui.QPushButton('Run', self)
        run_btn.clicked.connect(self.run)
        vbox.addWidget(run_btn)
        
        vbox.addStretch(1)
 
    def batch_options(self):
        return "AddNoise", self.option_box.values()
        
    def run(self):
        options = self.batch_options()[1]
        process = AddNoiseProcess(self.ivm)
        process.execute(options)

class SimMotionWidget(QpWidget):
    """
    Widget to simulate random motion on a 4D data set
    """
    def __init__(self, **kwargs):
        super(SimMotionWidget, self).__init__(name="Simulate motion", icon="reg", 
                                              desc="Simulate random motion on a 4D data set", 
                                              group="Simulation", **kwargs)

    def init_ui(self):
        vbox = QtGui.QVBoxLayout()
        self.setLayout(vbox)

        title = TitleWidget(self, title="Simulate Motion", help="sim_motion")
        vbox.addWidget(title)

        self.option_box = OptionBox("Options")
        data = self.option_box.add("Data set", DataOption(self.ivm, include_4d=True, include_3d=False), key="data")
        self.option_box.add("Motion standard deviation (mm)", NumericOption(minval=0, maxval=5, default=1, decimals=2), key="std")
        self.option_box.add("Padding (mm)", NumericOption(minval=0, maxval=10, default=5, decimals=1), key="padding", checked=True)
        self.option_box.add("Output name", OutputNameOption(src_data=data, suffix="_moving"), key="output-name")
        vbox.addWidget(self.option_box)

        run_btn = QtGui.QPushButton('Run', self)
        run_btn.clicked.connect(self.run)
        vbox.addWidget(run_btn)
        
        vbox.addStretch(1)

    def batch_options(self):
        return "SimMotion", self.option_box.values()
        
    def run(self):
        options = self.batch_options()[1]
        process = SimMotionProcess(self.ivm)
        process.execute(options)
