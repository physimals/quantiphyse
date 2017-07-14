"""

Author: Benjamin Irving (benjamin.irv@gmail.com)
Copyright (c) 2013-2015 University of Oxford, Benjamin Irving

- Data management framework

"""

from __future__ import division, print_function

import sys
import os
import math
import warnings
import glob

from PySide import QtCore, QtGui
from matplotlib import cm

import numpy as np

from .io import QpVolume, FileMetadata

class ImageVolumeManagement(QtCore.QAbstractItemModel):
    """
    ImageVolumeManagement
    1) Holds all image volumes used in analysis
    2) Better support for switching volumes instead of having a single volume hardcoded

    Has to inherit from a Qt base class that supports signals
    Note that the correct QT Model/View structure has not been set up but is intended in future
    """
    # Signals

    # Change to main volume
    sig_main_volume = QtCore.Signal(QpVolume)

    # Change to current overlay
    sig_current_overlay = QtCore.Signal(QpVolume)

    # Change to set of overlays (e.g. new one added)
    sig_all_overlays = QtCore.Signal(list)

    # Change to current ROI
    sig_current_roi = QtCore.Signal(QpVolume)

    # Change to set of ROIs (e.g. new one added)
    sig_all_rois = QtCore.Signal(list)

    def __init__(self):
        super(ImageVolumeManagement, self).__init__()
        self.reset()

    def reset(self):
        """
        Reset to empty, signalling any connected widgets
        """
        # Main background image
        self.vol = None

        self.voxel_sizes = [1.0, 1.0, 1.0]
        self.shape = []

        # Map from name to overlay object
        self.overlays = {}

        # Current overlay object
        self.current_overlay = None

        # Map from name to ROI object
        self.rois = {}

        # Processing artifacts
        self.artifacts = {}

        # Current ROI object
        self.current_roi = None

        # Current position of the cross hair as an array
        self.cim_pos = np.array([0, 0, 0, 0], dtype=np.int)

        self.sig_main_volume.emit(self.vol)
        self.sig_current_overlay.emit(self.current_overlay)
        self.sig_current_roi.emit(self.current_roi)
        self.sig_all_rois.emit(self.rois.keys())
        self.sig_all_overlays.emit(self.overlays.keys())

    def check_shape(self, shape):
        ndim = min(len(self.shape), len(shape))
        return list(self.shape[:ndim]) == list(shape[:ndim])

    def update_shape(self, shape):
        if not self.check_shape(shape):
            raise RuntimeError("Dimensions don't match - %s vs %s" % (self.shape, shape))

        for d in range(len(self.shape), min(len(shape), 4)):
            self.shape.append(shape[d])

    def set_main_volume(self, name):
        self._overlay_exists(name)
        
        self.vol = self.overlays[name]
        self.voxel_sizes = list(self.vol.md.voxel_sizes_ras)
        while (len(self.voxel_sizes) < 3):
            self.voxel_sizes.append(1)
        self.update_shape(self.vol.shape)

        self.cim_pos = [int(d/2) for d in self.shape]
        if self.vol.ndim == 3: self.cim_pos.append(0)
        self.sig_main_volume.emit(self.vol)

    def add_overlay(self, name, ov, make_current=False, make_main=False, signal=True):
        ov = ov.view(QpVolume)
        ov.set_as_data(name)
        if ov.md is None:
            ov.md = FileMetadata(name, shape=ov.shape, affine=self.vol.md.affine, voxel_sizes=self.voxel_sizes)
        
        self.update_shape(ov.shape)
        self.overlays[name] = ov
        
        # Make main volume if requested, or if the first volume, or if the first 4d volume
        # If not the main volume, set as current overlay if requested
        make_main = make_main or self.vol is None or (ov.ndim == 4 and self.vol.ndim == 3)
        if make_main:
            self.set_main_volume(name)
        elif make_current:
            self.set_current_overlay(name, signal)

        if signal:
            self.sig_all_overlays.emit(self.overlays.keys())

    def add_roi(self, name, roi, make_current=False, signal=True):
        roi = roi.astype(np.int32).view(QpVolume)
        roi.set_as_roi(name)
        if roi.md is None:
            roi.md = FileMetadata(name, shape=roi.shape, affine=self.vol.md.affine, voxel_sizes=self.voxel_sizes)

        if roi.range[0] < 0 or roi.range[1] > 2**32:
            raise RuntimeError("ROI must contain values between 0 and 2**32")

        if not np.equal(np.mod(roi, 1), 0).any():
           raise RuntimeError("ROI contains non-integer values.")

        self.update_shape(roi.shape)
        self.rois[name] = roi

        if signal:
            self.sig_all_rois.emit(self.rois.keys())
        if make_current:
            self.set_current_roi(name, signal)

    def _overlay_exists(self, name, invert=False):
        if name not in self.overlays:
            raise RuntimeError("Overlay %s does not exist" % name)

    def _roi_exists(self, name):
        if name not in self.rois:
            raise RuntimeError("ROI %s does not exist" % name)

    def is_main_volume(self, ovl):
        return self.vol is not None and ovl is not None and self.vol.name == ovl.name

    def is_current_overlay(self, ovl):
        return self.current_overlay is not None and ovl is not None and self.current_overlay.name == ovl.name

    def is_current_roi(self, roi):
        return self.current_roi is not None and roi is not None and self.current_roi.name == roi.name
        
    def set_current_overlay(self, name, signal=True):
        self._overlay_exists(name)
        self.current_overlay = self.overlays[name]
        if signal: self.sig_current_overlay.emit(self.current_overlay)

    def rename_overlay(self, name, newname, signal=True):
        self._overlay_exists(name)
        ovl = self.overlays[name]
        ovl.name = newname
        self.overlays[newname] = ovl
        del self.overlays[name]
        if signal: self.sig_all_overlays.emit(self.overlays.keys())

    def rename_roi(self, name, newname, signal=True):
        self._roi_exists(name)
        roi = self.rois[name]
        roi.name = newname
        self.rois[newname] = roi
        del self.rois[name]
        if signal: self.sig_all_rois.emit(self.rois.keys())

    def delete_overlay(self, name, signal=True):
        self._overlay_exists(name)
        del self.overlays[name]
        if self.current_overlay is not None and self.current_overlay.name == name:
            self.current_overlay = None
            if signal: self.sig_current_overlay.emit(None)
        if self.vol is not None and self.vol.name == name:
            self.vol = None
            if signal: self.sig_main_volume.emit(None)
        if signal: self.sig_all_overlays.emit(self.overlays.keys())

    def delete_roi(self, name, signal=True):
        self._roi_exists(name)
        del self.rois[name]
        if self.current_roi.name == name:
            self.current_roi = None
            if signal: self.sig_current_roi.emit(None)
        if signal: self.sig_all_rois.emit(self.rois.keys())

    def set_current_roi(self, name, signal=True):
        self._roi_exists(name)
        self.current_roi = self.rois[name]
        if signal:
            self.sig_current_roi.emit(self.current_roi)

    def get_overlay_value_curr_pos(self):
        """
        Get all the overlay values at the current position
        """
        overlay_value = {}

        # loop over all loaded overlays and save values in a dictionary
        for name, ovl in self.overlays.items():
            if ovl.ndim == 3:
                overlay_value[name] = ovl[self.cim_pos[0], self.cim_pos[1], self.cim_pos[2]]

        return overlay_value

    def get_current_enhancement(self):
        """
        Return enhancement curves for all 4D overlays whose 4th dimension matches that of the main volume
        """
        if self.vol is None: return [], {}
        if self.vol.ndim == 4:
            main_sig = self.vol[self.cim_pos[0], self.cim_pos[1], self.cim_pos[2], :]
        else:
            main_sig = []

        ovl_sig = {}
        for ovl in self.overlays.values():
            if ovl.ndim == 4 and (ovl.shape[3] == self.vol.shape[3]):
                ovl_sig[ovl.name] = ovl[self.cim_pos[0], self.cim_pos[1], self.cim_pos[2], :]

        return main_sig, ovl_sig

    def add_artifact(self, name, obj):
        """
        Add an 'artifact', which can be any result of a process which
        is not voxel data, e.g. a number, table, etc.

        Artifacts are only required to support str() conversion so they
        can be written to a file
        """
        self.artifacts[name] = obj
