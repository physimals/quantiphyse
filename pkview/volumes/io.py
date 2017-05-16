
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
import dcmstack
import numpy as np
import nrrd

class FileMetadata(object):
    """ Metadata from file. Newly created data objects get their metadata from the main Volume
        in use at the time"""
    ROI = 0
    DATA = 1

    ORIENT_TO_FILE = 0
    ORIENT_TO_RAS = 1

    def __init__(self, data, name=None, fname=None, affine=None, voxel_sizes=None, vtype=DATA, nifti_header=None, ignore_affine=False):
        self.name = name
        self.set_fname(fname)
        
        if voxel_sizes is not None:
            self.voxel_sizes = voxel_sizes
        else:
            self.voxel_sizes = [1.0,] * data.ndim

        if affine is not None:
            self.affine = affine
        else:
            self.affine = np.identity(4)

        self.range = (data.min(), data.max())
        self.dps = self._calc_dps()

        if nifti_header is not None:
            self._init_nifti(nifti_header, ignore_affine)

    def set_fname(self, fname):
        self.fname = fname
        if fname is not None:
            self.dir, self.basename = os.path.split(fname)
        else:
            self.dir, self.basename = None, None
        if self.name is None:
            self.name = self.basename

    def reorient(self, direction, data=None, voxel_sizes=None):
        """
        Permute and flip axes to turn data into file or RAS orientation

        returns modified data, and/or voxel sizes as required
        """
        ret = []
        try:
            dim_reorder, dim_flip = self._get_transform(direction)
            #print(dim_reorder, dim_flip)
            #print("Re-orienting shape ", data.shape)
            if data is not None:
                dim_reorder = dim_reorder[:data.ndim]
                new_data = np.transpose(data, dim_reorder)
                for d in dim_flip:
                    new_data = np.flip(new_data, d)
                ret.append(new_data)
            #print("to: ", new_data.shape)
            if voxel_sizes is not None:
                dim_reorder = dim_reorder[:len(voxel_sizes)]
                ret.append([voxel_sizes[d] for d in dim_reorder])
        except:
            # If something goes wrong here, just leave the data
            # as it is. It probably means the affine transformation
            # is nothing like orthogonal and therefore the dimension
            # order is not a permutation
            warnings.warn("Failed to re-orient - non-orthogonal affine?")
            raise
            ret = []
            if data is not None: ret.append(data)
            if voxel_sizes is not None: ret.append(voxel_sizes)
            
        if len(ret) == 1: return ret[0]
        else: return tuple(ret)
            
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

    def _init_nifti(self, hdr, ignore_affine=False):
        self.nifti_header = hdr
        self.affine = hdr.get_best_affine()
        self.voxel_sizes = self.reorient(FileMetadata.ORIENT_TO_RAS, voxel_sizes=hdr.get_zooms())

    def _get_transform(self, direction):
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
        if len(self.voxel_sizes) == 4: dim_order.append(3)
        return dim_order, dim_flip

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

    def value_str(self, pos):
        """ Return the data value at pos as a string to an appropriate
        number of decimal places"""
        return str(np.around(self[tuple(pos[:self.ndim])], self.md.dps))

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
            slices[d] = slice(s1, s2)
        
        return slices

    def get_pencol(self, region):
        """
        Get an RGB pen colour for a given region
        """
        return self.get_lut()[region]

    def set_as_roi(self):
        if not hasattr(self.md, "regions"):
            self.md.regions = np.unique(self)
            self.md.regions = self.md.regions[self.md.regions > 0]
            self.dps = 0

    def get_lut(self, alpha=None):
        """
        Get the colour look up table for the ROI.
        """
        cmap = getattr(cm, 'jet')
        mx = max(self.md.regions)
        lut = [[int(255 * rgb1) for rgb1 in cmap(float(v)/mx)[:3]] for v in range(mx+1)]
        lut = np.array(lut, dtype=np.ubyte)

        if alpha is not None:
            # add transparency
            alpha1 = np.ones((lut.shape[0], 1))
            alpha1 *= alpha
            alpha1[0] = 0
            lut = np.hstack((lut, alpha1))

        return lut

def _init_nifti(nii, ignore_affine):
    # NB: np.asarray appears to convert to an array instead of a numpy memmap.
    # Appears to improve speed drastically as well as stop a bug with accessing the subset of the array
    # memmap has been designed to save space on ram by keeping the array on the disk but does
    # horrible things with performance, and analysis especially when the data is on the network.
    data = np.asarray(nii.get_data()).view(QpVolume)
    md = FileMetadata(data, nifti_header=nii.get_header(), ignore_affine=ignore_affine)
    return data, md
        
def load(fname, vtype=FileMetadata.DATA, ignore_affine=False):
    if os.path.isdir(fname):
        # A directory. It ought to contain DICOMs. Convert them to a Nifti
        sys.stdout.write("Converting DICOMS in %s..." % (os.path.basename(fname)))
        sys.stdout.flush()
        src_dcms = glob.glob('%s/*.dcm' % fname)
        stacks = dcmstack.parse_and_stack(src_dcms)
        stack = stacks.values()[0]
        nii = stack.to_nifti()
        sys.stdout.write("DONE\n")
        sys.stdout.flush()
        # FIXME should we do this?
        if nii.shape[-1] == 1:
            nii = squeeze_image(nii)
        data, md = _init_nifti(nii, ignore_affine)

    elif fname.endswith(".nii") or fname.endswith(".nii.gz"):
        # File is a nifti
        nii = nib.load(fname)
        data, md = _init_nifti(nii, ignore_affine)

    elif fname.endswith(".nrrd"):
        # file is a nrrd
        data = nrrd.read(fname).view(QpVolume)
        md = FileMetadata(data)
    else:
        raise RuntimeError("%s: Unrecognized file type" % fname)

    ret = data.view(QpVolume)
    md.set_fname(fname)
    ret.md = md
    ret.remove_nans()
    if vtype == FileMetadata.ROI:
        ret = data.astype(np.int32)
    return ret

def save(data, fname):
    hdr = None
    affine = np.identity(4)
    if hasattr(data, "md"):
        # Invert axis transformations
        data = data.md.reorient(FileMetadata.ORIENT_TO_FILE, data=data)
        affine = data.md.affine
        try:
            hdr = getattr(data.md, "nifti_header")
        except:
            pass # create new with voxel sizes?
    
    img = nib.Nifti1Image(data, affine, header=hdr)
    img.update_header()
    img.to_filename(fname)
    data.md.set_fname(fname)
