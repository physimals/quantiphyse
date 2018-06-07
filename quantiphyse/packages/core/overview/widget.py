"""
Quantiphyse - Widget which displays list of all data loaded

Copyright (c) 2013-2018 University of Oxford
"""

from __future__ import print_function, division, absolute_import

from PySide import QtGui
from quantiphyse.gui.widgets import QpWidget, HelpButton, TextViewerDialog
from quantiphyse.utils import debug, get_icon, get_local_file
from quantiphyse import __contrib__, __acknowledge__

SUMMARY = """
The GUI enables analysis of an MRI volume, and multiple ROIs and data 
with pharmacokinetic modelling, subregion analysis and statistics included. 
Please use help (?) buttons for more online information on each widget and the entire GUI.

""" + \
"Creators: " + ", ".join([author for author in __contrib__]) + \
"\nAcknowlegements: " + ", ".join([ack for ack in __acknowledge__])

class OverviewWidget(QpWidget):
    """
    QpWidget which displays welcome info and a list of current data sets
    """

    def __init__(self, **kwargs):
        super(OverviewWidget, self).__init__(name="Volumes", icon="volumes", desc="Overview of volumes loaded", group="DEFAULT", position=0, **kwargs)

    def init_ui(self):
        layout = QtGui.QVBoxLayout()

        hbox = QtGui.QHBoxLayout()
        pixmap = QtGui.QPixmap(get_icon("quantiphyse_75.png"))
        lpic = QtGui.QLabel(self)
        lpic.setPixmap(pixmap)
        hbox.addWidget(lpic)
        hbox.addStretch(1)
        help_btn = HelpButton(self)
        hbox.addWidget(help_btn)
        layout.addLayout(hbox)

        summary_label = QtGui.QLabel(SUMMARY)
        summary_label.setWordWrap(True)
        layout.addWidget(summary_label)

        box = QtGui.QGroupBox()
        hbox = QtGui.QHBoxLayout()
        box.setLayout(hbox)
        disc = QtGui.QLabel("<font size=2> Disclaimer: This software has been developed for research purposes only, and "
                            "should not be used as a diagnostic tool. The authors or distributors will not be "
                            "responsible for any direct, indirect, special, incidental, or consequential damages "
                            "arising of the use of this software. By using the this software you agree to this disclaimer."
                            "<p>"
                            "Please read the Quantiphyse License for more information")
        disc.setWordWrap(True)
        hbox.addWidget(disc, 10)
        license_btn = QtGui.QPushButton("License")
        license_btn.clicked.connect(self._view_license)
        hbox.addWidget(license_btn)
        layout.addWidget(box)

        self.data_list = DataListWidget(self)
        layout.addWidget(self.data_list)

        hbox = QtGui.QHBoxLayout()
        btn = QtGui.QPushButton("Rename")
        btn.clicked.connect(self._rename)
        hbox.addWidget(btn)
        btn = QtGui.QPushButton("Delete")
        btn.clicked.connect(self._delete)
        hbox.addWidget(btn)
        btn = QtGui.QPushButton("Set as main data")
        btn.clicked.connect(self._set_main)
        hbox.addWidget(btn)
        layout.addLayout(hbox)

        self.setLayout(layout)

    def _view_license(self):
        license_file = get_local_file("licence.md")
        with open(license_file, "r") as f:
            text = f.read()
        dlg = TextViewerDialog(self, "Quantiphyse License", text=text)
        dlg.exec_()

    def _delete(self):
        if self.data_list.selected is not None:
            name = self.data_list.selected.name
            ok = QtGui.QMessageBox.warning(self, "Delete data", "Delete '%s'?" % name,
                                           QtGui.QMessageBox.Ok | QtGui.QMessageBox.Cancel)
            if ok:
                if name in self.ivm.data:
                    self.ivm.delete_data(name)
                else:
                    self.ivm.delete_roi(name)

    def _rename(self):
        if self.data_list.selected is not None:
            name = self.data_list.selected.name
            text, result = QtGui.QInputDialog.getText(self, "Renaming '%s'" % name, "New name", 
                                                      QtGui.QLineEdit.Normal, name)
            if result:
                if name in self.ivm.data:
                    self.ivm.rename_data(name, text)
                else:
                    self.ivm.rename_roi(name, text)

    def _set_main(self):
        if self.data_list.selected is not None:
            self.ivm.set_main_data(self.data_list.selected.name)
            
class DataListWidget(QtGui.QTableView):
    """
    Table showing loaded volumes
    """
    def __init__(self, parent):
        super(DataListWidget, self).__init__(parent)
        self.ivm = parent.ivm
        self._selected = None

        self.model = QtGui.QStandardItemModel()
        self.setModel(self.model)
        self._update_list()

        self.setSelectionBehavior(QtGui.QAbstractItemView.SelectRows)
        self.setSelectionMode(QtGui.QAbstractItemView.SingleSelection)
        self.setEditTriggers(QtGui.QAbstractItemView.NoEditTriggers)
        self.clicked.connect(self._clicked)

        self.ivm.sig_main_data.connect(self._update_list)
        self.ivm.sig_current_data.connect(self._update_selection)
        self.ivm.sig_all_data.connect(self._update_list)
        self.ivm.sig_current_roi.connect(self._update_selection)
        self.ivm.sig_all_rois.connect(self._update_list)

    @property
    def selected(self):
        """ Currently selected QpData """
        return self._selected

    def _get_table_items(self, data):
        fname = ""
        if hasattr(data, "fname") and data.fname is not None:
            fname = data.fname

        items = [
            QtGui.QStandardItem(data.name),
            QtGui.QStandardItem(str(data.roi)),
            QtGui.QStandardItem(fname)
        ]
        
        if fname:
            tooltip = fname
        else:
            tooltip = "Not saved to file"
        items[0].setToolTip(tooltip)
        return items

    def _update_list(self):
        try:
            self.blockSignals(True)
            self.model.clear()
            self.model.setColumnCount(3)
            self.model.setHorizontalHeaderLabels(["Name", "ROI?", "File"])
            self.horizontalHeader().setResizeMode(2, QtGui.QHeaderView.Stretch)
            for name in sorted(self.ivm.data.keys() + self.ivm.rois.keys()):
                data = self.ivm.data.get(name, self.ivm.rois.get(name))
                self.model.appendRow(self._get_table_items(data))
        finally:
            self.blockSignals(False)

    def _update_selection(self):
        pass

    def _clicked(self, idx):
        row = idx.row()
        name = self.model.item(row, 0).text()
        if name in self.ivm.rois:
            self._selected = self.ivm.rois[name]
            self.ivm.set_current_roi(name)
        else:
            self._selected = self.ivm.data[name]
            self.ivm.set_current_data(name)
