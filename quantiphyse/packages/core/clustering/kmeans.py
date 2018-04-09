"""
Quantiphyse - Analysis processes for Kmeans clustering

Copyright (c) 2013-2018 University of Oxford
"""

from __future__ import division, print_function, absolute_import

import time
import numpy as np
import sklearn.cluster as cl
from sklearn.decomposition import PCA

from quantiphyse.volumes.load_save import NumpyData
from quantiphyse.analysis import Process
from quantiphyse.utils.exceptions import QpException

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
        self.log = ""
        start1 = time.time()

        if data.nvols > 1:
            # Do PCA reduction
            norm_data = options.pop('norm-data', True)
            n_pca = options.pop('n-pca', 5)
            reduction = options.pop('reduction', 'pca')

            # Normalisation: The first 3 volumes (if present) are averaged to give the baseline
            baseline = np.mean(data.raw()[:, :, :, :min(3, data.nvols)], axis=-1)
            baseline_4d = np.expand_dims(baseline[mask], axis=-1)
            kmeans_data = kmeans_data / (baseline_4d + 0.001) - 1

            if reduction == "pca":
                self.log += "Using PCA dimensionality reduction"
                pca = PCA(n_components=n_pca)
                kmeans_data = pca.fit_transform(kmeans_data)

                if norm_data:
                    self.log += "Normalising PCA modes"
                    min1 = np.min(kmeans_data, axis=0)
                    kmeans_data = kmeans_data - np.tile(np.expand_dims(min1, axis=0),
                                                        (kmeans_data.shape[0], 1))
                    max1 = np.max(kmeans_data, axis=0)
                    kmeans_data = kmeans_data / np.tile(np.expand_dims(max1, axis=0),
                                                        (kmeans_data.shape[0], 1))
        else:
            kmeans_data = kmeans_data[:, np.newaxis]

        kmeans = cl.KMeans(init='k-means++', n_clusters=n_clusters, n_init=10, n_jobs=1)
        kmeans.fit(kmeans_data)
        
        self.log += "Elapsed time: %s" % (time.time() - start1)

        label_image = np.zeros(data.grid.shape, dtype=np.int)
        label_image[mask] = kmeans.labels_ + 1
        self.ivm.add_roi(NumpyData(label_image, grid=data.grid, name=output_name), make_current=True)

        self.status = Process.SUCCEEDED
