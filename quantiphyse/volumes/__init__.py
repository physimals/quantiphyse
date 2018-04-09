"""
Quantiphyse - Basic volume data classes

Concepts:

 - All data is 3D or 4D. 2D (or 1D?) data must be expanded to 3D on load. There is provision
   for 3D data to be 'interpreted' as 2D multi-volume data (there are broken Nifti files
   around like this)
 - All data is defined on a ``DataGrid`` which consists of the data shape and an affine transform
   from grid co-ordinate space to world space.
 - The 4th dimension (multiple volumes) is not part of the grid and has no impact on orientation.
 - Data objects support arbitrary slicing in a plane defined by an normal axis and a position
   relative to another grid. The output of this slice is an array, a mask (zero where outside range
   of data, plus a 2D affine transformation to map the data onto the slice grid)
 - Data objects also support resampling onto a grid, as required for some analysis methods

Copyright (c) 2013-2018 University of Oxford
"""

import math
import warnings

import numpy as np
import scipy
import pyqtgraph as pg

from PySide import QtGui

from quantiphyse.utils import debug, sf
from quantiphyse.utils.exceptions import QpException

# Tolerance for treating values as equal
# Used to determine if matrices are diagonal or identity
EQ_TOL = 1e-3

class DataGrid(object):
    """
    Defines a regular 3D grid in some 'world' space

    :ivar affine: 4D affine matrix which describes the transformation from
                  grid co-ordinates to standard space co-ordinates
    :ivar origin: 3D origin of grid in world co-ordinates (last column of ``affine``)
    :ivar transform: 3x3 submatrix of ``affine`` used to transform directions to world space
    :ivar spacing: Sequence of length 3 giving spacing between voxels in world units
    :ivar nvoxels: Number of voxels in the grid

    A DataGrid is not formally immutable but are not designed to be modified
    """

    def __init__(self, shape, affine):
        """
        Create a DataGrid object

        :param shape: Sequence of 3 integers giving number of voxels along each axis
        :param affine: 4x4 affine transformation to world co-ordinates
        """
        # Dimensionality of the grid - 3D only
        if len(shape) != 3:
            raise RuntimeError("Grid shape must be 3D")
        self.shape = list(shape)[:]

        # 3D Affine transformation from grid-space to standard space
        # This is a 4x4 matrix - includes constant offset (origin)
        if len(affine.shape) != 2 or affine.shape[0] != 4 or affine.shape[1] != 4:
            raise RuntimeError("Grid affine must be 4x4 matrix")

        self.affine = np.copy(affine)
        self.origin = tuple(affine[:3, 3])
        self.transform = affine[:3, :3]
        self.inv_transform = np.linalg.inv(self.transform)

        self.spacing = [np.linalg.norm(self.affine[:, i]) for i in range(3)]
        self.nvoxels = 1
        for d in range(3):
            self.nvoxels *= shape[d]

    def grid_to_grid(self, coord, from_grid=None, to_grid=None):
        """
        Transform grid co-ordinates to another grid's co-ordinates

        :param coords: 3D or 4D grid co-ordinates. If 4D, last entry is returned unchanged
        :param from_grid: DataGrid the input co-ordinates are relative to. They will be returned
                     relative to this grid
        :param to_grid: DataGrid the input co-ordinates are to be transformed into. The input
                   co-ordinates are assumed to be relative to this grid
        :return: List containing 3D or 4D co-ordinates
        """
        if from_grid is not None and to_grid is None:
            to_grid = self
        elif from_grid is None and to_grid is not None:
            from_grid = self
        else:
            raise RuntimeError("Exactly one of from_grid and to_grid must be specified")
        
        world = from_grid.grid_to_world(coord)
        return to_grid.world_to_grid(world)

    def grid_to_world(self, coords):
        """
        Transform grid co-ordinates to world co-ordinates

        :param coords: 3D or 4D grid co-ordinates. If 4D, last entry is returned unchanged
        :return: List containing 3D or 4D world co-ordinates
        """
        vec = np.array(coords[:3])
        world_coords = np.dot(self.transform, vec) + np.array(self.origin)
        if len(coords) == 4:
            return list(world_coords) + [coords[3]]
        else:
            return list(world_coords)

    def world_to_grid(self, coords):
        """
        Transform world co-ordinates to grid co-ordinates

        :param coords: 3D world co-ordinates. If 4D, last entry is returned unchanged
        :return: List containing 3D or 4D grid co-ordinates
        """
        vec = list(coords[:3])
        grid_coords = np.dot(self.inv_transform, (vec - np.array(self.origin)))
        if len(coords) == 4:
            return list(grid_coords) + [coords[3]]
        else:
            return list(grid_coords)

    def get_standard(self):
        """
        Return a new grid in approximate RAS order, by axis transposition
        and flipping only

        The result is a grid which defines the same space as the original
        with the same voxel spacing but where the x axis is increasing
        left->right, the y axis increases posterior->anterior and the
        z axis increases inferior->superior.
        """
        # We make slightly botched use of the Transform class for this - this
        # hack shouldn't be necessary really
        rasgrid = DataGrid([1, 1, 1], np.identity(4))
        t = Transform(self, rasgrid)
        reorder, flip, tmatrix = t._simplify_transforms(t.tmatrix[t.OUT2IN])
        new_shape = [self.shape[d] for d in reorder]
        return DataGrid(new_shape, tmatrix)

    def get_ras_axes(self):
        """
        Get the grid axes which best correspond to the RAS axes

        :return: List of four integers giving the axes indices of the R, A and S axes.
                 The fourth integer is always 3 indicating the volume axis
        """
        ret = []
        origin_grid = self.world_to_grid([0, 0, 0])
        for idx in range(3):
            vec = [0, 0, 0]
            vec[idx] = 1
            vec_grid = [v - o for v, o in zip(self.world_to_grid(vec), origin_grid)]
            axis = np.argmax(np.abs(vec_grid))
            ret.append(axis)
        return ret + [3, ]

    def matches(self, grid):
        """
        Determine if another grid matches this one

        :param grid: DataGrid instance
        :return: True if ``grid`` is identical to this grid
        """
        return np.array_equal(self.affine, grid.affine) and  np.array_equal(self.shape, grid.shape)

class OrthoSlice(DataGrid):
    """
    DataGrid defined as a 2D orthogonal slice through another grid

    Has same attributes as :class:`DataGrid`, in addition:

    :ivar basis: Sequence of two 3D basis vectors for the plane in world co-ordinates
    :ivar normal: 3D normal vector to the plane in world co-ordinates
    """

    def __init__(self, grid, zaxis, pos):
        """
        Create an OrthoSlice by taking a slice through an existing grid

        :param grid: DataGrid instance
        :param zaxis: Which axis is the normal axis for the slice (0, 1 or 2)
        :param pos: Position along ``axis`` to take the slice, in grid co-ordinates
        """
        affine = np.zeros((4, 4))
        shape = [1, 1, 1]
        col = 0
        for ax in range(3):
            if ax != zaxis:
                affine[:, col] = grid.affine[:, ax]
                shape[col] = grid.shape[ax]
                col += 1
            else:
                affine[:, 2] = grid.affine[:, ax]
        affine[:, 3] = grid.affine[:, 3] + pos * affine[:, 2]
        DataGrid.__init__(self, shape, affine)
        self.basis = [tuple(self.transform[:, 0]), tuple(self.transform[:, 1])]
        self.normal = tuple(self.transform[:, 2])

class Transform(object):
    """
    Transforms data on one grid into another

    :ivar tmatrix: Sequence of 2 4x4 affine transformations. First is out grid->in grid, the second
                   in_grid -> out_grid. The constants ``OUT2IN`` and ``IN2OUT`` allow you to index
                   which you require (most methods default to using ``OUT2IN``)
    """

    OUT2IN = 0
    IN2OUT = 1

    def __init__(self, in_grid, out_grid):
        """
        Construct a transformation from one grid to another

        :param in_grid: Input grid
        :param out_grid: Output grid
        """
        #debug("Transforming from")
        #debug(in_grid.affine)
        #debug("To")
        #debug(out_grid.affine)

        self.grid = [out_grid, in_grid]
        self.tmatrix = [None, None]

        # Affine transformation matrix from grid 2 to grid 1
        self.tmatrix[self.OUT2IN] = np.dot(np.linalg.inv(out_grid.affine), in_grid.affine)
        # Affine transformation matrix from grid 1 to grid 2
        self.tmatrix[self.IN2OUT] = np.linalg.inv(self.tmatrix[self.OUT2IN])

    def transform_position(self, v, direction=OUT2IN):
        """
        Transform a 3D position

        :param v: 3D position vector
        :param direction: Transform.OUT2IN to transform output grid position to input grid.
                          Transform.IN2OUT for opposite
        :return Transformed 3D position vector
        """
        return self.tmatrix[direction].dot(list(v) + [1,])[:3]

    def transform_direction(self, v, direction=OUT2IN):
        """
        Transform a 3D direction (displacement vector). This does not make use of the grid origins

        :param v: 3D direction vector
        :param direction: Transform.OUT2IN to transform output grid position to input grid.
                          Transform.IN2OUT for opposite
        :return Transformed 3D direction vector
        """
        return self.tmatrix[direction][:3, :3].dot(v)

    def transform_data(self, data, direction=OUT2IN):
        """
        Transform 3D or 4D data from one grid to another

        :param data: 3D or 4D Numpy data
        :param direction: Transform.OUT2IN to transform output grid position to input grid.
                          Transform.IN2OUT for opposite
        :return Transformed 3D or 4D data
        """
        reorder, flip, tmatrix = self._simplify_transforms(self.tmatrix[direction])

        # Perform the flips and transpositions which simplify the transformation
        # and may avoid the need for an affine transformation or make it a simple
        # scaling
        if len(flip) != 0:
            #debug("Flipping axes: ", self.flip)
            for d in flip:
                data = np.flip(data, d)

        if reorder != range(3):
            if data.ndim == 4:
                reorder = reorder + [3]
            #debug("Re-ordering axes: ", reorder)
            data = np.transpose(data, reorder)

        if not self._is_identity(tmatrix):
            # We were not able to reduce the transformation down to flips/transpositions
            # so we will need an affine transformation

            # scipy requires the out->in transform so invert our in->out transform
            tmatrix = np.linalg.inv(tmatrix)
            affine = tmatrix[:3, :3]
            offset = list(tmatrix[:3, 3])
            output_shape = self.grid[direction].shape[:]
            if data.ndim == 4:
                # Make 4D affine with identity transform in 4th dimension
                affine = np.append(affine, [[0, 0, 0]], 0)
                affine = np.append(affine, [[0], [0], [0], [1]], 1)
                offset.append(0)
                output_shape.append(data.shape[3])

            if self._is_diagonal(affine):
                # The transformation is diagonal, so use this sequence instead of
                # the full matrix - this will be faster
                affine = np.diagonal(affine)
            else:
                pass
            #debug("WARNING: affine_transform: ")
            #debug(affine)
            #debug("Offset = ", offset)
            #debug("Input shape=", data.shape, data.min(), data.max())
            #debug("Output shape=", output_shape)
            data = scipy.ndimage.affine_transform(data, affine, offset=offset,
                                                  output_shape=output_shape, order=0)

        return data

    def _is_diagonal(self, mat):
        return np.all(np.abs(mat - np.diag(np.diag(mat))) < EQ_TOL)

    def _is_identity(self, mat):
        return np.all(np.abs(mat - np.identity(mat.shape[0])) < EQ_TOL)

    def _simplify_transforms(self, mat):
        # Convert the transformation into optional re-ordering and flipping
        # of axes and a final optional affine transformation
        # This enables us to use faster methods in the case where the
        # grids are essentially the same or scaled

        # Flip/transpose the axes to put the biggest numbers on
        # the diagonal and make negative diagonal elements positive
        dim_order, dim_flip = [], []

        absmat = np.absolute(mat)
        for d in range(3):
            newd = np.argmax(absmat[:, d])
            dim_order.append(newd)
            if mat[newd, d] < 0:
                dim_flip.append(newd)

        new_mat = np.copy(mat)
        if sorted(dim_order) == range(3):
            # The transposition was consistent, so use it
            debug("Before simplification")
            debug(new_mat)
            new_shape = [self.grid[self.OUT2IN].shape[d] for d in dim_order]
            for idx, d in enumerate(dim_order):
                new_mat[:, d] = mat[:, idx]
            debug("After transpose", dim_order)
            debug(new_mat)
            for dim in dim_flip:
                # Change signs to positive to flip a dimension
                new_mat[:, dim] = -new_mat[:, dim]
            debug("After flip", dim_flip)
            debug(new_mat)
            for dim in dim_flip:
                # Adjust origin
                new_mat[:3, 3] = new_mat[:3, 3] - new_mat[:3, dim] * (new_shape[dim]-1)

            debug("After adjust origin", new_shape)
            debug(new_mat)

            return dim_order, dim_flip, new_mat
        else:
            # Transposition was inconsistent, just go with general
            # affine transform - this will work but might be slow
            return range(3), [], new_mat

class QpData(object):
    """
    3D or 4D data

    Data is defined on a DataGrid instance which defines a uniform grid in standard space.

    :ivar name: Identifying name for the data the :class:`ImageVolumeManagement` class will
                require this to be a valid and Python variable name and unique within the IVM.
    :ivar grid: :class:`DataGrid` instance the data is defined on
    :ivar nvols: Number of volumes (1=3D data)
    :ivar ndim: 3 or 4 for 3D or 4D data
    :ivar fname: File name data came from if relevant
    :ivar dps: Number of decimal places to display data to
    :ivar raw_2dt: Whether raw data is 3D but being interpreted as 2D multi-volume
    :ivar range: Data range tuple (min, max)
    :ivar roi: True if this data represents a region of interest
    """

    def __init__(self, name, grid, nvols, fname=None, roi=False):
        # Everyone needs a friendly name
        self.name = name

        # Grid the data was defined on.
        self.grid = grid

        # Number of volumes (1=3D data)
        self.nvols = nvols
        if self.nvols == 1:
            self.ndim = 3
        else:
            self.ndim = 4

        # File it was loaded from, if relevant
        self.fname = fname

        # Number of decimal places to display data to
        self.dps = 1

        # Whether raw data is 2d + time incorrectly returned as 3D
        self.raw_2dt = False


        # Treat as an ROI data set if requested
        self.set_roi(roi)

    def raw(self):
        """
        Return the raw data as a Numpy array

        Instances should implement this method to get the data from file
        or internal storage
        """
        raise NotImplementedError("Internal Error: raw() has not been implemented.")

    def range(self, vol=None):
        """
        Return data max and min

        Note that obtaining the range of a large 4D data set may be expensive!

        :param vol: Index of volume to use, if not specified use whole data set
        :return: Tuple of min value, max value
        """ 
        if vol is None:
            return self.raw().min(), self.raw().max()
        else:
            voldata = self.volume(vol)
            return voldata.min(), voldata.max()
        
    def volume(self, vol):
        """
        Get the specified volume from a multi-volume data set

        The default implementation calls raw() to return all data. Implementations may override
        e.g. to only load the required volume.

        If the specified volume is out of range for this data, returns the last volume

        :param vol: Volume number (0=first)
        """
        rawdata = self.raw()
        if self.ndim == 4:
            rawdata = rawdata[:, :, :, min(vol, self.nvols-1)]
        return rawdata

    def value(self, pos, grid=None, str=False):
        """
        Return the data value at a point

        :param pos: Position as a 3D or 4D vector. If 4D last value is the volume index
                    (0 for 3D). If ``grid`` not specified, position is in world space
        :param grid: If specified, interpret position in this ``DataGrid`` co-ordinate space.
        :param str: If True, return value as string to appropriate number of decimal places.
        """
        if grid is None:
            grid = DataGrid([1, 1, 1], np.identity(4))

        trans = Transform(grid, self.grid)
        data_pos = [int(v+0.5) for v in trans.transform_position(pos[:3])]

        rawdata = self.volume(pos[3])
        try:
            value = rawdata[tuple(data_pos)]
        except IndexError:
            value = 0
        
        if str:
            return sf(value)
            #return str(np.around(value, self.dps))
        else:
            return value

    def timeseries(self, pos, grid=None):
        """
        Return the time/volume series at a point

        :param pos: Position as a 3D or 4D vector. If 4D last value is the volume index
                    (0 for 3D). If ``grid`` not specified, position is in world space
        :param grid: If specified, interpret position in this ``DataGrid`` co-ordinate space.
        :return: List of values, one for each volume. For 3D data, sequence has length 1.
        """
        if self.nvols == 1:
            return [self.value(pos, grid), ]

        if grid is None:
            grid = DataGrid([1, 1, 1], np.identity(4))
            
        trans = Transform(grid, self.grid)
        data_pos = [int(v+0.5) for v in trans.transform_position(pos[:3])]

        rawdata = self.raw()
        try:
            return list(rawdata[data_pos[0], data_pos[1], data_pos[2], :])
        except IndexError:
            return []

    def mask(self, roi, region=None, vol=None, invert=False, output_flat=False, output_mask=False):
        """
        Mask the data

        :param roi: ROI data item If None, return all data
        :param region: If specified, return data within this region. Otherwise return 
                       data within any ROI region.
        :param vol: If specified, restrict output to this volume index
        :param invert: If True, invert the mask
        :param flat: If True, return unmasked data only as flattened arrray
        :param mask: If True, return boolean mask in same grid space as data
        :return If ``flat``, 1-D Numpy array containing unmasked data. Otherwise, Numpy array
                containing data with masked points zeroed. If ``mask`` also return
                a boolean mask in the same grid space as the data.
        """
        ret = []
        if vol is not None:
            data = self.vol(vol)
        else:
            data = self.raw()
        
        if roi is None:
            if output_flat:
                ret.append(data.flatten())
            else:
                ret.append(data)
            if output_mask:
                ret.append(np.ones(data.shape[:3], dtype=np.int))
        else:
            roi = roi.resample(self.grid)
            if region is None:
                mask = roi.raw() > 0
            else:
                mask = roi.raw() == region
            if invert:
                mask = np.logical_not(mask)
            
            if output_flat:
                ret.append(data[mask])
            else:
                masked = np.zeros(data.shape)
                masked[mask] = data[mask]
                ret.append(masked)
            if output_mask: 
                ret.append(mask)

        if len(ret) > 1:
            return tuple(ret)
        else:
            return ret[0]
        
    def resample(self, grid):
        """
        Resample the data onto a new grid

        :param grid: :class:`DataGrid` to resample the data on to
        :return: New :class:`QpData` object
        """
        t = Transform(self.grid, grid)
        rawdata = self.raw()
        if rawdata.ndim not in (3, 4):
            raise RuntimeError("Data must be 3D or 4D (padded if necessary")
        regridded_data = t.transform_data(rawdata)
        self._remove_nans(regridded_data)

        if self.roi:
            if regridded_data.min() < 0 or regridded_data.max() > 2**32:
                raise QpException("ROIs must contain values between 0 and 2**32")
            if not np.equal(np.mod(regridded_data, 1), 0).any():
                raise QpException("ROIs must contain integers only")
            regridded_data = regridded_data.astype(np.int32)

        from quantiphyse.volumes.load_save import NumpyData
        return NumpyData(data=regridded_data, grid=grid, name=self.name + "_resampled", roi=self.roi)

    def slice_data(self, plane, vol=0):
        """
        Extract a data slice in raw data resolution

        :param plane: OrthoSlice representing the slice to be extracted. Note that this
                      slice will not in general be defined on the same grid as the data
        :param vol: volume index for use if this is a 4D data set
        """
        rawdata = self.volume(vol)

        #debug("OrthoSlice: plane origin: %s" % str(plane.origin))
        #debug("OrthoSlice: plane v1: %s" % str(plane.basis[0]))
        #debug("OrthoSlice: plane v2: %s" % str(plane.basis[1]))
        #debug("OrthoSlice: plane n: %s" % str(plane.normal))

        trans = Transform(plane, self.grid)
        data_origin = trans.transform_position((0, 0, 0))
        data_normal = trans.transform_direction((0, 0, 1))
        data_naxis = np.argmax(np.absolute(data_normal))

        #debug("OrthoSlice: data origin: %s" % str(data_origin))
        #debug("OrthoSlice: data n: %s" % str(data_normal))
        #debug("OrthoSlice: data naxis: %i" % data_naxis)

        data_axes = range(3)
        del data_axes[data_naxis]
        slice_basis, slice_shape = [], []
        for ax in data_axes:
            vec = [0, 0, 0]
            vec[ax] = 1
            vec[data_naxis] = -(data_normal[ax] / data_normal[data_naxis])
            slice_basis.append(vec)
            slice_shape.append(rawdata.shape[ax])

        #debug("OrthoSlice: data b: %s (shape=%s)" % (str(slice_basis), str(slice_shape)))
        trans2 = Transform(self.grid, plane)
        trans_v = np.array([
            trans2.transform_direction(slice_basis[0]),
            trans2.transform_direction(slice_basis[1])
        ])
        trans_v = np.delete(trans_v, 2, 1)
        #debug("OrthoSlice: trans matrix: %s" % (str(trans_v)))
        slice_origin = [0, 0, 0]
        slice_origin[data_naxis] = np.dot(data_origin, data_normal) / data_normal[data_naxis]
        data_offset = data_origin - slice_origin + 0.5
        #debug("OrthoSlice: new origin: %s (offset=%s)" % (str(slice_origin), str(data_offset)))
        offset = -trans2.transform_direction(data_offset)[:2]
        #debug("OrthoSlice: new plane offset: %s" % (str(offset)))

        ax1, sign1 = self._is_ortho_vector(slice_basis[0])
        ax2, sign2 = self._is_ortho_vector(slice_basis[1])
        if ax1 is not None and ax2 is not None:
            slices = [None, None, None]
            slices[ax1] = self._get_slice(ax1, rawdata.shape[ax1], sign1)
            slices[ax2] = self._get_slice(ax2, rawdata.shape[ax2], sign2)

            pos = int(data_origin[data_naxis]+0.5)
            if pos >= 0 and pos < rawdata.shape[data_naxis]:
                slices[data_naxis] = pos
                debug("Using Numpy slice: ", slices, rawdata.shape)
                sdata = rawdata[slices]
                smask = np.ones(slice_shape)
            else:
                # Requested slice is outside the data range
                debug("Outside data range: %i, %i" % (pos, rawdata.shape[data_naxis]))
                sdata = np.zeros(slice_shape)
                smask = np.zeros(slice_shape)
        else:
            debug("Full affine slice")
            sdata = pg.affineSlice(rawdata, slice_shape, slice_origin, slice_basis, range(3))
            mask = np.ones(rawdata.shape)
            smask = pg.affineSlice(mask, slice_shape, data_origin, slice_basis, range(3))

        #debug(data_naxis, sdata)
        return sdata, trans_v, offset

    def _get_slice(self, axis, length, sign):
        if sign == 1:
            return slice(0, length, 1)
        else:
            return slice(length-1, None, -1)

    def _is_ortho_vector(self, vec):
        mod = np.linalg.norm(vec)
        for ax, v in enumerate(vec):
            if abs(abs(v/mod)-1) < EQ_TOL:
                return ax, math.copysign(1, v)
        return None, None

    def set_2dt(self):
        """
        Force 3D static data into the form of 2D multi-volume

        This is useful for some broken NIFTI files. Note that the 3D extent of the grid
        is completely ignored. In order to work, the underlying class must implement the
        change in raw().
        """
        if self.nvols != 1 or self.grid.shape[2] == 1:
            raise RuntimeError("Can only force to 2D timeseries if data was originally 3D static")

        self.raw_2dt = True
        self.nvols = self.grid.shape[2]
        self.ndim = 4

        # The grid transform can't be properly interpreted because basically the file is broken,
        # so just make it 2D and hope the remaining transform is sensible
        self.grid.shape[2] = 1

    def set_roi(self, roi):
        """
        Set whether data should be interpreted as a region of interest

        :param roi: If True, interpret as roi
        """
        self.roi = roi
        if self.roi:
            if self.nvols != 1:
                raise RuntimeError("ROIs must be static (single volume) 3D data")
            self.regions = np.unique(self.raw())
            self.regions = [int(r) for r in self.regions if r > 0]

    def get_bounding_box(self, ndim=3):
        """
        Returns a sequence of slice objects which
        describe the bounding box of this ROI.
        If ndim is specified, will return a bounding
        box of this number of dimensions, truncating
        and appending slices as required.

        This enables data to be
        easily restricted to the ROI region and
        reduce data copying.

        e.g.
        slices = roi.get_bounding_box(img.ndim)
        img_restric = data[slices]
        ... process img_restict, returning out_restrict
        out_full = np.zeros(img.shape)
        out_full[slices] = out_restrict
        """
        if not self.roi:
            raise RuntimeError("get_bounding_box() called on non-ROI data")

        slices = [slice(None)] * ndim
        for d in range(min(ndim, 3)):
            ax = [i for i in range(3) if i != d]
            nonzero = np.any(self.raw(), axis=tuple(ax))
            s1, s2 = np.where(nonzero)[0][[0, -1]]
            slices[d] = slice(s1, s2+1)

        return slices

    def _remove_nans(self, data):
        """
        Check for and remove nans from images
        """
        notnans = np.isfinite(data)
        if not np.all(notnans):
            warnings.warn("Image contains nans or infinity")
            data[np.logical_not(notnans)] = 0
