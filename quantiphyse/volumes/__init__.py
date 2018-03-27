"""
Quantiphyse - Basic volume data classes

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

        self.origin = tuple(affine[:3,3])
        self.transform = affine[:3,:3]
        self.inv_transform = np.linalg.inv(self.transform)

        self.spacing = [np.linalg.norm(self.affine[:,i]) for i in range(3)]
        self.nvoxels = 1
        for d in range(3): self.nvoxels *= shape[d]

    def grid_to_world(self, coords):
        return np.dot(self.transform, coords) + self.origin

    def world_to_grid(self, coords):
        return np.dot(self.inv_transform, (coords - self.origin))

    def reorient_ras(self):
        """ 
        Return a new grid in approximate RAS order, by axis transposition
        and flipping only

        The result is a grid which defines the same space as the original
        with the same voxel spacing but where the x axis is increasing
        left->right, the y axis increases posterior->anterior and the
        z axis increases inferior->superior.

        We make slightly botched use of the Transform class for this - this
        hack shouldn't be necessary really
        """
        rasgrid = DataGrid([1, 1, 1], np.identity(4))
        t = Transform(self, rasgrid)
        new_shape = [self.shape[d] for d in t.reorder]
        new_mat = t.tmatrix
        return DataGrid(new_shape, new_mat)

    def matches(self, grid):
        """
        Return True if grid is identical to this grid
        """
        return np.array_equal(self.affine, grid.affine) and  np.array_equal(self.shape, grid.shape)

class OrthoSlice(DataGrid):
    """
    Grid which is an orthogonal slice through another grid
    
    May be defined in two ways:

     - As an orthogonal slice through a grid, using ``ortho=(grid, zaxis, position)``
     - As a slice through an ``origin`` with two 3D ``basis_vectors``

    The following attributes are defined:

     - ``origin`` Starting point of the slice in world co-ordinates
     - ``basis_vectors`` Two 3D basis vectors for the plane in world co-ordinates
     - ``unit_vectors`` Normalized version of basis_vectors
    """
    def __init__(self, grid, zaxis, pos):
        affine = np.zeros((4, 4))
        shape = [1, 1, 1]
        col = 0
        for ax in range(3):
            if ax != zaxis:
                affine[:,col] = grid.affine[:,ax]
                shape[col] = grid.shape[ax]
                col += 1
            else:
                affine[:,2] = grid.affine[:,ax]
        affine[:,3] = grid.affine[:,3] + pos * affine[:,2]
        DataGrid.__init__(self, shape, affine)
        self.basis = [tuple(self.transform[:,0]), tuple(self.transform[:,1])]

    def slice_data(self, data, grid):
        """
        Extract a data slice in raw data resolution

        grid is the grid on which the slice position/direction is defined
        axis is the axis (relative to grid) the slice is normal to
        position is the position (relative to grid) of the slice position
        """
        
        print("OrthoSlice: grid origin: %s" % str(self.origin))
        print("OrthoSlice: grid v1: %s" % str(self.basis[0]))
        print("OrthoSlice: grid v2: %s" % str(self.basis[1]))

        trans = Transform(self, grid)
        data_origin = trans.transform_position((0, 0, 0))
        data_basis = [
            trans.transform_direction((1, 0, 0)),
            trans.transform_direction((0, 1, 0))
        ]
        print("OrthoSlice: data origin: %s" % str(data_origin))
        print("OrthoSlice: data v1: %s" % str(data_basis[0]))
        print("OrthoSlice: data v2: %s" % str(data_basis[1]))

        slice_shape, slice_v, slice_scale = [], [], []
        for idx in range(2):
            absv = np.absolute(data_basis[idx])
            bestd = np.argmax(absv)
            slice_shape.append(data.shape[bestd])
            scale = 1/absv[bestd]
            slice_v.append(data_basis[idx]*scale)
            slice_scale.append(scale)
        
        print("OrthoSlice: slice shape: %s" % str(slice_shape))
        print("OrthoSlice: slice v1: %s" % str(slice_v[0]))
        print("OrthoSlice: slice v2: %s" % str(slice_v[1]))
        print("OrthoSlice: slice scale: %s" % str(slice_scale))

        #if self.ortho:
        if False:
            sdata = data[self.ortho_slices]
        else:
            sdata = pg.affineSlice(data, slice_shape, data_origin, slice_v, range(3))
            mask = np.ones(data.shape)
            smask = pg.affineSlice(mask, slice_shape, data_origin, slice_v, range(3))
        return sdata, slice_scale, (0, 0)

    def is_ortho_vector(self, vec):
        for ax, v in enumerate(vec):
            if abs(abs(v)-1) < EQ_TOL:
                return ax, math.copysign(1, v)
        return None, None

# Tolerance for treating values as equal
# Used to determine if matrices are diagonal or identity
EQ_TOL = 1e-3

class Transform:
    """
    Transforms data on one grid into another
    """

    def __init__(self, in_grid, out_grid):
        debug("Transforming from")
        debug(in_grid.affine)
        debug("To")
        debug(out_grid.affine)

        # Convert the transformation into optional re-ordering and flipping
        # of axes and a final optional affine transformation
        # This enables us to use faster methods in the case where the
        # grids are essentially the same or scaled
        self.in_grid = in_grid
        self.out_grid = out_grid

        # Affine transformation matrix from grid 2 to grid 1
        self.tmatrix_raw = np.dot(np.linalg.inv(out_grid.affine), in_grid.affine)
        self.output_shape = out_grid.shape[:]

        # Generate potentially simplified transformation using re-ordering and flipping
        self.reorder, self.flip, self.tmatrix = self._simplify_transforms()

    def transform_position(self, v):
        return self.tmatrix_raw.dot(list(v) + [1,])[:3]

    def transform_direction(self, v):
        return self.tmatrix_raw[:3,:3].dot(v)

    def transform_data(self, data):
        # Perform the flips and transpositions which simplify the transformation
        # and may avoid the need for an affine transformation or make it a simple
        # scaling
        if len(self.flip) != 0:
            #debug("Flipping axes: ", self.flip)
            for d in self.flip: data = np.flip(data, d)

        if self.reorder != range(3):
            if data.ndim == 4: self.reorder = self.reorder + [3]
            #debug("Re-ordering axes: ", self.reorder)
            data = np.transpose(data, self.reorder)

        if not self._is_identity(self.tmatrix):
            # We were not able to reduce the transformation down to flips/transpositions
            # so we will need an affine transformation

            # scipy requires the out->in transform so invert our in->out transform
            tmatrix = np.linalg.inv(self.tmatrix)
            affine = tmatrix[:3,:3]
            offset = list(tmatrix[:3,3])
            output_shape = self.output_shape[:]
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
            else:
                pass
            #debug("WARNING: affine_transform: ")
            #debug(affine)
            #debug("Offset = ", offset)
            #debug("Input shape=", data.shape, data.min(), data.max())
            #debug("Output shape=", output_shape)
            data = scipy.ndimage.affine_transform(data, affine, offset=offset, output_shape=output_shape, order=0)
        
        return data
    
    def _is_diagonal(self, mat):
        return np.all(np.abs(mat - np.diag(np.diag(mat))) < EQ_TOL)

    def _is_identity(self, mat):
        return np.all(np.abs(mat - np.identity(mat.shape[0])) < EQ_TOL)
        
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
                dim_flip.append(newd)
     
        new_mat = np.copy(mat)
        if sorted(dim_order) == range(3):
            # The transposition was consistent, so use it
            #debug("Before simplification")
            #debug(new_mat)
            #debug(self.output_shape)
            new_shape = [self.in_grid.shape[d] for d in dim_order]
            for idx, d in enumerate(dim_order):
                new_mat[:,d] = mat[:,idx]
            #debug("After transpose", dim_order)
            #debug(new_mat)
            for dim in dim_flip:
                # Change signs to positive to flip a dimension
                new_mat[:,dim] = -new_mat[:,dim]
            #debug("After flip", dim_flip)
            #debug(new_mat)
            for dim in dim_flip:
                # Adjust origin
                new_mat[:3,3] = new_mat[:3, 3] - new_mat[:3, dim] * (new_shape[dim]-1)
                
            #debug("After adjust origin", new_shape)
            #debug(new_mat)

            return dim_order, dim_flip, new_mat
        else:
            # Transposition was inconsistent, just go with general
            # affine transform - this will work but might be slow
            return range(3), [], new_mat

class QpData:
    """
    3D or 4D data

    Data is defined on a DataGrid instance which defines a uniform grid in standard space.
    Data can be interpolated onto another grid for display or analysis purposes, however the
    original raw data and grid are preserved so file save can be done consistently without
    loss of information. In addition some visualisation or analysis may want to use the original
    raw data.
    """

    def __init__(self, name, grid, nvols, fname=None, roi=False):
        # Everyone needs a friendly name
        self.name = name

        # Grid the data was defined on. 
        self.rawgrid = grid
        self.w2raw = np.linalg.inv(self.rawgrid.affine)
        self.w2raw3 = np.linalg.inv(self.rawgrid.transform)

        # Number of volumes (1=3D data)
        self.nvols = nvols
        if self.nvols == 1: self.ndim = 3
        else: self.ndim = 4

        # File it was loaded from, if relevant
        self.fname = fname

        # Set standard grid to match raw grid, it will be changed when/if regrid() is called
        self.stddata = None
        self.stdgrid = grid

        # Basic default, updated when stddata is evaluated
        self.range = (0, 1)
        self.dps = 1

        # Whether raw data is 2d + time incorrectly returned as 3D
        self.raw_2dt = False

        # Whether to treat as an ROI data set
        self.set_roi(roi)

    def raw(self):
        raise NotImplementedError("Internal Error: raw() has not been implemented. This is a bug - please inform the authors")

    def std(self):
        if self.stddata is None:
            self._update_stddata()
        return self.stddata

    def set_2dt(self):
        """
        Force 3D static data into the form of a 2D + time

        This is useful for some broken NIFTI files. Note that the 3D extent of the grid
        is completely ignored. In order to work, the underlying class must implement the
        change in raw().
        """
        if self.nvols != 1 or self.rawgrid.shape[2] == 1:
            raise RuntimeError("Can only force to 2D timeseries if data was originally 3D static")

        self.raw_2dt = True
        # FIXME hack because it's not clear what to do with the grid apart from make sure it's 2D
        self.nvols = self.rawgrid.shape[2]
        self.ndim = 4
        self.rawgrid.shape[2] = 1
        self.stddata = None

    def regrid(self, grid):
        """
        Set the standard grid - i.e. the grid on which data returned
        by std() is defined.
        """
        if not self.stdgrid.matches(grid):
            debug("Regridding")
            self.stdgrid = grid
            #self._update_stddata()
        else:
            debug("Not bothering to regrid - no change")

    def strval(self, pos):
        """ 
        Return the data value at pos as a string to an appropriate
        number of decimal places
        """
        return sf(self.val(pos))
        #return str(np.around(self.val(pos), self.dps))

    def val(self, pos):
        """ 
        Return the data value at pos 
        """
        if pos[3] > self.nvols: pos[3] = self.nvols-1
        return self.std()[tuple(pos[:self.ndim])]

    def get_vol(self, vol):
        rawdata=self.raw()
        if self.ndim == 4:
            rawdata = rawdata[:,:,:,min(vol, self.nvols-1)]
        return rawdata
        
    def get_slice(self, plane, vol=0):
        rawdata=self.get_vol(vol)
        my_plane = SlicePlane(self.rawgrid, plane=plane)
        return my_plane.slice_data(rawdata), my_plane.scales, my_plane.offset

    def set_roi(self, roi):
        self.roi = roi
        if self.roi:
            if self.nvols != 1:
                raise RuntimeError("ROIs must be static (single volume) 3D data")
            self._update_stddata()

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
        img_restric = img.stddata[slices]
        ... process img_restict, returning out_restrict
        out_full = np.zeros(img.shape)
        out_full[slices] = out_restrict
        """
        if not self.roi:
            raise RuntimeError("get_bounding_box() called on non-ROI data")
            
        slices = [slice(None)] * ndim
        for d in range(min(ndim, 3)):
            ax = [i for i in range(3) if i != d]
            nonzero = np.any(self.std(), axis=tuple(ax))
            s1, s2 = np.where(nonzero)[0][[0, -1]]
            slices[d] = slice(s1, s2+1)
        
        return slices

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

    def _remove_nans(self, data):
        """
        Check for and remove nans from images
        """
        nans = np.isnan(data)
        if np.any(nans):
            warnings.warn("Image contains nans")
            data[nans] = 0

    def _update_stddata(self):
        #debug("Updating stddata for %s" % self.name)
        t = Transform(self.rawgrid, self.stdgrid)
        #debug("Raw grid: ")
        #debug(self.rawgrid.affine)
        #debug(self.rawgrid.shape)
        #debug("Std grid: ")
        #debug(self.stdgrid.affine)
        #debug(self.stdgrid.shape)
        rawdata = self.raw()
        if rawdata.ndim not in (3, 4):
            raise RuntimeError("Data must be 3D or 4D (padded if necessary")
        #debug("Raw data range: ", rawdata.min(), rawdata.max())
        self.stddata = t.transform_data(rawdata)
        #debug("Std data range: ", self.stddata.min(), self.stddata.max())
        self._remove_nans(self.stddata)  

        if self.roi:
            if self.stddata.min() < 0 or self.stddata.max() > 2**32:
                raise QpException("ROIs must contain values between 0 and 2**32")
            if not np.equal(np.mod(self.stddata, 1), 0).any():
                raise QpException("ROIs must contain integers only")
            self.stddata = self.stddata.astype(np.int32)
            self.dps = 0
            self.regions = np.unique(self.stddata)
            self.regions = self.regions[self.regions > 0]
        else:   
            self.dps = self._calc_dps()
            self.regions = []

        self.range = (self.stddata.min(), self.stddata.max())
        #debug("Done")
        