__author__ = 'engs1170'

from PySide import QtCore, QtGui
import numpy as np
from QtInherit.QtSubclass import QGroupBoxB


class RandomWalkerWidget(QtGui.QWidget):
    """
    Widget for clustering the tumour into various regions
    """

    sig_set_annotation = QtCore.Signal(int)
    sig_save_annotation = QtCore.Signal(bool)

    def __init__(self):
        super(RandomWalkerWidget, self).__init__()

        #self.setStatusTip("Click points on the 4D volume to see time curve")

        # Number of clusters inside the ROI
        self.combo = QtGui.QSpinBox(self)
        self.combo.setRange(0, 10)
        self.combo.setValue(1)
        #self.combo.activated[str].connect(self.emit_cchoice)
        self.combo.setToolTip("Set the label")

        #Run clustering button
        self.b1 = QtGui.QPushButton('Set', self)
        self.b1.clicked.connect(self.setAnnotLabel)

        #Run clustering button
        self.b2 = QtGui.QPushButton('Save annotation', self)
        self.b2.clicked.connect(self.saveAnnotLabel)

        l1 = QtGui.QVBoxLayout()
        l1.addWidget(self.combo)
        l1.addWidget(self.b1)
        l1.addWidget(self.b2)
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

    def setAnnotLabel(self):
        self.sig_set_annotation.emit(self.combo.value())

    def saveAnnotLabel(self):
        self.sig_save_annotation.emit(True)






