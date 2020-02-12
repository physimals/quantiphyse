"""
Quantiphyse - Dialog box for user registration

Copyright (c) 2013-2018 University of Oxford
"""

from __future__ import division, unicode_literals, print_function, absolute_import

import sys
import traceback
import warnings

import requests

try:
    from PySide import QtGui, QtCore, QtGui as QtWidgets
except ImportError:
    from PySide2 import QtGui, QtCore, QtWidgets

import quantiphyse.gui.dialogs
from quantiphyse.utils import get_icon, get_version
from quantiphyse._version import __license__

LICENSE_ACCEPTED_KEY = "license_accepted"

def license_accepted():
    settings = QtCore.QSettings()
    if settings.contains(LICENSE_ACCEPTED_KEY):
        try:
            return int(settings.value(LICENSE_ACCEPTED_KEY))
        except:
            # Invalid value - assume not accepted
            return 0
    return 0

def set_license_accepted(accepted=1):
    settings = QtCore.QSettings()
    settings.setValue(LICENSE_ACCEPTED_KEY, accepted)

def check_register():
    """
    Check if the user has accepted the license agreement and if not show the 
    license/registration dialog
    """
    if not license_accepted():
        accepted = LicenseDialog(quantiphyse.gui.dialogs.MAINWIN).exec_()
        set_license_accepted(accepted)
        if accepted:
            RegisterDialog(quantiphyse.gui.dialogs.MAINWIN).exec_()

    if not license_accepted():
        # User got the license dialog but did not accept it
        sys.exit(-1)

class LicenseDialog(QtGui.QDialog):
    """
    Dialog box which asks a first-time user to accept the license
    """
    def __init__(self, parent=None):
        QtGui.QDialog.__init__(self, parent)
        self.setWindowTitle("License Agreement")
        
        layout = QtGui.QVBoxLayout()

        hbox = QtGui.QHBoxLayout()
        pixmap = QtGui.QPixmap(get_icon("quantiphyse_75.png"))
        lpic = QtGui.QLabel(self)
        lpic.setPixmap(pixmap)
        hbox.addWidget(lpic)
        hbox.addStretch(1)
        layout.addLayout(hbox)

        layout.addWidget(QtGui.QLabel(""))

        # Welcome
        hbox = QtGui.QHBoxLayout()
        hbox.addStretch(1)
        hbox.addWidget(QtGui.QLabel("\n<font size=5>Welcome to Quantiphyse %s</font>" % get_version()))
        hbox.addStretch(1)
        layout.addLayout(hbox)

        label = QtGui.QLabel("Quantiphyse is <b>free for non-commercial use</b>. If you are interested in using the software "
                             "commercially, please contact the technology transfer company of the University: enquiries@innovation.ox.ac.uk")
        label.setWordWrap(True)
        layout.addWidget(label)

        # License agreement
        edit = QtGui.QTextEdit()
        edit.setCurrentFont(QtGui.QFont("Monospace", 8))
        edit.append(__license__)
        edit.append("</pre>")
        edit.moveCursor(QtGui.QTextCursor.Start)
        edit.ensureCursorVisible()
        layout.addWidget(edit)
        
        # Acceptance section
        self.agree_cb = QtGui.QCheckBox("I agree to abide by the terms of the Quantiphyse license")
        self.agree_cb.stateChanged.connect(self._agree_changed)
        layout.addWidget(self.agree_cb)

        # Buttons
        self.button_box = QtGui.QDialogButtonBox(QtGui.QDialogButtonBox.Ok|QtGui.QDialogButtonBox.Cancel)
        self.button_box.accepted.connect(self.accept)
        self.button_box.rejected.connect(self.reject)
        self.button_box.button(QtGui.QDialogButtonBox.Ok).setEnabled(False)
        layout.addWidget(self.button_box)

        self.setLayout(layout)
        self.setFixedSize(700, 800)

    def _agree_changed(self, state):
        self.button_box.button(QtGui.QDialogButtonBox.Ok).setEnabled(state)

class RegisterDialog(QtGui.QDialog):
    """
    Dialog box which asks a first-time user to  optionally send a registration email
    """
    def __init__(self, parent=None):
        QtGui.QDialog.__init__(self, parent)
        self.setWindowTitle("Optional Registration")
        
        layout = QtGui.QVBoxLayout()

        hbox = QtGui.QHBoxLayout()
        pixmap = QtGui.QPixmap(get_icon("quantiphyse_75.png"))
        lpic = QtGui.QLabel(self)
        lpic.setPixmap(pixmap)
        hbox.addWidget(lpic)
        hbox.addStretch(1)
        layout.addLayout(hbox)

        layout.addWidget(QtGui.QLabel(""))

        # Welcome
        hbox = QtGui.QHBoxLayout()
        hbox.addWidget(QtGui.QLabel("<font size=5>Optional Registration</font>"))
        layout.addLayout(hbox)

        # Registration section
        label = QtGui.QLabel("If you like you can register as a user. This is to "
                             "help us know where the software is being used.")
        label.setWordWrap(True)
        layout.addWidget(label)

        grid = QtGui.QGridLayout()
        grid.addWidget(QtGui.QLabel("<font size=2>Name"), 0, 0)
        self.name_edit = QtGui.QLineEdit()
        grid.addWidget(self.name_edit, 0, 1)
        grid.addWidget(QtGui.QLabel("<font size=2>Institution"), 0, 2)
        self.inst_edit = QtGui.QLineEdit()
        grid.addWidget(self.inst_edit, 0, 3)
        grid.addWidget(QtGui.QLabel("<font size=2>Email"), 1, 0)
        self.email_edit = QtGui.QLineEdit()
        grid.addWidget(self.email_edit, 1, 1, 1, 3)
        layout.addLayout(grid)

        # Buttons
        self.button_box = QtGui.QDialogButtonBox(QtGui.QDialogButtonBox.Ok|QtGui.QDialogButtonBox.Cancel)
        self.button_box.accepted.connect(self.send_register_email)
        self.button_box.rejected.connect(self.accept)
        layout.addWidget(self.button_box)

        self.setLayout(layout)
        self.setFixedWidth(700)

    def send_register_email(self):
        """
        Send registration email
        
        Note that this email service has been set only to send to the specified recipient
        so this cannot be used to spam anybody else! Also note that we catch all exceptions
        so any failure will not stop the user proceeding.
        """
        name = self.name_edit.text()
        inst = self.inst_edit.text()
        email = self.email_edit.text()
        if email:
            try:
                outcome = requests.post(
                    "https://api.mailgun.net/v3/sandboxd8aca8efc95348609a6d63f0c651f4d2.mailgun.org/messages",
                    auth=("api", "key-c0be61e997b71c2d0c43fa8aeb706a5c"),
                    data={"from": "Quantiphyse <postmaster@sandboxd8aca8efc95348609a6d63f0c651f4d2.mailgun.org>",
                          "to": "Martin Craig <martin.craig@eng.ox.ac.uk>",
                          "subject": "Quantiphyse Registration",
                          "text": "Name: %s\nInstitution: %s\nEmail: %s\n" % (name, inst, email)})
            except:
                traceback.print_exc()
                warnings.warn("Failed to send registration email")
        self.accept()
