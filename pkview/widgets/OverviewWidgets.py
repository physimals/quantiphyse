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

        hbox = QtGui.QHBoxLayout()
        pixmap = QtGui.QPixmap(get_icon("quantiphyse_75.png"))
        lpic = QtGui.QLabel(self)
        lpic.setPixmap(pixmap)
        hbox.addWidget(lpic)
        hbox.addStretch(1)
        b1 = HelpButton(self)
        hbox.addWidget(b1)
        layout.addLayout(hbox)

        ta = QtGui.QLabel("\n\nThe GUI enables analysis of an MRI volume, and multiple ROIs and overlays "
                          "with pharmacokinetic modelling, subregion analysis and statistics included. "
                          "Please use help (?) buttons for more online information on each widget and the entire GUI. "
                          " \n \n"
                          "Creator: Benjamin Irving (mail@birving.com) \n"
                          "Contributors: Benjamin Irving, Martin Craig, Michael Chappell")
        layout.addWidget(ta)

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
        layout.addWidget(box)

        self.vols = DataListWidget(self)
        layout.addWidget(self.vols)

        hbox = QtGui.QHBoxLayout()
        btn = QtGui.QPushButton("Rename")
        btn.clicked.connect(self.rename)
        hbox.addWidget(btn)
        btn = QtGui.QPushButton("Delete")
        btn.clicked.connect(self.delete)
        hbox.addWidget(btn)
        layout.addLayout(hbox)

        self.setLayout(layout)

    def rename(self):
        pass

    def delete(self):
        pass
        
class DataListWidget(QtGui.QTableWidget):
    """
    Table showing loaded volumes
    """
    def __init__(self, parent):
        super(DataListWidget, self).__init__(parent)
        self.ivm = parent.ivm
        self.setColumnCount(3)
        self.setHorizontalHeaderLabels(["Name", "Type", "File"])
        header = self.horizontalHeader();
        header.setResizeMode(2, QtGui.QHeaderView.Stretch);
        self.setSelectionBehavior(QtGui.QAbstractItemView.SelectRows)
        self.setSelectionMode(QtGui.QAbstractItemView.NoSelection)
        self.setEditTriggers(QtGui.QAbstractItemView.NoEditTriggers)
        self.cellClicked.connect(self.clicked)
        self.ivm.sig_main_volume.connect(self.update_list)
        self.ivm.sig_current_overlay.connect(self.update_list)
        self.ivm.sig_all_overlays.connect(self.update_list)
        self.ivm.sig_current_roi.connect(self.update_list)
        self.ivm.sig_all_rois.connect(self.update_list)

    def get_name(self, vol):
        if vol.fname is not None:
            name = vol.fname
        else:
            name = vol.name
        return name

    def add_volume(self, row, vol_type, vol, current=False):
        self.setItem(row, 0, QtGui.QTableWidgetItem(vol.name))
        self.setItem(row, 1, QtGui.QTableWidgetItem(vol_type))
        if vol.fname is not None:
            self.setItem(row, 2, QtGui.QTableWidgetItem(vol.fname))
            self.item(row, 0).setToolTip(vol.fname)
        if current:
            font = self.item(row, 0).font()
            font.setBold(True)
            self.item(row, 0).setFont(font)
            self.item(row, 1).setFont(font)
            self.item(row, 2).setFont(font)
        
    def update_list(self, list1):
        try:
            self.blockSignals(True)
            n = 1 + len(self.ivm.overlays) + len(self.ivm.rois)
            self.setRowCount(n)
            if self.ivm.vol is not None:
                self.add_volume(0, "Main volume", self.ivm.vol)
            row = 1
            for ovl in self.ivm.overlays.values():
                self.add_volume(row, "Overlay", ovl, ovl == self.ivm.current_overlay)
                row += 1
            for roi in self.ivm.rois.values():
                self.add_volume(row, "ROI", roi, roi == self.ivm.current_roi)
                row += 1
        finally:
            self.blockSignals(False)

    def clicked(self, row, col):
        if self.item(row, 1).text() == "Overlay":
            self.ivm.set_current_overlay(self.item(row, 0).text())
        elif self.item(row, 1).text() == "ROI":
            self.ivm.set_current_roi(self.item(row, 0).text())



