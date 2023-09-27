import pyqtgraph as pg

class Arrow(pg.ArrowItem):

    def __init__(self):
        pg.ArrowItem.__init__(self)

    def setColor(self, col):
        self.setPen(pg.mkPen(col))
        self.setBrush(pg.mkBrush(col))