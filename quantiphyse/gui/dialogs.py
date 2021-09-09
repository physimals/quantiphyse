"""
Quantiphyse - Custom dialog boxes

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

import os

from PySide2 import QtGui, QtCore, QtWidgets

MAINWIN = None

def set_main_window(win):
    """ Set the main window widget so it can be a parent to dialogs to make style match"""
    global MAINWIN
    MAINWIN = win

def error_dialog(msg, title="Warning", detail=None, subtitle="Details:"):
    """
    Show an error dialog box
    """
    text = msg.replace(os.linesep, "<br>")
    if detail is not None:
        detail_str = ""
        if isinstance(detail, (list, tuple)):
            for item in detail:
                detail_str += str(item) + os.linesep
        else:
            detail_str = str(detail)
        detail_str = detail_str.replace(os.linesep, "<br>")
        text += "<br><br><b>%s</b><br><br>%s" % (subtitle, detail_str)

    QtWidgets.QMessageBox.warning(MAINWIN, title, text, QtWidgets.QMessageBox.Close)

class MultiTextViewerDialog(QtWidgets.QDialog):
    """
    Text viewer dialog with multiple pages presented as tabs

    :param title: Overall title
    :param pages: Sequence of pages, each string content
    """

    def __init__(self, parent, title="Log", pages=()):
        super(MultiTextViewerDialog, self).__init__(parent)
        self.setWindowTitle(title)
        vbox = QtWidgets.QVBoxLayout()

        self.tabs = QtWidgets.QTabWidget()
        self._browsers = {}
        for heading, content in pages:
            browser = self._text_browser(content)
            self._browsers[heading] = browser
            self.tabs.addTab(browser, heading)

        vbox.addWidget(self.tabs)

        hbox = QtWidgets.QHBoxLayout()
        self.copy_btn = QtWidgets.QPushButton("Copy")
        self.copy_btn.clicked.connect(self._copy)
        hbox.addWidget(self.copy_btn)
        hbox.addStretch(1)
        self.button_box = QtWidgets.QDialogButtonBox(QtWidgets.QDialogButtonBox.Ok)
        self.button_box.accepted.connect(self.close)
        hbox.addWidget(self.button_box)
        vbox.addLayout(hbox)

        self.setLayout(vbox)
        self.resize(700, 500)

    def text(self, heading):
        if heading not in self._browsers:
            raise ValueError("Tab not found: %s" % heading)
        return self._browsers[heading].text()

    def setText(self, heading, content):
        if heading not in self._browsers:
            raise ValueError("Tab not found: %s" % heading)
        scrollbar = self._browsers[heading].verticalScrollBar()
        original_pos = scrollbar.value()
        was_at_end = original_pos == scrollbar.maximum()
        self._browsers[heading].setText(content)
        if was_at_end:
            scrollbar.setValue(scrollbar.maximum())
        else:
            scrollbar.setValue(original_pos)

    def _text_browser(self, content):
        browser = QtWidgets.QTextBrowser()
        browser.setFontFamily("Courier")
        browser.setText(content)
        return browser

    def _copy(self):
        clipboard = QtWidgets.QApplication.clipboard()
        clipboard.setText(self.tabs.currentWidget().toPlainText())

class TextViewerDialog(MultiTextViewerDialog):
    """
    Simple text viewer dialog box
    """

    def __init__(self, parent, title="Log", text=""):
        MultiTextViewerDialog.__init__(self, parent, title, [("", text)])
        self.tabs.tabBar().setVisible(False)

    @property
    def text(self):
        return MultiTextViewerDialog.text(self, "")

    @text.setter
    def text(self, newtext):
        self.setText("", newtext)

class MatrixViewerDialog(QtWidgets.QDialog):
    """
    Dialog box enabling a read-only viewing of a number matrix
    """

    def __init__(self, parent, vals, title="Data", text=""):
        super(MatrixViewerDialog, self).__init__(parent)
        self.setWindowTitle(title)
        vbox = QtWidgets.QVBoxLayout()

        self.table = QtWidgets.QTableWidget(len(vals), len(vals[0]))
        vbox.addWidget(self.table)
        for row, rvals in enumerate(vals):
            for col, val in enumerate(rvals):
                self.table.setItem(row, col, QtWidgets.QTableWidgetItem(str(val)))

        self.text = QtWidgets.QLabel(text)
        vbox.addWidget(self.text)

        self.button_box = QtWidgets.QDialogButtonBox(QtWidgets.QDialogButtonBox.Ok | QtWidgets.QDialogButtonBox.Cancel)
        self.button_box.accepted.connect(self.accept)
        self.button_box.rejected.connect(self.reject)
        vbox.addWidget(self.button_box)

        self.setLayout(vbox)
        self.resize(500, 500)

class GridEditDialog(QtWidgets.QDialog):
    """
    Dialog box enabling a numerical matrix to be edited
    """

    def __init__(self, parent, vals, col_headers=None, row_headers=None, title="Data", text="", expandable=(True, True)):
        super(GridEditDialog, self).__init__(parent)
        self.setWindowTitle(title)
        vbox = QtWidgets.QVBoxLayout()

        from .widgets import NumberGrid # prevent circular import dependency
        self.table = NumberGrid(vals, col_headers=col_headers, row_headers=row_headers, expandable=expandable)
        self.table.sig_changed.connect(self._validate)
        vbox.addWidget(self.table)

        self.text = QtWidgets.QLabel(text)
        vbox.addWidget(self.text)

        self.button_box = QtWidgets.QDialogButtonBox(QtWidgets.QDialogButtonBox.Ok | QtWidgets.QDialogButtonBox.Cancel)
        self.button_box.accepted.connect(self.accept)
        self.button_box.rejected.connect(self.reject)
        self.button_box.button(QtWidgets.QDialogButtonBox.Ok).setEnabled(False)
        vbox.addWidget(self.button_box)

        self.setLayout(vbox)

    def _validate(self):
        self.button_box.button(QtWidgets.QDialogButtonBox.Ok).setEnabled(self.table.valid())

class ChooseFromListDialog(QtWidgets.QDialog):
    """
    Dialog box enabling one item to be chosen from a list
    """

    def __init__(self, parent, values, return_values=None, title="Choose"):
        super(ChooseFromListDialog, self).__init__(parent)
        self.sel_text = None
        self.sel_data = None

        self.setWindowTitle(title)
        vbox = QtWidgets.QVBoxLayout()

        if return_values is None:
            return_values = values
        self._list = QtWidgets.QListWidget(self)
        for value, data in zip(values, return_values):
            item = QtWidgets.QListWidgetItem(value)
            item.setData(QtCore.Qt.UserRole, data)
            self._list.addItem(item)
            
        vbox.addWidget(self._list)
        self._list.itemClicked.connect(self._item_clicked)
        self._list.itemDoubleClicked.connect(self._item_double_clicked)

        self.button_box = QtWidgets.QDialogButtonBox(QtWidgets.QDialogButtonBox.Ok | QtWidgets.QDialogButtonBox.Cancel)
        self.button_box.accepted.connect(self.accept)
        self.button_box.rejected.connect(self.reject)
        self.button_box.button(QtWidgets.QDialogButtonBox.Ok).setEnabled(False)
        vbox.addWidget(self.button_box)

        self.setLayout(vbox)

    def _item_clicked(self, item):
        self.sel_text = item.text()
        self.sel_data = item.data(QtCore.Qt.UserRole)
        self.button_box.button(QtWidgets.QDialogButtonBox.Ok).setEnabled(True)

    def _item_double_clicked(self, item):
        self._item_clicked(item)
        self.accept()

class PlotDialog1d(QtWidgets.QDialog):
    """
    Dialog that shows a 1D plot
    """

    def __init__(self, parent, arr, title="Plot"):
        QtWidgets.QDialog.__init__(self, parent)

        if arr.ndim != 1:
            raise ValueError("Only for 1D plotting")

        self.setWindowTitle(title)
        vbox = QtWidgets.QVBoxLayout()
        self.setLayout(vbox)

        from quantiphyse.gui.plot import Plot
        plot_widget = Plot(self, title)
        plot_widget.add_line(arr)
        vbox.addWidget(plot_widget)

