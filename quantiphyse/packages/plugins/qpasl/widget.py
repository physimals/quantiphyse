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
from quantiphyse.utils import debug, warn
from quantiphyse.utils.exceptions import QpException

from quantiphyse.packages.plugins.quabber.process import FabberProcess, FABBER_FOUND

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

        if not FABBER_FOUND:
            vbox.addWidget(QtGui.QLabel("Fabber core library not found.\n\n You must install Fabber to use this widget"))
            return
        
        title = TitleWidget("ASL", help="asl", subtitle="Modelling for Arterial Spin Labelling MRI")
        vbox.addWidget(title)
              
        cite = Citation(FAB_CITE_TITLE, FAB_CITE_AUTHOR, FAB_CITE_JOURNAL)
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

        runBox = RunBox(self.get_process, self.get_rundata, title="Run ASL modelling", save_option=True)
        vbox.addWidget(runBox)
        vbox.addStretch(1)

        self.rundata = {}

        # General defaults
        self.rundata["save-mean"] = ""
        self.rundata["save-model-fit"] = ""
        self.rundata["noise"] = "white"
        self.rundata["max-iterations"] = "20"
        self.rundata["model"] = "aslrest"

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

    def get_process(self):
        return FabberProcess(self.ivm)

    def get_rundata(self):
        self.update_options()
        return self.rundata

    def update_options(self):
        # First preprocess the data to put it in the format the Fabber model expects.
        # This is outer grouping of TIs, then by repeats and finally tag/control pairs
        nvols = self.ivm.main.nvols
        ntis = len(self.plds.values())
        if nvols % ntis != 0:
            raise QpException("Number of volumes (%i) not consistent with %i PLDs" % (nvols, ntis))
        nrepeats = int(nvols / ntis)

        tcpairs = ctpairs = False
        if self.tc_combo.currentIndex() == 0:
            # Need to do tag/control subtraction
            if nrepeats % 2 != 0:
                raise QpException("Number of volumes (%i) not consistent with %i PLDs and tag/control pairs" % (nvols, ntis))
            nvols = int(nvols/2)
            nrepeats = int(nrepeats/2)
            if self.tc_ord_combo.currentIndex() == 0:
                tcpairs = True
            else:
                ctpairs = True

        debug("ntis=%i, nrepeats=%i, tcpairs=%i, ctpairs=%i, nvols=%i" % (ntis, nrepeats, tcpairs, ctpairs, nvols))
        asldata = np.zeros(list(self.ivm.grid.shape) + [nvols, ])
        out_idx = 0
        if tcpairs or ctpairs: npairs = 2
        else: npairs = 1
        for tidx in range(ntis):
            for ridx in range(nrepeats):
                idx1 = self.get_vol_idx(tidx, ntis, ridx, nrepeats, 0, npairs)
                idx2 = self.get_vol_idx(tidx, ntis, ridx, nrepeats, 1, npairs)
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
            raise QpException("Number of bolus durations must match number TIs if more than one value given")
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
            debug("%s: %s" % item)
        self.tc_combo.setCurrentIndex(1)
        return self.rundata
