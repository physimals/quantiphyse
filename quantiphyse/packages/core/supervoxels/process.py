"""
Quantiphyse - Analysis process for supervoxel clustering

Copyright (c) 2013-2018 University of Oxford
"""

import numpy as np
import skimage.segmentation 

from quantiphyse.utils.exceptions import QpException

from quantiphyse.analysis import Process
from quantiphyse.analysis.feat_pca import PcaFeatReduce

from .perfusionslic import PerfSLIC, slic_feat

class SupervoxelsProcess(Process):
    """
    Process to run 3d supervoxel generation
    """
    PROCESS_NAME = "Supervoxels"

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
        n_supervoxels = options.pop('n-supervoxels')
        sigma = options.pop('sigma', 1)
        recompute_seeds = options.pop('recompute-seeds', True)
        seed_type = options.get('seed-type', 'nrandom')
        data_name = options.pop('data', None)
        roi_name = options.pop('roi', None)
        output_name = options.pop('output-name', "supervoxels")
        img = self.get_data(options)

        if roi_name is None and self.ivm.current_roi is not None:
            roi = self.ivm.current_roi
        elif roi_name in self.ivm.rois:
            roi = self.ivm.rois[roi_name]
        else:
            roi = None

        if roi is not None:
            slices = roi.get_bounding_box()
            img = img[slices]
            mask = roi.std()[slices]
        else:
            mask = None

        if img.ndim > 3 and img.shape[3] > 1:
            # For 4D data, use PCA to reduce down to 3D
            ncomp = options.pop('n-components', 3)
            img = self.preprocess_pca(img, ncomp)
        else:
            # For 3D data scale to a range of 0-1
            if img.ndim > 3: img = np.squeeze(img, -1)
            img = img.astype(np.float32)
            img = (img - img.min()) / (img.max() - img.min())

        # FIXME enforce_connectivity=True does not seem to work in ROI mode?
        vox_sizes = [float(s)/self.ivm.grid.spacing[0] for s in self.ivm.grid.spacing]
        
        labels = slic_feat(img, n_segments=n_supervoxels, compactness=comp, sigma=sigma,
                           seed_type=seed_type, multichannel=False, multifeat=True,
                           enforce_connectivity=False, return_adjacency=False, spacing=vox_sizes,
                           mask=mask, recompute_seeds=recompute_seeds, n_random_seeds=n_supervoxels)
        labels = np.array(labels, dtype=np.int) + 1
        if roi is not None:
            newroi = np.zeros(roi.std().shape)
            newroi[slices] = labels
        else:
            newroi = labels
        self.ivm.add_roi(newroi, name=output_name, make_current=True)
        self.status = Process.SUCCEEDED

class MeanValuesProcess(Process):
    """
    Create new data set by replacing voxel values with mean within each ROI region
    """
    PROCESS_NAME="MeanValues"
    
    def __init__(self, ivm, **kwargs):
        Process.__init__(self, ivm, **kwargs)

    def run(self, options):
        roi_name = options.pop('roi', None)
        data_name = options.pop('data', None)
        output_name = options.pop('output-name', None)

        if roi_name is None:
            roi = self.ivm.current_roi
        else:
            roi = self.ivm.rois[roi_name]

        if data_name is None:
            data = self.ivm.main.std()
        else:
            data = self.ivm.data[data_name].std()

        if output_name is None:
            output_name = data.name + "_means"

        ov_data = np.zeros(data.shape)
        for region in roi.regions:
            if data.ndim > 3:
                ov_data[roi.std() == region] = np.mean(data[roi.std() == region], axis=0)
            else:
                ov_data[roi.std() == region] = np.mean(data[roi.std() == region])

        self.ivm.add_data(ov_data, name=output_name, make_current=True)
        self.status = Process.SUCCEEDED
