from __future__ import division, unicode_literals, absolute_import, print_function

from PySide import QtCore, QtGui

import pyqtgraph as pg
import numpy as np

#TODO create an non model based analysis tool which ties into creating new image objects

class SECurve(QtGui.QWidget):
    """
    Side widgets for plotting SE curves
    """

    def __init__(self):
        super(SECurve, self).__init__()

        win1 = pg.GraphicsWindow(title="Basic plotting examples")
        p1 = win1.addPlot(title="Signal enhancement curve")
        self.curve = p1.plot(pen=(200, 200, 200), symbolBrush=(255, 0, 0), symbolPen='k')

        l1 = QtGui.QVBoxLayout()
        self.button1 = QtGui.QPushButton("test OK 2")

        l1.addWidget(win1)
        l1.addWidget(self.button1)
        self.setLayout(l1)

    def __plot(self, values1):
        self.curve.setData(values1)

    @QtCore.Slot(np.ndarray)
    def sig_mouse(self, values1):
        self.__plot(values1)


class SECurve2(QtGui.QWidget):
    """
    Side widgets for plotting SE curves
    """

    def __init__(self):
        super(SECurve2, self).__init__()

        win1 = pg.GraphicsWindow(title="Basic plotting examples")
        p1 = win1.addPlot(title="Test plot")
        self.curve = p1.plot(pen='y')

        l1 = QtGui.QVBoxLayout()
        self.button1 = QtGui.QPushButton("test OK 2")

        l1.addWidget(win1)
        l1.addWidget(self.button1)
        self.setLayout(l1)

    def __plot(self, values1):
        self.curve.setData(values1)

    @QtCore.Slot(np.ndarray)
    def sig_mouse(self, values1):
        self.__plot(values1)
