"""

Author: Benjamin Irving (benjamin.irv@gmail.com)
Copyright (c) 2013-2015 University of Oxford, Benjamin Irving

"""

from __future__ import division, print_function, absolute_import

import time
import numpy as np
import sklearn.cluster as cl
from sklearn.decomposition import PCA


class KMeans3D:
    """

    """

    def __init__(self, img1, region1=None, invert_roi=0, labels1=None):
        """

        @param img1: image region
        @param n_clusters:  number of k-means clusters to generate
        @param region1: region of interest to cluster
        @param invert_roi:
        @param normdata:
        @param labels1: (Optional) separate clustering of different regions
        """
        Issue #38: OSX hangs with parallel jobs
        if sys.platform.startswith("darwin"):
            self.n_jobs = 1
        else:
            self.n_jobs = 2

        self.img1 = np.array(img1, dtype=np.float32)

        # ROI to process
        if region1 is None:
            self.region1 = np.ones(self.img1.shape[0:-1], dtype=bool)
        elif invert_roi == 1:
            self.region1 = np.logical_not(region1)
        else:
            self.region1 = np.array(region1, dtype=np.bool)

        self.voxel_se = self.img1[self.region1]
        self.voxel_se = self.voxel_se[:, np.newaxis]

        # Labels for the region
        if labels1 is None:
            # if no labels are given then all are set to 1
            self.labels1 = np.ones(self.voxel_se.shape[0], dtype=np.int)
        else:
            self.labels1 = labels1[self.region1]

        self.n_clusters = None
        self.cluster_centers_ = None
        self.label_image = np.zeros_like(img1, dtype=np.int)
        self.label1_range = None

    def run_single(self, n_clusters):
        self.n_clusters = n_clusters
        kmeans = cl.KMeans(init='k-means++', n_clusters=self.n_clusters, n_init=10, n_jobs=self.n_jobs)
        kmeans.fit(self.voxel_se)

        # label image
        self.label_image[self.region1] = kmeans.labels_ + 1
        self.label_vector = kmeans.labels_ + 1

        # find mean cluster curves
        self.cluster_centers_ = np.zeros((self.n_clusters, self.img1.shape[-1]))
        for ii in range(self.n_clusters):
            c1 = self.voxel_se[self.label_vector == ii + 1]
            self.cluster_centers_[ii, :] = c1.mean(axis=0)

    def get_label_image(self):
        return self.label_image, self.cluster_centers_


class KMeansPCA:
    """
    This class just implements KMeans for a 2D or 3D image
    """

    def __init__(self, img1, region1=None, invert_roi=0, labels1=None):
        """

        @param img1: image region
        @param n_clusters:  number of k-means clusters to generate
        @param region1: region of interest to cluster
        @param invert_roi:
        @param normdata:
        @param labels1: (Optional) separate clustering of different regions
        """
        Issue #38: OSX hangs with parallel jobs
        if sys.platform.startswith("darwin"):
            self.n_jobs = 1
        else:
            self.n_jobs = 6

        self.img1 = np.array(img1, dtype=np.float32)

        #ROI to process
        if region1 is None:
            self.region1 = np.ones(self.img1.shape[0:-1], dtype=bool)
        elif invert_roi == 1:
            self.region1 = np.logical_not(region1)
        else:
            self.region1 = np.array(region1, dtype=np.bool)

        # self.img1 = self.img1 * np.tile(np.expand_dims(self.region1, axis=-1), (1, 1, self.img1.shape[-1]))
        self.voxel_se = self.img1[self.region1]

        baseline1 = np.mean(self.img1[:, :, :, :3], axis=-1)
        # baseline1 = np.reshape(baseline1, (-1))
        baseline1sub = baseline1[self.region1]

        # Normalisation of the image
        self.voxel_se = self.voxel_se / (np.tile(np.expand_dims(baseline1sub, axis=-1), (1, self.img1.shape[-1])) + 0.001) - 1

        # Labels for the region
        if labels1 is None:
            # if no labels are given then all are set to 1
            self.labels1 = np.ones(self.voxel_se.shape[0], dtype=np.int)
        else:
            self.labels1 = labels1[self.region1]

        # self.voxel_se = np.reshape(self.img1, (-1, self.img1.shape[-1]))
        self.n_clusters = None

        self.reduced_data = None
        self.cluster_centers_ = None
        self.label_image = None
        self.label1_range = None

    def run_single(self, reduction='pca', opt_normdata=1, n_clusters=5, n_pca_components=5):
        """
        Run kmeans for the entire region

        @param reduction:
        @param opt_normdata:
        @return:
        """
        self.n_clusters = n_clusters
        # Outputs
        self.label_image = np.zeros(self.region1.shape)
        self.cluster_centers_ = np.zeros((self.n_clusters, self.img1.shape[-1]))

        kmeans = self._run(self.voxel_se, n_clusters=self.n_clusters, reduction=reduction,
                           opt_normdata=opt_normdata, n_pca_components=n_pca_components)

        # label image
        self.label_image[self.region1] = kmeans.labels_ + 1
        self.label_vector = kmeans.labels_ + 1

        # find mean cluster curves
        for ii in range(self.n_clusters):
            c1 = self.voxel_se[self.label_vector == ii + 1]
            self.cluster_centers_[ii, :] = c1.mean(axis=0)

        # Function just left as inpiration for how to map colors
        # Mapping plot colors to rgba
        # map1 = plt.cm.ScalarMappable(cmap=plt.cm.jet)
        # clrs1 = map1.to_rgba(range(0, int(self.label_image.max()) + 1))

    def get_label_image(self):
        """
        Returns the label centres and mean enhancement curves of clusters
        @return: label_image:
                cluster_centers_:
        """
        return self.label_image, self.cluster_centers_

    @staticmethod
    def _run(voxel_se, n_clusters=4, reduction='pca', opt_normdata=1, n_pca_components=5):
        """
        kmeans clustering

        @param reduction: choice between using and not using dimensionality reduction
        @return:
        """

        print("Timing...")
        start1 = time.time()

        if reduction is 'none':

            kmeans = cl.KMeans(init='k-means++', n_clusters=n_clusters, n_init=10, n_jobs=self.n_jobs)
            kmeans.fit(voxel_se)
            # self.cluster_centers_ = kmeans.cluster_centers_

        else:
            print("Using PCA dimensionality reduction")
            pca = PCA(n_components=n_pca_components)
            reduced_data = pca.fit_transform(voxel_se)

            if opt_normdata == 1:
                print("Normalising PCA modes")
                min1 = np.min(reduced_data, axis=0)
                reduced_data = reduced_data - np.tile(np.expand_dims(min1, axis=0),
                                                      (reduced_data.shape[0], 1))
                max1 = np.max(reduced_data, axis=0)
                reduced_data = reduced_data / np.tile(np.expand_dims(max1, axis=0),
                                                      (reduced_data.shape[0], 1))

            kmeans = cl.KMeans(init='k-means++', n_clusters=n_clusters, n_init=10, n_jobs=self.n_jobs)

            # kmeans = cl.AgglomerativeClustering(n_clusters=n_clusters)
            kmeans.fit(reduced_data)
            # converting the cluster centres back into the image feature space
            # self.cluster_centers_ = pca.inverse_transform(kmeans.cluster_centers_)

        print("Elapsed time: ", (time.time() - start1))

        return kmeans



