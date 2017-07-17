"""

Author: Benjamin Irving (benjamin.irv@gmail.com)
Copyright (c) 2013-2015 University of Oxford, Benjamin Irving

This files provides examples (currently 1) of how to implement widgets that provide
additional funcitonality to the core GUI. This could be process, visualisations or graphs.

Widgets are added to a tabbed sidebar on the right of the GUI

"""

from __future__ import division, unicode_literals, absolute_import, print_function

import numpy as np
import pyqtgraph as pg
from PySide import QtCore, QtGui

from ..QtInherit import HelpButton
from ..QtInherit.dialogs import error_dialog

class ExampleWidget(PkWidget):
    """
    Widget for setting a threshold to the image data inside the ROI. This is saved as an overlay.
    """
    def __init__(self, **kwargs):
        super(ExampleWidget, self).__init__(name="Threshold", desc="Threshold data", icon="quantiphyse", **kwargs)

    def init_ui(self):
        main_vbox = QtGui.QVBoxLayout()
        
        hbox = QtGui.QHBoxLayout()
        hbox.addWidget(QtGui.QLabel('<font size="5">Threshold volume</font>'))
        hbox.addStretch(1)
        hbox.addWidget(HelpButton(self))
        main_vbox.addLayout(hbox)

        explanation = QtGui.QLabel('This is a basic example of a \n'
                                   'widget for development purposes. \n'
                                   'A DCE-MRI image and ROI are \n'
                                   'loaded normally and clicking run \n'
                                   'creates an overlay only shows values \n'
                                   'in the ROI above a defined threshold.')
        main_vbox.addWidget(explanation)

        hbox = QtGui.QHBoxLayout()
        self.b1 = QtGui.QPushButton('Process', self)
        self.b1.clicked.connect(self.run_threshold)
        hbox.addWidget(self.b1)
        hbox.addStretch(1)

        hbox.addWidget(QtGui.QLabel('ROI threshold value:'))
        self.val_t1 = QtGui.QLineEdit('1', self)
        hbox.addWidget(self.val_t1)
        main_vbox.addLayout(hbox)
        
        hbox = QtGui.QHBoxLayout()
        hbox.addStretch(1)
        hbox.addWidget(QtGui.QLabel('Slice to threshold:'))
        self.val_s1 = QtGui.QLineEdit('0', self)
        hbox.addWidget(self.val_s1)
        main_vbox.addLayout(hbox)

        main_vbox.addStretch(1)
        self.setLayout(main_vbox)

    def run_threshold(self):
        # Check if an image and roi exists or otherwise throw an error
        if self.ivm.vol is None:
            error_dialog("No data loaded")
            return

        if self.ivm.current_roi is None:
            error_dialog("No ROI loaded")
            return

        slice = int(self.val_s1.text())
        thresh = float(self.val_t1.text())

        img = self.ivm.vol[:, :, :, slice1]
        img = img * (self.ivm.current_roi > 0)
        img[img1 < thresh] = 0

        self.ivm.add_overlay(choice1='thresh', img, set_current=True)


