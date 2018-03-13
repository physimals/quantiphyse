"""
Quantiphyse - Dialog box for user registration

Copyright (c) 2013-2018 University of Oxford
"""

from __future__ import division, unicode_literals, print_function, absolute_import

import requests

from PySide import QtGui

from ..utils import get_icon, get_version

class RegisterDialog(QtGui.QDialog):
    """
    Dialog box which asks a first-time user to send a registration email
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

        hbox = QtGui.QHBoxLayout()
        hbox.addStretch(1)
        hbox.addWidget(QtGui.QLabel("\n<font size=5>Welcome to Quantiphyse %s</font>" % get_version()))
        hbox.addStretch(1)
        layout.addLayout(hbox)

        label = QtGui.QLabel("\nPlease register as a user. We will not send any unsolicited communications, this is just to help us know where the software is being used")
        label.setWordWrap(True)
        layout.addWidget(label)

        grid = QtGui.QGridLayout()
        grid.addWidget(QtGui.QLabel("Name"), 0, 0)
        self.name_edit = QtGui.QLineEdit()
        grid.addWidget(self.name_edit, 0, 1)
        grid.addWidget(QtGui.QLabel("Institution"), 0, 2)
        self.inst_edit = QtGui.QLineEdit()
        grid.addWidget(self.inst_edit, 0, 3)
        grid.addWidget(QtGui.QLabel("Email"), 1, 0)
        self.email_edit = QtGui.QLineEdit()
        grid.addWidget(self.email_edit, 1, 1, 1, 3)
        layout.addLayout(grid)

        layout.addWidget(QtGui.QLabel("<font size=5>\nLicense Agreement</font>"))
        edit = QtGui.QTextEdit()
        # FIXME
        #lic_file = open(get_local_file("../licence.md"), "r")
        #try:
        #    for line in lic_file:
        #        edit.append(line)
        #finally:
        #    lic_file.close()
        #edit.moveCursor (QtGui.QTextCursor.Start)
        #edit.ensureCursorVisible()
        layout.addWidget(edit)

        label = QtGui.QLabel("""The Software is distributed "AS IS" under this Licence solely for non-commercial use. If you are interested in using the Software commercially, please contact the technology transfer company of the University, to negotiate a licence. Contact details are: enquiries@innovation.ox.ac.uk""")
        label.setWordWrap(True)
        layout.addWidget(label)

        self.agree_cb = QtGui.QCheckBox("I agree to abide by the terms of the Quantiphyse license")
        self.agree_cb.stateChanged.connect(self.agree_changed)
        layout.addWidget(self.agree_cb)
        
        self.button_box = QtGui.QDialogbutton_box(QtGui.QDialogbutton_box.Ok|QtGui.QDialogbutton_box.Cancel)
        self.button_box.accepted.connect(self.accept)
        self.button_box.rejected.connect(self.reject)
        self.button_box.button(QtGui.QDialogbutton_box.Ok).setEnabled(False)
        layout.addWidget(self.button_box)

        self.setLayout(layout)
        self.setFixedSize(600, 600)

    def agree_changed(self, state):
        self.button_box.button(QtGui.QDialogbutton_box.Ok).setEnabled(state)

    def send_register_email(self, name, inst, email):
        """
        Send registration email
        
        Note that this email service has been set only to send to the specified recipient
        so this cannot be used to spam anybody else!
        """
        return requests.post(
            "https://api.mailgun.net/v3/sandboxd8aca8efc95348609a6d63f0c651f4d2.mailgun.org/messages",
            auth=("api", "key-c0be61e997b71c2d0c43fa8aeb706a5c"),
            data={"from": "Quantiphyse <postmaster@sandboxd8aca8efc95348609a6d63f0c651f4d2.mailgun.org>",
                  "to": "Martin Craig <martin.craig@eng.ox.ac.uk>",
                  "subject": "Quantiphyse Registration",
                  "text": "Name: %s\nInstitution: %s\nEmail: %s\n" % (name, inst, email)})
