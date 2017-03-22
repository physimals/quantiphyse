"""

Author: Benjamin Irving (benjamin.irv@gmail.com)
Copyright (c) 2013-2015 University of Oxford, Benjamin Irving

"""

from PySide import QtGui

def error_dialog(msg, title="Warning"):
    QtGui.QMessageBox.warning(None, title, str(msg), QtGui.QMessageBox.Close)
                   