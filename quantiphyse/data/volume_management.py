"""
Quantiphyse - Data management framework

Copyright (c) 2013-2018 University of Oxford
"""

from __future__ import division

import logging
import keyword
import re

from PySide import QtCore

import numpy as np

from quantiphyse.utils import QpException

from .qpdata import QpData
from .load_save import NumpyData
from .extras import Extra

LOG = logging.getLogger(__name__)

class ImageVolumeManagement(QtCore.QObject):
    """
    Holds all image datas used in analysis

    Has to inherit from a Qt base class that supports signals

    Attributes
    ----------

      ``main`` 'main' QpData - typically viewed as a greyscale background
      ``data`` Mapping from data set name to QpData object
      ``current_data`` QpData which is the 'current' overlay data set
      ``current_roi`` QpData with ``roi=True`` used as the current ROI
      ``extras`` Mapping from name to object for miscellaneous extra data.
                 Extras must support string-conversion for writing to files.
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

    # Change to set of extras (e.g. new one added)
    sig_extras = QtCore.Signal(list)

    def __init__(self):
        super(ImageVolumeManagement, self).__init__()
        self.reset()

    def reset(self):
        """ Clear all data """
        self.main = None
        self.data = {}
        self.current_data = None
        self.current_roi = None
        self.extras = {}

        self.sig_main_data.emit(None)
        self.sig_current_data.emit(None)
        self.sig_current_roi.emit(None)
        self.sig_all_data.emit([])

    @property
    def rois(self):
        """
        :return: Dictionary of name : QpData for all data items which can be used as ROIs
        """
        return dict([(data.name, data) for data in self.data.values() if data.roi])

    def suggest_name(self, name, ensure_unique=True):
        """
        Suggest a name for new data that is suitable for use as a Python variable.
        If required, ensure name does not clash with existing names
        """
        # Remove invalid characters and make sure there's something left
        name = re.sub('[^0-9a-zA-Z_]', '', name)
        if not name: name = "data"

        # Add underscore if it's a keyword or starts with a digit
        if name[0] in ('0', '1', '2', '3', '4', '5', '6', '7', '8', '9') or keyword.iskeyword(name):
            name = "_" + name

        # Make it unique
        num = 1
        test_name = name
        while 1:
            if not ensure_unique or (test_name not in self.data):
                break
            num += 1
            test_name = "%s_%i" % (name, num)
        return test_name

    def _valid_name(self, name):
        if name is None or not re.match(r'[a-z_]\w*$', name, re.I) or keyword.iskeyword(name):
            raise QpException("'%s' is not a valid name" % name)

    def set_main_data(self, name):
        """
        Set the named data item as the main data

        :param name: Name of main data. Must be name of data item in IVM
        """
        self._data_exists(name)
        self.main = self.data[name]
        self.sig_main_data.emit(self.main)

    def add(self, data, name=None, grid=None, make_current=None, make_main=None, roi=None):
        """
        Add data item to IVM

        Data will be made the main data if make_main is True, or there is no main data
        
        Data will be made current if make_current is not specified and there is no
        current data, and make_main is not True

        :param data: Numpy array of QpData instance
        :param name: Name which must be a valid name not already used in this IVM
        :param grid: If data is a Numpy array, a DataGrid instance defining the orientation
        :param make_current: If True, make this the current data item
        :param make_main: If True, make this the main data.
        :param roi: If providing Numpy array, optionally specifies whether the data is an ROI or not
        """
        if isinstance(data, np.ndarray):
            if grid is None or name is None:
                raise RuntimeError("add: Numpy data must have a name and a grid")
            data = NumpyData(data, grid, name, roi=roi)       
        elif not isinstance(data, QpData):
            raise QpException("add: data must be Numpy array or QpData")

        if name is not None:
            data.name = name

        self._valid_name(data.name)
        
        # If replacing existing data, delete the old one first
        if data.name in self.data:
            self.delete(data.name)
            
        self.data[data.name] = data

        # Make main data if requested or if not specified and there is no current main data
        if make_main is None:
            make_main = self.main is None

        if make_main:
            self.set_main_data(data.name)

        # Emit the 'data changed' signal
        self.sig_all_data.emit(list(self.data.keys()))

        # Make current if requested, or if not specified and it is the first non-main data/ROI
        if make_current is None:
            make_current = ((data.roi and self.current_roi is None) or (not data.roi and self.current_data is None)) and not make_main
        if make_current:
            if data.roi:
                self.set_current_roi(data.name)
            else:
                self.set_current_data(data.name)

    def _data_exists(self, name):
        if name not in self.data:
            raise RuntimeError("Data '%s' does not exist" % name)

    def _roi_exists(self, name):
        if name not in self.rois:
            raise RuntimeError("ROI '%s' does not exist" % name)

    def is_main_data(self, qpd):
        """
        :param qpd: QpData instance
        :return: True if qpd is the main data
        """
        return self.main is not None and qpd is not None and self.main.name == qpd.name

    def is_current_data(self, qpd):
        """
        :param qpd: QpData instance
        :return: True if qpd is the current data
        """
        return self.current_data is not None and qpd is not None and self.current_data.name == qpd.name

    def is_current_roi(self, roi):
        """
        :param qpd: QpData instance
        :return: True if qpd is the current ROI
        """
        return self.current_roi is not None and roi is not None and self.current_roi.name == roi.name
        
    def set_current_data(self, name):
        """
        Set a named data item as the current data

        :param name: Name of data item which must exist within the IVM
        """
        if name is not None:
            self._data_exists(name)
            self.current_data = self.data[name]
        else:
            self.current_data = None
        self.sig_current_data.emit(self.current_data)

    def set_current(self, name):
        """
        Set a named data item as current (ROI or data as required)
        """
        if name is not None:
            self._data_exists(name)
            if self.data[name].roi:
                self.set_current_roi(name)
            else:
                self.set_current_data(name)
        else:
            self.set_current_data(None)
            self.set_current_roi(None)

    def rename(self, name, newname):
        """
        Rename a data item

        :param name: Name of data item which must exist within the IVM
        :param newname: New name for this data item
        """
        self._data_exists(name)
        qpd = self.data[name]
        qpd.name = newname
        self.data[newname] = qpd
        del self.data[name]
        self.sig_all_data.emit(list(self.data.keys()))

    def delete(self, name):
        """
        Delete a data item

        :param name: Name of data item which must exist within the IVM
        """
        self._data_exists(name)
        del self.data[name]
        if self.current_data is not None and self.current_data.name == name:
            self.current_data = None
            self.sig_current_data.emit(None)
        if self.main is not None and self.main.name == name:
            self.main = None
            self.sig_main_data.emit(None)
        self.sig_all_data.emit(list(self.data.keys()))

    def set_current_roi(self, name):
        """
        Set a named ROI as the current ROI

        :param name: Name of ROI which must exist within the IVM
        """
        if name is not None:
            self._roi_exists(name)
            self.current_roi = self.rois[name]
        else:
            self.current_roi = None
        self.sig_current_roi.emit(self.current_roi)

    def add_extra(self, name, obj):
        """
        Add an 'extra', which can be any result of a process which
        is not voxel data, e.g. a number, table, etc.

        Extras are required to support str() conversion so they
        can be written to a file

        :param name: Name to give the extra. If an extra already exists with this name
                     it will be overwritten
        :param obj: instance of Extra which should support str() conversion
        """
        if not isinstance(obj, Extra):
            raise ValueError("extra object must be subclasses of Extra")
        self.extras[name] = obj
        self.sig_extras.emit(self.extras.values())

    def values(self, pos, grid=None):
        """
        Get all the 3D data values at the current position

        :param pos: Position as a 3D or 4D vector. If 4D last value is the volume index
                    (0 for 3D). If ``grid`` not specified, position is in world space
        :param grid: If specified, interpret position in this ``DataGrid`` co-ordinate space.
        :return: Dictionary of data name : value
        """
        values = {}

        # loop over all loaded data and save values in a dictionary
        for name, qpd in self.data.items():
            if qpd.nvols == 1:
                values[name] = qpd.value(pos, grid)
                
        return values

    def timeseries(self, pos, grid=None):
        """
        Return time/volume series curves for all 4D data items
       
        :param pos: Position as a 3D or 4D vector. If 4D last value is the volume index
                    (0 for 3D). If ``grid`` not specified, position is in world space
        :param grid: If specified, interpret position in this ``DataGrid`` co-ordinate space.
        :return: Dictionary of data name : sequence of values
        """
        timeseries = {}
        for qpd in self.data.values():
            if qpd.nvols > 1:
                timeseries[qpd.name] = qpd.timeseries(pos, grid)
                
        return timeseries
