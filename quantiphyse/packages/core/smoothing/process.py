"""
Quantiphyse - Analysis processes for data smoothing

Copyright (c) 2013-2018 University of Oxford
"""

import scipy.ndimage.filters

from quantiphyse.utils import debug, warn, QpException
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
        data_name = options.pop("data", None)
        if data_name is None and self.ivm.current_data is None:
            raise QpException("No data found")
        elif data_name is None:
            data_name = self.ivm.current_data.name

        output_name = options.pop("output-name", "%s_smoothed" % data_name)
        kernel = options.pop("kernel", "gaussian")
        order = options.pop("order", 0)
        mode = options.pop("boundary-mode", "reflect")
        sigma = options.pop("sigma-list", None)
        if sigma is not None:
            sigma = sigma.replace(",", " ").split()
        else:
            sigma = options.pop("sigma", 1)
        
        data = self.ivm.data[data_name]
        output = scipy.ndimage.filters.gaussian_filter(data.raw(), sigma, order=order, mode=mode)
        self.ivm.add_data(NumpyData(output, grid=data.grid, name=output_name), make_current=True)

