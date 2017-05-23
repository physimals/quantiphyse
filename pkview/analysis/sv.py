import numpy as np

from . import Process
from .perfusionslic import PerfSLIC

class SupervoxelsProcess(Process):
    """
    Asynchronous background process to run supervoxel generation
    """

    def __init__(self, ivm, **kwargs):
        Process.__init__(self, ivm, **kwargs)

    def run(self, options):
        ncomp = options['n-components']
        comp = options['compactness']
        segment_size = options['segment-size']
        output_name = options.get('output-name', "supervoxels")
        
        slices = self.ivm.current_roi.get_bounding_box(ndim=self.ivm.vol.ndim)
        roi_slices = slices[:self.ivm.current_roi.ndim]
        img = self.ivm.vol[slices]
        mask = self.ivm.current_roi[roi_slices]
        vox_sizes = self.ivm.voxel_sizes[:3]

        #print("Initialise the perf slic class")
        ps1 = PerfSLIC(img, vox_sizes, mask=mask)
        #print("Normalising image...")
        ps1.normalise_curves()
        #print("Extracting features...")
        ps1.feature_extraction(n_components=ncomp)
        #print("Extracting supervoxels...")
        segments = ps1.supervoxel_extraction(compactness=comp, seed_type='nrandom',
                                            recompute_seeds=True, n_random_seeds=segment_size)
        # Add 1 to the supervoxel IDs as 0 is used as 'empty' value
        svdata = np.array(segments, dtype=np.int) + 1

        newroi = np.zeros(self.ivm.current_roi.shape)
        newroi[roi_slices] = svdata
        self.ivm.add_roi(output_name, newroi, make_current=True)
        self.status = Process.SUCCEEDED
