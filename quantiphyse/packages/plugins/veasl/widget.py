"""
VEASL Quantiphyse plugin

VEASL = Vessel Encoded ASL

Author: Martin Craig <martin.craig@eng.ox.ac.uk>
Copyright (c) 2016-2017 University of Oxford, Martin Craig
"""

from __future__ import division, unicode_literals, absolute_import, print_function

import sys
import os
import time
import traceback
import re
import tempfile

import numpy as np
from PySide import QtCore, QtGui

from quantiphyse.gui.widgets import QpWidget, HelpButton, BatchButton, OverlayCombo, NumericOption, NumberList, LoadNumbers, OrderList, OrderListButtons, NumberGrid, RunBox, Citation, TitleWidget
from quantiphyse.gui.dialogs import TextViewerDialog, error_dialog, GridEditDialog
from quantiphyse.analysis import Process
from quantiphyse.utils import debug, warn
from quantiphyse.utils.exceptions import QpException

from .process import VeaslProcess

CITE_TITLE = "A Fast Analysis Method for Non Invasive Imaging of Blood Flow in Individual Cerebral Arteries Using Vessel Encoded Arterial Spin Labelling Angiography."
CITE_AUTHOR = "Chappell MA, Okell TW, Payne SJ, Jezzard P, Woolrich MW."
CITE_JOURNAL = "Medical Image Analysis 16.4 (2012) 831-839"

class VeaslWidget(QpWidget):
    """
    Widget for running VEASL model fitting
    """
    def __init__(self, **kwargs):
        QpWidget.__init__(self, name="Veasl", icon="veasl", group="",
                          desc="Vessel Encoded ASL analysis", **kwargs)

    def local_file(self, name):
        """ Get the full pathname of a file stored in same folder as this widget's source """
        return os.path.abspath(os.path.join(os.path.dirname(__file__), name))
       
    def init_ui(self):
        mainGrid = QtGui.QVBoxLayout()
        self.setLayout(mainGrid)

        title = TitleWidget("VEASL - Vessel Encoded ASL", help="veasl")
        mainGrid.addWidget(title)
        
        cite = Citation(CITE_TITLE, CITE_AUTHOR, CITE_JOURNAL)
        mainGrid.addWidget(cite)

        # Options
        hbox = QtGui.QHBoxLayout()

        options_box = QtGui.QGroupBox()
        options_box.setTitle("Options")
        grid = QtGui.QGridLayout()
        options_box.setLayout(grid)
        
        self.nfpc = NumericOption("Sources per class", grid, ypos=0, xpos=0, default=2, intonly=True)
        grid.addWidget(QtGui.QLabel("Inference method"), 1, 0)
        self.method_combo = QtGui.QComboBox()
        self.method_combo.addItem("MAP")
        self.method_combo.addItem("MCMC")
        grid.addWidget(self.method_combo, 1, 1)
        grid.addWidget(QtGui.QLabel("Image list"), 2, 0)
        self.imlist = QtGui.QLineEdit("T0123456")
        grid.addWidget(self.imlist, 2, 1)
        grid.addWidget(QtGui.QLabel("Modulation matrix"), 3, 0)
        self.modmat_combo = QtGui.QComboBox()
        self.modmat_combo.addItem("Default")
        grid.addWidget(self.modmat_combo, 3, 1)

        hbox.addWidget(options_box)
        hbox.addStretch(1)
        mainGrid.addLayout(hbox)

        # Vessel locations
        hbox = QtGui.QHBoxLayout()

        vesselbox = QtGui.QGroupBox()
        vesselbox.setTitle("Initial vessel locations")
        grid = QtGui.QGridLayout()
        vesselbox.setLayout(grid)
        self.vesselxy = NumberGrid([[], []], row_headers=["X", "Y"], expandable=(True, False))
        self.vesselxy.loadFromFile(self.local_file("veslocs_default.txt"))
        grid.addWidget(self.vesselxy, 0, 1, 1, 2)

        hbox.addWidget(vesselbox)
        hbox.addStretch(1)
        mainGrid.addLayout(hbox)

        # Encoding setup
        hbox = QtGui.QHBoxLayout()

        encbox = QtGui.QGroupBox()
        encbox.setTitle("Encoding setup")
        grid = QtGui.QGridLayout()
        encbox.setLayout(grid)
        self.enc_mtx = NumberGrid([[],[],[],[]], row_headers=["CX", "CY", "\u03b8 (\u00b0)", "D"], expandable=(True, False))
        self.enc_mtx.loadFromFile(self.local_file("encode_default.txt"))
        grid.addWidget(self.enc_mtx, 0, 1, 1, 2)

        hbox.addWidget(encbox)
        hbox.addStretch(1)
        mainGrid.addLayout(hbox)

        # Modulation matrix
        #hbox = QtGui.QHBoxLayout()
        #modmatbox = QtGui.QGroupBox()
        #modmatbox.setTitle("Modulation matrix")
        #grid = QtGui.QGridLayout()
        #modmatbox.setLayout(grid)
        #self.modmat = NumberGrid([[]])
        #self.modmat.loadFromFile(self.local_file("modmat_default.txt"))
        #grid.addWidget(self.modmat, 0, 1, 1, 2)
        #hbox.addWidget(modmatbox)
        #hbox.addStretch(1)
        #mainGrid.addLayout(hbox)

        # Run box
        run_box = RunBox(self.get_process, self.get_rundata, title="Run VEASL")
        mainGrid.addWidget(run_box)

        mainGrid.addStretch(1)

    def activate(self):
        pass

    def deactivate(self):
        pass

    def batch_options(self):
        return "Veasl", self.get_rundata()

    def get_process(self):
        return VeaslProcess(self.ivm)

    def get_rundata(self):
        return {}
