"""
Quantiphyse - Analysis processes for data simulation

Copyright (c) 2013-2018 University of Oxford
"""
import math

import numpy as np
import scipy.ndimage.interpolation

from quantiphyse.data import DataGrid
from quantiphyse.utils import QpException
from quantiphyse.processes import Process

class AddNoiseProcess(Process):
    """
    Simple process for adding gaussian noise
    """
    PROCESS_NAME = "AddNoise"

    def __init__(self, ivm, **kwargs):
        Process.__init__(self, ivm, **kwargs)

    def run(self, options):
        data = self.get_data(options)

        output_name = options.pop("output-name", "%s_noisy" % data.name)
        std = float(options.pop("std"))

        noise = np.random.normal(loc=0, scale=std, size=list(data.grid.shape) + [data.nvols,])
        if data.nvols == 1: 
            noise = np.squeeze(noise, -1)
        noisy_data = data.raw() + noise
        self.ivm.add(noisy_data, grid=data.grid, name=output_name, make_current=True)

class SimMotionProcess(Process):
    """
    Simple process for adding gaussian noise
    """
    PROCESS_NAME = "SimMotion"

    def __init__(self, ivm, **kwargs):
        Process.__init__(self, ivm, **kwargs)

    def run(self, options):
        data = self.get_data(options)
        if data.ndim != 4:
            raise QpException("Can only simulate motion on 4D data")

        output_name = options.pop("output-name", "%s_moving" % data.name)
        std = float(options.pop("std"))
        std_voxels = [std / size for size in data.grid.spacing]
        output_grid = data.grid
        output_shape = data.grid.shape
            
        padding = options.pop("padding", 0)
        if padding > 0:
            padding_voxels = [int(math.ceil(padding / size)) for size in data.grid.spacing]
            # Need to adjust the origin so the output data lines up with the input
            output_origin = np.copy(data.grid.origin)
            output_shape = np.copy(data.grid.shape)
            output_affine = np.copy(data.grid.affine)
            for axis in range(3):
                output_origin[axis] -= np.dot(padding_voxels, data.grid.transform[axis, :])
                output_shape[axis] += 2*padding_voxels[axis]
            output_affine[:3, 3] = output_origin
            output_grid = DataGrid(output_shape, output_affine)

        moving_data = np.zeros(list(output_shape) + [data.nvols,])
        for vol in range(data.nvols):
            voldata = data.volume(vol)
            if padding > 0:
                voldata = np.pad(voldata, [(v, v) for v in padding_voxels], 'constant', constant_values=0) 
            shift = np.random.normal(scale=std_voxels, size=3)
            shifted_data = scipy.ndimage.interpolation.shift(voldata, shift)
            moving_data[..., vol] = shifted_data

        self.ivm.add(moving_data, grid=output_grid, name=output_name, make_current=True)
