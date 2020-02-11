"""
Quantiphyse - Custom ImageItem which can be masked by an ROI

Copyright (c) 2013-2019 University of Oxford
"""

from __future__ import division, unicode_literals, absolute_import

import collections
import logging

import numpy as np

import pyqtgraph as pg

from quantiphyse.utils.enums import Boundary

LOG = logging.getLogger(__name__)

class MaskableImage(pg.ImageItem):
    """
    Minor addition to ImageItem to allow it to be masked by an ROI
    """
    def __init__(self, image=None, **kwargs):
        pg.ImageItem.__init__(self, image, **kwargs)
        self.mask = None
        self.boundary = Boundary.TRANS

    def set_boundary_mode(self, mode):
        """
        Set the boundary mode, i.e. how data outside the colour map
        range is treated. It can be made transparent or clamped to
        the max/min colour

        :param mode: Boundary.TRANS or Boundary.CLAMP
        """
        self.boundary = mode
        self.updateImage()

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

            if self.boundary == Boundary.TRANS:
                # Make out of range values transparent
                trans = np.logical_or(self.image < self.levels[0], self.image > self.levels[1])
                argb[:, :, 3][trans] = 0
            elif self.boundary == Boundary.LOWERTRANS:
                # Make out of range values transparent
                trans = self.image < self.levels[0]
                argb[:, :, 3][trans] = 0
            elif self.boundary == Boundary.UPPERTRANS:
                # Make out of range values transparent
                trans = self.image > self.levels[1]
                argb[:, :, 3][trans] = 0

        self.qimage = pg.functions.makeQImage(argb, alpha)
