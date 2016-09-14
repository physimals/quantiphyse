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

from pkview.QtInherit import HelpButton


class ExampleWidget1(QtGui.QWidget):
    """
    Widget for setting a threshold to the image data inside the ROI. This is saved as an overlay.
    """

    # emit reset command t
    sig_emit_reset = QtCore.Signal(bool)

    def __init__(self, local_file_path):
        super(ExampleWidget1, self).__init__()

        self.local_file_path = local_file_path

        # self.setStatusTip("Click points on the 4D volume to see time curve")
        title1 = QtGui.QLabel("<font size=5> Example 1: Threshold volume</font>")
        bhelp = HelpButton(self, self.local_file_path)
        lhelp = QtGui.QHBoxLayout()
        lhelp.addWidget(title1)
        lhelp.addStretch(1)
        lhelp.addWidget(bhelp)

        explanation = QtGui.QLabel('This is a basic example of a \n'
                                   'widget for development purposes. \n'
                                   'A DCE-MRI image and ROI are \n'
                                   'loaded normally and clicking run \n'
                                   'creates an overlay only shows values \n'
                                   'in the ROI above a defined threshold.')

        # Run clustering button
        self.b1 = QtGui.QPushButton('Process', self)
        self.b1.clicked.connect(self.run_threshold)

        t1 = QtGui.QLabel('ROI threshold value:')
        self.val_t1 = QtGui.QLineEdit('1', self)

        s1 = QtGui.QLabel('Slice to threshold:')
        self.val_s1 = QtGui.QLineEdit('0', self)

        l03 = QtGui.QHBoxLayout()
        l03.addWidget(self.b1)
        l03.addStretch(1)
        l03.addWidget(t1)
        l03.addWidget(self.val_t1)

        l04 = QtGui.QHBoxLayout()
        l04.addStretch(1)
        l04.addWidget(s1)
        l04.addWidget(self.val_s1)

        # Outer layout
        l1 = QtGui.QVBoxLayout()
        l1.addLayout(lhelp)
        l1.addWidget(explanation)
        l1.addLayout(l03)
        l1.addLayout(l04)
        l1.addStretch(1)
        self.setLayout(l1)

        # Initialisation
        # Volume management widget
        self.ivm = None

    def add_image_management(self, image_vol_management):

        """
        Adding image management
        """
        self.ivm = image_vol_management

    def run_threshold(self):
        """
        Run kmeans clustering using normalised PCA modes
        """

        # Check if an image and roi exists or otherwise throw an error
        if self.ivm.get_image() is None:
            m1 = QtGui.QMessageBox()
            m1.setText("The image doesn't exist! Please load.")
            m1.setWindowTitle("PkView")
            m1.exec_()
            return

        if self.ivm.get_roi() is None:
            m1 = QtGui.QMessageBox()
            m1.setWindowTitle("PkView")
            m1.setText("The Image or ROI doesn't exist! Please load.")
            m1.exec_()
            return

        img = self.ivm.get_image()
        roi = self.ivm.get_roi()
        roi = roi > 0

        slice1 = int(self.val_s1.text())
        thresh1 = float(self.val_t1.text())

        img1 = img[:, :, :, slice1]
        img1 = img1 * roi
        img1[img1 < thresh1] = 0

        # Save the new overlay with name clusters
        # (force assigns it to the name specified
        # even if that name doesn't exist in the dictionary)
        self.ivm.set_overlay(choice1='clusters', ovreg=img1, force=True)
        self.ivm.set_current_overlay(choice1='clusters')
        # Tell the window to update the visualisation
        self.sig_emit_reset.emit(1)

        print("Done!")

