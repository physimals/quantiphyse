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

        self.spacing = [np.linalg.norm(self.affine[:,i]) for i in range(3)]

    def matches(self, grid):
        """ 
        Determine if this grid matches another

        Checks the affine and the shape to within a tolerance
        value after re-orienting both to approximate RAS order
        """
        ALLOWED_ERROR = 0.01
        g1 = self.reorient_ras()
        g2 = grid.reorient_ras()
        for s1, s2 in zip(g1.shape, g2.shape):
            if s1 != s2: return False
        for v1, v2 in zip(g1.affine.flatten(), g2.affine.flatten()):
            if abs(v1 - v2) >= ALLOWED_ERROR: return False
        return True

    def reorient_ras(self):
        """ 
        Return a new grid in approximate RAS order, by axis transposition
        and flipping only

        The result is a grid which defines the same space as the original
        with the same voxel spacing but where the x axis is increasing
        left->right, the y axis increases posterior->anterior and the
        z axis increases inferior->superior.
        """
        dim_order, dim_flip, new_affine, new_shape = self._get_diag_transform(self.affine)
        print(dim_order, dim_flip, new_shape)
        print(new_affine)
        return DataGrid(new_shape, new_affine)

    def _swap_cols(self, mat, c1, c2):
        # Swap columns of a matrix
        mat[:,[c1, c2]] = mat[:,[c2, c1]]
    
    def _get_diag_transform(self, mat):
        """ Get the transpositions/flips that will make a matrix as diagonal as possible """
        dim_order, dim_flip = [], []
        absmat = np.absolute(mat)
        for d in range(3):
            newd = np.argmax(absmat[:,d])
            dim_order.append(newd)
            if mat[newd, d] < 0:
                dim_flip.append(d)

        new_mat = np.copy(mat)
        new_shape = [self.shape[d] for d in dim_order]
        for idx, d in enumerate(dim_order):
            new_mat[:,d] = mat[:,idx]
        for dim in dim_flip:
            # Change signs to positive and adjust origin to flip a dimension
            new_mat[:,dim] = -new_mat[:,dim]
            new_mat[dim,3] = new_mat[dim, 3] - new_mat[0,dim] * new_shape[dim]

        return dim_order, dim_flip, new_mat, new_shape

class QpData:

    def __init__(self, name, data, grid, stdgrid=None, fname=None):
        # Everyone needs a friendly name
        self.name = name

        if stdgrid is None: 
            # Data is not to be regridded (i.e. it is being supplied on the OTG)
            self.data = data
            self.grid = grid
            self.rawdata = data
            self.rawgrid = grid
        else:
            self.rawdata = data
            self.rawgrid = rawgrid
            self.regrid(stdgrid)

        # File it was loaded from, if relevant
        self.fname = fname

        # Convenience attributes
        self.ndim = self.data.ndim
        self.range = (self.rawdata.min(), self.rawdata.max())
        if self.ndim == 4: self.nvols = self.data.shape[3]
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
        nans = np.isnan(self.data)
        if nans.sum() > 0:
            warnings.warn("Image contains nans")
            self.data[nans] = 0

    def regrid(self, grid):
        tmatrix = np.dot(np.linalg.inv(self.rawgrid.affine), grid.affine)
        print("Regridding", self.rawgrid.shape, grid.shape)
        print(tmatrix)
        # Try to turn the transformation matrix diagonal by flipping/permuting axes    
        dim_order, dim_flip, new_tmatrix, new_shape = grid._get_diag_transform(tmatrix)
        print("Diagonalized")
        print(dim_order, dim_flip)
        print(new_tmatrix)
        if sorted(dim_order) == range(3):
            print("Looks good, simplifying")
            if self.ndim == 4: dim_order.append(3)
            self.data = np.transpose(self.rawdata, dim_order)
            tmatrix = new_tmatrix
        
        if self.rawgrid.matches(grid):
            # In this case the flips/permutation is sufficient in itself
            # and new_tmatrix should be the identity
            print("Trivial transform - all done")
        else:
            affine = tmatrix[:3,:3]
            offset = list(tmatrix[:3,3])
            diagonal = np.diagonal(affine)
            if np.count_nonzero(affine - np.diag(diagonal)) == 0:
                # The transformation is diagonal, so use this sequence instead of 
                # the full matrix - this will be faster
                affine = diagonal
                print("It's diagonal - using ", affine)
            else:
                print("Using general affine transform")
                print(affine)
            output_shape = grid.shape
            if self.ndim == 4:
                # Make 4D affine with identity transform in 4th dimension
                affine = np.append(affine, [[0, 0, 0]], 0)
                affine = np.append(affine, [[0],[0],[0],[1]],1)
                offset.append(0)
                output_shape.append(self.nvols)

            print("Offset = ", offset)
            #print(np.linalg.eigh(affine))
            self.data = scipy.ndimage.affine_transform(self.rawdata, affine, offset=offset, output_shape=output_shape)
        print(self.data.min(), self.data.max())
        self.grid = grid

    def strval(self, pos):
        """ Return the data value at pos as a string to an appropriate
        number of decimal places"""
        return str(np.around(self.data[tuple(pos[:self.ndim])], self.dps))

    def get_slice(self, axes, mask=None, fill_value=None):
        """ 
        Get a slice at a given position

        axes is a sequence of tuples of (axis number, position)
        """
        sl = [slice(None)] * self.ndim
        for axis, pos in axes:
            if axis < self.ndim:
                sl[axis] = pos
        data = self.data[sl]

        if mask is not None:
            data = np.copy(data)
            mask_slice = mask.pos_slice(axes)
            if fill_value is None:
                # Less than the minimum
                fill_value = self.range[0] - 1
            data[mask_slice == 0] = fill_value
        return data

class QpRoi(QpData):

    def __init__(self):
        
        #if roi.range[0] < 0 or roi.range[1] > 2**32:
        #    raise RuntimeError("ROI must contain values between 0 and 2**32")
        #
        #if not np.equal(np.mod(roi, 1), 0).any():
        #   raise RuntimeError("ROI contains non-integer values.")

        QpData.__init__(self)
        self.dps = 0
        self.regions = np.unique(self.rawdata)
        self.regions = self.regions[self.regions > 0]

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
        img_restric = img.data[slices]
        ... process img_restict, returning out_restrict
        out_full = np.zeros(img.shape)
        out_full[slices] = out_restrict
        """
        if ndim == None: ndim = self.ndim
        slices = [slice(None)] * ndim
        for d in range(min(ndim, self.ndim)):
            ax = [i for i in range(self.ndim) if i != d]
            nonzero = np.any(self, axis=tuple(ax))
            s1, s2 = np.where(nonzero)[0][[0, -1]]
            slices[d] = slice(s1, s2+1)
        
        return slices
