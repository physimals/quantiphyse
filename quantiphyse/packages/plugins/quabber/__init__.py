"""
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

import nibabel as nib
import numpy as np
import pyqtgraph as pg
from PySide import QtCore, QtGui

from quantiphyse.gui.widgets import QpWidget, HelpButton, BatchButton, OverlayCombo, NumericOption, NumberList, LoadNumbers, OrderList, OrderListButtons, Citation, TitleWidget, RunBox
from quantiphyse.gui.dialogs import TextViewerDialog, error_dialog, GridEditDialog
from quantiphyse.analysis import Process
from quantiphyse.utils import debug, warn
from quantiphyse.utils.exceptions import QpException
from quantiphyse.volumes.io import save

from .process import FabberProcess
from .dialogs import OptionsDialog, PriorsDialog

FAB_CITE_TITLE = "Variational Bayesian inference for a non-linear forward model"
FAB_CITE_AUTHOR = "Chappell MA, Groves AR, Whitcher B, Woolrich MW."
FAB_CITE_JOURNAL = "IEEE Transactions on Signal Processing 57(1):223-236, 2009."

class FabberWidget(QpWidget):
    """
    Widget for running Fabber model fitting
    """
    def __init__(self, **kwargs):
        QpWidget.__init__(self, name="Fabber", icon="fabber", group="Fabber",
                          desc="Fabber Bayesian model fitting", **kwargs)
    
    def model_name(self, lib):
        match = re.match(".*fabber_models_(.+)\..+", lib, re.I)
        if match:
            return match.group(1).upper()
        else:
            return lib
    
    def init_ui(self):
        mainGrid = QtGui.QVBoxLayout()
        self.setLayout(mainGrid)

        if not FabberProcess.FABBER_FOUND:
            mainGrid.addWidget(QtGui.QLabel("Fabber core library not found.\n\n You must install Fabber to use this widget"))
            return

        self.rundata = {}
        self.rundata["model"] = "poly"
        self.rundata["degree"] = "2"
        self.rundata["method"] = "vb"
        self.rundata["save-mean"] = ""
        self.rundata["save-model-fit"] = ""
        #self.rundata["save-model-extras"] = ""

        title = TitleWidget(self, title="Fabber Bayesian Model Fitting", help="fabber")
        mainGrid.addWidget(title)
        
        cite = Citation(FAB_CITE_TITLE, FAB_CITE_AUTHOR, FAB_CITE_JOURNAL)
        mainGrid.addWidget(cite)

        # Options box
        optionsBox = QtGui.QGroupBox()
        optionsBox.setTitle('Options')
        optionsBox.setSizePolicy(QtGui.QSizePolicy.MinimumExpanding, QtGui.QSizePolicy.MinimumExpanding)
        grid = QtGui.QGridLayout()
        optionsBox.setLayout(grid)

        grid.addWidget(QtGui.QLabel("Model group"), 0, 0)
        self.modellibCombo = QtGui.QComboBox(self)
        self.modellibCombo.setSizeAdjustPolicy(QtGui.QComboBox.AdjustToContents)
        self.modellibCombo.addItem("GENERIC", "")
        for lib in FabberProcess.MODEL_LIBS:
            self.modellibCombo.addItem(self.model_name(lib), lib)
        self.modellibCombo.currentIndexChanged.connect(self.model_group_changed)
        self.modellibCombo.setCurrentIndex(0)

        grid.addWidget(self.modellibCombo, 0, 1)
        grid.addWidget(QtGui.QLabel("Model"), 1, 0)
        self.modelCombo = QtGui.QComboBox(self)
        self.modelCombo.setSizeAdjustPolicy(QtGui.QComboBox.AdjustToContents)
        self.modelCombo.currentIndexChanged.connect(self.model_changed)
        grid.addWidget(self.modelCombo, 1, 1)
        self.modelOptionsBtn = QtGui.QPushButton('Model Options', self)
        self.modelOptionsBtn.clicked.connect(self.show_model_options)
        grid.addWidget(self.modelOptionsBtn, 1, 2)
        
        grid.addWidget(QtGui.QLabel("Inference method"), 4, 0)
        self.methodCombo = QtGui.QComboBox(self)
        self.methodCombo.setSizeAdjustPolicy(QtGui.QComboBox.AdjustToContents)
        methods = self.fab().get_methods()
        for method in methods:
            self.methodCombo.addItem(method)
        self.methodCombo.setCurrentIndex(self.methodCombo.findText(self.rundata["method"]))
          
        self.methodCombo.currentIndexChanged.connect(self.method_changed)
        grid.addWidget(self.methodCombo, 4, 1)
        self.methodOptionsBtn = QtGui.QPushButton('Inference Options', self)
        self.methodOptionsBtn.clicked.connect(self.show_method_options)
        grid.addWidget(self.methodOptionsBtn, 4, 2)
        
        grid.addWidget(QtGui.QLabel("Parameter priors"), 5, 0)
        self.priorsBtn = QtGui.QPushButton('Edit', self)
        self.priorsBtn.clicked.connect(self.show_prior_options)
        grid.addWidget(self.priorsBtn, 5, 2)
        
        grid.addWidget(QtGui.QLabel("General Options"), 6, 0)
        self.generalOptionsBtn = QtGui.QPushButton('Edit', self)
        self.generalOptionsBtn.clicked.connect(self.show_general_options)
        grid.addWidget(self.generalOptionsBtn, 6, 2)
        
        mainGrid.addWidget(optionsBox)

        # Run box
        runBox = RunBox(self.get_process, self.get_rundata, title="Run Fabber", save_option=True)
        mainGrid.addWidget(runBox)

        # Load/save box
        fileBox = QtGui.QGroupBox()
        fileBox.setTitle('Load/Save options')
        fileBox.setSizePolicy(QtGui.QSizePolicy.MinimumExpanding, QtGui.QSizePolicy.MinimumExpanding)
        vbox = QtGui.QVBoxLayout()
        fileBox.setLayout(vbox)

        hbox = QtGui.QHBoxLayout()
        hbox.addWidget(QtGui.QLabel("Filename"))
        self.fileEdit = QtGui.QLineEdit()
        self.fileEdit.setReadOnly(True)
        hbox.addWidget(self.fileEdit)
        btn = QtGui.QPushButton("Open")
        btn.clicked.connect(self.open_file)
        hbox.addWidget(btn)
        self.saveBtn = QtGui.QPushButton("Save")
        self.saveBtn.clicked.connect(self.save_file)
        self.saveBtn.setEnabled(False)
        hbox.addWidget(self.saveBtn)
        btn = QtGui.QPushButton("Save As")
        btn.clicked.connect(self.save_as_file)
        hbox.addWidget(btn)
        vbox.addLayout(hbox)

        mainGrid.addWidget(fileBox)
        mainGrid.addStretch(1)

        self.model_group_changed()
        self.method_changed()

    def fab(self):
        from fabber import FabberLib
        return FabberLib(rundata=self.rundata, auto_load_models=False)

    def model_group_changed(self):
        idx = self.modellibCombo.currentIndex()
        if idx >= 0:
            lib = self.modellibCombo.itemData(idx)
            if lib != "":
                self.rundata["loadmodels"] = lib
            elif "loadmodels" in self.rundata:
                del self.rundata["loadmodels"]
            self.modellibCombo.setToolTip(lib)

            # Update the list of models
            models = self.fab().get_models()
            self.modelCombo.blockSignals(True)
            try:
                self.modelCombo.clear()
                for model in models:
                    self.modelCombo.addItem(model)
            finally:
                self.modelCombo.blockSignals(False)
                if self.rundata.get("model", "") in models:
                    self.modelCombo.setCurrentIndex(self.modelCombo.findText(self.rundata["model"]))
                else:
                    self.modelCombo.setCurrentIndex(0)
      
    def model_changed(self):
        model = self.modelCombo.currentText()
        self.rundata["model"] = model

    def method_changed(self):
        method = self.methodCombo.currentText()
        self.rundata["method"] = method

    def show_model_options(self):
        model = self.rundata["model"]
        dlg = OptionsDialog(self, ivm=self.ivm, rundata=self.rundata, desc_first=True)
        opts, desc = self.fab().get_options(model=model)
        dlg.set_title("Forward Model: %s" % model, desc)
        dlg.set_options(opts)
        if dlg.exec_():
            pass

    def show_method_options(self):
        method = self.rundata["method"]
        dlg = OptionsDialog(self, ivm=self.ivm, rundata=self.rundata, desc_first=True)
        opts, desc = self.fab().get_options(method=method)
        dlg.set_title("Inference method: %s" % method, desc)
        dlg.set_options(opts)
        dlg.fit_width()
        dlg.exec_()
        
    def show_general_options(self):
        dlg = OptionsDialog(self, ivm=self.ivm, rundata=self.rundata, desc_first=True)
        dlg.ignore("model", "method", "output", "data", "mask", "data<n>", "overwrite", "help",
                   "listmodels", "listmethods", "link-to-latest", "data-order", "dump-param-names",
                   "loadmodels")
        opts, desc = self.fab().get_options()
        dlg.set_options(opts)
        dlg.fit_width()
        dlg.exec_()
        
    def show_prior_options(self):
        dlg = PriorsDialog(self, ivm=self.ivm, rundata=self.rundata)
        try:
            params = self.fab().get_model_params(self.rundata)
        except Exception, e:
            raise QpException("Unable to get list of model parameters\n\n%s\n\nModel options must be set before parameters can be listed" % str(e))
        dlg.set_params(params)
        dlg.fit_width()
        dlg.exec_()
        
    def get_process(self):
        process = FabberProcess(self.ivm)
        return process

    def get_rundata(self):
        return self.rundata

    def save_file(self):
        self.rundata.save()

    def save_as_file(self):
        # fixme choose file name
        # fixme overwrite
        # fixme clone data
        fname = QtGui.QFileDialog.getSaveFileName()[0]
        self.rundata.set_file(fname)
        self.rundata.save()
        self.fileEdit.setText(fname)
        self.saveBtn.setEnabled(True)

    def open_file(self):
        filename = QtGui.QFileDialog.getOpenFileName()[0]
        if filename:
            self.fileEdit.setText(filename)
            self.rundata = dict(FabberRunData(filename))
            self.saveBtn.setEnabled(True)
            self.reset()

    def batch_options(self):
        return "Fabber", self.rundata

QP_WIDGETS = [FabberWidget]
QP_PROCESSES = [FabberProcess]
