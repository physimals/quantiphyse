"""
Quantiphyse - classes which draw 2D data slices

Copyright (c) 2013-2019 University of Oxford
"""

from __future__ import division, unicode_literals, absolute_import

import logging

import numpy as np

try:
    from PySide import QtGui, QtCore, QtGui as QtWidgets
except ImportError:
    from PySide2 import QtGui, QtCore, QtWidgets

import pyqtgraph as pg

from .maskable_image import MaskableImage

LOG = logging.getLogger(__name__)

class SliceDataView:
    """
    View of a QpData item on a 2D orthographic view
    """

    def __init__(self, qpdata, viewbox, plane, vol, view=None):
        """
        :param qpdata: QpData instance
        :param viewbox: pyqtgraph ViewBox instance
        :param view_metadata: View parameters
        """
        self._qpdata = qpdata
        self._viewbox = viewbox
        self._plane = plane
        self._vol = vol
        self._view = view
        self._redraw_options = [
            "visible",
            "roi_only",
            "z_value",
            "interp_order"
            "shade",
            "contour",
        ]
        self._img = MaskableImage()
        self._viewbox.addItem(self._img)
        LOG.debug("New slicedataview - redrawing")
        self.update()
        self.redraw()

        self._view.sig_changed.connect(self._view_changed)

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
        LOG.debug("visible? %s", self._view.visible)
        self._img.setVisible(self._view.visible)
        self._img.setZValue(self._view.z_value)
        self._img.set_boundary_mode(self._view.boundary)
        self._img.setLookupTable(self._view.lut, update=True)
        self._img.setLevels(self._view.cmap_range)
        LOG.debug("overlay cmap range %s", self._view.cmap_range)

    def redraw(self):
        """
        Update the image when the slice data may have changed
        and therefore may need re-extracting. This is more expensive
        than just changing image parameters so it is only triggered
        when required
        """
        self._redraw_image(interp_order=self._view.interp_order)

    def remove(self):
        LOG.debug("Removing slice view")
        self._viewbox.removeItem(self._img)

    def _view_changed(self, key, value):
        LOG.debug("View params changed: %s=%s", key, value)
        self.update()
        if key in self._redraw_options:
            self.redraw()

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
