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
    def __init__(self, ivl, view, *args, **kwargs):
        self.percentile = kwargs.pop("percentile", 100)
        kwargs["fillHistogram"] = False
        super(MultiImageHistogramWidget, self).__init__(*args, **kwargs)

        self.setBackground(None)
        self.ivl = ivl
        self.view = view
        self.vol = 0
        self.imgs = []
        self.updating = False

        self.ivl.sig_focus_changed.connect(self._focus_changed)
        self.view.sig_view_changed.connect(self._view_changed)
        self.sigLevelChangeFinished.connect(self._levels_changed)
        self.sigLevelsChanged.connect(self._levels_changed)
        self.sigLookupTableChanged.connect(self._lut_changed)
        self._view_changed()
        self._update_histogram()

    def add_img(self, img):
        """
        Add a pyqtgraph.ImageItem to the histogram
        """
        self.imgs.append(img)

    def remove_img(self, img):
        """
        Remove a pyqtgraph.ImageItem from the histogram
        """
        self.imgs.remove(img)

    def _view_changed(self):
        try:
            self.updating = True
            if self.view.get("cmap") != "custom":
                try:
                    self.gradient.loadPreset(self.view.get("cmap"))
                except KeyError:
                    self._set_matplotlib_gradient(self.view.get(("cmap")))
            
            if self.view.get("cmap_range") is not None:
                self.region.setRegion(self.view.get(("cmap_range")))

            #self.lut = None
            for img in self.imgs:
                img.setLookupTable(self._get_image_lut, update=True)
        finally:
            self.updating = False

    def _levels_changed(self):
        if not self.updating:
            self.view.set("cmap_range", list(self.region.getRegion()))

    def _lut_changed(self):
        if not self.updating:
            self.view.set("cmap", "custom")

    def _focus_changed(self, pos):
        if self.vol != pos[3]:
            self.vol = pos[3]
            self._update_histogram()
    
    def _update_histogram(self):
        if self.view.data is not None:
            arr = remove_nans(self.view.data.volume(self.vol))
            flat = arr.reshape(-1)
            img = pg.ImageItem(flat.reshape([1, -1]))
            hist = img.getHistogram()
            if hist[0] is None: return
            self.plot.setData(*hist)

    def _get_image_lut(self, img):
        lut = self.getLookupTable(img, alpha=True)
        if self.view is not None:
            for row in lut:
                row[3] = self.view.get("alpha")

        #self.lut = lut
        return lut

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
