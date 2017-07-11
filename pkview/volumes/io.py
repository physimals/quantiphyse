
from __future__ import division, print_function

import sys
import os
import math
import warnings
import glob
import types

from PySide import QtCore, QtGui
from matplotlib import cm

import nibabel as nib
import numpy as np
import nrrd

HAVE_DCMSTACK = True
try:
    import dcmstack, dicom
except:
    HAVE_DCMSTACK = False
    warnings.warn("DCMSTACK not found - will not be able to read DICOM folders")

class FileMetadata(object):
    """ Metadata from file. Newly created data objects get their metadata from the main Volume
        in use at the time"""
    ORIENT_TO_FILE = 0
    ORIENT_TO_RAS = 1

    def __init__(self, fname, affine=None, shape=None, voxel_sizes=None, dtype=None,
                 ignore_affine=False, force_t=False, squeeze_trailing=True):
        self.set_fname(fname)
        
        if affine is not None and not ignore_affine:
            self.affine = affine
        else:
            self.affine = np.identity(4)

        self.dim_order, self.dim_flip = {}, {}
        for direction in (self.ORIENT_TO_FILE, self.ORIENT_TO_RAS):
            self.dim_order[direction], self.dim_flip[direction] = self.get_transform(direction)

        if shape is not None:
            self.shape_orig = list(shape)
            self.shape_ras = self.reorient_dimdata(self.ORIENT_TO_RAS, shape)

        if voxel_sizes is not None:
            self.voxel_sizes_orig = list(voxel_sizes)
            self.voxel_sizes_ras = self.reorient_dimdata(self.ORIENT_TO_RAS, voxel_sizes)

        if force_t:
            self.shape_orig.insert(2, 1)
            self.shape_ras.insert(2, 1)
            self.voxel_sizes_orig.insert(2, self.voxel_sizes_orig[0])
            self.voxel_sizes_ras.insert(2, self.voxel_sizes_ras[0])
            
        if squeeze_trailing and len(self.shape_orig) == 4 and self.shape_orig[3] == 1:
            self.shape_orig = self.shape_orig[:3]
            self.shape_ras = self.shape_ras[:3]
            self.voxel_sizes_orig = self.voxel_sizes_orig[:3]
            self.voxel_sizes_ras = self.voxel_sizes_ras[:3]
            
        if dtype is not None:
            self.dtype = dtype

    def set_fname(self, fname):
        self.fname = fname
        if fname is not None:
            self.dir, self.basename = os.path.split(fname)
        else:
            self.dir, self.basename = None, None

    def reorient_dimdata(self, direction, dimdata):
        """
        Reorder dim data (e.g. voxel sizes) according to coordinate transformation
        """
        ret = []
        try:
            ret = [dimdata[d] for d in self.dim_order[direction] if d < len(dimdata)]
            if len(dimdata) == 4: ret.append(dimdata[3])
            return ret
        except:
            # If something goes wrong here, just leave the data
            # as it is. It probably means the affine transformation
            # is nothing like orthogonal and therefore the dimension
            # order is not a permutation
            warnings.warn("Failed to re-orient - non-orthogonal affine?")
            warnings.warn("Affine was: " + str(self.affine))
            warnings.warn("transforms: " + str(self.dim_order) + ", " + str(self.dim_flip))
            return dimdata

    def reorient_data(self, direction, data):
        """
        Permute and flip axes to turn data into file or RAS orientation

        returns modified data,
        """
        try:
            dim_order = self.dim_order[direction]
            #print("re-orienting data to ", dim_order, self.dim_flip)
            if data.ndim == 4: dim_order.append(3)
            new_data = np.transpose(data, dim_order)
            for d in self.dim_flip[direction]:
                new_data = np.flip(new_data, d)
            return new_data
        except:
            # If something goes wrong here, just leave the data
            # as it is. It probably means the affine transformation
            # is nothing like orthogonal and therefore the dimension
            # order is not a permutation
            warnings.warn("Failed to re-orient - non-orthogonal affine?")
            #raise
            return data
            
    def get_transform(self, direction):
        """
        Returns dim_order, dim_flip transformations
        to turn data into RAS order from file order or vice versa
        """
        if direction == FileMetadata.ORIENT_TO_FILE: affine = self.affine.transpose()
        else: affine = self.affine

        space_affine = affine[:3,:3]
        space_pos = np.absolute(space_affine)
        dim_order, dim_flip = [], []
        for d in range(3):
            newd = np.argmax(space_pos[:,d])
            dim_order.append(newd)
            if space_affine[newd, d] < 0:
                dim_flip.append(d)
        return dim_order, dim_flip

class NiftiMetadata(FileMetadata):
    def __init__(self, fname, hdr, **kwargs):
        self.nifti_header = hdr
        FileMetadata.__init__(self, fname, affine=hdr.get_best_affine(), shape=hdr.get_data_shape(), 
                              voxel_sizes=hdr.get_zooms(), dtype=hdr.get_data_dtype(), **kwargs)

class QpVolume(np.ndarray):
    """
    Subclass of Numpy array, adding metadata attribute and convenience methods.
    Numpy arrays are converted to this type when files are loaded, or when data is
    added to the IVM, using the view() method so underlying data is not copied.
    
    Method taken from https://docs.scipy.org/doc/numpy/user/basics.subclassing.html
    """

    def __new__(subtype, shape, dtype=float, buffer=None, offset=0,
          strides=None, order=None, md=None):
        # Create the ndarray instance of our type, given the usual
        # ndarray input arguments.  This will call the standard
        # ndarray constructor, but return an object of our type.
        # It also triggers a call to QpVolume.__array_finalize__
        obj = np.ndarray.__new__(subtype, shape, dtype, buffer, offset, strides, order)
        # set the new metadata attributes to the values passed
        obj.md = md
        # These attributes must exist but are initialized separately for ROIS and data
        obj.range = None
        obj.dps = None
        obj.regions = None
        obj.name = None
        return obj

    def __array_finalize__(self, obj):
        # ``self`` is a new object resulting from
        # ndarray.__new__(QpVolume, ...), therefore it only has
        # attributes that the ndarray.__new__ constructor gave it -
        # i.e. those of a standard ndarray.
        #
        # We could have got to the ndarray.__new__ call in 3 ways:
        # From an explicit constructor - e.g. QpVolume():
        #    obj is None
        #    (we're in the middle of the QpVolume.__new__
        #    constructor, and self.md will be set when we return to
        #    QpVolume.__new__)
        if obj is None: return
        # From view casting - e.g arr.view(QpVolume):
        #    obj is arr
        #    (type(obj) can be QpVolume)
        # From new-from-template - e.g qpvolume[:3]
        #    type(obj) is QpVolume
        #
        # Note that it is here, rather than in the __new__ method,
        # that we set the default value for 'md', because this
        # method sees all creation of default objects - with the
        # QpVolume.__new__ constructor, but also with
        # arr.view(QpVolume).
        self.md = getattr(obj, 'md', None)
        self.range = getattr(obj, 'range', None)
        self.dps = getattr(obj, 'dps', None)
        self.regions = getattr(obj, 'regions', None)
        self.name = getattr(obj, 'name', None)
        
    def set_as_roi(self, name):
        self.name = name
        self.range = (self.min(), self.max())
        self.dps = 0
        self.regions = np.unique(self)
        self.regions = self.regions[self.regions > 0]
        
    def set_as_data(self, name):
        self.name = name
        self.range = (float(self.min()), float(self.max()))
        self.dps = self._calc_dps()
        self.regions = []

    def value_str(self, pos):
        """ Return the data value at pos as a string to an appropriate
        number of decimal places"""
        return str(np.around(self[tuple(pos[:self.ndim])], self.dps))

    def pos_slice(self, *axes):
        """ 
        Get a slice at a given position

        axes is a sequence of tuples of (axis number, position)
        """
        sl = [slice(None)] * self.ndim
        for axis, pos in axes:
            sl[axis] = pos
        return self[sl]

    def remove_nans(self):
        """
        Check for and remove nans from images
        """
        nans = np.isnan(self)
        if nans.sum() > 0:
            warnings.warn("Image contains nans")
            self[nans] = 0

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

    def get_pencol(self, region):
        """
        Get an RGB pen colour for a given region
        """
        return self.get_lut()[region]

    def get_lut(self, alpha=None):
        """
        Get the colour look up table for the ROI.
        """
        cmap = getattr(cm, 'jet')
        if len(self.regions) == 0: mx = 1
        else: mx = max(self.regions)
        lut = [[int(255 * rgb1) for rgb1 in cmap(float(v)/mx)[:3]] for v in range(mx+1)]
        lut = np.array(lut, dtype=np.ubyte)

        if alpha is not None:
            # add transparency
            alpha1 = np.ones((lut.shape[0], 1))
            alpha1 *= alpha
            alpha1[0] = 0
            lut = np.hstack((lut, alpha1))

        return lut

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

class NiftiDataFile:
    def __init__(self, fname):
        self.fname = fname
        self.nii = nib.load(fname)
        self.md = NiftiMetadata(fname, self.nii.header)

    def get_info(self):
        return self.md.shape_ras, self.md.shape_orig, self.md.dtype

    def get_metadata(self):
        return self.md

    def get_data(self, ignore_affine=False, force_t=False):
        data = np.asarray(self.nii.get_data())

        if ignore_affine or force_t:
            # Need to create new metadata object as we are diverging from the strict contents
            # of the file
            md = NiftiMetadata(self.fname, self.nii.header, ignore_affine=ignore_affine, force_t=force_t)
        else:
            md = self.md

        while data.ndim < 3:
            # Must be at least 3D
            data = np.expand_dims(data, -1)
            
        if force_t and data.ndim < 4:
            data = np.expand_dims(data, 2)

        if not ignore_affine:
            data = md.reorient_data(FileMetadata.ORIENT_TO_RAS, data)

        if data.ndim == 4 and data.shape[3] == 1: data = np.squeeze(data, 3)
        data = data.view(QpVolume)
        data.remove_nans()
        data.md = md
        return data

class DicomFolder(NiftiDataFile):
    def __init__(self, fname):
        # A directory containing DICOMs. Convert them to Nifti
        sys.stdout.write("Converting DICOMS in %s..." % (os.path.basename(fname)))
        sys.stdout.flush()
        src_dcms = glob.glob('%s/*.dcm' % fname)
        stacks = dcmstack.parse_and_stack(src_dcms)
        stack = stacks.values()[0]
        self.nii = stack.to_nifti()
        sys.stdout.write("DONE\n")
        sys.stdout.flush()
        # FIXME should we do this?
        if self.nii.shape[-1] == 1:
            self.nii = nib.squeeze_image(self.nii)
        self.md = NiftiMetadata(fname + ".nii", self.nii.header)

class NrrdDataFile:
    def __init__(self, fname):
        raise RuntimeError("NRRD support not currently enabled")

def load(fname):
    if os.path.isdir(fname) and HAVE_DCMSTACK:
        return DicomFolder(fname)
    elif fname.endswith(".nii") or fname.endswith(".nii.gz"):
        return NiftiDataFile(fname)
    elif fname.endswith(".nrrd"):
        return NttrDataFile(fname)
    else:
        raise RuntimeError("%s: Unrecognized file type" % fname)

def save(data, fname):
    hdr = None
    affine = np.identity(4)
    if hasattr(data, "md"):
        # Invert axis transformations
        data = data.md.reorient_data(FileMetadata.ORIENT_TO_FILE, data)
        affine = data.md.affine
        try:
            hdr = getattr(data.md, "nifti_header")
        except:
            pass # create new with voxel sizes?
    
    img = nib.Nifti1Image(data, affine, header=hdr)
    img.update_header()
    img.to_filename(fname)
    data.md.set_fname(fname)
