"""
Quantiphyse - PCA reduction process

Copyright (c) 2013-2018 University of Oxford
"""
import numpy as np

from quantiphyse.data.extras import MatrixExtra
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
        self.explained_variance = []
        self.pca_modes = []
        self.mean = [0,]

    def run(self, options):
        data = self.get_data(options)
        roi = self.get_roi(options, data.grid)
        output_name = options.pop("output-name", "%s_pca" % data.name)
        norm_input = options.pop('norm-input', True)
        norm_type = options.pop('norm-type', "sigenh")
        norm_output = options.pop('norm-output', False)
        n_components = options.pop('n-components', 5)

        if data.ndim != 4:
            raise QpException("PCA reduction possible on 4D data only")
        elif data.nvols <= n_components:
            raise QpException("Number of PCA components must be less than number of data volumes")

        pca = PcaFeatReduce(n_components=n_components, norm_input=norm_input, norm_type=norm_type, norm_modes=norm_output)
        
        feature_images = pca.get_training_features(data.raw(), roi.raw(), feature_volume=True)
        for comp_idx in range(n_components):
            name = "%s%i" % (output_name, comp_idx)
            self.ivm.add(feature_images[:, :, :, comp_idx], grid=data.grid, name=name, make_current=(comp_idx == 0))

        #if options.pop("reduced-data", True):
        #    reduced = pca.pca.inverse_transform(feature_images)
        #    self.ivm.add(reduced, grid=data.grid, name=name + "_reduced")

        cumulative = 0
        var_rows = []
        for idx, variance in enumerate(pca.explained_variance()):
            cumulative += variance
            var_rows.append([idx, variance, cumulative])
        extra = MatrixExtra(output_name + "_variance", var_rows, col_headers=["PCA mode", "Explained variance", "Cumulative"])
        self.ivm.add_extra(extra.name, extra)

        modes = np.zeros((len(pca.mean()), len(pca.modes()) + 1))
        cols = []
        for idx, mode in enumerate(pca.modes()):
            modes[:, idx] = mode
            cols.append("Mode %i" % idx)
        modes[:, -1] = pca.mean()
        cols.append("Mean")
        extra = MatrixExtra(output_name + "_modes", modes, col_headers=cols)
        self.ivm.add_extra(extra.name, extra)
