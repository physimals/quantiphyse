"""
Quantiphyse - Dialog box for user registration

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

from __future__ import division, unicode_literals, print_function, absolute_import

import sys
import traceback
import warnings

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
    Check if the user has accepted the license agreement and if not exit
    the program
    """
    if not license_accepted():
        accepted = LicenseDialog(quantiphyse.gui.dialogs.MAINWIN).exec_()
        set_license_accepted(accepted)

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
