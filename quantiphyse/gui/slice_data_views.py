"""
Quantiphyse - classes which draw data slices

Copyright (c) 2013-2019 University of Oxford
"""

from __future__ import division, unicode_literals, absolute_import

import collections
import logging

from PySide import QtCore, QtGui
import numpy as np

import pyqtgraph as pg

from quantiphyse.gui.colors import get_lut

LOG = logging.getLogger(__name__)

BOUNDARY_TRANS = 0
BOUNDARY_CLAMP = 1
BOUNDARY_LOWERTRANS = 2
BOUNDARY_UPPERTRANS = 3

def initial_cmap_range(qpdata, percentile=100):
    """
    Get an initial colourmap range for a data item.

    This is taken by ignoring NaN and infinity and returning
    a percentile of the data range. By default returns
    the full min to max range.

    :return: Sequence of (min, max)
    """
    data = qpdata.volume(int(qpdata.nvols/2)).flatten()
    # This ignores infinite values too unlike np.nanmin/np.nanmax
    nonans = np.isfinite(data)
    cmin, cmax = np.min(data[nonans]), np.max(data[nonans])
    # Issue #101: if min is exactly zero, make it slightly more
    # as a heuristic for data sets where zero=background
    if cmin == 0:
        cmin = 1e-7*cmax

    if percentile < 100:
        perc_max = np.nanpercentile(data, percentile)
        if perc_max > cmin:
            cmax = perc_max

    return cmin, cmax

class MaskableImage(pg.ImageItem):
    """
    Minor addition to ImageItem to allow it to be masked by an ROI
    """
    def __init__(self, image=None, **kwargs):
        pg.ImageItem.__init__(self, image, **kwargs)
        self.mask = None
        self.boundary = BOUNDARY_TRANS

    def set_boundary_mode(self, mode):
        """
        Set the boundary mode, i.e. how data outside the colour map
        range is treated. It can be made transparent or clamped to
        the max/min colour

        :param mode: BOUNDARY_TRANS or BOUNDARY_CLAMP
        """
        self.boundary = mode

    def render(self):
        """
        Custom masked renderer based on PyQtGraph code
        """
        if self.image is None or self.image.size == 0:
            return
        if isinstance(self.lut, collections.Callable):
            lut = self.lut(self.image)
        else:
            lut = self.lut

        argb, alpha = pg.functions.makeARGB(self.image, lut=lut, levels=self.levels)
        if self.image.size > 1:
            if self.mask is not None:
                argb[:, :, 3][self.mask == 0] = 0

            if self.boundary == BOUNDARY_TRANS:
                # Make out of range values transparent
                trans = np.logical_or(self.image < self.levels[0], self.image > self.levels[1])
                argb[:, :, 3][trans] = 0
            elif self.boundary == BOUNDARY_LOWERTRANS:
                # Make out of range values transparent
                trans = self.image < self.levels[0]
                argb[:, :, 3][trans] = 0
            elif self.boundary == BOUNDARY_UPPERTRANS:
                # Make out of range values transparent
                trans = self.image > self.levels[1]
                argb[:, :, 3][trans] = 0

        self.qimage = pg.functions.makeQImage(argb, alpha)

class SliceDataView(QtCore.QObject):
    """
    View of a QpData item on a 2D orthographic view
    """

    def __init__(self, qpdata, viewbox, plane, vol):
        """
        :param qpdata: QpData instance
        :param viewbox: pyqtgraph ViewBox instance
        :param view_metadata: View parameters
        """
        self._qpdata = qpdata
        self._viewbox = viewbox
        self._plane = plane
        self._vol = vol

        self._default_options = {
            "visible" : False,
            "roi_only" : False,
            "boundary" : BOUNDARY_TRANS,
            "alpha" : 255,
            "cmap_range" : initial_cmap_range(self._qpdata),
            "z_value" : -1,
            "interp_order" : 0,
            "cmap" : "jet",
        }
        self._redraw_options = [
            "visible",
            "roi_only",
            "z_value",
            "interp_order"
            "shade",
            "contour",
        ]
        #self._qpdata.metadata["SliceDataView"] = self._qpdata.metadata.get("SliceDataView", {})
        self._qpdata.metadata.sig_changed.connect(self._metadata_changed)

        self._img = MaskableImage()
        self._viewbox.addItem(self._img)
        LOG.debug("New slicedataview - redrawing")
        self.update()
        self.redraw()

    @property
    def plane(self):
        return self._plane

    @plane.setter
    def plane(self, plane):
        if plane != self._plane:
            LOG.debug("Plane changed - redrawing")
            self._plane = plane
            self.redraw()

    @property
    def vol(self):
        return self._vol

    @vol.setter
    def vol(self, vol):
        if vol != self._vol and vol < self._qpdata.nvols:
            LOG.debug("Volume changed - redrawing")
            self._vol = vol
            self.redraw()

    def update(self):
        """
        Update the image without re-slicing the data
        """
        LOG.debug("visible? %s", self.visible)
        self._img.setVisible(self.visible)
        self._img.setZValue(self.z_value)
        self._img.set_boundary_mode(self.boundary)
        self._img.setLookupTable(get_lut(self.cmap), update=True)
        self._img.setLevels(self.cmap_range)
        LOG.debug("overlay cmap %s", get_lut(self.cmap, alpha=self.alpha))
        LOG.debug("overlay cmap range %s", self.cmap_range)

    def redraw(self):
        """
        Update the image when the slice data may have changed
        and therefore may need re-extracting. This is more expensive
        than just changing image parameters so it is only triggered
        when required
        """
        self._redraw_image()

    def remove(self):
        self._viewbox.removeItem(self._img)

    def _redraw_image(self, mask=None, interp_order=0):
        LOG.debug("slicedataview: redrawing image")
        LOG.debug(self._vol)
        LOG.debug("%s, %s", self._plane.basis, self._plane.normal)
        if self._img.isVisible():
            LOG.debug("visible")
            slicedata, slicemask, scale, offset = self._qpdata.slice_data(self._plane, vol=self._vol,
                                                                          interp_order=interp_order)
            self._img.setTransform(QtGui.QTransform(scale[0, 0], scale[0, 1],
                                                    scale[1, 0], scale[1, 1],
                                                    offset[0], offset[1]))
            self._img.setImage(slicedata, autoLevels=False)
            LOG.debug("Image data range: %f, %f", np.min(slicedata), np.max(slicedata))

            if mask is not None:
                maskdata, _, _, _ = mask.slice_data(self._plane)
                self._img.mask = np.logical_and(maskdata, slicemask)
            else:
                self._img.mask = slicemask

    def __getattr__(self, name):
        return self._qpdata.metadata.get(name, self._default_options.get(name, None))

    def __setattr__(self, name, value):
        if name[0] == "_" or name in ("plane", "vol"):
            super(SliceDataView, self).__setattr__(name, value)
        else:
            self._qpdata.metadata[name] = value

    def _metadata_changed(self, key):
        LOG.debug("View metadata changed: %s", key)
        self.update()
        if key in self._redraw_options:
            self.redraw()

class MainSliceDataView(SliceDataView):
    """
    Orthographic view for the main data.

    This is always greyscale and at the bottom of the stack
    """

    def __init__(self, qpdata, viewbox, plane, vol):
        self._cmap_range = initial_cmap_range(qpdata, percentile=99)
        SliceDataView.__init__(self, qpdata, viewbox, plane, vol)

    def update(self):
        """
        Update image view parameters without redrawing
        """
        LOG.debug("main data view updating")
        self._img.setVisible(True)
        self._img.setZValue(-999)
        self._img.set_boundary_mode(BOUNDARY_CLAMP)
        self._img.setLevels(self._cmap_range)
        LOG.debug("cmap range: %s", self._cmap_range)
