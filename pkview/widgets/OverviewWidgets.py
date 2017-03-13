from __future__ import print_function, division, absolute_import

from PySide import QtGui, QtCore
from ..QtInherit import HelpButton
from pkview.utils import get_icon
from pkview.widgets import PkWidget
from pkview.pkviewer import __version__

class OverviewWidget(PkWidget):

    def __init__(self, **kwargs):
        super(OverviewWidget, self).__init__(name="Volumes", icon="", desc="Overview of volumes loaded", **kwargs)

        layout = QtGui.QVBoxLayout()

        # List for volume management
        tb = QtGui.QLabel("<font size=50> PKView %s</font> \n" % __version__)

        pixmap = QtGui.QPixmap(get_icon("main_icon.png"))
        pixmap = pixmap.scaled(35, 35, QtCore.Qt.KeepAspectRatio)
        lpic = QtGui.QLabel(self)
        lpic.setPixmap(pixmap)

        b1 = HelpButton(self)
        l03 = QtGui.QHBoxLayout()
        l03.addWidget(lpic)
        l03.addWidget(tb)
        l03.addStretch(1)
        l03.addWidget(b1)

        ta = QtGui.QLabel("The GUI enables analysis of a DCE-MRI volume, ROI and multiple overlays "
                          "with pharmacokinetic modelling, subregion analysis and statistics included. "
                          "Please use help (?) buttons for more online information on each widget and the entire GUI. "
                          " \n \n"
                          "Creator: Benjamin Irving (mail@birving.com) \n"
                          "Contributors: Benjamin Irving, Martin Craig, Michael Chappell")
        box = QtGui.QGroupBox()
        vbox = QtGui.QVBoxLayout()
        box.setLayout(vbox)
        disc = QtGui.QLabel("<font size=2> Disclaimer: This software has been developed for research purposes only, and "
                          "should not be used as a diagnostic tool. The authors or distributors will not be "
                          "responsible for any direct, indirect, special, incidental, or consequential damages "
                          "arising of the use of this software. The current intention of this software is for "
                          "'in house' use only and should not be distributed without the explicit consent of the "
                          "authors."
                          "\n\n"
                          "By using the this software you agree to this disclaimer (see help for more information)</font>")
        vbox.addWidget(disc)
        ta.setWordWrap(True)
        disc.setWordWrap(True)

        t1 = QtGui.QLabel("Current overlays")
        self.l1 = CaseWidget(self)
        t2 = QtGui.QLabel("Current ROIs")
        self.l2 = RoiWidget(self)

        layout.addLayout(l03)
        layout.addWidget(ta)
        layout.addWidget(box)

        layout.addWidget(t1)
        layout.addWidget(self.l1)
        layout.addWidget(t2)
        layout.addWidget(self.l2)

        self.setLayout(layout)

class CaseWidget(QtGui.QListWidget):
    """
    Class to handle the organisation of the loaded volumes
    """
    def __init__(self, parent):
        super(CaseWidget, self).__init__(parent)
        self.list_current = []
        self.sel_current = ""
        self.ivm = None
        self.currentItemChanged.connect(self.emit_volume)
        self.ivm = parent.ivm
        self.ivm.sig_current_overlay.connect(self.update_current)
        self.ivm.sig_all_overlays.connect(self.update_list)

    def update_list(self, list1):
        self.list_current = list1[:]
        try:
            self.blockSignals(True)
            self.clear()
            for ii in self.list_current:
                self.addItem(ii)
        finally:
            self.blockSignals(False)

    def update_current(self, ovl):
        if ovl is not None:
            if self.sel_current != ovl.name:
                self.sel_current = ovl.name
                ind1 = self.list_current.index(ovl.name)
                try:
                    self.blockSignals(True)
                    self.setCurrentRow(ind1)
                finally:
                    self.blockSignals(False)

    @QtCore.Slot()
    def emit_volume(self, choice1, choice1_prev):
        if choice1 is not None:
            self.ivm.set_current_overlay(choice1.text(), signal=True)

class RoiWidget(QtGui.QListWidget):
    """
    Class to handle the organisation of the loaded ROIs
    """
    def __init__(self, parent):
        super(RoiWidget, self).__init__(parent)
        self.list_current = []
        self.sel_current = ""
        self.ivm = None
        self.currentItemChanged.connect(self.emit_volume)
        self.ivm = parent.ivm
        self.ivm.sig_current_roi.connect(self.update_current)
        self.ivm.sig_all_rois.connect(self.update_list)

    def update_list(self, list1):
        self.list_current = list1[:]
        try:
            self.blockSignals(True)
            self.clear()
            for ii in self.list_current:
                self.addItem(ii)
        finally:
            self.blockSignals(False)

    def update_current(self, roi):
        if roi is not None:
            if self.sel_current != roi.name:
                self.sel_current = roi.name
                ind1 = self.list_current.index(roi.name)
                try:
                    self.blockSignals(True)
                    self.setCurrentRow(ind1)
                finally:
                    self.blockSignals(False)

    @QtCore.Slot()
    def emit_volume(self, choice1, choice1_prev):
        if choice1 is not None:
            self.ivm.set_current_roi(choice1.text(), signal=True)



