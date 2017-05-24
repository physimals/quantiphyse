from PySide import QtGui

class LogViewerDialog(QtGui.QDialog):

    def __init__(self, parent, title="Log", log=""):
        super(LogViewerDialog, self).__init__(parent)
        self.setWindowTitle(title)
        vbox = QtGui.QVBoxLayout()

        self.text = QtGui.QTextBrowser()
        self.text.setText(log)
        vbox.addWidget(self.text)
        
        self.buttonBox = QtGui.QDialogButtonBox(QtGui.QDialogButtonBox.Ok)
        self.buttonBox.accepted.connect(self.close)
        vbox.addWidget(self.buttonBox)

        self.setLayout(vbox)

def error_dialog(msg, title="Warning", detail=None, subtitle="Details:"):
    text = msg
    if detail is not None:
        detail_str = ""
        try:
            for item in detail:
                detail_str += str(item).replace("\n", "<br>") + "<br>"
        except:
            detail_str = str(detail).replace("\n", "<br>")
        text += "<br><br><b>%s</b><br><br>%s" % (subtitle, detail_str)

    QtGui.QMessageBox.warning(None, title, text, QtGui.QMessageBox.Close)
                   