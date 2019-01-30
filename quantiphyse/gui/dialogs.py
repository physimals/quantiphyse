"""
Quantiphyse - Custom dialog boxes

Copyright (c) 2013-2018 University of Oxford
"""

import os

from PySide import QtGui

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

    QtGui.QMessageBox.warning(MAINWIN, title, text, QtGui.QMessageBox.Close)

class MultiTextViewerDialog(QtGui.QDialog):
    """
    Text viewer dialog with multiple pages presented as tabs

    :param title: Overall title
    :param pages: Sequence of pages, each string content
    """

    def __init__(self, parent, title="Log", pages=()):
        super(MultiTextViewerDialog, self).__init__(parent)
        self.setWindowTitle(title)
        vbox = QtGui.QVBoxLayout()

        self.tabs = QtGui.QTabWidget()
        self._browsers = {}
        for heading, content in pages:
            browser = self._text_browser(content)
            self._browsers[heading] = browser
            self.tabs.addTab(browser, heading)

        vbox.addWidget(self.tabs)
        
        hbox = QtGui.QHBoxLayout()
        self.copy_btn = QtGui.QPushButton("Copy")
        self.copy_btn.clicked.connect(self._copy)
        hbox.addWidget(self.copy_btn)
        hbox.addStretch(1)
        self.button_box = QtGui.QDialogButtonBox(QtGui.QDialogButtonBox.Ok)
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
        if was_at_end:
            self._browsers[heading].setText(content)
        if was_at_end:
            scrollbar.setValue(scrollbar.maximum())
        else:
            scrollbar.setValue(original_pos)

    def _text_browser(self, content):
        browser = QtGui.QTextBrowser()
        browser.setFontFamily("Courier")
        browser.setText(content)
        return browser

    def _copy(self):
        clipboard = QtGui.QApplication.clipboard()
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

class MatrixViewerDialog(QtGui.QDialog):
    """
    Dialog box enabling a read-only viewing of a number matrix
    """

    def __init__(self, parent, vals, title="Data", text=""):
        super(MatrixViewerDialog, self).__init__(parent)
        self.setWindowTitle(title)
        vbox = QtGui.QVBoxLayout()

        self.table = QtGui.QTableWidget(len(vals), len(vals[0]))
        vbox.addWidget(self.table)
        for row, rvals in enumerate(vals):
            for col, val in enumerate(rvals):
                self.table.setItem(row, col, QtGui.QTableWidgetItem(str(val)))
        
        self.text = QtGui.QLabel(text)
        vbox.addWidget(self.text)
        
        self.button_box = QtGui.QDialogButtonBox(QtGui.QDialogButtonBox.Ok | QtGui.QDialogButtonBox.Cancel)
        self.button_box.accepted.connect(self.accept)
        self.button_box.rejected.connect(self.reject)
        vbox.addWidget(self.button_box)

        self.setLayout(vbox)
        self.resize(500, 500)

class GridEditDialog(QtGui.QDialog):
    """
    Dialog box enabling a numerical matrix to be edited
    """

    def __init__(self, parent, vals, col_headers=None, row_headers=None, title="Data", text="", expandable=(True, True)):
        super(GridEditDialog, self).__init__(parent)
        self.setWindowTitle(title)
        vbox = QtGui.QVBoxLayout()

        from .widgets import NumberGrid # prevent circular import dependency
        self.table = NumberGrid(vals, col_headers=col_headers, row_headers=row_headers, expandable=expandable)
        self.table.sig_changed.connect(self._validate)
        vbox.addWidget(self.table)
        
        self.text = QtGui.QLabel(text)
        vbox.addWidget(self.text)
        
        self.button_box = QtGui.QDialogButtonBox(QtGui.QDialogButtonBox.Ok | QtGui.QDialogButtonBox.Cancel)
        self.button_box.accepted.connect(self.accept)
        self.button_box.rejected.connect(self.reject)
        self.button_box.button(QtGui.QDialogButtonBox.Ok).setEnabled(False)
        vbox.addWidget(self.button_box)

        self.setLayout(vbox)

    def _validate(self):
        self.button_box.button(QtGui.QDialogButtonBox.Ok).setEnabled(self.table.valid())
