"""
Quantiphyse - Extension to the PyQtGraph histogram to support multiple images

Copyright (c) 2013-2018 University of Oxford
"""

from __future__ import division, unicode_literals, absolute_import, print_function

from matplotlib import cm
import numpy as np

import pyqtgraph as pg

from quantiphyse.data.qpdata import remove_nans

class MultiImageHistogramWidget(pg.HistogramLUTWidget):
    """
    A histogram widget which has one array of 'source' data
    (which it gets the histogram itself and the initial levels from)
    and multiple image item views which are affected by changes to the
    levels or LUT
    """
    def __init__(self, *args, **kwargs):
        kwargs["fillHistogram"] = False
        super(MultiImageHistogramWidget, self).__init__(*args, **kwargs)

        self.setBackground(None)
        self._vol = 0
        self._qpdata = None
        self.updating = False

        #self.sigLevelChangeFinished.connect(self._levels_changed)
        #self.sigLevelsChanged.connect(self._levels_changed)
        #self.sigLookupTableChanged.connect(self._lut_changed)
        #self._update_histogram()

    def set_data(self, qpdata):
        """
        Add a view to the histogram
        """
        self._qpdata = qpdata
        self._update_cmap()
        self._update_histogram()

    def set_vol(self, vol):
        self._vol = vol
        self._update_histogram()

    def _update_histogram(self):
        if self._qpdata is not None:
            arr = remove_nans(self._qpdata.volume(self._vol))
            flat = arr.reshape(-1)
            img = pg.ImageItem(flat.reshape([1, -1]))
            hist = img.getHistogram()
            if hist[0] is None:
                return
            self.plot.setData(*hist)

    def _update_cmap(self):
        try:
            self.updating = True

            cmap_range = self._md("cmap_range")
            if cmap_range is not None:
                self.region.setRegion(cmap_range)

            cmap = self._md("cmap")
            if cmap != "custom":
                try:
                    self.gradient.loadPreset(cmap)
                except KeyError:
                    self._set_matplotlib_gradient(cmap)

            #self.lut = None
            # FIXME how to pass the LUT back to the image
            #for img in self.imgs:
            #    img.setLookupTable(self._get_image_lut, update=True)
        finally:
            self.updating = False

    def _levels_changed(self):
        if not self.updating:
            self.view.cmap_range = list(self.region.getRegion())

    def _lut_changed(self):
        if not self.updating:
            self._set_md("cmap", "custom")
            self._set_md("lut", self.gradient.ticks)

    def _set_matplotlib_gradient(self, name):
        """
        Slightly hacky method to copy MatPlotLib gradients to pyqtgraph.

        Is not perfect because Matplotlib specifies gradients in a different way to pyqtgraph
        (specifically there is a separate list of ticks for R, G and B). So we just sample
        the colormap at 10 points which is OK for most slowly varying gradients.
        """
        cmap = getattr(cm, name)
        ticks = [(pos, [255 * v for v in cmap(pos)]) for pos in np.linspace(0, 1, 10)]
        self.gradient.restoreState({'ticks': ticks, 'mode': 'rgb'})
