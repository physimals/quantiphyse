from PySide2 import QtCore

import pyqtgraph as pg

class VLine(pg.InfiniteLine):
    def __init__(self):
        pg.InfiniteLine.__init__(self, angle=90, movable=False)
        self.setPen(pg.mkPen((0, 255, 0), width=1.0, style=QtCore.Qt.DashLine))

class HLine(pg.InfiniteLine):
    def __init__(self):
        pg.InfiniteLine.__init__(self, angle=0, movable=False)
        self.setPen(pg.mkPen((0, 255, 0), width=1.0, style=QtCore.Qt.DashLine))
