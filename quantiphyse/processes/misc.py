"""
Quantiphyse - Miscellaneous generic analysis processes

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

import numpy as np
import scipy

from quantiphyse.data import NumpyData

from .process import Process

class RenameProcess(Process):
    """ 
    Rename data  
    """
    
    PROCESS_NAME = "Rename"

    def run(self, options):
        for name in list(options.keys()):
            newname = options.pop(name)
            self.ivm.rename(name, newname)

class DeleteProcess(Process):
    """
    Delete data or ROIs
    """

    PROCESS_NAME = "Delete"

    def __init__(self, ivm, **kwargs):
        Process.__init__(self, ivm, **kwargs)

    def run(self, options):
        for name in list(options.keys()):
            options.pop(name, None)
            if name in self.ivm.data: 
                self.ivm.delete(name)
            else:
                self.warn("Failed to delete %s: No such data or ROI" % name)

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
                slice_axis = fill_holes_slice
                new = np.copy(roi.raw())
                for slice_idx in range(new.shape[int(slice_axis)]):
                    slices = [slice(None), slice(None), slice(None)]
                    slices[slice_axis] = slice_idx
                    slices = tuple(slices)
                    new[slices] = scipy.ndimage.morphology.binary_fill_holes(new[slices])
            
                self.ivm.add(NumpyData(data=new, grid=roi.grid, name=output_name, roi=True))
