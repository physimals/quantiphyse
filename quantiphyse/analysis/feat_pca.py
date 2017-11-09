"""

Author: Benjamin Irving (benjamin.irv@gmail.com)
Copyright (c) 2013-2015 University of Oxford, Benjamin Irving

"""

from __future__ import division, print_function, absolute_import

import numpy as np
from sklearn.decomposition import PCA

from quantiphyse.utils import debug

from . import image_normalisation as inorm

class PcaFeatReduce(object):
    """
    Class for extracting PCA features from an image
    Returns features associated with each voxel
    """

    def __init__(self, img1, region1=None, labels1=None):
        """

        @param img1: 4D image to be processed
        @param region1: Optional sub region to extract
        @param labels1: (deprecated) labels are return with the region to make classification easier
        @return:
        """

        self.img1 = np.array(img1, dtype=np.float32)

        #Region to process
        if region1 is None:
            self.region1 = np.ones(self.img1.shape[0:-1], dtype=bool)
        else:
            self.region1 = np.array(region1, dtype=np.bool)

        self.img1 = self.img1 * np.tile(np.expand_dims(self.region1, axis=-1), (1, 1, 1, self.img1.shape[-1]))
        #features
        self.voxel_se = self.img1[self.region1]

        #Labels for the region
        if labels1 is None:
            #if no labels are given then all are set to 1
            self.labels1 = np.zeros(self.voxel_se.shape[0])
        else:
            self.labels1 = labels1[self.region1]

        # Variables
        self.reduced_data = None
        self.pca = None
        self.opt_normdata = None

    @staticmethod
    def normalise_im(im1, norm_type='perc'):
        image_norm = inorm.ImNorm(im1)
        #image_norm.scale_norm()
        if norm_type == 'perc':
            image_norm.scale_percentile()
            image_norm.offset_time()
        elif norm_type == 'max':
            image_norm.scale_max()
        else:
            raise ValueError('Scaling type does not exist')

        image_norm.smooth()
        #image_norm.scale_indv()
        im1 = image_norm.get_image()

        return im1

    def get_training_features(self, opt_normdata=1, opt_normimage=0, feature_volume=False, n_components=5, norm_type='perc'):

        """
        Return features for each voxel from the PCA reduction

        @param: feature_volume determines whether the features are returned as a list or an image

        @return:
        reduced_data = array representing the features for each voxel (row: voxel, column features)
        labels1 = roi labels (just return to make the next step of classification easier)
        """

        self.opt_normdata = opt_normdata
        self.opt_normimage = opt_normimage
        self.norm_type = norm_type

        if self.opt_normimage == 1:
            self.voxel_se = self.normalise_im(self.voxel_se, self.norm_type)

        debug("Using PCA dimensionality reduction")
        self.pca = PCA(n_components=n_components)
        reduced_data = self.pca.fit_transform(self.voxel_se)
        debug("Number of components", reduced_data.shape[1])

        if opt_normdata == 1:
            debug("Normalising PCA modes between 0 and 1")
            #TODO should maybe normalise based on lambda instead
            self.min1 = np.min(reduced_data, axis=0)
            reduced_data = reduced_data - np.tile(np.expand_dims(self.min1, axis=0),
                                                  (reduced_data.shape[0], 1))
            self.max1 = np.max(reduced_data, axis=0)
            reduced_data = reduced_data / np.tile(np.expand_dims(self.max1, axis=0),
                                                  (reduced_data.shape[0], 1))

        self.reduced_data = reduced_data

        if feature_volume is False:
            return self.reduced_data, self.labels1

        else:
            # return features in image format
            shape1 = np.array(self.img1.shape)
            shape1[-1] = self.reduced_data.shape[1]
            feature_image = np.zeros(shape1)
            feature_image[self.region1] = self.reduced_data

            return feature_image, self.labels1

    def get_projected_test_features(self, img1_test, region1_test=None, feature_volume=False, exclude=None):

        #Test region to process
        if region1_test is None:
            region1 = np.ones(img1_test.shape[0:-1], dtype=bool)
        else:
            region1 = np.array(region1_test, dtype=np.bool)

        #Exclude a region of the image from analysis
        if exclude is not None:
            regione = np.logical_not(np.array(exclude, dtype=np.bool))
            region1 = np.logical_and(region1, regione)

        #img1_test = img1_test * np.tile(np.expand_dims(region1, axis=-1), (1, 1, img1_test.shape[-1]))
        voxel_se_test = img1_test[region1]

        if self.opt_normimage == 1:
            voxel_se_test = self.normalise_im(voxel_se_test, self.norm_type)

        #Projecting the data using training set PCA
        if voxel_se_test.shape[1] > self.pca.mean_.shape[0]:
            debug("Warning: reducing input vector length")
            voxel_se_test = voxel_se_test[:, :self.pca.mean_.shape[0]]

        elif voxel_se_test.shape[1] < self.pca.mean_.shape[0]:
            debug("Warning: increasing input vector length")
            voxel_se_test = voxel_se_test[:, :self.pca.mean_.shape[0]]
            diff = self.pca.mean_.shape[0] - voxel_se_test.shape[1]
            add1 = np.expand_dims(voxel_se_test[:, -1], axis=1)
            for ww in range(diff):
                voxel_se_test = np.append(voxel_se_test, add1, axis=1)

        reduced_data_test = self.pca.transform(voxel_se_test)

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
            feature_image[region1] = reduced_data_test

            return feature_image

    def show_model_stats(self):
        var5 = np.sum(self.pca.explained_variance_ratio_[:5])
        var10 = np.sum(self.pca.explained_variance_ratio_[:10])

        debug("Variance: ", self.pca.explained_variance_ratio_)
        debug("Variance explained by 5 modes: ", var5)
        debug("Variance explained by 10 modes: ", var10)

#import matplotlib.pyplot as plt
#
#    def plot_curve_modes(self, num1=4):
#
#        time1 = 12.5*np.arange(len(self.pca.mean_))
#        plt.plot(time1, self.pca.mean_, linestyle='--',  color='k', linewidth=3, label='mean')
#        colors1 = ['b', 'g', 'c', 'm', 'r']
#
#        for ii in range(num1):
#            if ii == 0:
#                stddev = 1.0
#            else:
#                stddev = 2.0
#            plt.plot(time1, self.pca.mean_ + stddev * np.sqrt(self.pca.explained_variance_[ii]) * self.pca.components_[ii, :],
#                     color=colors1[ii], label='mode' + str(ii+1), linewidth=2)
#            plt.plot(time1, self.pca.mean_ - stddev * np.sqrt(self.pca.explained_variance_[ii]) * self.pca.components_[ii, :],
#                     color=colors1[ii], linewidth=2)
#
#        l1 = plt.legend()
#        plt.xlabel('Time (s)')
#        plt.ylabel('Normalised signal')
#
#        plt.show()




