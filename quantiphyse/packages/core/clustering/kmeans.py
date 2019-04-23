"""
Quantiphyse - Analysis processes for Kmeans clustering

Copyright (c) 2013-2018 University of Oxford
"""

from __future__ import division, print_function, absolute_import

import time
import numpy as np
import sklearn.cluster as cl

from quantiphyse.data import NumpyData
from quantiphyse.processes import Process, normalisation, PCA
from quantiphyse.utils import QpException

class KMeansProcess(Process):
    """
    Clustering for a 4D volume
    """

    PROCESS_NAME = "KMeans"

    def __init__(self, ivm, **kwargs):
        Process.__init__(self, ivm, **kwargs)

    def run(self, options):
        data = self.get_data(options)
        roi = self.get_roi(options, data.grid)
        n_clusters = options.pop('n-clusters', 5)
        invert_roi = options.pop('invert-roi', False)
        output_name = options.pop('output-name', data.name + '_clusters')
        
        kmeans_data, mask = data.mask(roi, invert=invert_roi, output_flat=True, output_mask=True)
        start1 = time.time()

        if data.nvols > 1:
            # Do PCA reduction
            norm_data = options.pop('norm-data', True)
            norm_type = options.pop('norm-type', "sigenh")
            n_pca = options.pop('n-pca', 5)
            reduction = options.pop('reduction', 'pca')

            if reduction == "pca":
                self.log("Using PCA dimensionality reduction")
                pca = PCA(n_components=n_pca, norm_input=True, norm_type=norm_type,
                          norm_modes=norm_data)
                kmeans_data = pca.get_training_features(kmeans_data)
            else:
                raise QpException("Unknown reduction method: %s" % reduction)
        else:
            kmeans_data = kmeans_data[:, np.newaxis]

        kmeans = cl.KMeans(init='k-means++', n_clusters=n_clusters, n_init=10, n_jobs=1)
        kmeans.fit(kmeans_data)
        
        self.log("Elapsed time: %s" % (time.time() - start1))

        label_image = np.zeros(data.grid.shape, dtype=np.int)
        label_image[mask] = kmeans.labels_ + 1
        self.ivm.add(NumpyData(label_image, grid=data.grid, name=output_name, roi=True), make_current=True)

class MeanValuesProcess(Process):
    """
    Create new data set by replacing voxel values with mean within each ROI region
    """
    PROCESS_NAME = "MeanValues"
    
    def __init__(self, ivm, **kwargs):
        Process.__init__(self, ivm, **kwargs)

    def run(self, options):
        data = self.get_data(options)
        roi = self.get_roi(options, data.grid)
        output_name = options.pop('output-name', data.name + "_means")

        in_data = data.raw()
        out_data = np.zeros(in_data.shape)
        for region in roi.regions:
            if data.ndim > 3:
                out_data[roi.raw() == region] = np.mean(in_data[roi.raw() == region], axis=0)
            else:
                out_data[roi.raw() == region] = np.mean(in_data[roi.raw() == region])

        self.ivm.add(NumpyData(out_data, grid=data.grid, name=output_name), make_current=True)
