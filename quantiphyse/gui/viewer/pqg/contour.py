import pyqtgraph as pg

class Contour(pg.IsocurveItem):

    def __init__(self):
        pg.IsocurveItem.__init__(self)

    def setColor(self, col):
        self.setPen(pg.mkPen(col, width=3))

class ViewBox(pg.ViewBox):

    def __init__(self):
        pg.ViewBox.__init__(self)

