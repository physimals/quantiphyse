"""
Quantiphyse - PCA implementation

Copyright (c) 2013-2018 University of Oxford
"""

from __future__ import division, print_function, absolute_import

import numpy as np
from sklearn.decomposition import PCA

from quantiphyse.utils import QpException, debug

from . import image_normalisation as inorm

def _normalise_data(data, norm_type='perc'):
    """
    Normalise image data
    """
    image_norm = inorm.ImNorm(data)
    if norm_type == 'perc':
        image_norm.scale_percentile()
        image_norm.offset_time()
    elif norm_type == 'max':
        image_norm.scale_max()
    else:
        raise ValueError('Scaling type does not exist')

    image_norm.smooth()
    #image_norm.scale_indv()
    return image_norm.get_image()

def _normalise_modes(data):
    """
    Normalise PCA modes
    """
    # TODO should maybe normalise based on lambda instead
    dmin = np.min(data, axis=0)
    data = data - np.tile(np.expand_dims(dmin, axis=0),
                          (data.shape[0], 1))
    dmax = np.max(data, axis=0)
    data = data / np.tile(np.expand_dims(dmax, axis=0),
                          (data.shape[0], 1))
    return data

def _flat_data_to_image(data, roi):
    # return features in image format
    image_shape = list(roi.shape)
    if data.ndim == 2:
        image_shape.append(data.shape[1])
    image = np.zeros(image_shape)
    image[roi] = data
    return image

class PcaFeatReduce(object):
    """
    Extract PCA features from 4D image data
    """

    def __init__(self, n_components, norm_modes=True, norm_input=False, norm_type='perc'):
        """
        :param data: 4D image to be processed
        :param roi: Optional sub region to extract
        """
        
        # Variables
        self.reduced_data = None
        self.pca = PCA(n_components=n_components)
        self.norm_modes = norm_modes
        self.norm_input = norm_input
        self.norm_type = norm_type

    def get_training_features(self, data, roi=None, feature_volume=False):
        """
        Train PCA reduction on data and return features for each voxel

        :param data: 4D data set
        :param roi: Optional 3D ROI
        :param feature_volume: determines whether the features are returned as a list or an image

        :return: If ``feature_volume``, 4D array with the same 3d dimensions as data and 
                 4th dimension=number of PCA components.
                 Otherwise, 2D array whose first dimension is unmasked voxels and 2nd dimension
                 is the PCA components
        """
        data_inmask, roi = self._mask(data, roi)

        debug("Using PCA dimensionality reduction")
        reduced_data = self.pca.fit_transform(data_inmask)
        debug("Number of components", reduced_data.shape[1])

        if self.norm_modes:
            debug("Normalising PCA modes between 0 and 1")
            reduced_data = _normalise_modes(reduced_data)

        if not feature_volume:
            return reduced_data

        return _flat_data_to_image(reduced_data, roi)

    def get_projected_test_features(self, data, roi=None, feature_volume=False):
        """
        Return features for each voxel from previously trained PCA modes

        :param data: 4D data set
        :param roi: Optional 3D ROI
        :param feature_volume: determines whether the features are returned as a list or an image

        :return: If ``feature_volume``, 4D array with the same 3d dimensions as data and 
                 4th dimension=number of PCA components.
                 Otherwise, 2D array whose first dimension is unmasked voxels and 2nd dimension
                 is the PCA components
        """
        data_inmask, roi = self._mask(data, roi)
        
        #Projecting the data using training set PCA
        if data_inmask.shape[1] != self.pca.mean_.shape[0]:
            raise QpException("Input data length does not match previous training data")
            
        reduced_data = self.pca.transform(data_inmask)

        # Scaling features
        if self.norm_modes:
            debug("Normalising PCA modes")
            reduced_data = _normalise_modes(reduced_data)

        if not feature_volume:
            return reduced_data
        
        return _flat_data_to_image(reduced_data, roi)

    def explained_variance(self):
        """
        Return the variance explained by including each of the modes cumulatively
        
        :return: Increasing sequence of numbers between 0 and 1 
        """ 
        return [np.sum(self.pca.explained_variance_ratio_[:n]) 
                for n in range(self.pca.n_components_)]

    def _mask(self, data, roi):
        data = np.array(data, dtype=np.float32)
        if roi is None:
            roi = np.ones(data.shape[0:-1], dtype=bool)
        else:
            roi = np.array(roi, dtype=np.bool)
        data_inmask = data[roi]

        if self.norm_input:
            data_inmask = _normalise_data(data_inmask, self.norm_type)
        return data_inmask, roi
    