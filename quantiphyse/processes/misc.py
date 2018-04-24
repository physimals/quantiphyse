"""
Quantiphyse - Miscellaneous generic analysis processes

Copyright (c) 2013-2018 University of Oxford
"""

import numpy as np
import scipy

from quantiphyse.data import NumpyData
from quantiphyse.utils import debug, QpException

from .process import Process

class ResampleProcess(Process):
    """ 
    Resample data 
    """

    PROCESS_NAME = "Resample"
    
    def run(self, options):
        data = self.get_data(options)
        order = options.pop("order", 1)
        output_name = options.pop("output-name", "%s_res" % data.name)
        grid_data = options.pop("grid", None)

        if grid_data is None:
            raise QpException("Must provide 'grid' option to specify data item to get target grid from")
        elif grid_data not in self.ivm.data:
            raise QpException("Data item '%s' not found" % grid_data)
        
        grid = self.ivm.data[grid_data].grid
        output_data = data.resample(grid, order=order)
        output_data.name = output_name
        self.ivm.add_data(output_data)
        self.status = Process.SUCCEEDED

class RenameDataProcess(Process):
    """ 
    Rename data  
    """
    
    PROCESS_NAME = "RenameData"

    def run(self, options):
        for name in options.keys():
            newname = options.pop(name)
            self.ivm.rename_data(name, newname)
          
        self.status = Process.SUCCEEDED

class RenameRoiProcess(Process):
    """ Rename ROI  """
    
    PROCESS_NAME = "RenameRoi"

    def run(self, options):
        for name in options.keys():
            newname = options.pop(name)
            self.ivm.rename_roi(name, newname)
            
        self.status = Process.SUCCEEDED

class RoiCleanupProcess(Process):
    """
    Fill holes, etc in ROI
    """
    
    PROCESS_NAME = "RoiCleanup"
    
    def __init__(self, ivm, **kwargs):
        Process.__init__(self, ivm, **kwargs)

    def run(self, options):
        roi_name = options.pop('roi', None)
        output_name = options.pop('output-name', "roi-cleaned")
        fill_holes_slice = options.pop('fill-holes-by-slice', None)

        if roi_name is None:
            roi = self.ivm.current_roi
        else:
            roi = self.ivm.rois[roi_name]

        if roi is not None:
            if fill_holes_slice is not None:
                # slice-by-slice hole filling, appropriate when ROIs defined slice-by-slice
                d = fill_holes_slice
                new = np.copy(roi.raw())
                for sl in range(new.shape[int(d)]):
                    slices = [slice(None), slice(None), slice(None)]
                    slices[d] = sl
                    new[slices] = scipy.ndimage.morphology.binary_fill_holes(new[slices])
            
                self.ivm.add_roi(NumpyData(data=new, grid=roi.grid, name=output_name))
        
        self.status = Process.SUCCEEDED
