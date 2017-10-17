"""
Author: Martin Craig <martin.craig@eng.ox.ac.uk>
Copyright (c) 2016-2017 University of Oxford, Martin Craig
"""
from __future__ import division, unicode_literals, absolute_import, print_function

import sys, os, warnings
import time
import traceback
import re
import tempfile

import nibabel as nib
import numpy as np
import pyqtgraph as pg
from PySide import QtCore, QtGui

from quantiphyse.utils import debug
from quantiphyse.utils.exceptions import QpException
from quantiphyse.gui.widgets import QpWidget, BatchButton, HelpButton

DESC = """This is an example of how to create a plugin widget"""

class ExamplePluginWidget(QpWidget):

    def __init__(self, **kwargs):
        super(ExamplePluginWidget, self).__init__(name="Example Plugin", 
                                                  desc="An example plugin",
                                                  group="plugins", **kwargs)

    def init_ui(self):
        layout = QtGui.QVBoxLayout()
        self.setLayout(layout)

        hbox = QtGui.QHBoxLayout()
        hbox.addWidget(QtGui.QLabel('<font size="5">Example Plugin Widget</font>'))
        hbox.addStretch(1)
        hbox.addWidget(BatchButton(self))
        hbox.addWidget(HelpButton(self, "example_plugin"))
        layout.addLayout(hbox)
        
        desc = QtGui.QLabel(DESC)
        desc.setWordWrap(True)
        layout.addWidget(desc)
        layout.addWidget(QtGui.QLabel(""))

    def activate(self):
        self.ivm.sig_all_data.connect(self.data_changed)

    def deactivate(self):
        self.ivm.sig_all_data.disconnect(self.data_changed)

    def data_changed(self, overlays):
        pass

    def batch_options(self):
        return "ExamplePluginProcess", {}
