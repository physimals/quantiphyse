"""
Quantiphyse - Analysis processes for data simulation

Copyright (c) 2013-2020 University of Oxford

Licensed under the Apache License, Version 2.0 (the "License");
you may not use this file except in compliance with the License.
You may obtain a copy of the License at

    http://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and
limitations under the License.
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
        if "std" in options:
            std = float(options.pop("std"))
        elif "percent" in options:
            percent = float(options.pop("percent"))
            std = np.mean(data.raw()) * float(percent) / 100
        elif "snr" in options:
            snr = float(options.pop("snr"))
            roi = self.get_roi(options, grid=data.grid)
            mode = options.pop("mode", "normal")
            if mode == "normal":
                signal = np.mean(data.raw()[roi.raw() > 0])
            elif mode == "diff":
                # Slightly hacky mode to support ASL data - define signal as
                # mean absolute value of pairwise subtracted time series
                # (abs means don't need to distinguish between TC and CT)
                # This mode is not exposed in the UI but is used in the
                # data simulation widget
                timeseries = data.raw()[roi.raw() > 0]
                diff = np.abs(timeseries[..., ::2] - timeseries[..., 1::2])
                signal = np.mean(diff)
            else:
                raise QpException("Unsupported noise mode: %s" % mode)

            std = signal / snr
        else:
            raise QpException("AddNoiseProcess: Must specify either std, percent or snr")

        self.debug("Adding noise with std=%s", std)
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
        std = float(options.pop("std", "0"))
        std_voxels = [std / size for size in data.grid.spacing]
        std_degrees = float(options.pop("std_rot", "0"))
        order = int(options.pop("order", "1"))
        output_grid = data.grid
        output_shape = data.grid.shape
            
        padding = options.pop("padding", 0)
        if padding > 0:
            padding_voxels = [int(math.ceil(padding / size)) for size in data.grid.spacing]
            for dim in range(3):
                if data.shape[dim] == 1:
                    padding_voxels[dim] = 0
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
        centre_offset = output_shape / 2
        for vol in range(data.nvols):
            voldata = data.volume(vol)
            if padding > 0:
                voldata = np.pad(voldata, [(v, v) for v in padding_voxels], 'constant', constant_values=0) 
            shift = np.random.normal(scale=std_voxels, size=3)
            for dim in range(3):
                if voldata.shape[dim] == 1:
                    shift[dim] = 0
            shifted_data = scipy.ndimage.shift(voldata, shift, order=order)

            # Generate random rotation and scale it to the random angle
            required_angle = np.random.normal(scale=std_degrees, size=1)
            rot = scipy.spatial.transform.Rotation.random().as_rotvec()
            rot_angle = np.degrees(np.sqrt(np.sum(np.square(rot))))
            rot *= required_angle / rot_angle
            rot_matrix = scipy.spatial.transform.Rotation.from_rotvec(rot).as_matrix()

            offset=centre_offset-centre_offset.dot(rot_matrix)
            rotated_data = scipy.ndimage.affine_transform(shifted_data, rot_matrix.T, offset=offset, order=order)
            moving_data[..., vol] = rotated_data

        self.ivm.add(moving_data, grid=output_grid, name=output_name, make_current=True)
