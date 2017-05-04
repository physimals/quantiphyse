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

def error_dialog(msg, title="Warning", detail="", subtitle="Details:"):
    text = msg
    if detail != "":
        text += "<br><br><b>%s</b><br><br>%s" % (subtitle, detail)

    QtGui.QMessageBox.warning(None, title, text, QtGui.QMessageBox.Close)
                   