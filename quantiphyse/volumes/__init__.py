import numpy as np

"""
Work-in-progress on Next Generation volume class

To support viewing of files in different spaces with 
interpolation so analysis can be done on a grid.

Basic concepts decided:

 - The One True Grid (OTG) is defined by the main volume. It consists of 
   a 3D shape, and a 3D affine which maps grid co-ordinates onto RAS
   coordinates.
 - All data is 3D or 4D. 2D (or 1D?) data will be expanded to 3D on load
 - The 4th dimension is not part of the grid and has no impact on orientation.
 - Every data object may have raw data (e.g. from file) and is also regridded onto
   the OTG. The affine transformations associated with a grid are used for this
 - When the main volume is changed, all data is regridded on to the new OTG
 - Data objects may be created already on the standard grid, they will not be
   regridded and the raw data / OTG data are the same
 - When a data object is set as the main data, its raw data is re-oriented
   (but NOT regridded) to be in approximate RAS format so image display 
   is consistent. Note that the transformations which describe the 
   new grid are not approximated and the OTG is not exactly RAS aligned but the
   image view labels (R/L, S/I, A/P) should be in roughly the right place.
 - This means that if the main data was loaded from a file its raw data and
   OTG data are not necessarily the same.

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
    def __init__(self, shape, affine):
        # Dimensionality of the grid
        self.shape = shape

        # 3D Affine transformation from grid-space to standard space
        # This is a 4x4 matrix - includes constant offset
        self.affine = np.copy(affine)

        self._get_spacing()

    def reorient_ras(self):
        """ 
        Re-orient grid to approximate RAS order, by axis transposition
        and flipping only
        """
        print(self.affine)
        print(self.shape, self.spacing)
        space_affine = self.affine[:3,:3]
        space_pos = np.absolute(space_affine)
        dim_order, dim_flip = [], []
        for d in range(3):
            newd = np.argmax(space_pos[:,d])
            dim_order.append(newd)
            if space_affine[newd, d] < 0:
                dim_flip.append(d)

        self.shape = [self.shape[d] for d in dim_order]
        for idx, d in enumerate(dim_order):
            self._swap_cols(self.affine, idx, d)
        for dim in dim_flip:
            self.affine[:,dim] = -self.affine[:,dim]
            self.affine[dim,3] = self.affine[dim, 3] - self.affine[0,dim] * self.shape[dim]
        self._get_spacing()
        print(dim_order, dim_flip)
        print(self.affine)
        print(self.shape, self.spacing)

    def _swap_cols(self, arr, c1, c2):
        arr[:,[c1, c2]] = arr[:,[c2, c1]]

    def _get_spacing(self):
        # Grid spacing in mm - derived from affine
        self.spacing = [np.linalg.norm(self.affine[:,i]) for i in range(3)]

class QpData:

    def __init__(self, name, data, grid, stdgrid=None, file=None):
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
        self.file = file

        # Convenience attributes
        self.ndim = self.data.ndim
        self.range = (self.rawdata.min(), self.rawdata.max())

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
        # Get the transform from raw co-ordinate space to standard space
        transform = np.dot(np.linalg.inv(grid.affine), self.rawgrid.affine)
        affine = transform[:3,:3]
        offset = transform[:3,3]
        self.data = scipy.ndimage.affine_transform(self.rawdata, affine, offset=offset, output_shape=grid.shape)
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
        data = self[sl]

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
