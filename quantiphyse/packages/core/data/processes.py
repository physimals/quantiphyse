"""
Quantiphyse - Processes for the data manipulation package

Copyright (c) 2013-2018 University of Oxford
"""

import numpy as np
import scipy.ndimage

from quantiphyse.data import NumpyData, DataGrid
from quantiphyse.utils import QpException
from quantiphyse.processes import Process

class ResampleProcess(Process):
    """ 
    Resample data 
    """

    PROCESS_NAME = "Resample"
    
    def run(self, options):
        data = self.get_data(options)
        if data.roi: 
            default_order=0
        else:
            default_order=1
        order = options.pop("order", default_order)
        resample_type = options.pop("type", "data")
        output_name = options.pop("output-name", "%s_res" % data.name)
        grid_data = options.pop("grid", None)
        factor = options.pop("factor", None)
        only2d = options.pop("2d", None)

        # The different types of resampling require significantly different strategies
        #
        # Data->Data resampling is implemented in the QpData class although this will give
        # results which are not ideal when resampling to a lower resolution.
        # Upsampling can use scipy.ndimage.zoom
        # Downsampling is nore naturally implemented as a mean over subvoxels using Numpy slicing
        #
        # Note that factor is an integer for now. It could easily be a float for upsampling but
        # this would break the downsampling algorithm (and make it significanlty more complex to
        # implement)
        #
        # This is all pretty messy now especially with the '2d only' option.
        if resample_type == "data":
            if grid_data is None:
                raise QpException("Must provide 'grid' option to specify data item to get target grid from")
            elif grid_data not in self.ivm.data:
                raise QpException("Data item '%s' not found" % grid_data)
            
            grid = self.ivm.data[grid_data].grid
            output_data = data.resample(grid, order=order)
        elif resample_type == "up":
            # Upsampling will need to use interpolation
            orig_data = data.raw()
            zooms = [factor for idx in range(3)]
            if only2d:
                zooms[2] = 1
            if data.ndim == 4:
                zooms.append(1)
            output_data = scipy.ndimage.zoom(orig_data, zooms, order=order)

            # Work out new grid origin
            voxel_offset = [float(factor-1)/(2*factor) for idx in range(3)]
            if only2d:
                voxel_offset[2] = 0
            offset = data.grid.grid_to_world(voxel_offset, direction=True)
            output_affine = np.array(data.grid.affine)
            for idx in range(3):
                if idx < 2 or not only2d:
                    output_affine[:3, idx] /= factor
            output_affine[:3, 3] -= offset

            output_grid = DataGrid(output_data.shape[:3], output_affine)
            output_data = NumpyData(output_data, grid=output_grid, name=output_name)
        elif resample_type == "down":
            # Downsampling takes a mean of the voxels inside the new larger voxel
            # Only uses integral factor at present
            orig_data = data.raw()
            new_shape = [max(1, int(dim_size / factor)) for  dim_size in orig_data.shape[:3]]
            if data.ndim == 4:
                new_shape.append(orig_data.shape[3])
            if only2d:
                new_shape[2] = orig_data.shape[2]

            # Note that output data must be float data type even if original data was integer
            output_data = np.zeros(new_shape, dtype=np.float32)
            num_samples = 0
            for start1 in range(factor):
                for start2 in range(factor):
                    for start3 in range(factor):
                        if start1 >= new_shape[0]*factor or start2 >= new_shape[1]*factor or start3 >= new_shape[2]*factor:
                            continue
                        slices = [
                            slice(start1, new_shape[0]*factor, factor),
                            slice(start2, new_shape[1]*factor, factor),
                            slice(start3, new_shape[2]*factor, factor),
                        ]
                        if only2d:
                            slices[2] = slice(None)
                        downsampled_data=orig_data[slices]
                        output_data += downsampled_data
                        num_samples += 1
            output_data /= num_samples
            # FIXME this will not work for 2D data
            voxel_offset = [0.5*(factor-1), 0.5*(factor-1), 0.5*(factor-1)]
            if only2d:
                voxel_offset[2] = 0
            offset = data.grid.grid_to_world(voxel_offset, direction=True)
            output_affine = np.array(data.grid.affine)
            for idx in range(3):
                if idx < 2 or not only2d:
                    output_affine[:3, idx] *= factor
            output_affine[:3, 3] += offset

            output_grid = DataGrid(output_data.shape[:3], output_affine)
            output_data = NumpyData(output_data, grid=output_grid, name=output_name)
        else:
            raise QpException("Unknown resampling type: %s" % resample_type)

        self.ivm.add(output_data, name=output_name, make_current=True, roi=data.roi and order == 0)
