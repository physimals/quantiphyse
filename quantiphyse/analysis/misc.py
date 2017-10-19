import numpy as np
import scipy

from quantiphyse.utils import debug
from quantiphyse.utils.exceptions import QpException

from . import Process

class RenameDataProcess(Process):
    """ Rename data  """
    def run(self, options):
        for name, newname in options.items():
            self.ivm.rename_data(name, newname)
            
        self.status = Process.SUCCEEDED

class RenameRoiProcess(Process):
    """ Rename ROI  """
    def run(self, options):
        for name, newname in options.items():
            self.ivm.rename_roi(name, newname)
            
        self.status = Process.SUCCEEDED

class RoiCleanupProcess(Process):
    """
    Fill holes, etc in ROI
    """
    def __init__(self, ivm, **kwargs):
        Process.__init__(self, ivm, **kwargs)
        self.ia = OverlayAnalysis(ivm=self.ivm)

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
                new = np.copy(roi.std())
                for sl in range(new.shape[int(d)]):
                    slices = [slice(None), slice(None), slice(None)]
                    slices[d] = sl
                    new[slices] = scipy.ndimage.morphology.binary_fill_holes(new[slices])
            
                self.ivm.add_roi(new, name=output_name)
        
        self.status = Process.SUCCEEDED
