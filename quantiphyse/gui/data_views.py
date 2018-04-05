"""
Quantiphyse - classes which draw data views

Copyright (c) 2013-2018 University of Oxford
"""

from __future__ import division, unicode_literals, absolute_import, print_function

import collections

from PySide import QtCore, QtGui
import numpy as np

import pyqtgraph as pg

from quantiphyse.utils import get_lut, get_pencol, debug
from quantiphyse.volumes import OrthoSlice, Transform, DataGrid
from quantiphyse.gui.widgets import OptionsButton

from .HistogramWidget import MultiImageHistogramWidget
from .pickers import DragMode, PICKERS, PointPicker

class MaskableImage(pg.ImageItem):
    """
    Minor addition to ImageItem to allow it to be masked by an RoiView
    """
    def __init__(self, image=None, **kwargs):
        pg.ImageItem.__init__(self, image, **kwargs)
        self.mask = None
        self.boundary = DataView.BOUNDARY_TRANS
        self.border = None

    def setBoundaryMode(self, mode):
        """
        Set the boundary mode, i.e. how data outside the colour map
        range is treated. It can be made transparent or clamped to
        the max/min colour

        :param mode: DataView.BOUNDARY_TRANS or DataView.BOUNDARY_CLAMP
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

            if self.boundary == DataView.BOUNDARY_TRANS:
                # Make out of range values transparent
                trans = np.logical_or(self.image < self.levels[0], self.image > self.levels[1])
                argb[:, :, 3][trans] = 0

        self.qimage = pg.functions.makeQImage(argb, alpha)

class DataView(QtCore.QObject):
    """
    View of a data item
    """

    BOUNDARY_TRANS = 0
    BOUNDARY_CLAMP = 1

    # Signals when view parameters are changed
    sig_changed = QtCore.Signal(object)

    def __init__(self, ivm):
        super(DataView, self).__init__()
        self.ivm = ivm

        self.default_options = {}
        self.cached_options = {}
        self.data = None
        self.opts = dict(self.default_options)

    def update(self, vb, slice_plane, slice_vol):
        """
        Draw the data onto the specified pg.ViewBox

        :param vb: pg.ViewBox to draw on to
        :param slice_plane: OrthoSlice defining the slice to draw
        :param slice_vol: Index of the volume to use
        """
        pass

class ImageDataView(DataView):
    """
    View of data rendered as an image slice
    """

    def __init__(self, ivm):
        super(ImageDataView, self).__init__(ivm)
        self.default_options = {
            "visible" : True,
            "roi_only" : False,
            "boundary" : self.BOUNDARY_CLAMP,
            "alpha" : 255,
            "cmap" : "grey",
            "cmap_range" : None,
            "z_value" : -1,
        }
        self.opts = dict(self.default_options)
        self.imgs = {}
        self.histogram = None
        self.mask = None

    def update(self, vb, slice_plane, slice_vol):
        img = self._get_img(vb)
        img.setVisible(self.data is not None and self.opts["visible"])
        if img.isVisible():
            slicedata, scale, offset = self.data.slice_data(slice_plane, vol=slice_vol)
            img.setTransform(QtGui.QTransform(scale[0, 0], scale[0, 1], scale[1, 0], scale[1, 1],
                                              offset[0], offset[1]))
            img.setImage(slicedata, autoLevels=False)
            if self.mask is not None and self.opts["roi_only"]:
                maskdata, _, _ = self.mask.slice_data(slice_plane)
                img.mask = maskdata
            else:
                img.mask = None
            img.setZValue(self.opts["z_value"])
            img.setBoundaryMode(self.opts["boundary"])

    def _get_img(self, vb):
        if vb.name not in self.imgs:
            img = MaskableImage(border='k')
            vb.addItem(img)
            self.imgs[vb.name] = img
            if self.histogram is not None:
                self.histogram.add_img(img)
        return self.imgs[vb.name]

    def _init_opts(self):
        """
        Retrieve view options from cache or use defaults
        """
        if self.data is not None:
            if self.data.name not in self.cached_options:
                self.cached_options[self.data.name] = dict(self.default_options)
            self.opts = self.cached_options[self.data.name]
        else:
            self.opts = dict(self.default_options)

    def _init_cmap(self, percentile=100):
        if self.data is not None and self.opts["cmap_range"] is None:
            # Initial colourmap range
            if percentile < 100:
                # FIXME percentile
                self.opts["cmap_range"] = [self.data.range[0], np.percentile(flat, percentile)]
            else:
                self.opts["cmap_range"] = list(self.data.range)

    def _cleanup_cache(self, data_items):
        """
        Remove data items which no longer exist from the option cache
        """
        for key in self.cached_options.keys():
            if key not in data_items:
                del self.cached_options[key]

class MainDataView(ImageDataView):
    """
    View of main data
    """

    def __init__(self, ivm):
        super(MainDataView, self).__init__(ivm)

        self.ivm.sig_main_data.connect(self._main_data_changed)
        self.ivm.sig_all_data.connect(self._cleanup_cache)

    def _main_data_changed(self, data):
        self.data = data
        self._init_opts()
        self._init_cmap()
        self.sig_changed.emit(self)

class OverlayView(ImageDataView):
    """
    View of the current overlay

    Stores details about visual parameters, e.g. color map and range
    """

    def __init__(self, ivm):
        super(OverlayView, self).__init__(ivm)

        self.default_options.update({
            "boundary" : self.BOUNDARY_TRANS,
            "cmap" : "jet",
            "z_value" : 0,
        })
        self._init_opts()

        self.ivm.sig_current_roi.connect(self._current_roi_changed)
        self.ivm.sig_current_data.connect(self._current_data_changed)
        self.ivm.sig_all_data.connect(self._cleanup_cache)

    def _current_roi_changed(self, roi):
        if roi is not None and self.data is not None:
            self.mask = roi.resample(self.data.grid)
        else:
            self.mask = None
        self.sig_changed.emit(self)

    def _current_data_changed(self, data):
        self.data = data
        self._init_opts()
        self._init_cmap()
        self._current_roi_changed(self.ivm.current_roi)
        self.sig_changed.emit(self)

class RoiView(ImageDataView):
    """
    View of a ROI,

    Stores details about visual parameters, e.g. display style (contour, shaded, etc)
    """

    def __init__(self, ivm):
        super(RoiView, self).__init__(ivm)

        self.default_options.update({
            "shade" : True,
            "contour" : False,
            "alpha" : 150,
            "outline_width" : 3.0,
            "z_value" : 1,
        })
        self._init_opts()
        self.contours = {}

        self.ivm.sig_current_roi.connect(self._current_roi_changed)
        self.ivm.sig_all_rois.connect(self._cleanup_cache)

    def update(self, vb, slice_plane, slice_vol):
        if self.data is not None:
            slicedata, scale, offset = self.data.slice_data(slice_plane)
            transform = QtGui.QTransform(scale[0, 0], scale[0, 1], scale[1, 0], scale[1, 1],
                                         offset[0], offset[1])

            img = self._get_img(vb)
            img.setVisible(self.opts["shade"])
            if img.isVisible():
                lut = get_lut(self.data, self.opts["alpha"])
                roi_levels = [0, len(lut)-1]
                img.setImage(slicedata, lut=lut, autoLevels=False, levels=roi_levels)
                img.setTransform(transform)
                img.setZValue(self.opts["z_value"])
                img.setBoundaryMode(DataView.BOUNDARY_TRANS)

            contours = self._get_contours(vb)
            n_contours = 0
            if self.opts["contour"]:
                # Update data and level for existing contour items, and create new ones if needed
                for val in self.data.regions:
                    pencol = get_pencol(self.data, val)
                    if val != 0:
                        if n_contours == len(contours):
                            contours.append(pg.IsocurveItem())
                            vb.addItem(contours[n_contours])

                        contour = contours[n_contours]
                        contour.setTransform(transform)
                        contour.setData(arr == val)
                        contour.setLevel(1)
                        contour.setPen(pg.mkPen(pencol, width=self.opts["outline_width"]))
                        n_contours += 1

            # Clear data from contours not required - FIXME delete them?
            for idx in range(n_contours, len(contours)):
                contours[idx].setData(None)

    def _get_contours(self, vb):
        if vb.name not in self.contours:
            self.contours[vb.name] = []
        return self.contours[vb.name]

    def _current_roi_changed(self, roi):
        self.data = roi
        self._init_opts()
        self.sig_changed.emit(self)
           