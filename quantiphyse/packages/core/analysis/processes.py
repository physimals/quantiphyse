"""
Quantiphyse - Generic analysis processes

Copyright (c) 2013-2020 University of Oxford

Licensed under the Apache License, Version 2.0 (the "License");
you may not use this file except in compliance with the License.
You may obtain a copy of the License at

    http://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and
limitations under the License.
"""
import sys

import six
import numpy as np
import scipy

from PySide2 import QtGui, QtCore, QtWidgets

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
        roi_names = options.pop('rois', None)

        if roi_name is None and roi_names is None:
            rois = [self.ivm.current_roi.name]
        elif roi_name is not None:
            rois = [roi_name]
        else:
            rois = []

        if roi_names:
            rois = rois + list(roi_names)

        col_idx = 0
        multi_roi = len(rois) > 1
        for roi_name in rois:
            if roi_name not in self.ivm.rois:
                self.warn("ROI not found: %s - ignoring" % roi_name)
                continue
            roi = self.ivm.rois[roi_name]
            sizes = roi.grid.spacing
            counts = np.bincount(roi.raw().flatten().astype(int))
            multi_region = len(roi.regions) > 1
            for region, name in roi.regions.items():
                if multi_roi and multi_region:
                    name = "%s %s" % (roi_name, name)
                elif multi_roi or not multi_region:
                    name = roi_name

                if sel_region is None or region == sel_region:
                    nvoxels = counts[region] if region < len(counts) else 0
                    vol = nvoxels*sizes[0]*sizes[1]*sizes[2]
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
    
    def _sample(self, arr):
        """
        Calculating exact median/quartiles is expensive, so can choose to 
        use a quicker approximation based on a sample
        """
        if not self.exact_median and arr.size > 1e6:
            indices = np.random.randint(0, arr.size, size=[int(1e6),])
            arr = np.take(arr, indices)
        return arr

    def median(self, arr):
        return np.nanmedian(self._sample(arr))

    def skew(self, arr):
        return scipy.stats.skew(arr.flatten(), nan_policy='omit')

    def kurtosis(self, arr):
        return scipy.stats.kurtosis(arr.flatten(), nan_policy='omit')

    def mode(self, arr):
        """
        For FWHM, fit a Gaussian and return peak location of that
        """
        loc, _scale = scipy.stats.norm.fit(arr)
        return loc

    def n(self, arr):
        return np.count_nonzero(~np.isnan(arr))

    def lq(self, arr):
        return np.nanquantile(self._sample(arr), 0.25)

    def uq(self, arr):
        return np.nanquantile(self._sample(arr), 0.75)

    def iqr(self, arr):
        uq, lq = np.nanquantile(self._sample(arr), [0.75, 0.25])
        return uq-lq

    def iqn(self, arr):
        uq, lq = np.nanquantile(self._sample(arr), [0.75, 0.25])   
        arr = arr[arr < uq]
        arr = arr[arr > lq]
        return np.count_nonzero(~np.isnan(arr))

    def iqmean(self, arr):
        uq, lq = np.nanquantile(self._sample(arr), [0.75, 0.25])   
        arr = arr[arr < uq]
        arr = arr[arr > lq]
        return np.nanmean(arr)

    def fwhm(self, arr):
        """
        For FWHM, fit a Gaussian and return fwhm of that
        """
        _loc, scale = scipy.stats.norm.fit(arr)
        return 2.355*scale

    def __init__(self, ivm, **kwargs):
        Process.__init__(self, ivm, **kwargs)
        self.model = QtGui.QStandardItemModel()
        
        self.STAT_IMPLS = {
            "mean" : np.nanmean,
            "std" : np.nanstd,
            "median" : self.median,
            "min" : np.nanmin,
            "max" : np.nanmax,
            "lq" : self.lq,
            "uq" : self.uq,
            "iqr" : self.iqr,
            "mode" : self.mode,
            "fwhm" : self.fwhm,
            "skewness" : self.skew,
            "kurtosis" : self.kurtosis,
            "iqmean" : self.iqmean,
            "n" : self.n,
            "iqn" : self.iqn,
        }

        self.STAT_NAMES = {
            "lq" : "Lower quartile",
            "uq" : "Upper quartile",
            "iqr" : "IQR",
            "iqmean" : "Interquartile mean",
            "iqn" : "Interquartile N",
            "mode" : "Mode estimate",
            "fwhm" : "FWHM estimate",
        }

        self.DEFAULT_STATS = ["mean", "median", "std", "min", "max"]

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

        qpdata_items = []
        for name in data_items:
            if name in self.ivm.data:
                qpdata_items.append(self.ivm.data[name])
            else:
                self.warn("Data item not found: %s - ignoring" % name)

        data_limits_dict = options.pop("data-limits", {})

        if output_name is None:
            output_name = "stats"

        stats = options.pop("stats", self.DEFAULT_STATS)
        if stats == "all":
            stats = list(self.STAT_IMPLS.keys())
        if not isinstance(stats, list):
            stats = [stats]
        for s in list(stats):
            if s not in self.STAT_IMPLS:
                self.warn("Unknown statistic: %s - ignoring" % s)
                stats.remove(s)

        roi_name = options.pop('roi', None)
        roi = None
        if roi_name is not None:
            roi = self.ivm.rois[roi_name]

        slice_dir = options.pop('slice-dir', None)
        slice_pos = options.pop('slice-pos', 0)
        sl = None
        if slice_dir is not None:
            sl = OrthoSlice(self.ivm.main.grid, slice_dir, slice_pos)

        vol = options.pop('vol', None)
        no_extra = options.pop('no-extras', False)
        self.exact_median = options.pop('exact-median', False)

        self.model.clear()
        for idx, s in enumerate(stats):
            stat_name = self.STAT_NAMES.get(s, s.capitalize())
            self.model.setVerticalHeaderItem(idx, QtGui.QStandardItem(stat_name))

        col = 0
        for data in qpdata_items:
            data_limits = data_limits_dict.get(data.name, (None, None))
            if not isinstance(data_limits, (list, tuple)) or len(data_limits) != 2:
                self.warn("Invalid data limits: %s - ignoring", data_limits)
                data_limits = (None, None)
            data_stats, roi_labels = self._get_summary_stats(data, stats, roi, data_limits, slice_loc=sl, vol=vol)
            for region_idx, label in enumerate(roi_labels):
                self.model.setHorizontalHeaderItem(col, QtGui.QStandardItem("%s %s" % (data.name, label)))
                for stat_idx, s in enumerate(stats):
                    self.model.setItem(stat_idx, col, QtGui.QStandardItem(sf(data_stats[s][region_idx])))    
                col += 1

        if not no_extra: 
            self.ivm.add_extra(output_name, table_to_extra(self.model, output_name))

    def _get_summary_stats(self, data, stats, roi=None, data_limits=(None, None), slice_loc=None, vol=None):
        """
        Get summary statistics

        :param data: QpData instance for the data to get stats from
        :param stats: List of names of statistics to extract - must be in STATS_IMPLS!
        :param roi: Restrict data to within this roi
        :param data_limits: If specified, min/max values of data to be considered for stats
        :param slice_loc: Restrict data to this OrthoSlice
        :param vol: Restrict data to this volume index
        :param exact_median: Use an exact median calculation rather than a faster approximation

        :return: Tuple of summary stats dictionary, roi labels
        """
        data_stats = {}
        for s in stats:
            data_stats[s] = []

        if roi is None:
            roi_labels = [""]
        else:
            roi_labels = list(roi.regions.values())
            # Special case to avoid ugly suffix when we just
            # have a single-region mask with no custom label
            if roi_labels == ["Region 1"]:
                roi_labels = [""]

        if vol is not None:
            if vol < data.nvols:
                data = data.volume(vol, qpdata=True)
            else:
                # Will cause zeros to be returned
                data = None

        if data is None:
            for s in stats:
                data_stats[s] = [0] * len(roi_labels)
            return data_stats, roi_labels

        # FIXME does this work with data defined on different grids?
        if slice_loc is None:
            data_arr = data.raw()
        else:
            data_arr, _, _, _ = data.slice_data(slice_loc)

        # Separate ROI and non-ROI cases to avoid making additional array copy
        # when there is no ROI
        if roi is not None:
            roi_arr = roi.resample(data.grid).raw()
            if slice_loc is not None:
                roi_arr, _, _, _ = roi.slice_data(slice_loc)

            for region in roi.regions:
                region_data = data_arr[roi_arr == region]
                for s in stats:
                    if region_data.size > 0:
                        stats_data = self._restrict_data(region_data, data_limits)
                        value = self.STAT_IMPLS[s](stats_data)
                        data_stats[s].append(value)
                    else:
                        data_stats[s].append(0)
        else:
            for s in stats:
                stats_data = self._restrict_data(data_arr, data_limits)
                value = self.STAT_IMPLS[s](stats_data)
                data_stats[s].append(value)

        return data_stats, roi_labels

    def _restrict_data(self, data, data_limits):
        dmin, dmax = data_limits
        if dmin is not None:
            data = data[data >= dmin]
        if dmax is not None:
            data = data[data <= dmax]
        return data

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
        is_roi = options.pop("output-is-roi", False)

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
                    self.ivm.add(result, grid=grid, name=name, roi=is_roi)
                except:
                    raise QpException("'%s' did not return valid data (Reason: %s)" % (proc, sys.exc_info()[1]))
