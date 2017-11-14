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

# Need the Fabber generic process
from quantiphyse.packages.plugins.quabber.process import FabberProcess, FABBER_FOUND

CEST_CITE_TITLE = "Quantitative Bayesian model-based analysis of amide proton transfer MRI"
CEST_CITE_AUTHOR = "Chappell, M. A., Donahue, M. J., Tee, Y. K., Khrapitchev, A. A., Sibson, N. R., Jezzard, P., & Payne, S. J."
CEST_CITE_JOURNAL = "Magnetic Resonance in Medicine. doi:10.1002/mrm.24474"

B0_DEFAULTS = ["3T", "9.4T"]

# Gyromagnetic ratio / 2PI
GYROM_RATIO_BAR = 42.5774806e6

# FIXME correct numbers
POOLS = [
    {"name" : "Water", "default" : True, "vals" : 
        { "3T" : [0,0,1.3,0.05],
          "9.4T" : [0,0,1.8,0.05]}
    },
    {"name" : "Amide", "default" : True, "vals" : 
        { "3T" : [3.5,20,0.77,0.01],
          "9.4T" : [3.5,30,1.8,0.001]}
    },
    {"name" : "NOE/MT", "default" : True, "vals" : 
        { "3T" : [-2.34,40,1.0,0.0004],
          "9.4T" : [-2.41,20,1.8,0.0005]}
    },
    {"name" : "NOE", "default" : False, "vals" : 
        { "3T" : [0,0,0,0], 
          "9.4T" : [0,0,0,0]}
    },
    {"name" : "MT", "default" : False, "vals" : 
        { "3T" : [0,0,0,0], 
          "9.4T" : [0,0,0,0]}
    },
    {"name" : "Amine", "default" : False, "vals" : 
        { "3T" : [0,0,0,0], 
          "9.4T" : [0,0,0,0]}
    },
]

class CESTWidget(QpWidget):
    """
    CEST-specific widget, using the Fabber process
    """

    def __init__(self, **kwargs):
        QpWidget.__init__(self, name="CEST", icon="cest", group="Fabber", desc="CEST analysis", **kwargs)
        
    def init_ui(self):
        vbox = QtGui.QVBoxLayout()
        self.setLayout(vbox)

        if not FABBER_FOUND:
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
        self.b0_combo.addItem("Custom")
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

        # Saturation field
        self.b1 = NumericOption("B1 (\u03bcT)", grid, ypos=2, xpos=0, default=0.55, decimals=6)
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
        self.pr = NumericOption("Pulse Repeats", grid, ypos=6, xpos=0, default=1, intonly=True)
#        self.pr.spin.setSizePolicy(QtGui.QSizePolicy.Maximum, QtGui.QSizePolicy.Preferred)
        
        vbox.addWidget(seqBox)
    
        # Pools
        poolBox = QtGui.QGroupBox()
        poolBox.setTitle("Pools")
        poolVbox = QtGui.QVBoxLayout()
        poolBox.setLayout(poolVbox)

        grid = QtGui.QGridLayout()
        row, col = 0, 0
        NUM_ROWS = 2
        self.pool_cbs, self.custom_poolvals = {}, {}
        for pool in POOLS:
            name = pool["name"]
            self.custom_poolvals[name] = pool["vals"]["9.4T"]
            self.pool_cbs[name] = QtGui.QCheckBox(name)
            self.pool_cbs[name].setChecked(pool["default"])
            self.pool_cbs[name].stateChanged.connect(self.update_pools)
            grid.addWidget(self.pool_cbs[name], row, col)
            row += 1
            if row == NUM_ROWS:
                row = 0
                col += 1
        self.custom_label = QtGui.QLabel("")
        self.custom_label.setStyleSheet("QLabel { color : red; }")
        grid.addWidget(self.custom_label, NUM_ROWS, 0)
        edit_btn = QtGui.QPushButton("Edit")
        edit_btn.clicked.connect(self.edit_pools)
        grid.addWidget(edit_btn, NUM_ROWS, 1)
        reset_btn = QtGui.QPushButton("Reset")
        reset_btn.clicked.connect(self.reset_pools)
        grid.addWidget(reset_btn, NUM_ROWS, 2)
        poolVbox.addLayout(grid)

        # Fabber Options
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

        # Run box
        runBox = RunBox(self.get_process, self.get_rundata, title="Run CEST modelling", save_option=True)
        vbox.addWidget(runBox)
        vbox.addStretch(1)
        
        # General defaults which never change
        self.rundata = {}
        self.rundata["save-mean"] = ""
        self.rundata["save-model-fit"] = ""
        self.rundata["noise"] = "white"
        self.rundata["max-iterations"] = "20"
        self.rundata["model"] = "cest"
        self.rundata["save-model-extras"] = ""

        # Placeholders to be replaced with temp files
        self.rundata["pools"] = "pools.mat"
        self.rundata["ptrain"] = "ptrain.mat"
        self.rundata["spec"] = "dataspec.mat"

        self.poolvals_edited = False
        self.b0_combo.setCurrentIndex(1)
        self.update_ui()
        self.update_pools()

    def b0_changed(self):
        self.b0_sel = self.b0_combo.currentText()
        if self.b0_combo.currentIndex() == 2:
            # Custom B0
            self.b0_custom.setVisible(True)
            self.b0 = self.b0_spin.value()
        else:
            self.b0_custom.setVisible(False)
            self.b0 = float(self.b0_sel[:-1])
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
        self.pools = []
        for pool in POOLS:
            if self.pool_cbs[pool["name"]].isChecked():
                if self.b0_sel == "Custom" or self.poolvals_edited:
                    # Using custom values
                    vals = self.custom_poolvals[pool["name"]]
                else:
                    # Using default values
                    vals = pool["vals"][self.b0_sel]
                self.pools.append((pool["name"], vals))
        debug(self.pools)

    def edit_pools(self):
        vals, pool_headers = [], []
        for name, pvals in self.pools:
            pool_headers.append(name)
            vals.append(pvals)
        val_headers = ["PPM offset", "Exch rate", "T1", "T2"]
        d = GridEditDialog(self, vals, col_headers=val_headers, row_headers=pool_headers, expandable=(False, False))
        if d.exec_():
            vals = d.table.values()
            for row, pool in enumerate(self.pools):
                self.custom_poolvals[pool[0]] = vals[row]
            self.custom_label.setText("Edited")
            self.poolvals_edited = True
            self.update_pools()

    def reset_pools(self):
        self.custom_label.setText("")
        self.poolvals_edited = False
        self.update_pools()

    def update_options(self):
        if self.spatial_cb.isChecked():
            self.rundata["method"] = "spatialvb"
            self.rundata["param-spatial-priors"] = "MN+"
        else:
            self.rundata["method"] = "vb"
            self.rundata.pop("param-spatial-priors", None)
            
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
            self.rundata.pop("t12prior", None)
            
        for n in range(prior_num, len(POOLS)*2+1):
            self.rundata.pop("PSP_byname%i" % n, None)
            self.rundata.pop("PSP_byname%i_type" % n, None)
            self.rundata.pop("PSP_byname%i_image" % n, None)

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
                debug("Unsat", idx, self.unsat_combo.currentIndex())
                if idx == 0 and self.unsat_combo.currentIndex() in (0, 2):
                    b1 = 0
                elif idx == len(freqs)-1 and self.unsat_combo.currentIndex() in (1, 2):
                    b1 = 0
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
        for name, vals in self.pools:
            if name == "Water":
                # Embed the B0 value in the top left
                vals = [self.b0 * GYROM_RATIO_BAR,] + vals[1:]
            poolmat += "\t".join([str(v) for v in vals]) + "\n"
        debug(poolmat)
        return poolmat

    def write_temp(self, name, data):
        f = tempfile.NamedTemporaryFile(prefix=name, delete=False)
        f.write(data) 
        f.close()
        return f.name

    def get_process(self):
        process = FabberProcess(self.ivm)
        process.sig_finished.connect(self.extra_postproc)
        return process

    def get_rundata(self):
        self.update_options()
        self.rundata["ptrain"] = self.write_temp("ptrain", self.get_ptrain())
        self.rundata["spec"] = self.write_temp("dataspec", self.get_dataspec())
        self.rundata["pools"] = self.write_temp("poolmat", self.get_poolmat())
        self.rundata["debug"] = ""
        for item in self.rundata.items():
            debug("%s: %s" % item)
        import fabber
        fab = fabber.FabberLib(auto_load_models=True)
        debug("Additional outputs", fab.get_model_outputs(self.rundata))
        return self.rundata

    def batch_options(self):
        support_files = [("poolmat.mat", self.get_poolmat()),
                         ("dataspec.mat", self.get_dataspec()),
                         ("ptrain.mat", self.get_ptrain())]
        return "Fabber", self.rundata, support_files

    def extra_postproc(self, status, results, log):
        # Remove temp files after run completes
        os.remove(self.rundata["ptrain"])
        os.remove(self.rundata["spec"])
        os.remove(self.rundata["pools"])

        # Update 'volumes' axis to contain frequencies
        # FIXME removed as effectively requires frequencies to be
        # ordered and doesn't seem to look very good either
        #if status == Process.SUCCEEDED:
        #    self.update_volumes_axis()    
