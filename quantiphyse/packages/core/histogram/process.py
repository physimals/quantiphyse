"""
Quantiphyse - PCA reduction process

Copyright (c) 2013-2018 University of Oxford
"""
from quantiphyse.utils import QpException, table_to_str
from quantiphyse.processes import Process

import numpy as np

from PySide import QtGui

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
        else:
            data_items = [self.ivm.data[data_name]]

        if not data_items:
            raise QpException("No data to calculate histogram")
        
        roi = self.get_roi(options, use_current=False)
        
        sel_region = options.pop('region', None)
        dmin = options.pop('min', None)
        dmax = options.pop('max', None)
        bins = options.pop('bins', 100)
        vol = options.pop('vol', None)
        prob = options.pop('yscale', 'count').lower().startswith("prob")
        output_name = options.pop('output-name', "histogram")

        self.model.setHorizontalHeaderItem(0, QtGui.QStandardItem("x0"))
        self.model.setHorizontalHeaderItem(1, QtGui.QStandardItem("x1"))  
        self.xvals, self.edges, self.hist = None, None, {}
        col = 2
        
        for data in data_items:
            if vol is not None:
                rawdata = data.volume(vol)
            else:
                rawdata = data.raw()
            hrange = [dmin, dmax]
            if dmin is None: hrange[0] = np.min(rawdata)
            if dmax is None: hrange[1] = np.max(rawdata)

            if roi is None:
                roi_fordata = np.ones(data.grid.shape)
                regions = [1,]
            else:
                roi_fordata = roi.resample(data.grid).raw()
                regions = roi.regions

            for region in regions:
                if sel_region is not None and region != sel_region:
                    self.debug("Ignoring region %i", region)
                    continue
                region_data = rawdata[roi_fordata == region]
                yvals, edges = np.histogram(region_data, bins=bins, range=hrange, density=prob)

                if self.xvals is None:
                    self.edges = edges
                    self.xvals = [(edges[i] + edges[i+1])/2 for i in range(len(edges)-1)]
                    for idx in range(len(edges)-1):
                        self.model.setVerticalHeaderItem(idx, QtGui.QStandardItem(""))
                        self.model.setItem(idx, 0, QtGui.QStandardItem(str(self.edges[idx])))
                        self.model.setItem(idx, 1, QtGui.QStandardItem(str(self.edges[idx+1])))
                if len(regions) > 1:
                    name = "%s\nRegion %i" % (data.name, region)
                else:
                    name = data.name
                self.model.setHorizontalHeaderItem(col, QtGui.QStandardItem(name))
                for idx, v in enumerate(yvals):
                    self.model.setItem(idx, col, QtGui.QStandardItem(str(v)))
                if data.name not in self.hist: self.hist[data.name] = {}
                self.hist[data.name][region] = yvals
                col += 1

        if not options.pop('no-extras', False): 
            self.debug("Adding %s" % output_name)
            self.ivm.add_extra(output_name, table_to_str(self.model))
