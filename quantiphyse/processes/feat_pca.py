"""
Quantiphyse - PCA implementation

Copyright (c) 2013-2018 University of Oxford
"""

from __future__ import division, print_function, absolute_import

import numpy as np
from sklearn.decomposition import PCA
from scipy.ndimage.filters import gaussian_filter1d

from quantiphyse.utils import QpException, LogSource
from . import normalisation as norm

def _flat_data_to_image(data, roi):
    # return features in image format
    image_shape = list(roi.shape)
    if data.ndim == 2:
        image_shape.append(data.shape[1])
    image = np.zeros(image_shape)
    image[roi] = data
    return image

class PcaFeatReduce(LogSource):
    """
    Extract PCA features from 4D image data

    Thin wrapper around sklearn.decomposition.PCA
    """

    def __init__(self, n_components, norm_modes=True, norm_input=False, norm_type='perc'):
        """
        :param data: 4D image to be processed
        :param roi: Optional sub region to extract
        """
        LogSource.__init__(self)

        # Variables
        self.pca = PCA(n_components=n_components)
        self.norm_modes = norm_modes
        self.norm_input = norm_input
        self.norm_type = norm_type

    def get_training_features(self, data, roi=None, smooth_timeseries=None, feature_volume=False):
        """
        Train PCA reduction on data and return features for each voxel

        :param data: 4D data set
        :param roi: Optional 3D ROI
        :param smooth_timeseries: Optional sigma for 1D Gaussian smoothing of each voxel timeseries
        :param feature_volume: determines whether the features are returned as a list or an image

        :return: If ``feature_volume``, 4D array with the same 3d dimensions as data and 
                 4th dimension=number of PCA components.
                 Otherwise, 2D array whose first dimension is unmasked voxels and 2nd dimension
                 is the PCA components
        """
        data_inmask, roi = self._mask(data, roi, smooth_timeseries)

        self.debug("Using PCA dimensionality reduction")
        reduced_data = self.pca.fit_transform(data_inmask)
        self.debug("Number of components", reduced_data.shape[1])

        if self.norm_modes:
            self.debug("Normalising PCA modes between 0 and 1")
            reduced_data = norm.normalise(reduced_data, "indiv")

        if not feature_volume:
            return reduced_data

        return _flat_data_to_image(reduced_data, roi)

    def get_projected_test_features(self, data, roi=None, smooth_timeseries=None, feature_volume=False):
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
        data_inmask, roi = self._mask(data, roi, smooth_timeseries)
        
        #Projecting the data using training set PCA
        if data_inmask.shape[1] != self.pca.mean_.shape[0]:
            raise QpException("Input data length does not match previous training data")
            
        reduced_data = self.pca.transform(data_inmask)

        # Scaling features
        if self.norm_modes:
            self.debug("Normalising PCA modes")
            reduced_data = norm.normalise(reduced_data, "indiv")

        if not feature_volume:
            return reduced_data
        
        return _flat_data_to_image(reduced_data, roi)

    def explained_variance(self, cumulative=False):
        """
        Return the variance explained by including each of the modes cumulatively
        
        :param cumulative: If True, variance explained will be cumulative (i.e.
                           variance explained by all modes up to and including each
                           mode)
        :return: Sequence of numbers giving variance explained for each component. 
        """ 
        if cumulative:
            return [np.sum(self.pca.explained_variance_ratio_[:n+1]) 
                    for n in range(self.pca.n_components_)]
        else:
            return self.pca.explained_variance_ratio_

    def modes(self):
        """
        :return: Fitted PCA modes
        """
        #return norm.normalise(self.pca.components_, "indiv")
        return [comp + self.pca.mean_ for comp in self.pca.components_]

    def mean(self):
        """
        :return: Training data mean
        """
        #return np.squeeze(norm.normalise(np.expand_dims(self.pca.mean_, axis=0), "indiv"))
        return self.pca.mean_

    def _mask(self, data, roi, smooth_timeseries):
        if roi is None:
            roi = np.ones(data.shape[0:-1], dtype=bool)
        else:
            roi = np.array(roi, dtype=np.bool)
        data_inmask = data[roi]

        if self.norm_input:
            data_inmask = norm.normalise(data_inmask, self.norm_type)

        if smooth_timeseries is not None:
            data_inmask = gaussian_filter1d(data_inmask, sigma=smooth_timeseries, axis=-1)
        return data_inmask, roi
