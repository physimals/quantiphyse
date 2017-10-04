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

from ...gui.widgets import HelpButton, BatchButton, OverlayCombo, NumericOption, NumberList, LoadNumbers, OrderList, OrderListButtons
from ...gui.dialogs import TextViewerDialog, error_dialog, GridEditDialog
from ...analysis import Process
from ...analysis.fab import FabberProcess
from .. import QpWidget
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

class FabberWidget(QpWidget):
    """
    Widget for running Fabber model fitting
    """

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
        runBox = self.run_box(self.start_task)

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
        self.rundata["save-model-fit"] = ""
        self.rundata["save-model-extras"] = ""
        self.reset()

    def run_box(self, start_fn):
        runBox = QtGui.QGroupBox()
        runBox.setTitle('Running')
        runBox.setSizePolicy(QtGui.QSizePolicy.MinimumExpanding, QtGui.QSizePolicy.MinimumExpanding)
        runVbox = QtGui.QVBoxLayout()
        runBox.setLayout(runVbox)

        hbox = QtGui.QHBoxLayout()
        self.runBtn = QtGui.QPushButton('Run modelling', self)
        self.runBtn.clicked.connect(start_fn)
        hbox.addWidget(self.runBtn)
        self.progress = QtGui.QProgressBar(self)
        self.progress.setStatusTip('Progress of Fabber model fitting. Be patient. Progress is only updated in chunks')
        hbox.addWidget(self.progress)
        self.logBtn = QtGui.QPushButton('View log', self)
        self.logBtn.clicked.connect(self.view_log)
        self.logBtn.setEnabled(False)
        hbox.addWidget(self.logBtn)
        runVbox.addLayout(hbox)

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
        runVbox.addLayout(hbox)

        return runBox

    def activate(self):
        self.ivm.sig_all_data.connect(self.overlays_changed)

    def deactivate(self):
        self.ivm.sig_all_data.disconnect(self.overlays_changed)

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
        if self.ivm.main is None:
            error_dialog("No data loaded")
            return

        # set the progress value
        self.progress.setValue(0)
        self.runBtn.setEnabled(False)
        self.logBtn.setEnabled(False)

        self.process = FabberProcess(self.ivm)
        self.process.sig_finished.connect(self.run_finished)
        self.process.sig_progress.connect(self.update_progress)
        self.process.run(self.rundata)

    def run_finished(self, status, results, log):
        """
        Callback called when an async fabber run completes
        """
        try:
            self.log = log
            if status == Process.SUCCEEDED:
                if self.savefilesCb.isChecked():
                    save_folder = self.saveFolderEdit.text()       
                    for ovl in results[0].data:
                        save(self.ivm.data[ovl], os.path.join(save_folder, ovl.name + ".nii"))
                        logfile = open(os.path.join(save_folder, "logfile"), "w")
                        logfile.write(self.log)
                        logfile.close()
            else:
                raise results
                QtGui.QMessageBox.warning(None, "Fabber error", "Fabber failed to run:\n\n" + str(results),
                                        QtGui.QMessageBox.Close)
        finally:
            self.runBtn.setEnabled(True)
            self.logBtn.setEnabled(True)

    def update_progress(self, complete):
        self.progress.setValue(100*complete)

    def view_log(self):
         self.logview = TextViewerDialog(text=self.log, parent=self)
         self.logview.show()
         self.logview.raise_()

CITE_CEST = """
Modelling for Chemical Exchange Saturation Transfer MRI<br><br>
<i>Chappell, M. A., Donahue, M. J., Tee, Y. K., Khrapitchev, A. A., Sibson, N. R., Jezzard, P., & Payne, S. J. (2012).<br>
Quantitative Bayesian model-based analysis of amide proton transfer MRI. Magnetic Resonance in Medicine. doi:10.1002/mrm.24474</i>
"""

# FIXME correct numbers
CEST_POOLVAL_TYPES = ["3T", "9.4T"]

CEST_POOLS = [
    {"name" : "Water", "default" : True, "vals" : 
        ["4.00252e8     0       1.8     0.05", 
         "1.2774e8      0       1.3     0.05"]
    },
    {"name" : "Amide", "default" : True, "vals" : 
        ["3.5           30      1.8     0.001", 
         "3.5           20      0.77    0.01"]
    },
    {"name" : "NOE", "default" : True, "vals" : 
        ["-2.41          20     1.8     0.0005", 
         "-2.34         40      1.0     0.0004"]
    },
    {"name" : "MT", "default" : False, "vals" : 
        ["0 0 0 0", 
         "0 0 0 0"]
    },
    {"name" : "Amine", "default" : False, "vals" : 
        ["0 0 0 0", 
         "0 0 0 0"]
    },
]

class CESTWidget(FabberWidget):
    """
    CEST-specific widget, using the Fabber process
    """

    def __init__(self, **kwargs):
        super(FabberWidget, self).__init__(name="CEST", icon="cest", 
                                           desc="CEST analysis",
                                           **kwargs)
        
    def init_ui(self):
        vbox = QtGui.QVBoxLayout()
        self.setLayout(vbox)

        try:
            self.fabber_ex, self.fabber_lib, self.model_libs = find_fabber()
            if self.fabber_lib is None:
                vbox.addWidget(QtGui.QLabel("Fabber core library not found.\n\n You must install FSL and Fabber to use this widget"))
                return
        except:
            vbox.addWidget(QtGui.QLabel("Could not load Fabber Python API.\n\n You must install FSL and Fabber to use this widget"))
            return

        hbox = QtGui.QHBoxLayout()
        hbox.addWidget(QtGui.QLabel('<font size="5">CEST</font>'))
        hbox.addStretch(1)
        hbox.addWidget(BatchButton(self))
        hbox.addWidget(HelpButton(self, "cest"))
        vbox.addLayout(hbox)
        
        cite = QtGui.QLabel(CITE_CEST)
        cite.setWordWrap(True)
        vbox.addWidget(cite)
        vbox.addWidget(QtGui.QLabel(""))

        seqBox = QtGui.QGroupBox()
        seqBox.setTitle("Sequence")
        grid = QtGui.QGridLayout()
        grid.setColumnStretch(2, 1)
        seqBox.setLayout(grid)

        grid.addWidget(QtGui.QLabel("Frequency offsets"), 0, 0)
        self.freq_offsets = NumberList([1, 2, 3, 4, 5])
        grid.addWidget(self.freq_offsets, 0, 1, 1, 2)
        self.load_freq_offsets = LoadNumbers(self.freq_offsets)
        grid.addWidget(self.load_freq_offsets, 0, 3)

        self.b1 = NumericOption("B1 (\u03bcT)", grid, ypos=1, xpos=0, default=0.55, decimals=6)
        hbox = QtGui.QHBoxLayout()
        self.unsat_cb = QtGui.QCheckBox("Unsaturated")
        self.unsat_cb.stateChanged.connect(self.update_ui)
        hbox.addWidget(self.unsat_cb)
        self.unsat_combo = QtGui.QComboBox()
        self.unsat_combo.addItem("first")
        self.unsat_combo.addItem("last")
        self.unsat_combo.addItem("first and last  ")
        hbox.addWidget(self.unsat_combo)
        hbox.addStretch(1)
        grid.addLayout(hbox, 1, 2)
        
 #       self.b1.spin.setSizePolicy(QtGui.QSizePolicy.Maximum, QtGui.QSizePolicy.Preferred)

        grid.addWidget(QtGui.QLabel("Saturation"), 2, 0)
        self.sat_combo = QtGui.QComboBox()
        self.sat_combo.addItem("Continuous Saturation   ")
        self.sat_combo.addItem("Pulsed Saturation   ")
        self.sat_combo.currentIndexChanged.connect(self.update_ui)
        self.sat_combo.setSizeAdjustPolicy(QtGui.QComboBox.AdjustToContents)
#        self.sat_combo.setSizePolicy(QtGui.QSizePolicy.Maximum, QtGui.QSizePolicy.Preferred)
        grid.addWidget(self.sat_combo, 2, 1)

        # Continuous saturation
        self.st = NumericOption("Saturation times (s)", grid, ypos=3, xpos=0, default=2.0)
#        self.st.spin.setSizePolicy(QtGui.QSizePolicy.Maximum, QtGui.QSizePolicy.Preferred)

        # Pulsed saturation
        self.pms_label = QtGui.QLabel("Pulse Magnitudes")
        grid.addWidget(self.pms_label, 4, 0)
        self.pms = NumberList([0, 0, 0, 0])
        grid.addWidget(self.pms, 4, 1, 1, 2)
        self.load_pms = LoadNumbers(self.pms)
        grid.addWidget(self.load_pms, 4, 3)
        self.pds_label = QtGui.QLabel("Pulse Durations (s)")
        grid.addWidget(self.pds_label, 5, 0)
        self.pds = NumberList([0, 0, 0, 0])
        grid.addWidget(self.pds, 5, 1, 1, 2)
        self.load_pds = LoadNumbers(self.pds)
        grid.addWidget(self.load_pds, 5, 3)
        self.pr = NumericOption("Pulse Repeats", grid, ypos=6, xpos=0, default=1, intonly=True)
#        self.pr.spin.setSizePolicy(QtGui.QSizePolicy.Maximum, QtGui.QSizePolicy.Preferred)
        
        vbox.addWidget(seqBox)
    
        poolBox = QtGui.QGroupBox()
        poolBox.setTitle("Pools")
        poolVbox = QtGui.QVBoxLayout()
        poolBox.setLayout(poolVbox)

        grid = QtGui.QGridLayout()
        row, col = 0, 0
        NUM_ROWS = 2
        self.pool_cbs, self.custom_poolvals = {}, {}
        for pool in CEST_POOLS:
            name = pool["name"]
            self.custom_poolvals[name] = pool["vals"][0]
            self.pool_cbs[name] = QtGui.QCheckBox(name)
            self.pool_cbs[name].setChecked(pool["default"])
            self.pool_cbs[name].stateChanged.connect(self.update_pools)
            grid.addWidget(self.pool_cbs[name], row, col)
            row += 1
            if row == NUM_ROWS:
                row = 0
                col += 1
        self.poolval_combo = QtGui.QComboBox()
        for poolval_type in CEST_POOLVAL_TYPES:
            self.poolval_combo.addItem("%s defaults" % poolval_type)
        self.poolval_combo.addItem("custom")
        self.poolval_combo.currentIndexChanged.connect(self.update_pools)
        grid.addWidget(self.poolval_combo, row+1, 0, 1, 2)
        edit_btn = QtGui.QPushButton("Edit")
        edit_btn.clicked.connect(self.edit_pools)
        grid.addWidget(edit_btn, row+1, 2)
        poolVbox.addLayout(grid)

        anBox = QtGui.QGroupBox()
        anBox.setTitle("Analysis")
        anVbox = QtGui.QVBoxLayout()
        anBox.setLayout(anVbox)

        grid = QtGui.QGridLayout()
        self.spatial_cb = QtGui.QCheckBox("Spatial smoothing")
        grid.addWidget(self.spatial_cb, 0, 0, 1, 2)
        self.t12_cb = QtGui.QCheckBox("Allow uncertainty in T1/T2 values")
        self.t12_cb.stateChanged.connect(self.update_ui)
        grid.addWidget(self.t12_cb, 1, 0, 1, 2)
        self.t1_cb = QtGui.QCheckBox("T1 map")
        self.t1_cb.stateChanged.connect(self.update_ui)
        grid.addWidget(self.t1_cb, 2, 0)
        self.t1_ovl = OverlayCombo(self.ivm, static_only=True)
        self.t1_ovl.setEnabled(False)
        grid.addWidget(self.t1_ovl, 2, 1)
        self.t2_cb = QtGui.QCheckBox("T2 map")
        self.t2_cb.stateChanged.connect(self.update_ui)
        grid.addWidget(self.t2_cb, 3, 0)
        self.t2_ovl = OverlayCombo(self.ivm, static_only=True)
        self.t2_ovl.setEnabled(False)
        grid.addWidget(self.t2_ovl, 3, 1)
        anVbox.addLayout(grid)

        hbox = QtGui.QHBoxLayout()
        hbox.addWidget(poolBox)
        hbox.addWidget(anBox)
        hbox.addStretch(1)
        vbox.addLayout(hbox)

        runBox = self.run_box(self.start_cest)
        vbox.addWidget(runBox)
        vbox.addStretch(1)

        self.rundata = FabberRunData()

        # General defaults
        self.rundata["fabber_lib"] = self.fabber_lib
        self.rundata["save-mean"] = ""
        self.rundata["save-model-fit"] = ""
        self.rundata["noise"] = "white"
        self.rundata["max-iterations"] = "20"
        self.rundata["model"] = "cest"

        # Placeholders to be replaced with temp files
        self.rundata["pools"] = "pools.mat"
        self.rundata["ptrain"] = "ptrain.mat"
        self.rundata["spec"] = "dataspec.mat"

        self.update_ui()
        self.update_pools()

    def update_volumes_axis(self):
        """ 
        Update 'volumes' axis to use the frequency offsets in 
        graphs etc.
        
        Options should be handled much more cleanly than this!
        """
        freqs  = self.freq_offsets.values()
        if self.ivm.main.ndim == 4 and len(freqs) == self.ivm.main.nvols:
            self.opts.t_combo.setCurrentIndex(1)
            self.opts.t_scale = self.freq_offsets.values()
            self.opts.sig_options_changed.emit(self)

    def update_pools(self):
        poolval_idx = self.poolval_combo.currentIndex()
        self.pools = []
        for pool in CEST_POOLS:
            if self.pool_cbs[pool["name"]].isChecked():
                if poolval_idx < self.poolval_combo.count()-1:
                    # Using default values
                    vals = pool["vals"][poolval_idx]
                else:
                    # Using custom values
                    vals = self.custom_poolvals[pool["name"]]

                self.pools.append((pool["name"], vals))
        print(self.pools)

    def edit_pools(self):
        vals, pool_headers = [], []
        for name, pvals in self.pools:
            pool_headers.append(name)
            rvals = [float(v) for v in pvals.split()]
            vals.append(rvals)
        val_headers = ["PPM offset", "Exch rate", "T1", "T2"]
        d = GridEditDialog(self, vals, col_headers=val_headers, row_headers=pool_headers, expandable=False)
        if d.exec_():
            vals = d.table.values()
            for row, pool in enumerate(self.pools):
                rvals = vals[row]
                self.custom_poolvals[pool[0]] = " ".join([str(v) for v in rvals])
            self.poolval_combo.setCurrentIndex(self.poolval_combo.count()-1)
            self.update_pools()

    def overlays_changed(self, overlays):
        # Not required for CEST widget
        pass

    def update_options(self):
        if self.spatial_cb.isChecked():
            self.rundata["method"] = "spatialvb"
            self.rundata["param-spatial-priors"] = "MN+"
        else:
            self.rundata["method"] = "vb"
            del self.rundata["param-spatial-priors"]
            
        prior_num = 1
        if self.t12_cb.isChecked():
            self.rundata["t12prior"] = ""
            if self.t1_cb.isChecked():
                self.rundata["PSP_byname%i" % prior_num] = "T1a"
                self.rundata["PSP_byname%i_type" % prior_num] = "I"
                self.rundata["PSP_byname%i_image" % prior_num] = self.t1_ovl.currentText()
                prior_num += 1

            if self.t2_cb.isChecked():
                self.rundata["PSP_byname%i" % prior_num] = "T2a"
                self.rundata["PSP_byname%i_type" % prior_num] = "I"
                self.rundata["PSP_byname%i_image" % prior_num] = self.t2_ovl.currentText()
                prior_num += 1
        else:
            del self.rundata["t12prior"]
            
        for n in range(prior_num, len(CEST_POOLS)*2+1):
            del self.rundata["PSP_byname%i" % n]
            del self.rundata["PSP_byname%i_type" % n]
            del self.rundata["PSP_byname%i_image" % n]

    def update_ui(self):
        """ Update visibility / enabledness of widgets """
        self.pulsed = self.sat_combo.currentIndex() == 1
        self.st.spin.setVisible(not self.pulsed)
        self.st.label.setVisible(not self.pulsed)
        self.pds.setVisible(self.pulsed)
        self.pds_label.setVisible(self.pulsed)
        self.load_pds.setVisible(self.pulsed)
        self.pms.setVisible(self.pulsed)
        self.pms_label.setVisible(self.pulsed)
        self.load_pms.setVisible(self.pulsed)
        self.pr.spin.setVisible(self.pulsed)
        self.pr.label.setVisible(self.pulsed)
        self.t1_cb.setEnabled(self.t12_cb.isChecked())
        self.t2_cb.setEnabled(self.t12_cb.isChecked())
        self.t1_ovl.setEnabled(self.t12_cb.isChecked() and self.t1_cb.isChecked())
        self.t2_ovl.setEnabled(self.t12_cb.isChecked() and self.t2_cb.isChecked())
        self.unsat_combo.setEnabled(self.unsat_cb.isChecked())

    def get_dataspec(self):
        dataspec = ""
        freqs = self.freq_offsets.values()
        for idx, freq in enumerate(freqs):
            if self.pulsed:
                repeats = self.pr.spin.value()
            else:
                repeats = 1
            b1 = self.b1.spin.value()/1e6
            if self.unsat_cb.isChecked():
                print("Unsat", idx, self.unsat_combo.currentIndex())
                if idx == 0 and self.unsat_combo.currentIndex() in (0, 2):
                    b1 = 0
                elif idx == len(freqs)-1 and self.unsat_combo.currentIndex() in (1, 2):
                    b1 = 0
            dataspec += "%g %g %i\n" % (freq, b1, repeats)
        print(dataspec)
        return dataspec

    def get_ptrain(self):
        ptrain = ""
        if self.pulsed:
            if not self.pms.valid() or not self.pms.valid():
                raise RuntimeError("Non-numeric values in pulse specification")
            pms = self.pms.values()
            pds = self.pds.values()
            if len(pms) != len(pds):
                raise RuntimeError("Pulse magnitude and duration must contain the same number of values")
            for pm, pd in zip(pms, pds):
                ptrain += "%g %g\n" % (pm, pd)
        else:
            ptrain += "1 %g\n" % self.st.spin.value()
        print(ptrain)
        return ptrain

    def get_poolmat(self):
        poolmat = "\n".join([p[1] for p in self.pools])
        print(poolmat)
        return poolmat

    def write_temp(self, name, data):
        f = tempfile.NamedTemporaryFile(prefix=name, delete=False)
        f.write(data) 
        f.close()
        return f.name

    def start_cest(self):
        self.update_options()
        self.rundata["ptrain"] = self.write_temp("ptrain", self.get_ptrain())
        self.rundata["spec"] = self.write_temp("dataspec", self.get_dataspec())
        self.rundata["pools"] = self.write_temp("poolmat", self.get_poolmat())
        self.rundata["debug"] = ""

        for item in self.rundata.items():
            print("%s: %s" % item)
        self.start_task()

    def run_finished(self, status, results, log):
        # Remove temp files after run completes
        os.remove(self.rundata["ptrain"])
        os.remove(self.rundata["spec"])
        os.remove(self.rundata["pools"])

        # Then do default Fabber actions
        FabberWidget.run_finished(self, status, results, log)

        # Update 'volumes' axis to contain frequencies
        # FIXME removed as effectively requires frequencies to be
        # ordered and doesn't seem to look very good either
        #if status == Process.SUCCEEDED:
        #    self.update_volumes_axis()    

CITE_ASL = """
Modelling for Arterial Spin Labelling MRI<br><br>
<i>Chappell MA, Groves AR, Whitcher B, Woolrich MW. Variational Bayesian inference for a non-linear forward model. 
IEEE Transactions on Signal Processing 57(1):223-236, 2009.</i><br><br>
<b>This widget is a UI preview and is not yet functional</b>
"""

class AslDataPreview(QtGui.QWidget):
    def __init__(self, order, tagfirst, parent=None):
        QtGui.QWidget.__init__(self, parent)
        self.set_order(order, tagfirst)
        self.hfactor = 0.95
        self.vfactor = 0.95
        self.cols = {"R" : (128, 128, 255, 128), "T" : (255, 128, 128, 128), "P" : (128, 255, 128, 128)}
        self.setFixedHeight(self.fontMetrics().height()*4)
    
    def set_order(self, order, tagfirst):
        self.order = order
        self.tagfirst = tagfirst
        self.labels = {"R" : ("Repeat ", "R"), "T" : ("TI " , "TI")}
        if tagfirst:
            self.labels["P"] = (("Tag", "Control"), ("T", "C"))
        else:
            self.labels["P"] = (("Control", "Tag"), ("C", "T"))
        self.repaint()

    def get_label(self, code, short):
        labels = self.labels[code]
        if short: return labels[1]
        else: return labels[0]
        
    def draw_groups(self, p, groups, ox, oy, width, height, cont=False):
        if len(groups) == 0: return
        else:
            small = width < 100
            group = groups[0]
            label = self.get_label(group, small)
            col = self.cols[group]
            if cont:
                p.fillRect(ox, oy, width-1, height-1, QtGui.QBrush(QtGui.QColor(*col)))
                p.drawText(ox, oy, width-1, height, QtCore.Qt.AlignHCenter, "...")
                self.draw_groups(p, groups[1:], ox, oy+height, width, height, cont=True)
            elif group == "P":
                w = width/2
                for c in range(2):
                    p.fillRect(ox+c*w, oy, w-1, height-1, QtGui.QBrush(QtGui.QColor(*col)))
                    p.drawText(ox+c*w, oy, w-1, height, QtCore.Qt.AlignHCenter, label[c])
                    self.draw_groups(p, groups[1:], ox+c*w, oy+height, w, height)
            else:
                w = 2*width/5
                for c in range(2):
                    p.fillRect(ox+c*w, oy, w-1, height-1, QtGui.QBrush(QtGui.QColor(*col)))
                    p.drawText(ox+c*w, oy, w-1, height, QtCore.Qt.AlignHCenter, label + str(c+1))
                    self.draw_groups(p, groups[1:], ox+c*w, oy+height, w, height)
                self.draw_groups(p, groups, ox+2*w, oy, w/2, height, cont=True)

    def paintEvent(self, ev):
        h, w = self.height(), self.width()
        group_height = h*self.vfactor / len(self.order)
        group_width = self.hfactor*w
        ox = w*(1-self.hfactor)/2
        oy = h*(1-self.vfactor)/2
        p = QtGui.QPainter(self)
#        p.begin()
        self.draw_groups(p, self.order, ox, oy, group_width, group_height)
 #       p.end()
        
class ASLWidget(FabberWidget):
    """
    ASL-specific widget, using the Fabber process
    """

    def __init__(self, **kwargs):
        super(FabberWidget, self).__init__(name="ASL", icon="fabber", 
                                           desc="ASL analysis",
                                           **kwargs)
        self.groups = {"P" : "Tag/Control pairs", "R" : "Repeats", "T" : "TIs"}
        self.default_order = "TRP"

    def init_ui(self):
        vbox = QtGui.QVBoxLayout()
        self.setLayout(vbox)

        try:
            self.fabber_ex, self.fabber_lib, self.model_libs = find_fabber()
            if self.fabber_lib is None:
                vbox.addWidget(QtGui.QLabel("Fabber core library not found.\n\n You must install FSL and Fabber to use this widget"))
                return
        except:
            vbox.addWidget(QtGui.QLabel("Could not load Fabber Python API.\n\n You must install FSL and Fabber to use this widget"))
            return

        hbox = QtGui.QHBoxLayout()
        hbox.addWidget(QtGui.QLabel('<font size="5">ASL</font>'))
        hbox.addStretch(1)
        hbox.addWidget(BatchButton(self))
        hbox.addWidget(HelpButton(self, "asl"))
        vbox.addLayout(hbox)
        
        cite = QtGui.QLabel(CITE_ASL)
        cite.setWordWrap(True)
        vbox.addWidget(cite)

        preprocBox = QtGui.QGroupBox("Preprocessing")
        grid = QtGui.QGridLayout()
        preprocBox.setLayout(grid)

        grid.addWidget(QtGui.QLabel("Data format"), 0, 0)
        self.tc_combo = QtGui.QComboBox()
        self.tc_combo.addItem("Tag-control pairs")
        self.tc_combo.addItem("Tag-control subtracted")
        self.tc_combo.currentIndexChanged.connect(self.update_ui)
        grid.addWidget(self.tc_combo, 0, 1)
        self.tc_ord_combo = QtGui.QComboBox()
        self.tc_ord_combo.addItem("Tag first")
        self.tc_ord_combo.addItem("Control first")
        self.tc_ord_combo.currentIndexChanged.connect(self.update_ui)
        grid.addWidget(self.tc_ord_combo, 0, 2)

        grid.addWidget(QtGui.QLabel("Data grouping\n(top = outermost)"), 1, 0, alignment=QtCore.Qt.AlignTop)
        self.group_list = OrderList()
        grid.addWidget(self.group_list, 1, 1)
        self.list_btns = OrderListButtons(self.group_list)
        grid.addLayout(self.list_btns, 1, 2)
        # Have to set items after adding to grid or sizing doesn't work right
        self.group_list.setItems([self.groups[g] for g in self.default_order])
        self.group_list.sig_changed.connect(self.update_ui)

        self.data_preview = AslDataPreview(self.default_order, True)
        grid.addWidget(self.data_preview, 2, 0, 1, 3)

        vbox.addWidget(preprocBox)

        dataBox = QtGui.QGroupBox("Acquisition")
        grid = QtGui.QGridLayout()
        dataBox.setLayout(grid)

        # FIXME add multiband readout options?

        grid.addWidget(QtGui.QLabel("Labelling"), 0, 0)
        self.lbl_combo = QtGui.QComboBox()
        self.lbl_combo.addItem("cASL/pcASL")
        self.lbl_combo.addItem("pASL")
        self.lbl_combo.currentIndexChanged.connect(self.update_ui)
        grid.addWidget(self.lbl_combo, 0, 1)

        self.plds_label = QtGui.QLabel("PLDs")
        grid.addWidget(self.plds_label, 1, 0)
        self.plds = NumberList([1.5,])
        grid.addWidget(self.plds, 1, 1, 1, 2)

        grid.addWidget(QtGui.QLabel("Bolus Durations"), 2, 0)
        self.taus = NumberList([1.4,])
        grid.addWidget(self.taus, 2, 1, 1, 2)

        vbox.addWidget(dataBox)

        analysisBox = QtGui.QGroupBox("Analysis")
        grid = QtGui.QGridLayout()
        analysisBox.setLayout(grid)

        self.bat = NumericOption("Bolus arrival time (s)", grid, ypos=0, xpos=0, default=1.3, decimals=2)
        self.ie = NumericOption("Inversion efficiency", grid, ypos=1, xpos=0, default=0.85, decimals=2)
        self.t1 = NumericOption("T1 (s)", grid, ypos=0, xpos=2, default=1.3, decimals=2)
        self.t1b = NumericOption("T1b (s)", grid, ypos=1, xpos=2, default=1.65, decimals=2)

        self.spatial_cb = QtGui.QCheckBox("Spatial smoothing")
        grid.addWidget(self.spatial_cb, 4, 0, 1, 2)
        self.t1_cb = QtGui.QCheckBox("Allow uncertainty in T1 values")
        grid.addWidget(self.t1_cb, 5, 0, 1, 2)
        self.mv_cb = QtGui.QCheckBox("Include macro vascular component")
        grid.addWidget(self.mv_cb, 6, 0, 1, 2)
        self.fixtau_cb = QtGui.QCheckBox("Fix bolus duration")
        grid.addWidget(self.fixtau_cb, 4, 2, 1, 2)
        #self.pvc_cb = QtGui.QCheckBox("Partial volume correction")
        #grid.addWidget(self.pvc_cb, 5, 2, 1, 2)

        vbox.addWidget(analysisBox)

        runBox = self.run_box(self.start_asl)
        vbox.addWidget(runBox)
        vbox.addStretch(1)

        self.rundata = FabberRunData()

        # General defaults
        self.rundata["fabber_lib"] = self.fabber_lib
        self.rundata["save-mean"] = ""
        self.rundata["save-model-fit"] = ""
        self.rundata["noise"] = "white"
        self.rundata["max-iterations"] = "20"
        self.rundata["model"] = "aslrest"

        self.update_ui()

    def overlays_changed(self, overlays):
        # Not required for ASL widget
        pass

    def update_ui(self):
        """ Update visibility / enabledness of widgets """
        self.tc_ord_combo.setEnabled(self.tc_combo.currentIndex() == 0)
        tagfirst = self.tc_ord_combo.currentIndex() == 0
        order = ""
        for item in self.group_list.items():
            code = [k for k, v in self.groups.items() if v == item][0]
            print(item, code)
            order += code
        print(order)
        self.data_preview.set_order(order, tagfirst)
        casl = self.lbl_combo.currentIndex() == 0
        if casl:
            self.plds_label.setText("PLDs")
        else:
            self.plds_label.setText("TIs")

    def get_vol_idx(self, tidx, ntis, ridx, nrepeats, tcidx, ntcs):
        idx = 0
        for code in self.data_preview.order:
            if code == "R":
                idx *= nrepeats
                idx += ridx
            elif code == "T":
                idx *= ntis
                idx += tidx
            else:
                idx *= ntcs
                idx += tcidx
        return idx

    def start_asl(self):
        # First preprocess the data to put it in the format the Fabber model expects.
        # This is outer grouping of TIs, then by repeats and finally tag/control pairs
        nvols = self.ivm.main.nvols
        ntis = len(self.plds.values())
        if nvols % ntis != 0:
            raise RuntimeError("Number of volumes (%i) not consistent with %i PLDs" % (nvols, ntis))
        nrepeats = int(nvols / ntis)

        tcpairs = ctpairs = False
        if self.tc_combo.currentIndex() == 0:
            # Need to do tag/control subtraction
            if nrepeats % 2 != 0:
                raise RuntimeError("Number of volumes (%i) not consistent with %i PLDs and tag/control pairs" % (nvols, ntis))
            nvols = int(nvols/2)
            nrepeats = int(nrepeats/2)
            if self.tc_ord_combo.currentIndex() == 0:
                tcpairs = True
            else:
                ctpairs = True

        print("ntis=%i, nrepeats=%i, tcpairs=%i, ctpairs=%i, nvols=%i" % (ntis, nrepeats, tcpairs, ctpairs, nvols))
        asldata = np.zeros(list(self.ivm.grid.shape) + [nvols, ])
        out_idx = 0
        if tcpairs or ctpairs: npairs = 2
        else: npairs = 1
        for tidx in range(ntis):
            for ridx in range(nrepeats):
                idx1 = self.get_vol_idx(tidx, ntis, ridx, nrepeats, 0, npairs)
                idx2 = self.get_vol_idx(tidx, ntis, ridx, nrepeats, 1, npairs)
                print("tidx=%i, ridx=%i, vidx=%i" % (tidx, ridx, in_idx))
                if ctpairs:
                    # Do control - tag
                    print("Doing %i - %i" % (idx1, idx2))
                    asldata[:,:,:,out_idx] = self.ivm.main.std()[:,:,:,idx1] - self.ivm.main.std()[:,:,:,idx2]
                elif tcpairs:
                    # Do control - tag
                    print("Doing %i - %i" % (idx2, idx1))
                    asldata[:,:,:,out_idx] = self.ivm.main.std()[:,:,:,idx2] - self.ivm.main.std()[:,:,:,idx1]
                else:
                    asldata[:,:,:,out_idx] = self.ivm.main.std()[:,:,:,idx1]
                out_idx += 1

#        meandiff = np.mean(asldata, 3)
#        self.ivm.add_data(meandiff, name="diff", make_current=True)
        self.ivm.add_data(asldata, name="asldata", make_main=True)
        
        # Acquisition parameters
        if self.lbl_combo.currentIndex() == 0:
            self.rundata["casl"] = ""
        else:
            del self.rundata["casl"]

        tis = self.plds.values()
        taus = self.taus.values()
        singletau = None
        if len(taus) == 1:
            singletau = taus[0]
            self.rundata["tau"] = str(singletau)
        elif len(tis) != len(taus):
            raise RuntimeError("Number of bolus durations must match number TIs if more than one value given")
        else:
            for idx, tau in enumerate(tau):
                self.rundata["tau%i" % (idx+1)] = str(tau)
        
        for idx, ti in enumerate(tis):
            if "casl" in self.rundata:
                if singletau is not None: ti += singletau
                else: ti += taus[idx]
            self.rundata["ti%i" % (idx+1)] = str(ti)

        self.rundata["repeats"] = str(nrepeats)

        # Starting values
        self.rundata["t1"] = str(self.t1.spin.value())
        self.rundata["t1b"] = str(self.t1b.spin.value())
        self.rundata["bat"] = str(self.bat.spin.value())
        # FIXME inversion efficiency?
        # FIXME batsd

        # Analysis options
        self.rundata["infertiss"] = ""
        self.rundata["inctiss"] = ""

        if self.spatial_cb.isChecked():
            self.rundata["method"] = "spatialvb"
        else:
            self.rundata["method"] = "vb"

        if self.t1_cb.isChecked():
            self.rundata["infert1"] = ""
            self.rundata["inct1"] = ""
        else:
            del self.rundata["infert1"]
            del self.rundata["inct1"]

        if self.mv_cb.isChecked():
            self.rundata["inferart"] = ""
            self.rundata["incart"] = ""
        else:
            del self.rundata["inferart"]
            del self.rundata["incart"]
            
        if not self.fixtau_cb.isChecked():
            self.rundata["infertau"] = ""
            self.rundata["inctau"] = ""
        else:
            del self.rundata["infetau"]
            del self.rundata["inctau"]

        for item in self.rundata.items():
            print("%s: %s" % item)
        self.start_task()
        self.tc_combo.setCurrentIndex(1)


