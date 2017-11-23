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

from quantiphyse.gui.widgets import QpWidget, HelpButton, BatchButton, OverlayCombo, NumericOption, NumberGrid, NumberList, LoadNumbers, OrderList, OrderListButtons, Citation, TitleWidget, RunBox
from quantiphyse.gui.dialogs import TextViewerDialog, error_dialog, GridEditDialog
from quantiphyse.analysis import Process
from quantiphyse.utils import debug, warn, get_plugins
from quantiphyse.utils.exceptions import QpException

CEST_CITE_TITLE = "Quantitative Bayesian model-based analysis of amide proton transfer MRI"
CEST_CITE_AUTHOR = "Chappell, M. A., Donahue, M. J., Tee, Y. K., Khrapitchev, A. A., Sibson, N. R., Jezzard, P., & Payne, S. J."
CEST_CITE_JOURNAL = "Magnetic Resonance in Medicine. doi:10.1002/mrm.24474"

B0_DEFAULTS = ["3T", "9.4T", "Custom"]

# Gyromagnetic ratio / 2PI
GYROM_RATIO_BAR = 42.5774806e6

class Pool:
    def __init__(self, name, enabled, vals=None, userdef=False):
        self.name = name
        self.enabled = enabled
        if vals is None: vals = {}
        for b0 in B0_DEFAULTS:
            if b0 not in vals: vals[b0] = [0,0,0,0]
        self.original_vals = vals
        self.userdef = userdef
        self.vals = dict(self.original_vals)

    def reset(self):
        if not self.userdef:
            self.vals = dict(self.original_vals)

class PoolEditDialog(QtGui.QDialog):
    """
    Thoughts on custom pools:

     - Make pool selection checkboxes into list. No scrollbars with defaults!
     - Provide 'New Pool' button?
     - Leave 'Edit' as it is?
     - Ideally, save custom pools for future!
    """
    HEADERS = ["PPM offset", "Exch rate", "T1", "T2"]

    def __init__(self, parent, pools, b0):
        super(PoolEditDialog, self).__init__(parent)
        self.setWindowTitle("Edit Pools")
        self.pools = pools
        self.b0 = b0

        vbox = QtGui.QVBoxLayout()
        self.setLayout(vbox)

        # Need a layout to contain the table so we can remove and replace it when new pools are added
        self.tbox = QtGui.QHBoxLayout()
        self._init_table()
        vbox.addLayout(self.tbox)

        hbox = QtGui.QHBoxLayout()
        
        btn = QtGui.QPushButton("New Pool")
        btn.clicked.connect(self._new_pool)
        hbox.addWidget(btn)

        self.buttonBox = QtGui.QDialogButtonBox(QtGui.QDialogButtonBox.Ok | QtGui.QDialogButtonBox.Cancel)
        self.buttonBox.accepted.connect(self.accept)
        self.buttonBox.rejected.connect(self.reject)
        hbox.addWidget(self.buttonBox)

        vbox.addLayout(hbox)

    def _init_table(self):
        self.table = NumberGrid([p.vals[self.b0] for p in self.pools if p.enabled], 
                                col_headers=self.HEADERS,
                                row_headers=[p.name for p in self.pools if p.enabled], 
                                expandable=(False, False))
        self.table.itemChanged.connect(self._table_changed)
        self.tbox.addWidget(self.table)

    def _new_pool(self):
        """
        Ask for name then init values
        """
        name, result = QtGui.QInputDialog.getText(self, "New Pool", "Name for pool", QtGui.QLineEdit.Normal)
        if result:
            self.pools.append(Pool(name, enabled=True))
        self.tbox.takeAt(0)
        self._init_table()

    def _table_changed(self):
        self.buttonBox.button(QtGui.QDialogButtonBox.Ok).setEnabled(self.table.valid())

class CESTWidget(QpWidget):
    """
    CEST-specific widget, using the Fabber process
    """

    pools = [
        Pool("Water", True,  { "3T" : [0,0,1.3,0.05], "9.4T" : [0,0,1.8,0.05]}),
        Pool("Amide", True,  { "3T" : [3.5,20,0.77,0.01], "9.4T" : [3.5,30,1.8,0.001]}),
        Pool("NOE/MT", True, { "3T" : [-2.34,40,1.0,0.0004],  "9.4T" : [-2.41,20,1.8,0.0005]}),
        Pool("NOE", False, { "3T" : [0,0,0,0], "9.4T" : [0,0,0,0]}),
        Pool("MT", False, { "3T" : [0,0,0,0], "9.4T" : [0,0,0,0]}),
        Pool("Amine", False, { "3T" : [0,0,0,0], "9.4T" : [0,0,0,0]}),
    ]

    def __init__(self, **kwargs):
        QpWidget.__init__(self, name="CEST", icon="cest", group="Fabber", desc="CEST analysis", **kwargs)
        
    def init_ui(self):
        vbox = QtGui.QVBoxLayout()
        self.setLayout(vbox)

        try:
            self.FabberProcess = get_plugins("processes", "FabberProcess")[0]
        except:
            self.FabberProcess = None

        if self.FabberProcess is None or not self.FabberProcess.FABBER_FOUND:
            vbox.addWidget(QtGui.QLabel("Fabber core library not found.\n\n You must install Fabber to use this widget"))
            return
    
        title = TitleWidget(self, help="cest", subtitle="Modelling for Chemical Exchange Saturation Transfer MRI")
        vbox.addWidget(title)
        
        cite = Citation(CEST_CITE_TITLE, CEST_CITE_AUTHOR, CEST_CITE_JOURNAL)
        vbox.addWidget(cite)

        seqBox = QtGui.QGroupBox()
        seqBox.setTitle("Sequence")
        grid = QtGui.QGridLayout()
        grid.setColumnStretch(2, 1)
        seqBox.setLayout(grid)

        # Table of frequency offsets
        grid.addWidget(QtGui.QLabel("Frequency offsets"), 0, 0)
        self.freq_offsets = NumberList([1, 2, 3, 4, 5])
        grid.addWidget(self.freq_offsets, 0, 1, 1, 2)
        self.load_freq_offsets = LoadNumbers(self.freq_offsets)
        grid.addWidget(self.load_freq_offsets, 0, 3)

        # Field strength - this affects pool values selected
        grid.addWidget(QtGui.QLabel("B0"), 1, 0)
        self.b0_combo = QtGui.QComboBox()
        self.poolval_combo = QtGui.QComboBox()
        for b0 in B0_DEFAULTS:
            self.b0_combo.addItem(b0)
        self.b0_combo.currentIndexChanged.connect(self.b0_changed)
        grid.addWidget(self.b0_combo, 1, 1)

        self.b0_custom = QtGui.QWidget()
        hbox = QtGui.QHBoxLayout()
        self.b0_custom.setLayout(hbox)
        self.b0_spin = QtGui.QDoubleSpinBox()
        self.b0_spin.setValue(3.0)
        self.b0_spin.valueChanged.connect(self.b0_changed)
        hbox.addWidget(self.b0_spin)
        hbox.addWidget(QtGui.QLabel("T"))
        hbox.addStretch(1)
        label = QtGui.QLabel("WARNING: Pool values will need editing")
        label.setStyleSheet("QLabel { color : red; }")
        hbox.addWidget(label)
        grid.addWidget(self.b0_custom, 1, 2)

        # B1 field
        self.b1 = NumericOption("B1 (\u03bcT)", grid, ypos=2, xpos=0, default=0.55, decimals=6)
        hbox = QtGui.QHBoxLayout()
        #self.unsat_cb = QtGui.QCheckBox("Unsaturated")
        #self.unsat_cb.stateChanged.connect(self.update_ui)
        #hbox.addWidget(self.unsat_cb)
        #self.unsat_combo = QtGui.QComboBox()
        #self.unsat_combo.addItem("first")
        #self.unsat_combo.addItem("last")
        #self.unsat_combo.addItem("first and last  ")
        #hbox.addWidget(self.unsat_combo)
        hbox.addStretch(1)
        grid.addLayout(hbox, 2, 2)
        
        grid.addWidget(QtGui.QLabel("Saturation"), 3, 0)
        self.sat_combo = QtGui.QComboBox()
        self.sat_combo.addItem("Continuous Saturation   ")
        self.sat_combo.addItem("Pulsed Saturation   ")
        self.sat_combo.currentIndexChanged.connect(self.update_ui)
        self.sat_combo.setSizeAdjustPolicy(QtGui.QComboBox.AdjustToContents)
        grid.addWidget(self.sat_combo, 3, 1)

        # Continuous saturation
        self.st = NumericOption("Saturation times (s)", grid, ypos=4, xpos=0, default=2.0)

        # Pulsed saturation
        self.pms_label = QtGui.QLabel("Pulse Magnitudes")
        grid.addWidget(self.pms_label, 5, 0)
        self.pms = NumberList([0, 0, 0, 0])
        grid.addWidget(self.pms, 5, 1, 1, 2)
        self.load_pms = LoadNumbers(self.pms)
        grid.addWidget(self.load_pms, 5, 3)
        self.pds_label = QtGui.QLabel("Pulse Durations (s)")
        grid.addWidget(self.pds_label, 6, 0)
        self.pds = NumberList([0, 0, 0, 0])
        grid.addWidget(self.pds, 6, 1, 1, 2)
        self.load_pds = LoadNumbers(self.pds)
        grid.addWidget(self.load_pds, 6, 3)
        self.pr = NumericOption("Pulse Repeats", grid, ypos=7, xpos=0, default=1, intonly=True)
        
        vbox.addWidget(seqBox)
    
        # Pools
        poolBox = QtGui.QGroupBox()
        poolBox.setTitle("Pools")
        poolVbox = QtGui.QVBoxLayout()
        poolBox.setLayout(poolVbox)

        self.poolgrid = QtGui.QGridLayout()
        self.populate_poolgrid()
        poolVbox.addLayout(self.poolgrid)

        hbox = QtGui.QHBoxLayout()
        self.custom_label = QtGui.QLabel("")
        self.custom_label.setStyleSheet("QLabel { color : red; }")
        hbox.addWidget(self.custom_label)
        edit_btn = QtGui.QPushButton("Edit")
        edit_btn.clicked.connect(self.edit_pools)
        hbox.addWidget(edit_btn)
        reset_btn = QtGui.QPushButton("Reset")
        reset_btn.clicked.connect(self.reset_pools)
        hbox.addWidget(reset_btn)
        poolVbox.addLayout(hbox)

        # Fabber Options
        anBox = QtGui.QGroupBox()
        anBox.setTitle("Analysis")
        anVbox = QtGui.QVBoxLayout()
        anBox.setLayout(anVbox)

        grid = QtGui.QGridLayout()
        self.spatial_cb = QtGui.QCheckBox("Spatial regularization")
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

        # Run box
        runBox = RunBox(self.get_process_model, self.get_rundata_model, title="Run model-based analysis", save_option=True)
        vbox.addWidget(runBox)
        vbox.addStretch(1)
        
        # Run box
        runBox = RunBox(self.get_process_lda, self.get_rundata_lda, title="Run Lorentzian Difference analysis", save_option=True)
        vbox.addWidget(runBox)
        vbox.addStretch(1)

        self.poolvals_edited = False
        self.b0_combo.setCurrentIndex(1)
        self.update_ui()

    def populate_poolgrid(self):
        row, col = 0, 0
        NUM_POOL_COLS = 3
        for pool in self.pools:
            if col == NUM_POOL_COLS:
                col = 0
                row += 1
            existing = self.poolgrid.itemAtPosition(row, col)
            if existing is not None:
                existing.widget().setParent(None)
            cb = QtGui.QCheckBox(pool.name)
            cb.setChecked(pool.enabled)
            cb.stateChanged.connect(self.pool_enabled(pool))
            self.poolgrid.addWidget(cb, row, col)
            col += 1

    def pool_enabled(self, pool):
        def cb(state):
            pool.enabled = state
        return cb

    def b0_changed(self):
        self.b0_sel = self.b0_combo.currentText()
        if self.b0_combo.currentIndex() == 2:
            # Custom B0
            self.b0_custom.setVisible(True)
            self.b0 = self.b0_spin.value()
        else:
            self.b0_custom.setVisible(False)
            self.b0 = float(self.b0_sel[:-1])

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

    def edit_pools(self):
        d = PoolEditDialog(self, self.pools, self.b0_sel)
        if d.exec_():
            enabled_pools = [p for p in self.pools if p.enabled]
            for pool, vals in zip(enabled_pools, d.table.values()):
                pool.vals[self.b0_sel] = vals
            self.custom_label.setText("Edited")
            self.populate_poolgrid()
            self.poolvals_edited = True

    def reset_pools(self):
        self.custom_label.setText("")
        self.poolvals_edited = False
        for pool in self.pools:
            pool.reset()
            
    def get_rundata(self):
        # General defaults which never change
        rundata = {}
        rundata["save-mean"] = ""
        rundata["save-model-fit"] = ""
        rundata["noise"] = "white"
        rundata["max-iterations"] = "20"
        rundata["model"] = "cest"
        rundata["save-model-extras"] = ""

        # Placeholders to be replaced with temp files
        rundata["pools"] = "pools.mat"
        rundata["ptrain"] = "ptrain.mat"
        rundata["spec"] = "dataspec.mat"
        
        if self.spatial_cb.isChecked():
            rundata["method"] = "spatialvb"
            rundata["param-spatial-priors"] = "MN+"
        else:
            rundata["method"] = "vb"
            rundata.pop("param-spatial-priors", None)
            
        prior_num = 1
        if self.t12_cb.isChecked():
            rundata["t12prior"] = ""
            if self.t1_cb.isChecked():
                rundata["PSP_byname%i" % prior_num] = "T1a"
                rundata["PSP_byname%i_type" % prior_num] = "I"
                rundata["PSP_byname%i_image" % prior_num] = self.t1_ovl.currentText()
                prior_num += 1

            if self.t2_cb.isChecked():
                rundata["PSP_byname%i" % prior_num] = "T2a"
                rundata["PSP_byname%i_type" % prior_num] = "I"
                rundata["PSP_byname%i_image" % prior_num] = self.t2_ovl.currentText()
                prior_num += 1
        else:
            rundata.pop("t12prior", None)
        return rundata

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
        #self.unsat_combo.setEnabled(self.unsat_cb.isChecked())

    def get_dataspec(self):
        dataspec = ""
        freqs = self.freq_offsets.values()
        for idx, freq in enumerate(freqs):
            if self.pulsed:
                repeats = self.pr.spin.value()
            else:
                repeats = 1
            b1 = self.b1.spin.value()/1e6
            #if self.unsat_cb.isChecked():
            #    debug("Unsat", idx, self.unsat_combo.currentIndex())
            #    if idx == 0 and self.unsat_combo.currentIndex() in (0, 2):
            #        b1 = 0
            #    elif idx == len(freqs)-1 and self.unsat_combo.currentIndex() in (1, 2):
            #        b1 = 0
            dataspec += "%g %g %i\n" % (freq, b1, repeats)
        debug(dataspec)
        return dataspec

    def get_ptrain(self):
        ptrain = ""
        if self.pulsed:
            if not self.pms.valid() or not self.pms.valid():
                raise QpException("Non-numeric values in pulse specification")
            pms = self.pms.values()
            pds = self.pds.values()
            if len(pms) != len(pds):
                raise QpException("Pulse magnitude and duration must contain the same number of values")
            for pm, pd in zip(pms, pds):
                ptrain += "%g %g\n" % (pm, pd)
        else:
            ptrain += "1 %g\n" % self.st.spin.value()
        debug(ptrain)
        return ptrain

    def get_poolmat(self):
        poolmat = ""
        for pool in self.pools:
            vals = pool.vals[self.b0_sel]
            if pool.name == "Water":
                # Embed the B0 value in the top left
                vals = [self.b0 * GYROM_RATIO_BAR,] +vals[1:]
            if pool.enabled:
                poolmat += "\t".join([str(v) for v in vals]) + "\n"
        debug(poolmat)
        return poolmat

    def write_temp(self, name, data):
        f = tempfile.NamedTemporaryFile(prefix=name, delete=False)
        f.write(data) 
        f.close()
        return f.name

    def batch_options(self):
        support_files = [("poolmat.mat", self.get_poolmat()),
                         ("dataspec.mat", self.get_dataspec()),
                         ("ptrain.mat", self.get_ptrain())]
        return "Fabber", self.get_rundata(), support_files

    def get_process_model(self):
        process = self.FabberProcess(self.ivm)
        process.sig_finished.connect(self.postproc)
        return process

    def get_rundata_model(self):
        rundata = self.get_rundata()
        rundata["ptrain"] = self.write_temp("ptrain", self.get_ptrain())
        rundata["spec"] = self.write_temp("dataspec", self.get_dataspec())
        rundata["pools"] = self.write_temp("poolmat", self.get_poolmat())
        rundata["debug"] = ""
        self.tempfiles = [rundata[s] for s in ("pools", "ptrain", "spec")]
        
        for item in rundata.items():
            debug("%s: %s" % item)
        return rundata

    def postproc(self, status, results, log, exception):
         # Remove temp files after run completes
        for fname in self.tempfiles:
            try:
                os.remove(fname)
            except:
                warn("Failed to delete temp file: %s" % fname)

        # Update 'volumes' axis to contain frequencies
        # FIXME removed as effectively requires frequencies to be
        # ordered and doesn't seem to look very good either
        #if status == Process.SUCCEEDED:
        #    self.update_volumes_axis()    

    def postproc_lda(self, status, results, log, exception):
        # Rename residuals and change sign convention
        resids = self.ivm.data["residuals"]
        ld = -resids.std()
        self.ivm.delete_data("residuals")
        self.ivm.add_data(ld, name="lorenz_diff", make_current=True)

    def get_process_lda(self):
        # FIXME need special process to get the residuals only
        process = self.FabberProcess(self.ivm)
        process.sig_finished.connect(self.postproc)
        process.sig_finished.connect(self.postproc_lda)
        return process
        
    def get_rundata_lda(self):
        rundata = self.get_rundata()
        rundata["ptrain"] = self.write_temp("ptrain", self.get_ptrain())
        rundata["spec"] = self.write_temp("dataspec", self.get_dataspec())
        rundata["debug"] = ""
        
        # LDA is the residual data (data - modelfit)
        rundata.pop("save-mean", None)
        rundata.pop("save-zstat", None)
        rundata.pop("save-std", None)
        rundata.pop("save-model-fit", None)
        rundata.pop("save-model-extras", None)
        rundata["save-residuals"] = ""

        # Restrict fitting to parts of the z-spectrum with |ppm| <= 1 or |ppm| >= 30
        # This is done by 'masking' the timepoints so Fabber still reads in the
        # full data and still outputs a prediction at each point, however the
        # masked points are not used in the parameter fitting
        masked_idx = 1
        for idx, f in enumerate(self.freq_offsets.values()):
            if f < 0: f = -f
            if f > 1 and f < 30:
                rundata["mt%i" % masked_idx] = idx+1
                masked_idx += 1

        # Temporarily disable non-water pools just to generate the poolmat file
        enabled_pools = []
        for idx, p in enumerate(self.pools):
            if p.enabled:
                enabled_pools.append(p.name)
            p.enabled = (idx == 0)

        rundata["pools"] = self.write_temp("poolmat", self.get_poolmat())
        self.tempfiles = [rundata[s] for s in ("pools", "ptrain", "spec")]

        # Return pools to previous state
        current_pools = []
        for idx, p in enumerate(self.pools):
            p.enabled = (p.name in enabled_pools)

        for k in sorted(rundata.keys()):
            debug("%s: %s" % (k, rundata[k]))
        return rundata