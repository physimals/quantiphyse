"""
Quantiphyse - radial profile process

Copyright (c) 2013-2018 University of Oxford
"""
import six

import numpy as np

from PySide import QtGui

from quantiphyse.utils import QpException, table_to_extra
from quantiphyse.processes import Process

class RadialProfileProcess(Process):
    """
    Calculate radial profile for a data set
    """
    
    PROCESS_NAME = "RadialProfile"
    
    def __init__(self, ivm, **kwargs):
        Process.__init__(self, ivm, **kwargs)
        self.model = QtGui.QStandardItemModel()

    def run(self, options):
        data_items = options.pop('data', None)
        if data_items is None:
            data_items = self.ivm.data.keys()
        elif isinstance(data_items, six.string_types):
            data_items = [data_items,]
            
        if not data_items:
            raise QpException("No data to calculate radial profile")
        
        data_items = [self.ivm.data[name] for name in data_items]
        roi = self.get_roi(options, use_current=False)
        
        #roi_region = options.pop('region', None)
        centre = options.pop('centre')
        if isinstance(centre, six.string_types):
            centre = [float(v) for v in centre.split(",")]
        vol = None
        if len(centre) == 4:
            vol = centre[3]
        
        output_name = options.pop('output-name', "radial-profile")
        bins = options.pop('bins', 20)

        self.model.clear()
        self.rp = {}
        
        grid = data_items[0].grid
        voxel_sizes = grid.spacing

        # Generate an array whose entries are integer values of the distance
        # from the centre. Set masked values to distance of -1
        x, y, z = np.indices(grid.shape)
        r = np.sqrt((voxel_sizes[0]*(x - centre[0]))**2 + (voxel_sizes[1]*(y - centre[1]))**2 + (voxel_sizes[2]*(z - centre[2]))**2)
        if roi is not None:
            r[roi == 0] = -1
        rmin = r[r > 0].min()

        # Generate histogram of number of voxels in each bin
        # Use the range parameter to ignore masked values with negative distances
        voxels_per_bin, self.edges = np.histogram(r, bins=bins, range=(rmin, r.max()))

        # Prevent divide by zero, if there are no voxels in a bin, this is OK because
        # there will be no data either
        voxels_per_bin[voxels_per_bin == 0] = 1
        self.xvals = [(self.edges[i] + self.edges[i+1])/2 for i in range(len(self.edges)-1)]

        for idx, xval in enumerate(self.xvals):
            self.model.setVerticalHeaderItem(idx, QtGui.QStandardItem(str(xval)))

        for col, data in enumerate(data_items):
            self.model.setHorizontalHeaderItem(col, QtGui.QStandardItem("%s" % data.name))
                
            weights = data.resample(grid).volume(vol)

            # Generate histogram by distance, weighted by data
            rpd, _ = np.histogram(r, weights=weights, bins=bins, range=(rmin, r.max()))

            # Divide by number of voxels in each bin to get average value by distance.
            rp = rpd / voxels_per_bin
            for idx, v in enumerate(rp):
                self.model.setItem(idx, col, QtGui.QStandardItem(str(v)))
            self.rp[data.name] = rp

        self.ivm.add_extra(output_name, table_to_extra(self.model, output_name))
