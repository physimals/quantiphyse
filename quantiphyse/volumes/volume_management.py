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
import keyword
import re

from PySide import QtCore, QtGui

import numpy as np

from . import QpData

class ImageVolumeManagement(QtCore.QObject):
    """
    ImageVolumeManagement
    1) Holds all image datas used in analysis
    2) Better support for switching volumes instead of having a single volume hardcoded

    Has to inherit from a Qt base class that supports signals
    Note that the correct QT Model/View structure has not been set up but is intended in future
    """
    # Signals

    # Change to main data
    sig_main_data = QtCore.Signal(object)

    # Change to current data
    sig_current_data = QtCore.Signal(object)

    # Change to set of data (e.g. new one added)
    sig_all_data = QtCore.Signal(list)

    # Change to current ROI
    sig_current_roi = QtCore.Signal(object)

    # Change to set of ROIs (e.g. new one added)
    sig_all_rois = QtCore.Signal(list)

    def __init__(self):
        super(ImageVolumeManagement, self).__init__()
        self.reset()

    def reset(self):
        """
        Reset to empty, signalling any connected widgets
        """
        # Main background data
        self.main = None

        # One True Grid
        self.grid = None

        # Map from name to data object
        self.data = {}

        # Current data object
        self.current_data = None

        # Map from name to ROI object
        self.rois = {}

        # Current ROI object
        self.current_roi = None

        # Processing artifacts
        self.artifacts = {}

        # Current position of the cross hair as an array
        # FIXME move to view?
        self.cim_pos = np.array([0, 0, 0, 0], dtype=np.int)

        self.sig_main_data.emit(None)
        self.sig_current_data.emit(None)
        self.sig_current_roi.emit(None)
        self.sig_all_rois.emit([])
        self.sig_all_data.emit([])

    def suggest_name(self, name):
        """
        Suggest a name for new data that does not clash with existing names and is
        suitable for use as a Python variable.
        """
        # Remove invalid characters
        name = re.sub('[^0-9a-zA-Z_]', '', name)

        # Remove leading characters until we find a letter or underscore
        name = re.sub('^[^a-zA-Z_]+', '', name)

        # Add underscore if it's a keyword
        if keyword.iskeyword(name):
            name += "_"

        # Make it unique
        n = 1
        while 1:
            if name not in self.data and name not in self.rois:
                break
            n += 1
            name = "%s_%i" % (name, n)
        return name

    def _valid_name(self, name):
        if not re.match(r'[a-z_]\w*$', name, re.I) or keyword.iskeyword(name):
            raise RuntimeError("'%s' is not a valid name" % name)

    def set_main_data(self, name):
        self._data_exists(name)
        
        self.main = self.data[name]
        self.grid = self.main.rawgrid.reorient_ras()
        print("Main data raw grid")
        print(self.main.rawgrid.affine)
        print("RAS aligned")
        print(self.grid.affine)

        self.main.regrid(self.grid)
        
        self.cim_pos = [int(d/2) for d in self.grid.shape]
        if self.main.ndim == 4:
            self.cim_pos.append(int(self.main.nvols/2))
        else:
            self.cim_pos.append(0)
        self.sig_main_data.emit(self.main)

    def add_qpdata(self, qpdata, make_current=False, make_main=False):
        self._valid_name(qpdata.name)
        self.data[qpdata.name] = qpdata
        
        # Make main data if requested, or if the first data, or if the first 4d data
        # If not, regrid it onto the current OTG
        make_main = make_main or self.main is None or (qpdata.ndim == 4 and self.main.ndim == 3)
        if make_main:
            self.set_main_data(qpdata.name)
        else:
            qpdata.regrid(self.grid)

        if make_current:
            self.set_current_data(qpdata.name)
        self.sig_all_data.emit(self.data.keys())

    def add_npdata(self, name, npdata, make_current=False, make_main=False):
        qpdata = QpData(name, npdata, self.grid)
        self.add_qpdata(qpdata, make_current, make_main)

    def add_qproi(self, qproi, make_current=False, signal=True):
        self._valid_name(qproi.name)
        self.rois[qproi.name] = qproi

        if self.grid is not None:
            # FIXME regridding ROIs needs some thought!
            qproi.regrid(self.grid)

        if make_current:
            self.set_current_roi(qpdata.name)
            
        self.sig_all_rois.emit(self.rois.keys())

    def add_nproi(self, name, nproi, make_current=False, make_main=False):
        qproi = QpRoi(name, nproi, self.grid)
        self.add_qproi(qproi, make_current, make_main)

    def _data_exists(self, name, invert=False):
        if name not in self.data:
            raise RuntimeError("data %s does not exist" % name)

    def _roi_exists(self, name):
        if name not in self.rois:
            raise RuntimeError("ROI %s does not exist" % name)

    def is_main_data(self, qpd):
        return self.main is not None and qpd is not None and self.main.name == qpd.name

    def is_current_data(self, qpd):
        return self.current_data is not None and qpd is not None and self.current_data.name == qpd.name

    def is_current_roi(self, roi):
        return self.current_roi is not None and roi is not None and self.current_roi.name == roi.name
        
    def set_current_data(self, name):
        self._data_exists(name)
        self.current_data = self.data[name]
        self.sig_current_data.emit(self.current_data)

    def rename_data(self, name, newname):
        self._data_exists(name)
        qpd = self.data[name]
        qpd.name = newname
        self.data[newname] = qpd
        del self.data[name]
        self.sig_all_data.emit(self.data.keys())

    def rename_roi(self, name, newname):
        self._roi_exists(name)
        roi = self.rois[name]
        roi.name = newname
        self.rois[newname] = roi
        del self.rois[name]
        self.sig_all_rois.emit(self.rois.keys())

    def delete_data(self, name):
        self._data_exists(name)
        del self.data[name]
        if self.current_data is not None and self.current_data.name == name:
            self.current_data = None
            self.sig_current_data.emit(None)
        if self.main is not None and self.main.name == name:
            self.main = None
            self.sig_main_data.emit(None)
        self.sig_all_data.emit(self.data.keys())

    def delete_roi(self, name, signal=True):
        self._roi_exists(name)
        del self.rois[name]
        if self.current_roi.name == name:
            self.current_roi = None
            self.sig_current_roi.emit(None)
        self.sig_all_rois.emit(self.rois.keys())

    def set_current_roi(self, name, signal=True):
        self._roi_exists(name)
        self.current_roi = self.rois[name]
        self.sig_current_roi.emit(self.current_roi)

    def get_data_value_curr_pos(self):
        """
        Get all the 3D data values at the current position
        """
        data_value = {}

        # loop over all loaded data and save values in a dictionary
        for name, qpd in self.data.items():
            if qpd.ndim == 3:
                data_value[name] = qpd[self.cim_pos[0], self.cim_pos[1], self.cim_pos[2]]

        return data_value

    def get_current_enhancement(self):
        """
        Return enhancement curves for all 4D data whose 4th dimension matches that of the main data
        """
        if self.main is None: return [], {}
        if self.main.ndim == 4:
            main_sig = self.main[self.cim_pos[0], self.cim_pos[1], self.cim_pos[2], :]
        else:
            main_sig = []

        qpd_sig = {}
        for qpd in self.data.values():
            if qpd.ndim == 4 and (qpd.nvols == self.main.nvols):
                qpd_sig[qpd.name] = qpd[self.cim_pos[0], self.cim_pos[1], self.cim_pos[2], :]

        return main_sig, qpd_sig

    def add_artifact(self, name, obj):
        """
        Add an 'artifact', which can be any result of a process which
        is not voxel data, e.g. a number, table, etc.

        Artifacts are only required to support str() conversion so they
        can be written to a file
        """
        self.artifacts[name] = obj
