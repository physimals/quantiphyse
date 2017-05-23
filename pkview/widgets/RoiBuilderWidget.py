"""
Author: Martin Craig
Copyright (c) 2017 University of Oxford
"""

from __future__ import division, unicode_literals, absolute_import, print_function

import numpy as np
from PySide import QtCore, QtGui

from pkview.QtInherit.dialogs import error_dialog
from pkview.QtInherit import HelpButton
from pkview.widgets import PkWidget
from pkview.ImageView import PickMode

class RoiBuilderWidget(PkWidget):
    """
    Widget for building ROIs
    """

    def __init__(self, **kwargs):
        super(RoiBuilderWidget, self).__init__(name="ROI Builder", icon="roibuild", desc="Build ROIs", **kwargs)

    def init_gui(self):
        layout = QtGui.QVBoxLayout()
        
        hbox = QtGui.QHBoxLayout()
        title = QtGui.QLabel("<font size=5>ROI Builder</font>")
        hbox.addWidget(title)
        hbox.addStretch(1)
        help_btn = HelpButton(self, "roi_builder")
        hbox.addWidget(help_btn)
        layout.addLayout(hbox)

        layout.addStretch(1)
        self.setLayout(layout)

    def activate(self):
        self.ivl.set_picker(PickMode.LASSO)

    def deactivate(self):
        self.ivl.set_picker(PickMode.SINGLE)