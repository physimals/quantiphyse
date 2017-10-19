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
                                                  group="Examples", **kwargs)

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

class ExampleWidget(QpWidget):
    """
    Widget for setting a threshold to the image data inside the ROI. This is saved as an overlay.
    """
    def __init__(self, **kwargs):
        super(ExampleWidget, self).__init__(name="Threshold", desc="Threshold data", icon="quantiphyse", **kwargs)

    def init_ui(self):
        main_vbox = QtGui.QVBoxLayout()
        
        hbox = QtGui.QHBoxLayout()
        hbox.addWidget(QtGui.QLabel('<font size="5">Threshold volume</font>'))
        hbox.addStretch(1)
        hbox.addWidget(HelpButton(self))
        main_vbox.addLayout(hbox)

        explanation = QtGui.QLabel('This is a basic example of a \n'
                                   'widget for development purposes. \n'
                                   'A DCE-MRI image and ROI are \n'
                                   'loaded normally and clicking run \n'
                                   'creates an overlay only shows values \n'
                                   'in the ROI above a defined threshold.')
        main_vbox.addWidget(explanation)

        hbox = QtGui.QHBoxLayout()
        self.b1 = QtGui.QPushButton('Process', self)
        self.b1.clicked.connect(self.run_threshold)
        hbox.addWidget(self.b1)
        hbox.addStretch(1)

        hbox.addWidget(QtGui.QLabel('ROI threshold value:'))
        self.val_t1 = QtGui.QLineEdit('1', self)
        hbox.addWidget(self.val_t1)
        main_vbox.addLayout(hbox)
        
        hbox = QtGui.QHBoxLayout()
        hbox.addStretch(1)
        hbox.addWidget(QtGui.QLabel('Slice to threshold:'))
        self.val_s1 = QtGui.QLineEdit('0', self)
        hbox.addWidget(self.val_s1)
        main_vbox.addLayout(hbox)

        main_vbox.addStretch(1)
        self.setLayout(main_vbox)

    def run_threshold(self):
        # Check if an image and roi exists or otherwise throw an error
        if self.ivm.vol is None:
            raise QpException("No data loaded")

        if self.ivm.current_roi is None:
            raise QpException("No ROI loaded")

        slice = int(self.val_s1.text())
        thresh = float(self.val_t1.text())

        img = self.ivm.vol[:, :, :, slice1]
        img = img * (self.ivm.current_roi > 0)
        img[img1 < thresh] = 0

        self.ivm.add_overlay('thresh', img, set_current=True)

