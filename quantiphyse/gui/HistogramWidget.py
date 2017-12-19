
from __future__ import division, unicode_literals, absolute_import, print_function

from matplotlib import cm
import numpy as np

import pyqtgraph as pg

from ..utils import debug

class MultiImageHistogramWidget(pg.HistogramLUTWidget):
    """
    A histogram widget which has one array of 'source' data
    (which it gets the histogram itself and the initial levels from)
    and multiple image item views which are affected by changes to the
    levels or LUT
    """
    def __init__(self, ivm, ivl, imgs, *args, **kwargs):
        self.percentile = kwargs.pop("percentile", 100)
        kwargs["fillHistogram"] = False
        super(MultiImageHistogramWidget, self).__init__(*args, **kwargs)
        self.setBackground(None)
        self.ivm = ivm
        self.ivl = ivl
        self.ivl.sig_focus_changed.connect(self._focus_changed)
        self.vol = 0
        self.imgs = imgs
        self.dv = None
        self.sigLevelChangeFinished.connect(self._update_region)
        self.sigLevelsChanged.connect(self._update_region)
        self.sigLookupTableChanged.connect(self._update_lut)
        self._update_lut()
        self._update_region()

    def set_data_view(self, dv):
        """
        Set the source data viewfor the histogram widget. This will be a
        3d or 4d volume, so we flatten it to 2d in order to use the PyQtGraph
        methods to extract a histogram

        @percentile specifies that the initial LUT range should be set to this
        percentile of the data - for main volume it is useful to set this 
        to 99% to improve visibility
        """
        if self.dv is not None:
            self.dv.sig_changed.disconnect(self._update)
        self.dv = dv

        if self.dv is not None:
            self._update(dv)

            # Only needs to be done once for a new DV
            self._update_histogram()
            arr = dv.data().std()
            self.dv.sig_changed.connect(self._update)
        else:
            self.plot.setData([], [])
            self.region.setRegion([0, 1])

    def _update(self, dv):
        try:
            self.gradient.loadPreset(self.dv.cmap)
        except KeyError:
            self._setMatplotlibGradient(self.dv.cmap)
        self.region.setRegion(self.dv.cmap_range)
        self.lut = None
        self._update_lut()

    def _update_region(self):
        for img in self.imgs:
            if img is not None:
                img.setLevels(self.region.getRegion())
        if self.dv is not None:
            self.dv.cmap_range = list(self.region.getRegion())

    def _update_lut(self):
        for img in self.imgs:
            if img is not None:
                img.setLookupTable(self._get_image_lut, update=True)

    def _update_histogram(self):
        data = self.dv.data()
        arr = data.get_slice([(3, self.vol),])

        flat = arr.reshape(-1)
        if self.percentile < 100: self.region.lines[1].setValue(np.percentile(flat, self.percentile))
        ii = pg.ImageItem(flat.reshape([1, -1]))
        h = ii.getHistogram()
        if h[0] is None: return
        self.plot.setData(*h)

    def _focus_changed(self, pos):
        if self.vol != pos[3]:
            self.vol = pos[3]
            if self.dv is not None:
                self._update_histogram()
    
    def _get_image_lut(self, img):
        lut = self.getLookupTable(img, alpha=True)
        if self.dv is not None:
            for row in lut[1:]:
                row[3] = self.dv.alpha

        self.lut = lut
        return lut

    def _setMatplotlibGradient(self, name):
        """
        Slightly hacky method to copy MatPlotLib gradients to pyqtgraph.

        Is not perfect because Matplotlib specifies gradients in a different way to pyqtgraph
        (specifically there is a separate list of ticks for R, G and B). So we just sample
        the colormap at 10 points which is OK for most slowly varying gradients.
        """
        cmap = getattr(cm, name)
        ticks = [(pos, [255 * v for v in cmap(pos)]) for pos in np.linspace(0, 1, 10)]
        self.gradient.restoreState({'ticks': ticks, 'mode': 'rgb'})
