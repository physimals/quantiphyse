import os

from PySide import QtGui

from ..utils import debug

MAINWIN = None

def set_main_window(w):
    """ Set the main window widget so it can be a parent to dialogs to make style match"""
    global MAINWIN
    MAINWIN = w

def error_dialog(msg, title="Warning", detail=None, subtitle="Details:"):
    text = msg.replace(os.linesep, "<br>")
    if detail is not None:
        detail_str = ""
        try:
            for item in detail:
                detail_str += str(item) + os.linesep
        except:
            detail_str = str(detail)
        detail_str = detail_str.replace(os.linesep, "<br>")
        text += "<br><br><b>%s</b><br><br>%s" % (subtitle, detail_str)

    QtGui.QMessageBox.warning(MAINWIN, title, text, QtGui.QMessageBox.Close)

class MultiTextViewerDialog(QtGui.QDialog):

    def __init__(self, parent, title="Log", pages=[]):
        super(MultiTextViewerDialog, self).__init__(parent)
        self.setWindowTitle(title)
        vbox = QtGui.QVBoxLayout()

        self.tabs = QtGui.QTabWidget()
        for heading, content in pages:
            browser = self._text_browser(content)
            self.tabs.addTab(browser, heading)

        vbox.addWidget(self.tabs)
        
        self.buttonBox = QtGui.QDialogButtonBox(QtGui.QDialogButtonBox.Ok)
        self.buttonBox.accepted.connect(self.close)
        vbox.addWidget(self.buttonBox)

        self.setLayout(vbox)
        self.resize(700, 500)

    def _text_browser(self, content):
        tb = QtGui.QTextBrowser()
        tb.setFontFamily("Courier")
        tb.setText(content)
        return tb
        
class TextViewerDialog(QtGui.QDialog):

    def __init__(self, parent, title="Log", text=""):
        super(TextViewerDialog, self).__init__(parent)
        self.setWindowTitle(title)
        vbox = QtGui.QVBoxLayout()

        self.text_browser = QtGui.QTextBrowser()
        self.text_browser.setFontFamily("Courier")
        self.text_browser.setText(text)
        vbox.addWidget(self.text_browser)
        
        self.buttonBox = QtGui.QDialogButtonBox(QtGui.QDialogButtonBox.Ok)
        self.buttonBox.accepted.connect(self.close)
        vbox.addWidget(self.buttonBox)

        self.setLayout(vbox)
        self.resize(700, 500)

class MatrixViewerDialog(QtGui.QDialog):

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
        
        self.buttonBox = QtGui.QDialogButtonBox(QtGui.QDialogButtonBox.Ok | QtGui.QDialogButtonBox.Cancel)
        self.buttonBox.accepted.connect(self.accept)
        self.buttonBox.rejected.connect(self.reject)
        vbox.addWidget(self.buttonBox)

        self.setLayout(vbox)
        self.resize(500, 500)

class GridEditDialog(QtGui.QDialog):

    def __init__(self, parent, vals, col_headers=None, row_headers=None, title="Data", text="", expandable=(True, True)):
        super(GridEditDialog, self).__init__(parent)
        self.setWindowTitle(title)
        vbox = QtGui.QVBoxLayout()

        from .widgets import NumberGrid # prevent circular import dependency
        self.table = NumberGrid(vals, col_headers=col_headers, row_headers=row_headers, expandable=expandable)
        self.table.itemChanged.connect(self._table_changed)
        vbox.addWidget(self.table)
        
        self.text = QtGui.QLabel(text)
        vbox.addWidget(self.text)
        
        self.buttonBox = QtGui.QDialogButtonBox(QtGui.QDialogButtonBox.Ok | QtGui.QDialogButtonBox.Cancel)
        self.buttonBox.accepted.connect(self.accept)
        self.buttonBox.rejected.connect(self.reject)
        vbox.addWidget(self.buttonBox)

        self.setLayout(vbox)

    def _table_changed(self):
        self.buttonBox.button(QtGui.QDialogButtonBox.Ok).setEnabled(self.table.valid())
