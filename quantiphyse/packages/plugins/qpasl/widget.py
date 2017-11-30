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

import numpy as np
from PySide import QtCore, QtGui

from quantiphyse.gui.widgets import QpWidget, HelpButton, BatchButton, OverlayCombo, NumericOption, NumberList, LoadNumbers, OrderList, OrderListButtons, Citation, TitleWidget, RunBox
from quantiphyse.gui.dialogs import TextViewerDialog, error_dialog, GridEditDialog
from quantiphyse.analysis import Process
from quantiphyse.utils import debug, warn, get_plugins
from quantiphyse.utils.exceptions import QpException

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
        
FAB_CITE_TITLE = "Variational Bayesian inference for a non-linear forward model"
FAB_CITE_AUTHOR = "Chappell MA, Groves AR, Whitcher B, Woolrich MW."
FAB_CITE_JOURNAL = "IEEE Transactions on Signal Processing 57(1):223-236, 2009."

class ASLWidget(QpWidget):
    """
    ASL-specific widget, using the Fabber process
    """
    def __init__(self, **kwargs):
        QpWidget.__init__(self, name="ASL", icon="asl",  group="Fabber", desc="ASL analysis", **kwargs)
        self.groups = {"P" : "Tag/Control pairs", "R" : "Repeats", "T" : "TIs"}
        self.default_order = "TRP"

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
        
        title = TitleWidget(self, help="asl", subtitle="Modelling for Arterial Spin Labelling MRI")
        vbox.addWidget(title)
              
        cite = Citation(FAB_CITE_TITLE, FAB_CITE_AUTHOR, FAB_CITE_JOURNAL)
        vbox.addWidget(cite)

        self.tabs = QtGui.QTabWidget()
        vbox.addWidget(self.tabs)

        # Preprocessing tab
        preprocTab = QtGui.QWidget()
        grid = QtGui.QGridLayout()
        preprocTab.setLayout(grid)

        grid.addWidget(QtGui.QLabel("Data format"), 0, 0)
        self.tc_combo = QtGui.QComboBox()
        self.tc_combo.addItem("Tag-control pairs")
        self.tc_combo.addItem("Tag-control subtracted")
        self.tc_combo.addItem("Multiphase")
        self.tc_combo.currentIndexChanged.connect(self.update_ui)
        grid.addWidget(self.tc_combo, 0, 1)
        self.tc_ord_combo = QtGui.QComboBox()
        self.tc_ord_combo.addItem("Tag first")
        self.tc_ord_combo.addItem("Control first")
        self.tc_ord_combo.currentIndexChanged.connect(self.update_ui)
        grid.addWidget(self.tc_ord_combo, 0, 2)

        self.ntis = NumericOption("Number of TIs/PLDs", grid, ypos=1, xpos=0, default=1, intonly=True, minval=1)
        
        grid.addWidget(QtGui.QLabel("Data grouping\n(top = outermost)"), 2, 0, alignment=QtCore.Qt.AlignTop)
        self.group_list = OrderList()
        grid.addWidget(self.group_list, 2, 1)
        self.list_btns = OrderListButtons(self.group_list)
        grid.addLayout(self.list_btns, 2, 2)
        # Have to set items after adding to grid or sizing doesn't work right
        self.group_list.setItems([self.groups[g] for g in self.default_order])
        self.group_list.sig_changed.connect(self.update_ui)

        grid.addWidget(QtGui.QLabel("Data order preview"), 3, 0)
        self.data_preview = AslDataPreview(self.default_order, True)
        grid.addWidget(self.data_preview, 4, 0, 1, 3)

        self.preproc_btn = QtGui.QPushButton("Preprocess data")
        self.preproc_btn.clicked.connect(self.preprocess)
        self.preprocessed = False
        grid.addWidget(self.preproc_btn, 5, 0)

        grid.setRowStretch(6, 1)

        self.tabs.addTab(preprocTab, "Preprocessing")

        # Model-based analysis tab

        analysisTab = QtGui.QWidget()
        a_vbox = QtGui.QVBoxLayout()
        analysisTab.setLayout(a_vbox)

        # FIXME add multiband readout options?
        grid = QtGui.QGridLayout()
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
        a_vbox.addLayout(grid)

        grid = QtGui.QGridLayout()
        self.bat = NumericOption("Bolus arrival time (s)", grid, ypos=0, xpos=0, default=1.3, decimals=2)
        self.ie = NumericOption("Inversion efficiency", grid, ypos=1, xpos=0, default=0.85, decimals=2)
        self.t1 = NumericOption("T1 (s)", grid, ypos=0, xpos=2, default=1.3, decimals=2)
        self.t1b = NumericOption("T1b (s)", grid, ypos=1, xpos=2, default=1.65, decimals=2)

        self.spatial_cb = QtGui.QCheckBox("Spatial regularization")
        grid.addWidget(self.spatial_cb, 4, 0, 1, 2)
        self.t1_cb = QtGui.QCheckBox("Allow uncertainty in T1 values")
        grid.addWidget(self.t1_cb, 5, 0, 1, 2)
        self.mv_cb = QtGui.QCheckBox("Include macro vascular component")
        grid.addWidget(self.mv_cb, 6, 0, 1, 2)
        self.fixtau_cb = QtGui.QCheckBox("Fix bolus duration")
        grid.addWidget(self.fixtau_cb, 4, 2, 1, 2)
        #self.pvc_cb = QtGui.QCheckBox("Partial volume correction")
        #grid.addWidget(self.pvc_cb, 5, 2, 1, 2)
        a_vbox.addLayout(grid)

        self.runbox = RunBox(self.get_process, self.get_rundata, title="Run ASL modelling", save_option=True)
        a_vbox.addWidget(self.runbox)
        a_vbox.addStretch(1)

        self.tabs.addTab(analysisTab, "Analysis")
        self.update_ui()

    def activate(self):
        self.ivm.sig_main_data.connect(self.main_data_changed)

    def deactivate(self):
        self.ivm.sig_main_data.disconnect(self.main_data_changed)
        
    def main_data_changed(self, data):
        if data != "asldata":
            # Main data has changed and it is NOT out preprocessed data! That
            # means it needs preprocessing before we can send it to Fabber
            self.preprocessed = False
            self.update_ui()

    def update_ui(self):
        """ Update visibility / enabledness of widgets """
        self.tc_ord_combo.setEnabled(self.tc_combo.currentIndex() == 0)
        tagfirst = self.tc_ord_combo.currentIndex() == 0
        order = ""
        for item in self.group_list.items():
            code = [k for k, v in self.groups.items() if v == item][0]
            debug(item, code)
            order += code
        debug(order)
        self.data_preview.set_order(order, tagfirst)
        casl = self.lbl_combo.currentIndex() == 0
        if casl:
            self.plds_label.setText("PLDs")
        else:
            self.plds_label.setText("TIs")

        self.runbox.runBtn.setEnabled(self.preprocessed)

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

    def preprocess(self):
        """
        Preprocess the data to put it in the format the Fabber model expects.
        This is outer grouping of TIs, then by repeats and finally tag/control pairs
        
        FIXME multiphase not yet supported
        """
        nvols = self.ivm.main.nvols
        ntis = self.ntis.value()
        if nvols % ntis != 0:
            raise QpException("Number of volumes (%i) not consistent with %i PLDs" % (nvols, ntis))
        self.nrepeats = int(nvols / ntis)

        tcpairs = ctpairs = False
        if self.tc_combo.currentIndex() == 0:
            # Need to do tag/control subtraction
            if self.nrepeats % 2 != 0:
                raise QpException("Number of volumes (%i) not consistent with %i PLDs and tag/control pairs" % (nvols, ntis))
            nvols = int(nvols/2)
            self.nrepeats = int(self.nrepeats/2)
            if self.tc_ord_combo.currentIndex() == 0:
                tcpairs = True
            else:
                ctpairs = True

        debug("ntis=%i, nrepeats=%i, tcpairs=%i, ctpairs=%i, nvols=%i" % (ntis, self.nrepeats, tcpairs, ctpairs, nvols))
        asldata = np.zeros(list(self.ivm.grid.shape) + [nvols, ])
        out_idx = 0
        if tcpairs or ctpairs: npairs = 2
        else: npairs = 1
        for tidx in range(ntis):
            for ridx in range(self.nrepeats):
                idx1 = self.get_vol_idx(tidx, ntis, ridx, self.nrepeats, 0, npairs)
                idx2 = self.get_vol_idx(tidx, ntis, ridx, self.nrepeats, 1, npairs)
                debug("tidx=%i, ridx=%i, tc1=%i, tc2=%i" % (tidx, ridx, idx1, idx2))
                if ctpairs:
                    # Do control - tag
                    debug("Doing %i - %i" % (idx1, idx2))
                    asldata[:,:,:,out_idx] = self.ivm.main.std()[:,:,:,idx1] - self.ivm.main.std()[:,:,:,idx2]
                elif tcpairs:
                    # Do control - tag
                    debug("Doing %i - %i" % (idx2, idx1))
                    asldata[:,:,:,out_idx] = self.ivm.main.std()[:,:,:,idx2] - self.ivm.main.std()[:,:,:,idx1]
                else:
                    asldata[:,:,:,out_idx] = self.ivm.main.std()[:,:,:,idx1]
                out_idx += 1

#        meandiff = np.mean(asldata, 3)
#        self.ivm.add_data(meandiff, name="diff", make_current=True)
        self.ivm.add_data(asldata, name="asldata", make_main=True)
        self.preprocessed = True
        self.update_ui()
       
    def get_process(self):
        return self.FabberProcess(self.ivm)

    def get_rundata(self):
        # General defaults
        self.rundata = {}
        self.rundata["save-mean"] = ""
        self.rundata["save-model-fit"] = ""
        self.rundata["noise"] = "white"
        self.rundata["max-iterations"] = "20"
        self.rundata["model"] = "aslrest"

        # Acquisition parameters
        if self.lbl_combo.currentIndex() == 0:
            self.rundata["casl"] = ""
        else:
            self.rundata.pop("casl", None)

        tis = self.plds.values()
        if len(tis) != self.ntis.value():
            raise QpException("Number of TIs/PLDs must match number specified in preprocessing")
           
        taus = self.taus.values()
        singletau = None
        if len(taus) == 1:
            singletau = taus[0]
            self.rundata["tau"] = str(singletau)
        elif len(tis) != len(taus):
            raise QpException("Number of bolus durations must match number TIs if more than one value given")
        else:
            for idx, tau in enumerate(tau):
                self.rundata["tau%i" % (idx+1)] = str(tau)
        
        for idx, ti in enumerate(tis):
            if "casl" in self.rundata:
                if singletau is not None: ti += singletau
                else: ti += taus[idx]
            self.rundata["ti%i" % (idx+1)] = str(ti)

        self.rundata["repeats"] = str(self.nrepeats)

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
            self.rundata.pop("infert1", None)
            self.rundata.pop("inct1", None)

        if self.mv_cb.isChecked():
            self.rundata["inferart"] = ""
            self.rundata["incart"] = ""
        else:
            self.rundata.pop("inferart", None)
            self.rundata.pop("incart", None)
            
        if not self.fixtau_cb.isChecked():
            self.rundata["infertau"] = ""
            self.rundata["inctau"] = ""
        else:
            self.rundata.pop("infetau", None)
            self.rundata.pop("inctau", None)

        for item in self.rundata.items():
            debug("%s: %s" % item)
        self.tc_combo.setCurrentIndex(1)
        return self.rundata
