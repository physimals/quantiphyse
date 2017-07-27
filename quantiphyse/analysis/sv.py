import numpy as np
import skimage.segmentation 

from . import Process
from .perfusionslic import PerfSLIC
from .feat_pca import PcaFeatReduce
from .perfusionslic import slic_feat

class Supervoxels4DProcess(Process):
    """
    Process to run supervoxel generation
    """

    def __init__(self, ivm, **kwargs):
        Process.__init__(self, ivm, **kwargs)

    def run(self, options):
        ncomp = options['n-components']
        comp = options['compactness']
        n_supervoxels = options['n-supervoxels']
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
                                            recompute_seeds=True, n_random_seeds=n_supervoxels)
        # Add 1 to the supervoxel IDs as 0 is used as 'empty' value
        svdata = np.array(segments, dtype=np.int) + 1

        newroi = np.zeros(self.ivm.current_roi.shape)
        newroi[roi_slices] = svdata
        self.ivm.add_roi(output_name, newroi, make_current=True)
        self.status = Process.SUCCEEDED

class SupervoxelsProcess(Process):
    """
    Process to run 3d supervoxel generation
    """

    def __init__(self, ivm, **kwargs):
        Process.__init__(self, ivm, **kwargs)

    def preprocess_pca(self, img, ncomp, normalise_input_image=True, norm_type='perc'):
        """
        Do PCA analysis on 4D image to turn it into a 3D image suitable for SLIC
        """
        # Normalize enhancement curves using first 3 points (FIXME magic number)
        baseline = np.mean(img[:, :, :, :3], axis=-1)
        img = img - np.tile(np.expand_dims(baseline, axis=-1), (1, 1, 1, img.shape[-1]))
        
        # Run PCA feature extraction
        fe = PcaFeatReduce(img)
        feat_image, _ = fe.get_training_features(opt_normdata=True, opt_normimage=normalise_input_image,
                                                  feature_volume=True, n_components=ncomp, norm_type=norm_type)
        return feat_image

    def run(self, options):
        comp = options.pop('compactness', 0.1)
        n_supervoxels = options['n-supervoxels']
        sigma = options.pop('sigma', 1)
        recompute_seeds = options.pop('recompute-seeds', True)
        seed_type = options.get('seed-type', 'nrandom')
        data_name = options.pop('data', None)
        roi_name = options.pop('roi', None)
        output_name = options.get('output-name', "supervoxels")
        
        if roi_name is None and self.ivm.current_roi is not None:
            roi = self.ivm.current_roi
        elif roi_name is not None:
            roi = self.ivm.rois[roi_name]

        if data_name is None:
            img = self.ivm.vol
        else:
            img = self.ivm.overlays[data_name]
    
        if roi is not None:
            slices = roi.get_bounding_box(ndim=self.ivm.vol.ndim)
            img = img[slices[:img.ndim]]
            mask =roi[slices[:roi.ndim]]
        else:
            mask = None

        if img.ndim == 4:
            # For 4D data, use PCA to reduce down to 3D
            ncomp = options.pop('n-components', 3)
            img = self.preprocess_pca(img, ncomp)
        else:
            # For 3D data scale to a range of 0-1
            img = img.astype(np.float)
            img = (img - img.min()) / (img.max() - img.min())

        # FIXME enforce_connectivity=True does not seem to work in ROI mode?
        vox_sizes = [float(s)/self.ivm.voxel_sizes[0] for s in self.ivm.voxel_sizes[:3]]
        
        labels = slic_feat(img, n_segments=n_supervoxels, compactness=comp, sigma=sigma,
                           seed_type=seed_type, multichannel=False, multifeat=True,
                           enforce_connectivity=False, return_adjacency=False, spacing=vox_sizes,
                           mask=mask, recompute_seeds=recompute_seeds, n_random_seeds=n_supervoxels)
        labels = np.array(labels, dtype=np.int) + 1
        
        if roi is not None:
            newroi = np.zeros(self.ivm.shape[:3])
            newroi[slices[:newroi.ndim]] = labels
        else:
            newroi = labels
        self.ivm.add_roi(output_name, newroi, make_current=True)
        self.status = Process.SUCCEEDED