"""
Quantiphyse - Generic analysis processes

Copyright (c) 2013-2018 University of Oxford
"""
import sys

import six
import numpy as np
import scipy

from PySide import QtGui

from quantiphyse.data import NumpyData, OrthoSlice
from quantiphyse.utils import QpException, table_to_extra, sf
from quantiphyse.processes import Process

class CalcVolumesProcess(Process):
    """
    Calculate volume of ROI region or regions
    """

    PROCESS_NAME = "CalcVolumes"

    def __init__(self, ivm, **kwargs):
        Process.__init__(self, ivm, **kwargs)
        self.model = QtGui.QStandardItemModel()

    def run(self, options):
        self.model.clear()
        self.model.setVerticalHeaderItem(0, QtGui.QStandardItem("Num voxels"))
        self.model.setVerticalHeaderItem(1, QtGui.QStandardItem("Volume (mm^3)"))

        roi_name = options.pop('roi', None)
        sel_region = options.pop('region', None)

        if roi_name is None:
            roi = self.ivm.current_roi
        else:
            roi = self.ivm.rois[roi_name]

        if roi is not None:
            sizes = roi.grid.spacing
            counts = np.bincount(roi.raw().flatten().astype(np.int))
            col_idx = 0
            for region, name in roi.regions.items():
                if sel_region is None or region == sel_region:
                    nvoxels = counts[region]
                    vol = counts[region]*sizes[0]*sizes[1]*sizes[2]
                    self.model.setHorizontalHeaderItem(col_idx, QtGui.QStandardItem(name))
                    self.model.setItem(0, col_idx, QtGui.QStandardItem(str(nvoxels)))
                    self.model.setItem(1, col_idx, QtGui.QStandardItem(str(vol)))
                    col_idx += 1

        if not options.pop('no-extras', False):
            output_name = options.pop('output-name', "roi-vols")
            self.ivm.add_extra(output_name, table_to_extra(self.model, output_name))

class DataStatisticsProcess(Process):
    """
    Calculate summary statistics on data
    """
    
    PROCESS_NAME = "DataStatistics"
    
    def __init__(self, ivm, **kwargs):
        Process.__init__(self, ivm, **kwargs)
        self.model = QtGui.QStandardItemModel()

    def run(self, options):
        data_name = options.pop('data', None)
        output_name = options.pop('output-name', None)
        if data_name is None:
            data_items = self.ivm.data.keys()
        elif isinstance(data_name, six.string_types):
            data_items = [data_name,]
            if output_name is None:
                output_name = "%s_stats" % data_name
        else:
            data_items = data_name
        data_items = [self.ivm.data[name] for name in data_items]
        if output_name is None:
            output_name = "stats"

        roi_name = options.pop('roi', None)
        roi = None
        if roi_name is not None:
            roi = self.ivm.rois[roi_name]

        slice_dir = options.pop('slice-dir', None)
        slice_pos = options.pop('slice-pos', 0)
        sl = None
        if slice_dir is not None:
            sl = OrthoSlice(self.ivm.main.grid, slice_dir, slice_pos)
        
        no_extra = options.pop('no-extras', False)
        hist_bins = options.pop('hist-bins', 20)
        hist_range = options.pop('hist-bins', None)
        
        self.model.clear()
        self.model.setVerticalHeaderItem(0, QtGui.QStandardItem("Mean"))
        self.model.setVerticalHeaderItem(1, QtGui.QStandardItem("Median"))
        self.model.setVerticalHeaderItem(2, QtGui.QStandardItem("STD"))
        self.model.setVerticalHeaderItem(3, QtGui.QStandardItem("Min"))
        self.model.setVerticalHeaderItem(4, QtGui.QStandardItem("Max"))

        col = 0
        for data in data_items:
            stats1, roi_labels, _, _ = self.get_summary_stats(data, roi, hist_bins=hist_bins, hist_range=hist_range, slice_loc=sl)
            for ii in range(len(stats1['mean'])):
                self.model.setHorizontalHeaderItem(col, QtGui.QStandardItem("%s\n%s" % (data.name, roi_labels[ii])))
                self.model.setItem(0, col, QtGui.QStandardItem(sf(stats1['mean'][ii])))
                self.model.setItem(1, col, QtGui.QStandardItem(sf(stats1['median'][ii])))
                self.model.setItem(2, col, QtGui.QStandardItem(sf(stats1['std'][ii])))
                self.model.setItem(3, col, QtGui.QStandardItem(sf(stats1['min'][ii])))
                self.model.setItem(4, col, QtGui.QStandardItem(sf(stats1['max'][ii])))
                col += 1

        if not no_extra: 
            self.ivm.add_extra(output_name, table_to_extra(self.model, output_name))

    def get_summary_stats(self, data, roi=None, hist_bins=20, hist_range=None, slice_loc=None):
        """
        Get summary statistics

        :param data: QpData instance for the data to get stats from
        :param roi: Restrict data to within this roi

        :return: Sequence of summary stats dictionary, roi labels
        """
        # Checks if either ROI or data is None
        if roi is not None:
            roi = roi.resample(data.grid)
        else:
            roi = NumpyData(np.ones(data.grid.shape[:3]), data.grid, "temp", roi=True)

        if data is None:
            stat1 = {'mean': [0], 'median': [0], 'std': [0], 'max': [0], 'min': [0]}
            return stat1, list(roi.regions.keys()), np.array([0, 0]), np.array([0, 1])

        stat1 = {'mean': [], 'median': [], 'std': [], 'max': [], 'min': []}
        hist1 = []
        hist1x = []

        if slice_loc is None:
            data_arr = data.raw()
            roi_arr = roi.raw()
        else:
            data_arr, _, _, _ = data.slice_data(slice_loc)
            roi_arr, _, _, _ = roi.slice_data(slice_loc)

        regions = []
        for region, name in roi.regions.items():
            # get data for a single label of the roi
            in_roi = data_arr[roi_arr == region]
            if in_roi.size > 0:
                mean, med, std = np.mean(in_roi), np.median(in_roi), np.std(in_roi)
                mx, mn = np.max(in_roi), np.min(in_roi)
            else:
                mean, med, std, mx, mn = 0, 0, 0, 0, 0

            stat1['mean'].append(mean)
            stat1['median'].append(med)
            stat1['std'].append(std)
            stat1['max'].append(mx)
            stat1['min'].append(mn)
            regions.append(name)

            y, x = np.histogram(in_roi, bins=hist_bins, range=hist_range)
            hist1.append(y)
            hist1x.append(x)

        return stat1, regions, hist1, hist1x

class OverlayStatsProcess(DataStatisticsProcess):
    """
    For backwards compatibility
    """
    PROCESS_NAME = "OverlayStats"
    
class ExecProcess(Process):
    """
    Process which can execute arbitrary Python code
    """
    
    PROCESS_NAME = "Exec"
    
    def __init__(self, ivm, **kwargs):
        Process.__init__(self, ivm, **kwargs)
        self.model = QtGui.QStandardItemModel()

    def run(self, options):
        exec_globals = {'np': np, 'scipy' : scipy, 'ivm': self.ivm}

        # For general Numpy operations we will need a grid to put the
        # results back into. This is specified by the 'grid' option.
        # Note that all data is combined using their raw grids so these
        # must all match if the result is to work - that is the user's job!
        gridfrom = options.pop("grid", None)
        if gridfrom is None:
            grid = self.ivm.main.grid
        else:
            grid = self.ivm.data[gridfrom].grid

        for name, data in self.ivm.data.items():
            exec_globals[name] = data.raw()

        for name in list(options.keys()):
            proc = options.pop(name)
            if name in ("exec", "_"):
                for code in proc:
                    try:
                        exec(code, exec_globals)
                    except:
                        raise QpException("'%s' is not valid Python code (Reason: %s)" % (code, sys.exc_info()[1]))
            else:
                try:
                    result = eval(proc, exec_globals)
                    self.ivm.add(result, grid=grid, name=name)
                except:
                    raise QpException("'%s' did not return valid data (Reason: %s)" % (proc, sys.exc_info()[1]))
