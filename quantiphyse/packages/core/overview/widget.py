"""
Quantiphyse - Widget which displays list of all data loaded

Copyright (c) 2013-2020 University of Oxford

Licensed under the Apache License, Version 2.0 (the "License");
you may not use this file except in compliance with the License.
You may obtain a copy of the License at

    http://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and
limitations under the License.
"""

from __future__ import print_function, division, absolute_import

import os
import logging

from PySide2 import QtGui, QtCore, QtWidgets

from quantiphyse.data import save, load
from quantiphyse.gui.widgets import QpWidget, HelpButton, TextViewerDialog
from quantiphyse.gui.viewer.view_options_dialog import ViewerOptions
from quantiphyse.utils import default_save_dir, get_icon, get_local_file
from quantiphyse.utils.enums import Visibility
from quantiphyse import __contrib__, __acknowledge__, __license__

SUMMARY = "\nCreators: " + ", ".join([author for author in __contrib__]) \
          + "\nAcknowlegements: " + ", ".join([ack for ack in __acknowledge__])

LOG = logging.getLogger(__name__)

class IvmDebugger:
    """
    Simple class which logs data changes in the IVM to help with debugging
    """
    def __init__(self, ivm):
        self._ivm = ivm
        self._known_data = []
        self._md_changed_cbs = {}
        self._ivm.sig_all_data.connect(self._data_changed)
        self._ivm.sig_current_data.connect(self._current_data_changed)
        self._ivm.sig_current_data.connect(self._current_roi_changed)
        self._data_changed(self._ivm.data.keys())

    def _data_changed(self, data_names):
        LOG.debug("data changed")

        for name in data_names:
            qpdata = self._ivm.data[name]
            if qpdata not in self._known_data:
                LOG.debug("New data: %s %s %s ", qpdata.name, qpdata.view, qpdata.metadata)
                self._known_data.append(qpdata)
                qpdata.view.sig_changed.connect(self._get_md_changed_cb(qpdata))
        
        for qpdata in self._known_data[:]:
            if qpdata.name not in data_names:
                LOG.debug("Removed data: %s %s %s", qpdata.name, qpdata.view, qpdata.metadata)
                qpdata.view.sig_changed.disconnect(self._get_md_changed_cb(qpdata))
                self._known_data.remove(qpdata)

    def _get_md_changed_cb(self, qpdata):
        if qpdata not in self._md_changed_cbs:
            def _cb(key, value):
                LOG.debug("MD changed: %s: %s=%s", qpdata.name, key, value)
            self._md_changed_cbs[qpdata] = _cb
        return self._md_changed_cbs[qpdata]

    def _current_data_changed(self, qpdata):
        if qpdata is not None:
            LOG.debug("Current data: %s", qpdata.name)
        else:
            LOG.debug("Current data: None")

    def _current_roi_changed(self, qpdata):
        if qpdata is not None:
            LOG.debug("Current ROI: %s", qpdata.name)
        else:
            LOG.debug("Current data: None")

class OverviewWidget(QpWidget):
    """
    QpWidget which displays welcome info and a list of current data sets
    """

    def __init__(self, **kwargs):
        super(OverviewWidget, self).__init__(name="Volumes", icon="volumes", desc="Overview of volumes loaded",
                                             group="DEFAULT", position=0, **kwargs)

    def init_ui(self):
        layout = QtWidgets.QVBoxLayout()

        hbox = QtWidgets.QHBoxLayout()
        pixmap = QtGui.QPixmap(get_icon("quantiphyse_75.png"))
        lpic = QtWidgets.QLabel(self)
        lpic.setPixmap(pixmap)
        hbox.addWidget(lpic)
        hbox.addStretch(1)
        help_btn = HelpButton(self)
        hbox.addWidget(help_btn)
        layout.addLayout(hbox)

        summary_label = QtWidgets.QLabel(SUMMARY)
        summary_label.setWordWrap(True)
        layout.addWidget(summary_label)

        box = QtWidgets.QGroupBox()
        hbox = QtWidgets.QHBoxLayout()
        box.setLayout(hbox)
        disc = QtWidgets.QLabel("<font size=2> Disclaimer: This software has been developed for research purposes only, and "
                            "should not be used as a diagnostic tool. The authors or distributors will not be "
                            "responsible for any direct, indirect, special, incidental, or consequential damages "
                            "arising of the use of this software. By using the this software you agree to this disclaimer."
                            "<p>"
                            "Please read the Quantiphyse License for more information")
        disc.setWordWrap(True)
        hbox.addWidget(disc, 10)
        license_btn = QtWidgets.QPushButton("License")
        license_btn.clicked.connect(self._view_license)
        hbox.addWidget(license_btn)
        layout.addWidget(box)

        self.data_list = DataListWidget(self)
        layout.addWidget(self.data_list)

        hbox = QtWidgets.QHBoxLayout()
        
        self._up_btn = self._btn(hbox, QtGui.QIcon(get_icon("up.png")), "Raise data set in viewing order", self._up)
        self._down_btn = self._btn(hbox, QtGui.QIcon(get_icon("down.png")), "Lower data set in viewing order", self._down)
        self._btn(hbox, QtGui.QIcon(get_icon("delete.png")), "Delete selected data set", self._delete)
        self._btn(hbox, QtGui.QIcon(get_icon("save.png")), "Save selected data set", self._save)
        self._btn(hbox, QtGui.QIcon(get_icon("reload.png")), "Reload selected data set", self._reload)
        self._btn(hbox, QtGui.QIcon(get_icon("rename.png")), "Rename selected data set", self._rename)
        self._btn(hbox, QtGui.QIcon(get_icon("main_data.png")), "Make selected data set the main (background) data", self._set_main)
        self._btn(hbox, QtGui.QIcon(get_icon("roi_or_data.png")), "Mark/unmark selected data set as an ROI", self._toggle_roi)

        hbox.addStretch(1)
        self._single_multi_btn = self._btn(hbox, QtGui.QIcon(get_icon("multi_overlay.png")), "Switch between single and multi overlay modes", self._toggle_single_multi)
        self._btn(hbox, QtGui.QIcon(get_icon("options.png")), "Viewer options", self._viewer_options)

        layout.addLayout(hbox)
        self.setLayout(layout)
        self._toggle_single_multi()

    def _btn(self, hbox, icon, tooltip, callback):
        btn = QtWidgets.QPushButton()
        btn.setIcon(icon)
        btn.setToolTip(tooltip)
        btn.setStatusTip(tooltip)
        btn.setFixedSize(24, 24)
        btn.clicked.connect(callback)
        hbox.addWidget(btn)
        return btn

    def _viewer_options(self):
        ViewerOptions(self, self.ivl).exec_()

    def _toggle_single_multi(self):
        self.ivl.multiview = not self.ivl.multiview
        self._up_btn.setVisible(self.ivl.multiview)
        self._down_btn.setVisible(self.ivl.multiview)
        if self.ivl.multiview:
            self._single_multi_btn.setIcon(QtGui.QIcon(get_icon("single_overlay.png")))
        else:
            self._single_multi_btn.setIcon(QtGui.QIcon(get_icon("multi_overlay.png")))

    def _view_license(self):
        dlg = TextViewerDialog(self, "Quantiphyse License", text=__license__)
        dlg.exec_()

    def _delete(self):
        if self.data_list.selected is not None:
            name = self.data_list.selected.name
            btn = QtWidgets.QMessageBox.warning(self, "Delete data", "Delete '%s'?" % name,
                                            QtWidgets.QMessageBox.Ok | QtWidgets.QMessageBox.Cancel)
            if btn == QtWidgets.QMessageBox.Ok:
                self.ivm.delete(name)

    def _rename(self):
        if self.data_list.selected is not None:
            name = self.data_list.selected.name
            text, result = QtWidgets.QInputDialog.getText(self, "Renaming '%s'" % name, "New name",
                                                      QtWidgets.QLineEdit.Normal, name)
            if result:
                self.ivm.rename(name, text)

    def _save(self):
        if self.data_list.selected is not None:
            name = self.data_list.selected.name
            data = self.ivm.data[name]
            if hasattr(data, "fname") and data.fname is not None:
                fname = data.fname
            else:
                fname = os.path.join(default_save_dir(), name + ".nii")
            fname, _ = QtWidgets.QFileDialog.getSaveFileName(self, 'Save file', dir=fname,
                                                         filter="NIFTI files (*.nii *.nii.gz)")
            if fname != '':
                save(self.ivm.data[name], fname)
            else: # Cancelled
                pass

    def _reload(self):
        if self.data_list.selected is not None:
            name = self.data_list.selected.name
            data = self.ivm.data[name]
            if hasattr(data, "fname") and data.fname:
                new_data = load(data.fname)
                new_data.roi = data.roi
                self.ivm.add(new_data, name=data.name)
                new_data.metadata.update(data.metadata)
                new_data.view.update(data.view)

    def _set_main(self):
        if self.data_list.selected is not None:
            self.ivm.set_main_data(self.data_list.selected.name)

    def _toggle_roi(self):
        if self.data_list.selected is not None:
            # FIXME this should not be so difficult
            qpdata = self.data_list.selected
            qpdata.roi = not qpdata.roi
            self.ivm.add(qpdata)

    def _down(self):
        # FIXME code duplication
        if self.data_list.selected is not None:
            last_data = None
            for data in sorted(self.ivm.data.values(), key=lambda x: x.view.z_order):
                if data == self.data_list.selected and last_data is not None:
                    current_z = data.view.z_order
                    data.view.z_order = last_data.view.z_order
                    last_data.view.z_order = current_z
                last_data = data

    def _up(self):
        if self.data_list.selected is not None:
            last_data = None
            for data in sorted(self.ivm.data.values(), key=lambda x: x.view.z_order):
                if last_data == self.data_list.selected:
                    current_z = data.view.z_order
                    data.view.z_order = last_data.view.z_order
                    last_data.view.z_order = current_z
                last_data = data

class DataListWidget(QtWidgets.QTableView):
    """
    Table showing loaded volumes
    """
    def __init__(self, parent):
        super(DataListWidget, self).__init__(parent)
        self.setStyleSheet("font-size: 10px; alternate-background-color: #6c6c6c;")

        self.ivm = parent.ivm
        self.ivl = parent.ivl
        self._selected = None
        self._known_data = []
        self._roi_icon = QtGui.QIcon(get_icon("roi_data.png"))
        self._data_icon = QtGui.QIcon(get_icon("data.png"))
        self._main_icon = QtGui.QIcon(get_icon("main_data.png"))
        self._vis_icon = QtGui.QIcon(get_icon("visible.png"))
        self._main_vis_icon = QtGui.QIcon(get_icon("main_ovl.png"))

        self.model = QtGui.QStandardItemModel()
        self.setModel(self.model)
        self._update_list()

        self.setSelectionBehavior(QtWidgets.QAbstractItemView.SelectRows)
        self.setSelectionMode(QtWidgets.QAbstractItemView.SingleSelection)
        self.setEditTriggers(QtWidgets.QAbstractItemView.NoEditTriggers)
        self.setShowGrid(False)
        self.setTextElideMode(QtCore.Qt.ElideLeft)
        self.setAlternatingRowColors(True)
        self.verticalHeader().setVisible(False)
        self.verticalHeader().setDefaultSectionSize(self.verticalHeader().minimumSectionSize()+2)
        self.horizontalHeader().setVisible(True)
        self.horizontalHeader().setDefaultAlignment(QtCore.Qt.AlignLeft)

        self.selectionModel().currentRowChanged.connect(self._current_row_changed)
        self.ivm.sig_all_data.connect(self._data_changed)
        self.ivm.sig_main_data.connect(self._update_vis_icons)
        self.ivm.sig_current_data.connect(self._set_current)
        self.ivm.sig_current_roi.connect(self._set_current)

    @property
    def selected(self):
        """ Currently selected QpData """
        return self._selected

    def _set_current(self, qpdata):
        if qpdata is not None:
            matches = self.model.findItems(qpdata.name, QtCore.Qt.MatchExactly, 1)
            if matches:
                index = matches[0].index()
                self.setCurrentIndex(index)

    def _data_changed(self, data_names):
        for name in data_names:
            qpdata = self.ivm.data[name]
            if qpdata not in self._known_data:
                self._known_data.append(qpdata)
                qpdata.view.sig_changed.connect(self._view_metadata_changed)
        
        for qpdata in self._known_data[:]:
            if qpdata.name not in data_names:
                qpdata.view.sig_changed.disconnect(self._view_metadata_changed)
                self._known_data.remove(qpdata)

        self._update_list()

    def _view_metadata_changed(self, key, _value):
        if key == "visible":
            self._update_vis_icons()
        elif key == "z_order":
            self._update_list()

    def _get_table_items(self, data):
        fname = ""
        if hasattr(data, "fname") and data.fname is not None:
            fname = data.fname

        items = [
            QtGui.QStandardItem(""),
            QtGui.QStandardItem(data.name),
            QtGui.QStandardItem(fname)
        ]

        if fname:
            tooltip = fname
        else:
            tooltip = "Not saved to file"

        for item in items:
            item.setToolTip(tooltip)
        return items

    def _update_list(self):
        try:
            self.blockSignals(True)
            scroll_pos = self.verticalScrollBar().value()

            self.model.clear()
            self.model.setColumnCount(3)
            self.model.setHorizontalHeaderLabels(["", "Name", "File"])
            self.model.setHeaderData(0, QtCore.Qt.Horizontal, self._vis_icon, QtCore.Qt.DecorationRole)
            self.horizontalHeader().setResizeMode(0, QtWidgets.QHeaderView.ResizeToContents)
            self.horizontalHeader().setResizeMode(1, QtWidgets.QHeaderView.ResizeToContents)
            self.horizontalHeader().setResizeMode(2, QtWidgets.QHeaderView.Stretch)
            for row, data in enumerate(sorted(self.ivm.data.values(), key=lambda x: -x.view.z_order)):
                self.model.appendRow(self._get_table_items(data))

                index = self.model.index(row, 1)
                self.model.setData(index, self._roi_icon if data.roi else self._data_icon, QtCore.Qt.DecorationRole)
                self._update_vis_icon(row, data)

            self._set_current(self.selected)
            self.verticalScrollBar().setValue(scroll_pos)
        finally:
            self.blockSignals(False)

    def _update_vis_icons(self):
        for row, data in enumerate(sorted(self.ivm.data.values(), key=lambda x: -x.view.z_order)):
            self._update_vis_icon(row, data)

    def _update_vis_icon(self, row, qpdata):
        is_main = qpdata == self.ivm.main
        is_visible = qpdata.view.visible == Visibility.SHOW
        if is_main and is_visible:
            icon = self._main_vis_icon
        elif is_main:
            icon = self._main_icon
        elif is_visible:
            icon = self._vis_icon
        else:
            icon = None
        index = self.model.index(row, 0)
        self.model.setData(index, icon, QtCore.Qt.DecorationRole)

    def _selection(self, index):
        row, col = index.row(), index.column()
        item = self.model.item(row, 1)
        if item is None:
            return row, col, None
        else:
            return row, col, self.ivm.data.get(item.text(), None)

    def _current_row_changed(self, index):
        row, col, qpdata = self._selection(index)
        self._selected = qpdata
        if qpdata is None:
            return

        # HACK In multi-view mode we also set the 'current' data on selection. We don't 
        # do this in single-view mode (unless the visibility column is explicitly
        # clicked on) because the single view enforcer will make the 'current' data/roi
        # the visible one. Hence in multiview mode we need to detect clicks on the visibility
        # icon directly and toggle the visibility accordingly.
        if self.ivl.multiview or col == 0:
            if qpdata.roi:
                self.ivm.set_current_roi(qpdata.name)
            else:
                self.ivm.set_current_data(qpdata.name)

        if self.ivl.multiview and col == 0:
            if qpdata.view.visible == Visibility.SHOW:
                qpdata.view.visible = Visibility.HIDE
            else:
                qpdata.view.visible = Visibility.SHOW

        self._update_vis_icon(row, qpdata)
