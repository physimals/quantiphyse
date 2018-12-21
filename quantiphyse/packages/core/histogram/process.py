"""
Quantiphyse - PCA reduction process

Copyright (c) 2013-2018 University of Oxford
"""
import six

from quantiphyse.data.extras import MatrixExtra
from quantiphyse.utils import QpException
from quantiphyse.processes import Process

import numpy as np

class HistogramProcess(Process):
    """
    Calculate histogram for a data set 
    """
    
    PROCESS_NAME = "Histogram"
    
    def __init__(self, ivm, **kwargs):
        Process.__init__(self, ivm, **kwargs)

    def run(self, options):
        data_items = options.pop('data', None)
        if data_items is None:
            data_items = self.ivm.data.keys()
        elif isinstance(data_items, six.string_types):
            data_items = [data_items,]

        if not data_items:
            raise QpException("No data to calculate histogram")
        
        data_items = [self.ivm.data[name] for name in data_items]
        roi = self.get_roi(options, use_current=False)
        
        sel_region = options.pop('region', None)
        dmin = options.pop('min', None)
        dmax = options.pop('max', None)
        bins = options.pop('bins', 100)
        vol = options.pop('vol', None)
        prob = options.pop('yscale', 'count').lower().startswith("prob")
        output_name = options.pop('output-name', "histogram")

        yvals, col_headers = {}, ["left", "right", "centre",]
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
                regions = {1 : ""}
            else:
                roi_fordata = roi.resample(data.grid).raw()
                regions = roi.regions

            for region, region_name in regions.items():
                if sel_region is not None and region != sel_region:
                    self.debug("Ignoring region %i", region)
                    continue

                region_data = rawdata[roi_fordata == region]
                data_vals, edges = np.histogram(region_data, bins=bins, range=hrange, density=prob)
                    
                if region_name:
                    name = "%s\n%s" % (data.name, region_name)
                else:
                    name = data.name

                col_headers.append(name)
                yvals[name] = data_vals
            
        xvals = [[edges[idx], edges[idx+1], (edges[idx]+edges[idx+1])/2] for idx in range(len(edges)-1)]
        rows = []
        for idx, row in enumerate(xvals):
            for name in col_headers[3:]:
                row += [yvals[name][idx],]
            rows.append(row)

        if not options.pop('no-extras', False):
            self.debug("Adding %s" % output_name)
            extra = MatrixExtra(output_name, rows, col_headers=col_headers)
            self.debug(str(extra))
            self.ivm.add_extra(output_name, extra)
