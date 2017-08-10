import math
import warnings

import numpy as np
import scipy

"""
Work-in-progress on Next Generation volume class

To support viewing of files in different spaces with 
interpolation so analysis can be done on a grid.

Basic concepts decided:

 - The One True Grid (OTG) is defined by the main volume. It consists of 
   a 3D shape, and a 3D affine which maps grid co-ordinates onto
   coordinates in standard space.
 - All data is 4D. 2D (or 1D?) data will be expanded to 4D on load
 - The 4th dimension is not part of the grid and has no impact on orientation.
 - Every data object may have raw data (e.g. from file) and is also regridded onto
   the OTG. The affine transformations associated with a grid are used for this
 - When a grid 'matches' the OTG (i.e. defines the same voxels, although possibly
   with different axis order/directions), regridding will be implemented by
   axis transpositions/flips to avoid the cost of regridding a large 4D volume 
   using general affine transformations.
 - If the regridding transformation 'looks' diagonal we will pass it to the
   transform function as a sequence to reduce computational cost.
 - When the main volume is changed, the OTG is changed to and approximately RAS oriented 
   copy of the main data's raw grid. so the image view is consistent. All data is then 
   regridded on to the new OTG. Note that the OTG will not be exactly RAS aligned
   but the image view labels (R/L, S/I, A/P) should be in roughly the right place.
 - This means that if the main data was loaded from a file its raw data and
   OTG data are not necessarily the same.
 - Data objects may be created already on the standard grid, they will not be
   regridded and the raw data / OTG data are the same

For consideration
 - Initially only OTG data will be used for viewing and analysis
 - Raw data could be used for viewing and potentially some analysis 
   (e.g. volume averages which do not depend on slicing)
 - Raw data could be swapped to disk (mem-mapped) to avoid keeping 2 copies
   of everything - might have an impact if required for analysis
 - 4D data - for now the 4th dimension will need to match but could start
   off with crude workaround (e.g. if it doesn't just use the first volume)
   and think about how multiple 4D data could be accommodated.
 - We could expand the OTG to accommodate data outside its range?

"""

class DataGrid:
    """
    Defines a regular 3D grid in standard space

    A grid consists of :
      - A 4D affine matrix which describes the transformation from 
        grid co-ordinates to standard space co-ordinates
      - A 3D shape (number of points in x, y, z dimensions)

    From the grid affine may be derived:
      - The grid spacing in standard units (mm)
      - The grid origin in standard space (last column of the affine)
      - The grid 3D transformation matrix (first 3x3 submatrix of the affine)

    The objects are not formally immutable but are not designed to be modified
    """

    def __init__(self, shape, affine):
        # Dimensionality of the grid - 3D only
        if len(shape) != 3: 
            raise RuntimeError("Grid shape must be 3D")
        self.shape = list(shape)[:]

        # 3D Affine transformation from grid-space to standard space
        # This is a 4x4 matrix - includes constant offset
        if len(affine.shape) != 2 or affine.shape[0] != 4 or affine.shape[1] != 4: 
            raise RuntimeError("Grid afine must be 4x4 matrix")
        self.affine = np.copy(affine)

        self.origin = affine[:3,3]
        self.transform = affine[:3,:3]

        self.spacing = [np.linalg.norm(self.affine[:,i]) for i in range(3)]
        self.nvoxels = 1
        for d in range(3): self.nvoxels *= shape[d]

    def reorient_ras(self):
        """ 
        Return a new grid in approximate RAS order, by axis transposition
        and flipping only

        The result is a grid which defines the same space as the original
        with the same voxel spacing but where the x axis is increasing
        left->right, the y axis increases posterior->anterior and the
        z axis increases inferior->superior.
        """
        rasgrid = DataGrid([1,1,1], np.identity(4))
        t = Transform(rasgrid, self)
        new_shape = [self.shape[d] for d in t.reorder]
        return DataGrid(new_shape, t.tmatrix)

class Transform:
    """
    Transforms data on one grid into another
    """

    # Tolerance for treating values as equal
    # Used to determine if matrices are diagonal or identity
    EQ_TOL = 1e-10

    def __init__(self, in_grid, out_grid):
        # Convert the transformation into optional re-ordering and flipping
        # of axes and a final optional affine transformation
        # This enables us to use faster methods in the case where the
        # grids are essentially the same or scaled
        self.in_grid = in_grid
        self.out_grid = out_grid

        # Affine transformation matrix from grid 2 to grid 1
        self.tmatrix_raw = np.dot(np.linalg.inv(in_grid.affine), out_grid.affine)
        self.output_shape = out_grid.shape[:]
        print("Transform: output shape=", self.output_shape)

        # Generate potentially simplified transformation using re-ordering and flipping
        self.reorder, self.flip, self.tmatrix = self._simplify_transforms()

    def _is_diagonal(self, mat):
        print("Is diagonal?")
        print(np.abs(mat - np.diag(np.diag(mat))))
        return np.all(np.abs(mat - np.diag(np.diag(mat))) < self.EQ_TOL)

    def _is_identity(self, mat):
        return np.all(np.abs(mat - np.identity(mat.shape[0])) < self.EQ_TOL)
        
    def _simplify_transforms(self):
        # Flip/transpose the axes to put the biggest numbers on
        # the diagonal and make negative diagonal elements positive
        dim_order, dim_flip = [], []
        mat = self.tmatrix_raw
        
        absmat = np.absolute(mat)
        for d in range(3):
            newd = np.argmax(absmat[:,d])
            dim_order.append(newd)
            if mat[newd, d] < 0:
                dim_flip.append(d)
     
        if sorted(dim_order) == range(3):
            # The transposition was consistent, so use it
            print("Using re-order and flip: ", dim_order, dim_flip)
            new_mat = np.copy(mat)
            new_shape = [self.output_shape[d] for d in dim_order]
            for idx, d in enumerate(dim_order):
                new_mat[:,d] = mat[:,idx]
            for dim in dim_flip:
                # Change signs to positive to flip a dimension
                new_mat[:,dim] = -new_mat[:,dim]
            for dim in dim_flip:
                # Adjust origin 
                new_mat[:3,3] = new_mat[:3, 3] - new_mat[:3, dim] * (new_shape[dim] -1)
            if self._is_identity(new_mat):
                # The remaining matrix is the identity so do not need to use it
                print("Remaining affine is identity - not using")
                new_mat = None
            else:
                print("Remaining affine: ")
                print(new_mat)
            return dim_order, dim_flip, new_mat
        else:
            # Transposition was inconsistent, just go with general
            # affine transform - this will work but might be slow
            return None, None, mat

    def transform_data(self, data):
        if self.reorder is not None:
            if data.ndim == 4: self.reorder = self.reorder + [3]
            #print("Re-ordering axes: ", self.reorder)
            data = np.transpose(data, self.reorder)
        if self.flip is not None:
            #print("Flipping axes: ", self.flip)
            for d in self.flip: data = np.flip(data, d)
        if self.tmatrix is not None:
            #print("Doing an affine transformation")
            affine = self.tmatrix[:3,:3]
            offset = list(self.tmatrix[:3,3])
            output_shape = self.output_shape[:]
            print("transform_data: output shape=", self.output_shape, output_shape)
            if data.ndim == 4:
                # Make 4D affine with identity transform in 4th dimension
                affine = np.append(affine, [[0, 0, 0]], 0)
                affine = np.append(affine, [[0],[0],[0],[1]],1)
                offset.append(0)
                output_shape.append(data.shape[3])

            if self._is_diagonal(affine):
                # The transformation is diagonal, so use this sequence instead of 
                # the full matrix - this will be faster
                affine = np.diagonal(affine)
                print("Matrix is diagonal - ", affine)
            else:
                print("Matrix is not diagonal - using general affine transform")
                print(affine)

            print("Offset = ", offset)
            print("affine_transform: output_shape=", output_shape)
            data = scipy.ndimage.affine_transform(data, affine, offset=offset, output_shape=output_shape)
        return data

class QpData:
    """
    3D or 4D data

    Data is defined on a DataGrid instance which defines a uniform grid in standard space.
    Data can be interpolated onto another grid for display or analysis purposes, however the
    original raw data and grid are preserved so file save can be done consistently without
    loss of information. In addition some visualisation or analysis may want to use the original
    raw data.
    """

    def __init__(self, name, data, grid, fname=None):
        if data.ndim not in (3, 4):
            raise RuntimeError("QpData must be 3D or 4D (padded if necessary")
        
        # Everyone needs a friendly name
        self.name = name

        # Original data and the grid it was defined on. 
        self.raw = data
        self.rawgrid = grid

        # Set standard data to match, it will be changed when/if regrid() is called
        self.std = data
        self.stdgrid = grid

        # File it was loaded from, if relevant
        self.fname = fname

        # Convenience attributes
        self.ndim = self.std.ndim
        self.range = (self.raw.min(), self.raw.max())
        if self.ndim == 4: self.nvols = self.raw.shape[3]
        else: self.nvols = 1

        self.dps = self._calc_dps()
        self._remove_nans()

    def _calc_dps(self):
        """
        Return appropriate number of decimal places for presenting data values
        """
        if self.range[0] == self.range[1]:
            # Pathological case where data is uniform
            return 0
        else:
            # Look at range of data and allow decimal places to give at least 1% steps
            return max(1, 3-int(math.log(self.range[1]-self.range[0], 10)))

    def _remove_nans(self):
        """
        Check for and remove nans from images
        """
        nans = np.isnan(self.std)
        if nans.sum() > 0:
            warnings.warn("Image contains nans")
            self.std[nans] = 0

    def make_2d_timeseries(self):
        """
        Force 3D static data into the form of a 2D + time

        This is useful for some broken NIFTI files. Note that the 3D extent of the grid
        is completely ignored
        """
        if self.nvols != 1 or self.rawgrid.shape[2] == 1:
            raise RuntimeError("Can only force to 2D timeseries if data was originally 3D static")

        raise RuntimeError("Not implemented yet")

    def regrid(self, grid):
        """
        Update data onto the specified grid. The original raw data is not affected
        """
        print("Regridding, raw=%s, new=%s" % (str(self.rawgrid.shape), str(grid.shape)))
        print("Raw grid")
        print(self.rawgrid.affine)
        print("New grid")
        print(grid.affine)
        t = Transform(self.rawgrid, grid)
        self.std = t.transform_data(self.raw)
        self.stdgrid = grid
        print("New data shape=", self.std.shape)
        print("New data range=", self.std.min(), self.std.max())

    def strval(self, pos):
        """ 
        Return the data value at pos as a string to an appropriate
        number of decimal places
        """
        return str(np.around(self.val(pos), self.dps))

    def val(self, pos):
        """ 
        Return the data value at pos 
        """
        if pos[3] > self.nvols: pos[3] = self.nvols-1
        return self.std[tuple(pos[:self.ndim])]

    def get_slice(self, axes, mask=None, fill_value=None):
        """ 
        Get a slice at a given position

        axes - a sequence of tuples of (axis number, position)
        mask - if specified, data outside the mask is given a fixed fill value
        fill_value - fill value, if not specified a value less than the data minimum is used
        """
        sl = [slice(None)] * self.ndim
        for axis, pos in axes:
            if axis >= self.ndim:
                pass
            elif pos < self.std.shape[axis]:
                # Handle case where 4th dimension is out of range
                sl[axis] = pos
            else:
                sl[axis] = self.std.shape[axis]-1
        data = self.std[sl]

        if mask is not None:
            data = np.copy(data)
            mask_slice = mask.get_slice(axes)
            if fill_value is None:
                # Less than the minimum
                fill_value = self.range[0] - 0.000001
                #print("fillval = ", fill_value, self.range)
            data[mask_slice == 0] = fill_value
        return data

    def as_roi(self):
        return QpRoi(self.name, self.raw, self.rawgrid, self.fname)

class QpRoi(QpData):
    """
    Subclass containing an ROI (region of interest)

    ROIs must contain integers - each distinct value identifies 
    a region, 0 is outside the ROI
    """

    def __init__(self, name, data, grid, fname=None):
        if data.ndim != 3:
           raise RuntimeError("ROIs must be static (single volume) 3D data")

        if data.min() < 0 or data.max() > 2**32:
            raise RuntimeError("ROI must contain values between 0 and 2**32")
        
        if not np.equal(np.mod(data, 1), 0).any():
           raise RuntimeError("ROI contains non-integer values.")

        QpData.__init__(self, name, data.astype(np.int32), grid, fname)

        self.dps = 0
        self.regions = np.unique(self.raw)
        self.regions = self.regions[self.regions > 0]

    def regrid(self, grid):
        """
        When regridding an ROI need to make sure output data
        is integers
        """
        QpData.regrid(self, grid)
        print(self.std.min(), self.std.max())

    def get_bounding_box(self, ndim=None):
        """
        Returns a sequence of slice objects which
        describe the bounding box of this ROI.
        If ndim is specified, will return a bounding 
        box of this number of dimensions, truncating
        and appending slices as required.

        This enables image or overlay data to be
        easily restricted to the ROI region and
        reduce data copying.

        e.g. 
        slices = roi.get_bounding_box(img.ndim)
        img_restric = img.std[slices]
        ... process img_restict, returning out_restrict
        out_full = np.zeros(img.shape)
        out_full[slices] = out_restrict
        """
        if ndim is None: ndim = self.ndim
        slices = [slice(None)] * ndim
        for d in range(min(ndim, self.ndim)):
            ax = [i for i in range(self.ndim) if i != d]
            nonzero = np.any(self.std, axis=tuple(ax))
            s1, s2 = np.where(nonzero)[0][[0, -1]]
            slices[d] = slice(s1, s2+1)
        
        return slices
