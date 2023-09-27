import pyqtgraph as pg

class ViewWidget(pg.GraphicsView):

    def __init__(self, name):
        pg.GraphicsView.__init__(self)
        
        # View box to display graphics items
        self._viewbox = pg.ViewBox(name=name, border=pg.mkPen((0x6c, 0x6c, 0x6c), width=2.0))
        self._viewbox.setAspectLocked(True)
        self._viewbox.setBackgroundColor([0, 0, 0])
        self._viewbox.enableAutoRange()
        self.setCentralItem(self._viewbox)

        # Dummy image item which enables us to translate click co-ordinates
        # into image space co-ordinates even when there is no data in the view
        self._dummy = pg.ImageItem()
        self._dummy.setVisible(False)
        self._viewbox.addItem(self._dummy, ignoreBounds=True)

    def reset(self):
        """ Reset the viewer to show all data sets"""
        # Adjust axis scaling to that of the viewing grid so voxels have correct relative size FIXME mess IVL is from subclass
        self._viewbox.setAspectLocked(True, ratio=(self._ivl.grid.spacing[self.xaxis] / self._ivl.grid.spacing[self.yaxis]))
        self.debug("Auto range")
        self._viewbox.autoRange()

    def redraw(self):
        """ Force a redraw of the viewer, e.g. if data has changed """
        for view in self._data_views.values():
            view.redraw()

    def add(self, item, *args, **kwargs):
        self._viewbox.addItem(item, *args, **kwargs)
        
    def remove(self, item):
        self._viewbox.removeItem(item)

    def invertX(self, invert):
        self._viewbox.invertX(invert)

    def coordsFromMouse(self, pos):
        return self._dummy.mapFromScene(pos)
