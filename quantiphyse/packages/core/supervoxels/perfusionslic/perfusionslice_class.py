"""
Quantiphyse - Class wrapper for supervoxel generation

Copyright (c) 2013-2018 University of Oxford
"""

from __future__ import division, print_function, unicode_literals

import warnings

import numpy as np
import scipy.ndimage as ndi

from quantiphyse.processes.feat_pca import PcaFeatReduce
from quantiphyse.utils import LogSource

from . import slic_feat

class PerfSLIC(LogSource):
    """
    PerfSLIC
    Object that creates and visualises supervoxels created from 4D perfusion images

    Benjamin Irving
    20141124
    """

    def __init__(self, img, vox_sizes, mask=None):
        """
        :param img1: 4D image to load
        :param vox_size: voxel size of loaded image
        :return:
        """
        LogSource.__init__(self)

        self.img1 = img
        # cython is sensitive to the double definition
        self.vox_size = np.asarray(vox_sizes/vox_sizes[0], dtype=np.double)
        self.mask = mask

        self.segments = None
        self.adj_mat = None
        self.border_mat = None
        self.feat1_image = None
        self.img_slice = None
        self.zoom_factor = None
        self.n_components = None
        self.fe = None

    def normalise_curves(self):
        """
        :param use_roi: Normalise within an roi
        :return:
        """

        # ~~~~~~~~~~~~~~~~~~~~~ 1) Normalise enhancement curves (optional) ~~~~~~~~~~~~~~~~~~~~~~

        self.debug("Image norm")
        baseline1 = np.mean(self.img1[:, :, :, :3], axis=-1)
        self.img1 = self.img1 - np.tile(np.expand_dims(baseline1, axis=-1), (1, 1, 1, self.img1.shape[-1]))

    def feature_extraction(self, n_components=5, normalise_input_image=1, norm_type='perc'):
        """
        :param n_components:
        :param normalise_input_image: Normalise the input image
        :param norm_type: 'max' or 'perc'
        :return:
        """

        # ~~~~~~~~~~~~~~~~~~~~~~ 2) Feature extraction ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

        self.n_components = n_components
        self.fe = PcaFeatReduce(n_components=self.n_components, norm_modes=True, norm_input=normalise_input_image, norm_type=norm_type)
        self.feat1_image = self.fe.get_training_features(self.img1, feature_volume=True)

    def get_component(self, comp_choice):
        """
        Component to save
        :return:
        """

        return self.feat1_image[:, :, :, comp_choice]


    def zoom(self, zoomfactor=2):
        """
        Experimental
        :param zoomfactor:
        :return:
        """
        self.zoom_factor = zoomfactor
        warnings.warn('Experimental feature')
        self.feat1_image = ndi.interpolation.zoom(self.feat1_image, [zoomfactor, zoomfactor, zoomfactor, 1], order=0)

    def supervoxel_extraction(self, compactness=0.05, sigma=1, seed_type='grid',
                              segment_size=400, recompute_seeds=False, n_random_seeds=10):
        """
        Just a wrapper for the SLIC interface
        :param compactness:
        :param sigma:
        :param seed_type: 'grid', 'nrandom'
                        Type of seed point initiliasation which is either based on a grid of no points or randomly
                        assigned within an roi
        :param segment_size: Mean supervoxel size (assuming no ROI but can be used with an ROI as standard)
        :param recompute_seeds: True or False
                                Recompute the initialisation points based on spatial distance within a ROI
        :param n_random_seeds:
        :return:
        """

        # ~~~~~~~~~~~~~~~~~~~~~~ 3) SLIC ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        n_segments = int(self.feat1_image.shape[0] * self.feat1_image.shape[1] * self.feat1_image.shape[2]/segment_size)
        self.segments, self.adj_mat, self.border_mat = slic_feat(self.feat1_image,
                                                                 n_segments=n_segments,
                                                                 compactness=compactness,
                                                                 sigma=sigma,
                                                                 seed_type=seed_type,
                                                                 multichannel=False, multifeat=True,
                                                                 enforce_connectivity=False,
                                                                 return_adjacency=True,
                                                                 spacing=self.vox_size,
                                                                 mask=self.mask,
                                                                 recompute_seeds=recompute_seeds,
                                                                 n_random_seeds=n_random_seeds)

        return self.segments

    def return_adjacency_matrix(self):
        return self.adj_mat

    def return_border_list(self):
        return np.asarray(self.border_mat, dtype=bool)

    def return_adjacency_as_list(self):
        """
        Ruturn a list of adjacent supervoxels for each supervoxel
        :return:
        """

        # saving nearest neighbour data
        self.debug("Converting neighbour array to list...")
        neigh_store = []
        for pp in range(self.adj_mat.shape[0]):
            n1_ar = np.array(self.adj_mat[int(pp), :] == 1)
            sv_neigh = n1_ar.nonzero()[0]
            neigh_store.append(sv_neigh)

        return neigh_store
