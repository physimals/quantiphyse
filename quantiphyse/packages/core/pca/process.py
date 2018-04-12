"""
Quantiphyse - PCA reduction process

Copyright (c) 2013-2018 University of Oxford
"""
import numpy as np

from quantiphyse.utils import QpException
from quantiphyse.processes import Process
from quantiphyse.processes.feat_pca import PcaFeatReduce

class PcaProcess(Process):
    """
    Process to do PCA (Principal Component Analysis) reduction on 4D data
    """
    PROCESS_NAME = "PCA"

    def __init__(self, ivm, **kwargs):
        Process.__init__(self, ivm, **kwargs)

    def run(self, options):
        data = self.get_data(options)
        roi = self.get_roi(options, data.grid)
        output_name = options.pop("output-name", "%s_pca" % data.name)
        norm_input = options.pop('norm-input', True)
        norm_output = options.pop('norm-output', False)
        n_components = options.pop('n-components', 5)

        if data.ndim != 4:
            raise QpException("PCA reduction possible on 4D data only")
        elif data.nvols <= n_components:
            raise QpException("Number of PCA components must be less than number of data volumes")

        img, mask = data.raw(), roi.raw()
        if norm_input:
            # Normalisation: The first 3 volumes (if present) are averaged to give the baseline
            baseline = np.mean(img[:, :, :, :min(3, data.nvols)], axis=-1)
            baseline_4d = np.expand_dims(baseline, axis=-1)
            img = img / (baseline_4d + 0.001) - 1

        pca = PcaFeatReduce(n_components=n_components, norm_modes=norm_output)
        feature_images = pca.get_training_features(img, mask, feature_volume=True)
        debug("PCA explained variance")
        debug(pca.explained_variance())

        for comp_idx in range(n_components):
            name = "%s%i" % (output_name, comp_idx)
            self.ivm.add_data(feature_images[:, :, :, comp_idx], grid=data.grid, name=name)

        self.status = Process.SUCCEEDED
