"""
Quantiphyse - Generic analysis processes

Copyright (c) 2013-2018 University of Oxford
"""

import numpy as np
import scipy
import sys

from PySide import QtGui

from quantiphyse.data import NumpyData, OrthoSlice
from quantiphyse.utils import QpException, table_to_str, debug, sf
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
            counts = np.bincount(roi.raw().flatten())
            for idx, region in enumerate(roi.regions()):
                if sel_region is None or region == sel_region:
                    nvoxels = counts[region]
                    vol = counts[region]*sizes[0]*sizes[1]*sizes[2]
                    self.model.setHorizontalHeaderItem(idx, QtGui.QStandardItem("Region %i" % region))
                    self.model.setItem(0, idx, QtGui.QStandardItem(str(nvoxels)))
                    self.model.setItem(1, idx, QtGui.QStandardItem(str(vol)))

        if not options.pop('no-extras', False):
            output_name = options.pop('output-name', "roi-vols")
            self.ivm.add_extra(output_name, table_to_str(self.model))


class HistogramProcess(Process):
    """
    Calculate histogram for a data set 
    """
    
    PROCESS_NAME = "Histogram"
    
    def __init__(self, ivm, **kwargs):
        Process.__init__(self, ivm, **kwargs)
        self.model = QtGui.QStandardItemModel()

    def run(self, options):
        data_name = options.pop('data', None)
        if data_name is None:
            data_items = self.ivm.data.values()
            grid = self.ivm.main.grid
        else:
            data_items = [self.ivm.data[data_name]]
            grid = data_items[0].grid

        if len(data_items) == 0:
            raise QpException("No data to calculate histogram")
        
        roi = self.get_roi(options, grid)
        roi_labels = roi.regions()
        
        sel_region = options.pop('region', None)
        dmin = options.pop('min', None)
        dmax = options.pop('max', None)
        bins = options.pop('bins', 20)
        output_name = options.pop('output-name', "histogram")

        self.model.setHorizontalHeaderItem(0, QtGui.QStandardItem("x0"))
        self.model.setHorizontalHeaderItem(1, QtGui.QStandardItem("x1"))  
        self.xvals, self.edges, self.hist = None, None, {}
        col = 2
        
        for data in data_items:
            hrange = [dmin, dmax]
            if dmin is None: hrange[0] = np.min(data.raw())
            if dmax is None: hrange[1] = np.max(data.raw())
            for region in roi_labels:
                debug("Doing %s region %i" % (data.name, region))
                if sel_region is not None and region != sel_region:
                    debug("Ignoring this region")
                    continue
                roi_fordata = roi.resample(data.grid).raw()
                region_data = data.raw()[roi_fordata == region]
                yvals, edges = np.histogram(region_data, bins=bins, range=hrange)
                if self.xvals is None:
                    self.edges = edges
                    self.xvals = [(edges[i] + edges[i+1])/2 for i in range(len(edges)-1)]
                    for idx in range(len(edges)-1):
                        self.model.setVerticalHeaderItem(idx, QtGui.QStandardItem(""))
                        self.model.setItem(idx, 0, QtGui.QStandardItem(str(self.edges[idx])))
                        self.model.setItem(idx, 1, QtGui.QStandardItem(str(self.edges[idx+1])))
                self.model.setHorizontalHeaderItem(col, QtGui.QStandardItem("%s\nRegion %i" % (data.name, region)))
                for idx, v in enumerate(yvals):
                    self.model.setItem(idx, col, QtGui.QStandardItem(str(v)))
                if data.name not in self.hist: self.hist[data.name] = {}
                self.hist[data.name][region] = yvals
                col += 1

        if not options.pop('no-extras', False): 
            debug("Adding %s" % output_name)
            self.ivm.add_extra(output_name, table_to_str(self.model))

class RadialProfileProcess(Process):
    """
    Calculate radial profile for a data set
    """
    
    PROCESS_NAME = "RadialProfile"
    
    def __init__(self, ivm, **kwargs):
        Process.__init__(self, ivm, **kwargs)
        self.model = QtGui.QStandardItemModel()

    def run(self, options):
        data_name = options.pop('data', None)
        if data_name is None:
            data_items = self.ivm.data.values()
            grid = self.ivm.main.grid
        else:
            data_items = [self.ivm.data[data_name]]
            grid = data_items[0].grid

        if len(data_items) == 0:
            raise QpException("No data to calculate radial profile")
        
        roi = self.get_roi(options, grid).raw()
        
        #roi_region = options.pop('region', None)
        centre = options.pop('centre')
        if isinstance(centre, basestring):
            centre = [float(v) for v in centre.split(",")]
        vol = 0
        if len(centre) == 4:
            vol = centre[3]
        
        output_name = options.pop('output-name', "radial-profile")
        no_extra = options.pop('no-extras', False)
        bins = options.pop('bins', 20)

        self.model.clear()
        self.rp = {}
        
        voxel_sizes = grid.spacing

        # Generate an array whose entries are integer values of the distance
        # from the centre. Set masked values to distance of -1
        x, y, z = np.indices(grid.shape)
        r = np.sqrt((voxel_sizes[0]*(x - centre[0]))**2 + (voxel_sizes[1]*(y - centre[1]))**2 + (voxel_sizes[2]*(z - centre[2]))**2)
        r[roi==0] = -1
        rmin = r[roi>0].min()

        # Generate histogram of number of voxels in each bin
        # Use the range parameter to ignore masked values with negative distances
        voxels_per_bin, self.edges = np.histogram(r, bins=bins, range=(rmin, r.max()))

        # Prevent divide by zero, if there are no voxels in a bin, this is OK because
        # there will be no data either
        voxels_per_bin[voxels_per_bin==0] = 1
        self.xvals = [(self.edges[i] + self.edges[i+1])/2 for i in range(len(self.edges)-1)]

        for idx, xval in enumerate(self.xvals):
            self.model.setVerticalHeaderItem(idx, QtGui.QStandardItem(str(xval)))

        for col, data in enumerate(data_items):
            self.model.setHorizontalHeaderItem(col, QtGui.QStandardItem("%s" % data.name))
                
            weights = data.resample(grid).volume(vol)

            # Generate histogram by distance, weighted by data
            rpd, junk = np.histogram(r, weights=weights, bins=bins, range=(rmin, r.max()))

            # Divide by number of voxels in each bin to get average value by distance.
            rp = rpd / voxels_per_bin
            for idx, v in enumerate(rp):
                self.model.setItem(idx, col, QtGui.QStandardItem(str(v)))
            self.rp[data.name] = rp

        if not no_extra: 
            self.ivm.add_extra(output_name, table_to_str(self.model))

class DataStatisticsProcess(Process):
    """
    Calculate summary statistics on data
    """
    
    PROCESS_NAME = "OverlayStats"
    
    def __init__(self, ivm, **kwargs):
        Process.__init__(self, ivm, **kwargs)
        self.model = QtGui.QStandardItemModel()

    def run(self, options):
        data_name = options.pop('data', None)
        if data_name is None:
            data_items = self.ivm.data.values()
            output_name = options.pop('output-name', "stats")
        else:
            data_items = [self.ivm.data[data_name]]
            output_name = options.pop('output-name', "%s_stats" % data_name)
            
        roi_name = options.pop('roi', None)
        if roi_name is None:
            roi = self.ivm.current_roi
        else:
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
            stats1, roi_labels, hist1, hist1x = self.get_summary_stats(data, roi, hist_bins=hist_bins, hist_range=hist_range, slice=sl)
            for ii in range(len(stats1['mean'])):
                self.model.setHorizontalHeaderItem(col, QtGui.QStandardItem("%s\nRegion %i" % (data.name, roi_labels[ii])))
                self.model.setItem(0, col, QtGui.QStandardItem(sf(stats1['mean'][ii])))
                self.model.setItem(1, col, QtGui.QStandardItem(sf(stats1['median'][ii])))
                self.model.setItem(2, col, QtGui.QStandardItem(sf(stats1['std'][ii])))
                self.model.setItem(3, col, QtGui.QStandardItem(sf(stats1['min'][ii])))
                self.model.setItem(4, col, QtGui.QStandardItem(sf(stats1['max'][ii])))
                col += 1

        if not no_extra: 
            self.ivm.add_extra(output_name, table_to_str(self.model))

    def get_summary_stats(self, data, roi=None, hist_bins=20, hist_range=None, slice=None):
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

        if (data is None):
            stat1 = {'mean': [0], 'median': [0], 'std': [0], 'max': [0], 'min': [0]}
            return stat1, roi.regions(), np.array([0, 0]), np.array([0, 1])

        stat1 = {'mean': [], 'median': [], 'std': [], 'max': [], 'min': []}
        hist1 = []
        hist1x = []

        if slice is None:
            data_arr = data.raw()
            roi_arr = roi.raw()
        else:
            data_arr, _, _, _ = data.slice_data(slice)
            roi_arr, _, _, _ = roi.slice_data(slice)

        for region in roi.regions():
            # get data for a single label of the roi
            in_roi = data_arr[roi_arr == region]
            if in_roi.size > 0:
                mean, med, std = np.mean(in_roi), np.median(in_roi), np.std(in_roi)
                mx, mn = np.max(in_roi), np.min(in_roi)
            else:
                mean, med, std, mx, mn = 0,0,0,0,0

            stat1['mean'].append(mean)
            stat1['median'].append(med)
            stat1['std'].append(std)
            stat1['max'].append(mx)
            stat1['min'].append(mn)

            y, x = np.histogram(in_roi, bins=hist_bins, range=hist_range)
            hist1.append(y)
            hist1x.append(x)

        return stat1, roi.regions(), hist1, hist1x

class ExecProcess(Process):
    
    PROCESS_NAME = "Exec"
    
    def __init__(self, ivm, **kwargs):
        Process.__init__(self, ivm, **kwargs)
        self.model = QtGui.QStandardItemModel()

    def run(self, options):
        globals = {'np': np, 'scipy' : scipy, 'ivm': self.ivm}

        # For general Numpy operations we will need a grid to put the
        # results back into. This is specified by the 'grid' option.
        # Note that all data is combined using their raw grids so these
        # must all match if the result is to work - that is the user's job!
        self.grid = self.ivm.main.grid

        for name, data in self.ivm.data.items():
            globals[name] = data.raw()
        for name, roi in self.ivm.rois.items():
            globals[name] = roi.raw()

        for name in options.keys():
            proc = options.pop(name)
            if name == "grid":
                self.grid = self.ivm.data[options[name]].grid
            if name == "exec":
                for code in proc:
                    try:
                        exec(code, globals)
                    except:
                        raise QpException("'%s' is not valid Python code (Reason: %s)" % (code, sys.exc_info()[1]))
            else:
                try:
                    result = eval(proc, globals)
                    self.ivm.add_data(result, grid=self.grid, name=name)
                except:
                    raise QpException("'%s' did not return valid data (Reason: %s)" % (proc, sys.exc_info()[1]))

