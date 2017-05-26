"""
Author: Martin Craig <martin.craig@eng.ox.ac.uk>
Copyright (c) 2016-2017 University of Oxford, Martin Craig
"""

from __future__ import division, unicode_literals, absolute_import, print_function

import sys, os, warnings
import time
import traceback
import re

import nibabel as nib
import numpy as np
import pyqtgraph as pg
from PySide import QtCore, QtGui

from ...QtInherit import HelpButton, BatchButton
from ...QtInherit.dialogs import TextViewerDialog, error_dialog
from ...analysis import Process
from ...analysis.fab import FabberProcess
from .. import PkWidget
from .views import *
from .dialogs import ModelOptionsDialog, MatrixEditDialog

try:
    from fabber import FabberRunData, find_fabber
except:
    warnings.warn("Failed to import Fabber API - widget will be disabled")
    traceback.print_exc()

CITE = """
<i>Chappell, M.A., Groves, A.R., Woolrich, M.W.
"Variational Bayesian inference for a non-linear forward model"
IEEE Trans. Sig. Proc., 2009, 57(1), 223-236</i>
"""

class FabberWidget(PkWidget):
    """
    Widget for running Fabber model fitting
    """

    """ Signal emitted when async Fabber finished"""
    sig_finished = QtCore.Signal(tuple)

    def __init__(self, **kwargs):
        super(FabberWidget, self).__init__(name="Fabber", icon="fabber", 
                                           desc="Fabber Bayesian model fitting",
                                           **kwargs)
    
    def model_name(self, lib):
        match = re.match(".*fabber_models_(.+)\..+", lib, re.I)
        if match:
            return match.group(1).upper()
        else:
            return lib
    
    def model_group_changed(self, idx):
        if idx >= 0:
            lib = self.modellibCombo.itemData(idx)
            if lib != "":
                self.rundata["loadmodels"] = lib
            else:
                del self.rundata["loadmodels"]
            self.modellibCombo.setToolTip(lib)
        
    def init_ui(self):
        mainGrid = QtGui.QVBoxLayout()
        self.setLayout(mainGrid)

        try:
            self.fabber_ex, self.fabber_lib, self.model_libs = find_fabber()
            if self.fabber_lib is None:
                mainGrid.addWidget(QtGui.QLabel("Fabber core library not found.\n\n You must install FSL and Fabber to use this widget"))
                return
        except:
            mainGrid.addWidget(QtGui.QLabel("Could not load Fabber Python API.\n\n You must install FSL and Fabber to use this widget"))
            return

        hbox = QtGui.QHBoxLayout()
        hbox.addWidget(QtGui.QLabel('<font size="5">Fabber Bayesian Model Fitting</font>'))
        hbox.addStretch(1)
        hbox.addWidget(BatchButton(self))
        hbox.addWidget(HelpButton(self, "fabber"))
        mainGrid.addLayout(hbox)
        
        cite = QtGui.QLabel(CITE)
        cite.setWordWrap(True)
        mainGrid.addWidget(cite)
        mainGrid.addWidget(QtGui.QLabel(""))

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
        for lib in self.model_libs:
            self.modellibCombo.addItem(self.model_name(lib), lib)
        self.modellibCombo.currentIndexChanged.connect(self.model_group_changed)
        self.modellibCombo.setCurrentIndex(0)

        grid.addWidget(self.modellibCombo, 0, 1)
        grid.addWidget(QtGui.QLabel("Model"), 1, 0)
        self.modelCombo = QtGui.QComboBox(self)
        self.modelCombo.setSizeAdjustPolicy(QtGui.QComboBox.AdjustToContents)
        grid.addWidget(self.modelCombo, 1, 1)
        self.modelOptionsBtn = QtGui.QPushButton('Model Options', self)
        grid.addWidget(self.modelOptionsBtn, 1, 2)
        
        grid.addWidget(QtGui.QLabel("Inference method"), 4, 0)
        self.methodCombo = QtGui.QComboBox(self)
        self.methodCombo.setSizeAdjustPolicy(QtGui.QComboBox.AdjustToContents)
        grid.addWidget(self.methodCombo, 4, 1)
        self.methodOptionsBtn = QtGui.QPushButton('Inference Options', self)
        grid.addWidget(self.methodOptionsBtn, 4, 2)
        
        grid.addWidget(QtGui.QLabel("Parameter priors"), 5, 0)
        self.priorsBtn = QtGui.QPushButton('Edit', self)
        grid.addWidget(self.priorsBtn, 5, 2)
        
        grid.addWidget(QtGui.QLabel("General Options"), 6, 0)
        self.generalOptionsBtn = QtGui.QPushButton('Edit', self)
        grid.addWidget(self.generalOptionsBtn, 6, 2)
        
        mainGrid.addWidget(optionsBox)

        # Model options box
        #modelOptionsBox = QtGui.QGroupBox()
        #modelOptionsBox.setTitle('Model Options')
        #self.modelOptionsGrid = QtGui.QGridLayout()
        #modelOptionsBox.setLayout(self.modelOptionsGrid)
        #mainGrid.addWidget(modelOptionsBox)

        # Run box
        runBox = QtGui.QGroupBox()
        runBox.setTitle('Running')
        runBox.setSizePolicy(QtGui.QSizePolicy.MinimumExpanding, QtGui.QSizePolicy.MinimumExpanding)
        vbox = QtGui.QVBoxLayout()
        runBox.setLayout(vbox)

        hbox = QtGui.QHBoxLayout()
        self.runBtn = QtGui.QPushButton('Run modelling', self)
        self.runBtn.clicked.connect(self.start_task)
        hbox.addWidget(self.runBtn)
        self.progress = QtGui.QProgressBar(self)
        self.progress.setStatusTip('Progress of Fabber model fitting. Be patient. Progress is only updated in chunks')
        hbox.addWidget(self.progress)
        self.logBtn = QtGui.QPushButton('View log', self)
        self.logBtn.clicked.connect(self.view_log)
        self.logBtn.setEnabled(False)
        hbox.addWidget(self.logBtn)
        vbox.addLayout(hbox)

        hbox = QtGui.QHBoxLayout()
        self.savefilesCb = QtGui.QCheckBox("Save copy of output data")
        hbox.addWidget(self.savefilesCb)
        self.saveFolderEdit = QtGui.QLineEdit()
        hbox.addWidget(self.saveFolderEdit)
        btn = QtGui.QPushButton("Choose folder")
        btn.clicked.connect(self.chooseOutputFolder)
        hbox.addWidget(btn)
        self.savefilesCb.stateChanged.connect(self.saveFolderEdit.setEnabled)
        self.savefilesCb.stateChanged.connect(btn.setEnabled)
        vbox.addLayout(hbox)

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

        # Keep references to the option dialogs so we can update any image option views as overlays change
        self.modelOpts = ModelOptionsView(dialog=ModelOptionsDialog(self), btn=self.modelOptionsBtn, mat_dialog=MatrixEditDialog(self), desc_first=True)
        self.methodOpts = MethodOptionsView(dialog=ModelOptionsDialog(self), btn=self.methodOptionsBtn, mat_dialog=MatrixEditDialog(self), desc_first=True)
        self.generalOpts = OptionsView(dialog=ModelOptionsDialog(self), btn=self.generalOptionsBtn, mat_dialog=MatrixEditDialog(self), desc_first=True)
        self.priors = PriorsView(dialog=ModelOptionsDialog(self), btn=self.priorsBtn)

        self.views = [
            ModelMethodView(modelCombo=self.modelCombo, methodCombo=self.methodCombo),
            self.modelOpts, self.methodOpts, self.generalOpts, self.priors,
        ]

        self.generalOpts.ignore("output", "data", "mask", "data<n>", "overwrite", "method", "model", "help",
                                "listmodels", "listmethods", "link-to-latest", "data-order", "dump-param-names",
                                "loadmodels")
        self.rundata = FabberRunData()
        self.rundata["fabber_lib"] = self.fabber_lib
        self.rundata["save-mean"] = ""
        self.reset()

        self.process = FabberProcess(self.ivm)
        self.process.sig_finished.connect(self.run_finished_gui)
        self.process.sig_progress.connect(self.update_progress)

    def activate(self):
        self.ivm.sig_all_overlays.connect(self.overlays_changed)

    def deactivate(self):
        self.ivm.sig_all_overlays.disconnect(self.overlays_changed)

    def chooseOutputFolder(self):
        outputDir = QtGui.QFileDialog.getExistingDirectory(self, 'Choose directory to save output')
        if outputDir:
            self.saveFolderEdit.setText(outputDir)

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
            self.rundata = FabberRunData(filename)
            self.saveBtn.setEnabled(True)
            self.reset()

    def reset(self):
        for view in self.views: self.rundata.add_view(view)

    def overlays_changed(self, overlays):
        """
        Update image data views
        """
        global CURRENT_OVERLAYS
        CURRENT_OVERLAYS = overlays
        for dialog in (self.methodOpts, self.modelOpts, self.methodOpts):
            for view in dialog.views.values():
                if isinstance(view, ImageOptionView):
                    view.update_list()
        self.priors.overlays = overlays
        self.priors.repopulate()

    def batch_options(self):
        return "Fabber", self.rundata

    def start_task(self):
        """
        Start running the Fabber modelling on button click
        """
        if self.ivm.vol is None:
            error_dialog("No data loaded")
            return

        # set the progress value
        self.progress.setValue(0)
        self.runBtn.setEnabled(False)
        self.logBtn.setEnabled(False)

        self.process.run(self.rundata)

    def run_finished_gui(self, status, results, log):
        """
        Callback called when an async fabber run completes
        """
        self.log = log
        if status == Process.SUCCEEDED:
            save_files = self.savefilesCb.isChecked()     
            if save_files:
                save_folder = self.saveFolderEdit.text()       
                for ovl in results[0].data:
                    self.ivm.overlays[ovl].save_nifti(os.path.join(save_folder, ovl.name))
                    logfile = open(os.path.join(save_folder, "logfile"), "w")
                    logfile.write(self.log)
                    logfile.close()
        else:
            QtGui.QMessageBox.warning(None, "Fabber error", "Fabber failed to run:\n\n" + str(results),
                                      QtGui.QMessageBox.Close)

        self.runBtn.setEnabled(True)
        self.logBtn.setEnabled(status == Process.SUCCEEDED)

    def update_progress(self, complete):
        self.progress.setValue(100*complete)

    def view_log(self):
         self.logview = TextViewerDialog(log=self.log, parent=self)
         self.logview.show()
         self.logview.raise_()
