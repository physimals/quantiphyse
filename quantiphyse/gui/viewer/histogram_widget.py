"""
Quantiphyse - Custom histogram display widget

Copyright (c) 2013-2018 University of Oxford
"""

from __future__ import division, unicode_literals, absolute_import, print_function

from matplotlib import cm
import numpy as np

import pyqtgraph as pg

from quantiphyse.data.qpdata import remove_nans

class HistogramWidget(pg.HistogramLUTWidget):
    """
    Displays histogram and colour map from a view metadata object
    and allows them to be updated interactivately

    The histogram is taken from a QpData instance. Normally the 
    colourmap is also taken from the .view property of the QpData, however
    it is possible to set the custom_view property to substitute another
    set of viewing metadata. This is used to implement the 'background'
    main data view.
    """
    def __init__(self, ivl, *args, **kwargs):
        kwargs["fillHistogram"] = False
        super(HistogramWidget, self).__init__(*args, **kwargs)
        self.setBackground(None)

        self._qpdata = None
        self._custom_view = None
        self._vol = 0
        self._updating = False

        ivl.sig_focus_changed.connect(self._focus_changed)
        self.sigLevelChangeFinished.connect(self._levels_changed)
        self.sigLevelsChanged.connect(self._levels_changed)
        self.sigLookupTableChanged.connect(self._lut_changed)

    @property
    def qpdata(self):
        """
        QpData object containing the data to display.

        If the view metadata is not set explicitly, the view property
        of the qpdata is used
        """
        return self._qpdata

    @qpdata.setter
    def qpdata(self, qpdata):
        if self.view is not None:
            try:
                self.view.sig_changed.disconnect(self._view_changed)
            except:
                print("his: except1")

        self._qpdata = qpdata
        if self.view is not None:
            self.view.sig_changed.connect(self._view_changed)
        self._update_cmap()
        self._update_histogram()

    @property
    def view(self):
        """
        Metadata object containing view properties
        """
        if self._qpdata is not None and self._custom_view is None:
            return self._qpdata.view
        else:
            return self._custom_view

    @property
    def custom_view(self):
        return self._custom_view

    @custom_view.setter
    def custom_view(self, view):
        if self.view is not None:
            try:
                self.view.sig_changed.disconnect(self._view_changed)
            except:
                print("his: except2")

        self._custom_view = view
        if self.view is not None:
            self.view.sig_changed.connect(self._view_changed)
        self._update_cmap()

    @property
    def vol(self):
        """
        Current volume index being displayed on the histogram
        """
        return self._vol

    @vol.setter
    def vol(self, vol):
        if vol != self._vol:
            self._vol = vol
            self._update_histogram()

    def _focus_changed(self, focus):
        self.vol = focus[3]

    def _view_changed(self, key, _value):
        if key in ("cmap", "cmap_range"):
            self._update_cmap()

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
        if self.view is not None:
            try:
                self._updating = True

                cmap_range = self.view.cmap_range
                if cmap_range is not None:
                    self.region.setRegion(cmap_range)

                cmap = self.view.cmap
                if not cmap:
                    cmap = "jet"
        
                if cmap != "custom":
                    try:
                        self.gradient.loadPreset(cmap)
                    except KeyError:
                        self._set_matplotlib_gradient(cmap)
                else:
                    # FIXME some other components sets a custom cmap
                    # need to convert to ticks and update gradient
                    pass

            finally:
                self._updating = False

    def _levels_changed(self):
        if self.view is not None and not self._updating:
            self.view.cmap_range = list(self.region.getRegion())

    def _lut_changed(self):
        if self.view is not None and not self._updating:
            # FIXME
            pass
            #self.view.lut = [tuple(row) for row in self.gradient.getLookupTable(255)]
            #self.view.cmap = "custom"

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

class CurrentDataHistogramWidget(HistogramWidget):
    """
    Displays histogram and colour map from current data
    """
    def __init__(self, ivl, *args, **kwargs):
        super(CurrentDataHistogramWidget, self).__init__(ivl, *args, **kwargs)
        ivl.ivm.sig_current_data.connect(self._current_data_changed)

    def _current_data_changed(self, qpdata):
        self.qpdata = qpdata
