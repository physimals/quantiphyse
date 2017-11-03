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
from quantiphyse.utils import debug, warn, load_matrix
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
        grid.addWidget(QtGui.QLabel("Modulation matrix"), 3, 0)
        self.modmat_combo = QtGui.QComboBox()
        self.modmat_combo.addItem("Default")
        grid.addWidget(self.modmat_combo, 3, 1)
        grid.addWidget(QtGui.QLabel("Infer vessel locations"), 4, 0)
        self.loc_combo = QtGui.QComboBox()
        self.loc_combo.addItem("Fixed positions", None)
        self.loc_combo.addItem("Infer co-ordinates", "xy")
        self.loc_combo.addItem("Infer rigid transformation", "rigid")
        self.loc_combo.addItem("Infer affine transformation", "affine")
        self.loc_combo.setCurrentIndex(1)
        grid.addWidget(self.loc_combo, 4, 1)
        grid.addWidget(QtGui.QLabel("Infer flow velocity"), 5, 0)
        self.infer_v_cb = QtGui.QCheckBox()
        grid.addWidget(self.infer_v_cb, 5, 1)
        hbox.addWidget(options_box)
        hbox.setAlignment(options_box, QtCore.Qt.AlignTop)

        imlist_box = QtGui.QGroupBox()
        imlist_box.setTitle("Image list")
        grid = QtGui.QGridLayout()
        imlist_box.setLayout(grid)
        self.imlist = OrderList([])
        grid.addWidget(self.imlist, 0, 0)
        hbox.addWidget(imlist_box)
        hbox.setAlignment(imlist_box, QtCore.Qt.AlignTop)

        hbox.addStretch(1)
        mainGrid.addLayout(hbox)

        # Vessel locations
        hbox = QtGui.QHBoxLayout()

        vesselbox = QtGui.QGroupBox()
        vesselbox.setTitle("Initial vessel locations")
        grid = QtGui.QGridLayout()
        vesselbox.setLayout(grid)
        self.vesselxy = NumberGrid([[], []], row_headers=["X", "Y"], expandable=(True, False), fix_height=True)
        grid.addWidget(self.vesselxy, 0, 1, 1, 2)
        self.vesselxy.loadFromFile(self.local_file("veslocs_default.txt"))
        
        hbox.addWidget(vesselbox, 2)
        hbox.addStretch(1)
        mainGrid.addLayout(hbox)

        # Encoding setup
        hbox = QtGui.QHBoxLayout()

        encbox = QtGui.QGroupBox()
        encbox.setTitle("Encoding setup")
        grid = QtGui.QGridLayout()
        encbox.setLayout(grid)
        self.enc_mtx = NumberGrid([[],[],[],[]], row_headers=["CX", "CY", "\u03b8 (\u00b0)", "D"], expandable=(True, False), fix_height=True)
        grid.addWidget(self.enc_mtx, 0, 1, 1, 2)

        hbox.addWidget(encbox, 2)
        hbox.addStretch(1)
        mainGrid.addLayout(hbox)
        
        # Run box
        run_box = RunBox(self.get_process, self.get_rundata, title="Run VEASL")
        mainGrid.addWidget(run_box)

        mainGrid.addStretch(1)
        self.main_data_changed()

    def activate(self):
        self.ivm.sig_main_data.connect(self.main_data_changed)

    def deactivate(self):
        self.ivm.sig_main_data.disconnect(self.main_data_changed)

    def main_data_changed(self):
        if self.ivm.main is not None:
            nvols = self.ivm.main.nvols
            self.imlist.setItems(["Tag", "Control"] + ["Encoding %i" % (i+1) for i in range(nvols-2)])
            matrix, nrows, ncols = load_matrix(self.local_file("encode_default.txt"))
            if nvols > ncols:
                matrix = [row[:nvols] for row in matrix]
            elif nvols < ncols:
                matrix = [row + [0,] * (nvols - ncols) for row in matrix]
            self.enc_mtx.setValues(matrix)
        else:
            self.imlist.setItems(["<No data loaded>"])
            self.enc_mtx.loadFromFile(self.local_file("encode_default.txt"))

    def get_imlist(self):
        imlist = ""
        for v in self.imlist.items():
            if v == "Tag":
                imlist += "T"
            elif v == "Control":
                imlist += "0"
            else:
                imlist += str(int(v.split(" ", 1)[1]))
        print(imlist)
        return imlist

    def batch_options(self):
        return "Veasl", self.get_rundata()

    def get_process(self):
        return VeaslProcess(self.ivm)

    def get_rundata(self):
        return {"vesloc" : self.vesselxy.values(), 
                "modmat" : self.local_file("modmat_default.txt"),
                "encdef" : self.enc_mtx.values(),
                "nfpc"   : self.nfpc.spin.value(),
                "imlist" : self.get_imlist(),
                "infer_loc" : self.loc_combo.itemData(self.loc_combo.currentIndex()),
                "infer_v" : self.infer_v_cb.isChecked()}
