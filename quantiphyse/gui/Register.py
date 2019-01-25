"""
Quantiphyse - Dialog box for user registration

Copyright (c) 2013-2018 University of Oxford
"""

from __future__ import division, unicode_literals, print_function, absolute_import

import sys
import traceback
import warnings

import requests

from PySide import QtGui, QtCore

import quantiphyse.gui.dialogs
from quantiphyse.utils import get_icon, get_version, get_local_file

LICENSE_ACCEPTED_KEY = "license_accepted"

def check_register():
    """
    Check if the user has accepted the license agreement and if not show the 
    license/registration dialog
    """
    settings = QtCore.QSettings()
    if not settings.contains(LICENSE_ACCEPTED_KEY) or not settings.value(LICENSE_ACCEPTED_KEY):
        dialog = RegisterDialog(quantiphyse.gui.dialogs.MAINWIN)
        accepted = dialog.exec_()
        settings.setValue(LICENSE_ACCEPTED_KEY, accepted)
        if accepted:
            dialog.send_register_email()
    if not settings.value(LICENSE_ACCEPTED_KEY):
        sys.exit(-1)

class RegisterDialog(QtGui.QDialog):
    """
    Dialog box which asks a first-time user to accept the license and optionally 
    send a registration email
    """
    def __init__(self, parent=None):
        QtGui.QDialog.__init__(self, parent)
        
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

        # Registration section
        box = QtGui.QGroupBox("Registration (optional - can leave blank)")
        vbox = QtGui.QVBoxLayout()
        box.setLayout(vbox)
        label = QtGui.QLabel("<font size=3>We will not send any unsolicited communications,"
                             "this is just to help us know where the software is being used")
        label.setWordWrap(True)
        vbox.addWidget(label)

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
        vbox.addLayout(grid)
        layout.addWidget(box)

        # License agreement
        box = QtGui.QGroupBox("License agreement")
        vbox = QtGui.QVBoxLayout()
        box.setLayout(vbox)
        edit = QtGui.QTextEdit()
        # FIXME
        lic_file = open(get_local_file("../licence.md"), "r")
        try:
            edit.setCurrentFont(QtGui.QFont("Monospace", 8))
            for line in lic_file:
                edit.append(line.rstrip())
            edit.append("</pre>")
        finally:
            lic_file.close()
        edit.moveCursor(QtGui.QTextCursor.Start)
        edit.ensureCursorVisible()
        vbox.addWidget(edit)
        layout.addWidget(box)
        
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
