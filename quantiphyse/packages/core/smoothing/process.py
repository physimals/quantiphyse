"""
Quantiphyse - Analysis processes for data smoothing

Copyright (c) 2013-2018 University of Oxford
"""

import scipy.ndimage.filters

from quantiphyse.processes import Process
from quantiphyse.data import NumpyData

class SmoothingProcess(Process):
    """
    Simple process for Gaussian smoothing
    """
    PROCESS_NAME = "Smooth"

    def __init__(self, ivm, **kwargs):
        Process.__init__(self, ivm, **kwargs)

    def run(self, options):
        data = self.get_data(options)

        output_name = options.pop("output-name", "%s_smoothed" % data.name)
        #kernel = options.pop("kernel", "gaussian")
        order = options.pop("order", 0)
        mode = options.pop("boundary-mode", "reflect")
        sigma = options.pop("sigma", 1.0)

        # Sigma is in mm so scale with data voxel sizes
        if isinstance(sigma, (int, float)):
            sigmas = [float(sigma) / size for size in data.grid.spacing]
        else:
            sigmas = [float(sig) / size for sig, size in zip(sigma, data.grid.spacing)]

        # Smooth multiple volumes independently
        if data.nvols > 1:
            sigmas += [0, ]

        output = scipy.ndimage.filters.gaussian_filter(data.raw(), sigmas, order=order, mode=mode)
        self.ivm.add(NumpyData(output, grid=data.grid, name=output_name), make_current=True)
