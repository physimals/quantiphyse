"""
Quantiphyse - PCA implementation

Copyright (c) 2013-2018 University of Oxford
"""

from __future__ import division, print_function, absolute_import

import numpy as np
from sklearn.decomposition import PCA

from quantiphyse.utils import debug

from . import image_normalisation as inorm
from . import normalisation as norm

class PcaFeatReduce(object):
    """
    Class for extracting PCA features from an image
    Returns features associated with each voxel
    """

    def __init__(self, img1, roi=None):
        """

        @param img1: 4D image to be processed
        @param roi: Optional sub region to extract
        @return:
        """
        self.img1 = img1

        if roi is None:
            self.roi = np.ones(self.img1.shape[0:-1], dtype=bool)
        else:
            self.roi = np.array(roi, dtype=np.bool)
        self.data_inmask = self.img1[self.roi]

        # Variables
        self.reduced_data = None
        self.pca = None
        self.opt_normdata = None

    def get_training_features(self, opt_normdata=1, opt_normimage=0, feature_volume=False, n_components=5, norm_type='perc'):

        """
        Return features for each voxel from the PCA reduction

        @param: feature_volume determines whether the features are returned as a list or an image

        @return:
        reduced_data = array representing the features for each voxel (row: voxel, column features)
        """

        self.opt_normdata = opt_normdata
        self.opt_normimage = opt_normimage
        self.norm_type = norm_type

        if self.opt_normimage == 1:
            self.data_inmask = norm.normalise(self.data_inmask, self.norm_type)
            
        debug("Using PCA dimensionality reduction")
        self.pca = PCA(n_components=n_components)
        reduced_data = self.pca.fit_transform(self.data_inmask)
        debug("Number of components", reduced_data.shape[1])

        if opt_normdata == 1:
            debug("Normalising PCA modes between 0 and 1")
            reduced_data = norm.normalise(reduced_data, "indiv")
            #TODO should maybe normalise based on lambda instead
            #self.min1 = np.min(reduced_data, axis=0)
            #reduced_data = reduced_data - np.tile(np.expand_dims(self.min1, axis=0),
            #                                      (reduced_data.shape[0], 1))
            #self.max1 = np.max(reduced_data, axis=0)
            #reduced_data = reduced_data / np.tile(np.expand_dims(self.max1, axis=0),
            #                                      (reduced_data.shape[0], 1))

        print("rednorm mean", np.mean(reduced_data), reduced_data.shape)
        self.reduced_data = reduced_data

        if feature_volume is False:
            return self.reduced_data

        else:
            # return features in image format
            shape1 = np.array(self.img1.shape)
            shape1[-1] = self.reduced_data.shape[1]
            feature_image = np.zeros(shape1)
            feature_image[self.roi] = self.reduced_data

            return feature_image

    def get_projected_test_features(self, img1_test, roi_test=None, feature_volume=False, exclude=None):

        #Test region to process
        if roi_test is None:
            roi = np.ones(img1_test.shape[0:-1], dtype=bool)
        else:
            roi = np.array(roi_test, dtype=np.bool)

        #Exclude a region of the image from analysis
        if exclude is not None:
            regione = np.logical_not(np.array(exclude, dtype=np.bool))
            roi = np.logical_and(roi, regione)

        #img1_test = img1_test * np.tile(np.expand_dims(roi, axis=-1), (1, 1, img1_test.shape[-1]))
        data_inmask_test = img1_test[roi]

        if self.opt_normimage == 1:
            data_inmask_test = self.normalise_im(data_inmask_test, self.norm_type)

        #Projecting the data using training set PCA
        if data_inmask_test.shape[1] > self.pca.mean_.shape[0]:
            debug("Warning: reducing input vector length")
            data_inmask_test = data_inmask_test[:, :self.pca.mean_.shape[0]]

        elif data_inmask_test.shape[1] < self.pca.mean_.shape[0]:
            debug("Warning: increasing input vector length")
            data_inmask_test = data_inmask_test[:, :self.pca.mean_.shape[0]]
            diff = self.pca.mean_.shape[0] - data_inmask_test.shape[1]
            add1 = np.expand_dims(data_inmask_test[:, -1], axis=1)
            for ww in range(diff):
                data_inmask_test = np.append(data_inmask_test, add1, axis=1)

        reduced_data_test = self.pca.transform(data_inmask_test)

        # Scaling features
        if self.opt_normdata == 1:
            debug("Normalising PCA modes")
            reduced_data_test = reduced_data_test - np.tile(np.expand_dims(self.min1, axis=0),
                                                            (reduced_data_test.shape[0], 1))
            reduced_data_test = reduced_data_test / np.tile(np.expand_dims(self.max1, axis=0),
                                                            (reduced_data_test.shape[0], 1))

        if feature_volume is False:
            return reduced_data_test

        else:
            # return features in image format
            shape1 = np.array(img1_test.shape)
            shape1[-1] = reduced_data_test.shape[1]
            feature_image = np.zeros(shape1)
            feature_image[roi] = reduced_data_test

            return feature_image

    def show_model_stats(self):
        var5 = np.sum(self.pca.explained_variance_ratio_[:5])
        var10 = np.sum(self.pca.explained_variance_ratio_[:10])

        debug("Variance: ", self.pca.explained_variance_ratio_)
        debug("Variance explained by 5 modes: ", var5)
        debug("Variance explained by 10 modes: ", var10)
