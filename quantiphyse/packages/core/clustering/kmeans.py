"""
Quantiphyse - Analysis processes for Kmeans clustering

Copyright (c) 2013-2018 University of Oxford
"""

from __future__ import division, print_function, absolute_import

import sys
import time
import numpy as np
import sklearn.cluster as cl
from sklearn.decomposition import PCA

from quantiphyse.analysis import Process
from quantiphyse.utils.exceptions import QpException

class KMeansPCAProcess(Process):
    """
    Clustering for a 4D volume
    """

    PROCESS_NAME = "KMeansPCA"

    def __init__(self, ivm, **kwargs):
        Process.__init__(self, ivm, **kwargs)

    def run(self, options):
        n_clusters = options.pop('n-clusters', 5)
        norm_data = options.pop('norm-data', True)
        n_pca = options.pop('n-pca', 5)
        reduction = options.pop('reduction', 'pca')
        invert_roi = options.pop('invert-roi', False)
        output_name = options.pop('output-name', 'clusters')
        data_name = options.pop('data', None)
        roi_name = options.pop('roi', None)
        
        # 4D data
        if data_name is not None:
            data = self.ivm.data[data_name]
        elif self.ivm.main is not None:
            data = self.ivm.main
        else:
            raise QpException("No data specified and no current volume")

        if data.nvols < 2:
            raise QpException("Can only run PCA clustering on 4D data - '%s' is 3D" % data_name)
            
        # ROI to process
        roi = None
        if roi_name is not None:
            roi = self.ivm.rois.get(roi_name, None)
        elif self.ivm.current_roi is not None:
            roi = self.ivm.current_roi
        else:
            invert_roi = False

        # Normalisation of the image. The first 3 volumes (if present) are averaged to 
        # give the baseline
        voxel_se, mask = data.mask(roi, invert=invert_roi, flat=True, mask=True)
        img = data.raw().astype(np.float32)
        baseline1 = np.mean(img[:, :, :, :min(3, img.shape[3])], axis=-1)
        baseline1sub = np.expand_dims(baseline1, axis=-1)[mask]
        voxel_se = voxel_se / (np.tile(baseline1sub, (1, img.shape[-1])) + 0.001) - 1

        # Outputs
        self.log = ""
        start1 = time.time()

        if reduction == 'none':
            kmeans = cl.KMeans(init='k-means++', n_clusters=n_clusters, n_init=10, n_jobs=1)
            kmeans.fit(voxel_se)
            # self.cluster_centers_ = kmeans.cluster_centers_
        else:
            self.log += "Using PCA dimensionality reduction"
            pca = PCA(n_components=n_pca)
            print(voxel_se.shape)
            reduced_data = pca.fit_transform(voxel_se)

            if norm_data:
                self.log += "Normalising PCA modes"
                min1 = np.min(reduced_data, axis=0)
                reduced_data = reduced_data - np.tile(np.expand_dims(min1, axis=0),
                                                      (reduced_data.shape[0], 1))
                max1 = np.max(reduced_data, axis=0)
                reduced_data = reduced_data / np.tile(np.expand_dims(max1, axis=0),
                                                      (reduced_data.shape[0], 1))

            kmeans = cl.KMeans(init='k-means++', n_clusters=n_clusters, n_init=10, n_jobs=1)

            # kmeans = cl.AgglomerativeClustering(n_clusters=n_clusters)
            kmeans.fit(reduced_data)
            # converting the cluster centres back into the image feature space
            # self.cluster_centers_ = pca.inverse_transform(kmeans.cluster_centers_)

        self.log += "Elapsed time: %s" % (time.time() - start1)

        label_image = np.zeros(img.shape[:3])
        label_image[mask] = kmeans.labels_ + 1
        self.ivm.add_roi(NumpyData(label_image, grid=data.grid, name=output_name), make_current=True)
        self.ivm.add_roi(label_image, name=output_name, make_current=True)

        self.status = Process.SUCCEEDED

class KMeans3DProcess(Process):
    """
    Clustering process for 3D data
    """

    PROCESS_NAME = "KMeans3D"
    
    def __init__(self, ivm, **kwargs):
        Process.__init__(self, ivm, **kwargs)

    def run(self, options):
        n_clusters = options.pop('n-clusters', 5)
        invert_roi = options.pop('invert-roi', False)
        output_name = options.pop('output-name', 'clusters')
        data_name = options.pop('data', None)
        roi_name = options.pop('roi', None)
        
        # 3D data
        if data_name is not None:
            data = self.ivm.data[data_name]
        elif self.ivm.main is not None:
            data = self.ivm.main
        else:
            raise QpException("No data specified and no current volume")

        if data.nvols > 1:
            raise QpException("Can only run PCA clustering on 3D data - '%s' is 4D" % data_name)
            
        # ROI to use
        roi = None
        if roi_name is not None:
            roi = self.ivm.rois.get(roi_name, None)
        elif self.ivm.current_roi is not None:
            roi = self.ivm.current_roi
        else:
            invert_roi = False

        # Get unmasked data and cluster
        voxel_se, mask = data.mask(roi, invert=invert_roi, flat=True, mask=True)
        voxel_se = voxel_se[:, np.newaxis]
        kmeans = cl.KMeans(init='k-means++', n_clusters=n_clusters, n_init=10, n_jobs=1)
        kmeans.fit(voxel_se)

        # label regions
        label_image = np.zeros(data.shape, dtype=np.int)
        roi_data = roi.resample(data.grid)
        label_image[roi_data.raw() > 0] = kmeans.labels_ + 1
        self.ivm.add_roi(NumpyData(label_image, grid=data.grid, name=output_name), make_current=True)
        
        self.status = Process.SUCCEEDED
