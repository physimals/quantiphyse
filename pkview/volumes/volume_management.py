"""

Author: Benjamin Irving (benjamin.irv@gmail.com)
Copyright (c) 2013-2015 University of Oxford, Benjamin Irving

- Data management framework

"""

from __future__ import division, print_function

import sys
import os
import math
import warnings
import glob

from PySide import QtCore, QtGui
from matplotlib import cm

import nibabel as nib
import dcmstack
import numpy as np
import nrrd

class Volume(object):
    """
    Image data class

    Subclasses specifically for overlays and ROIs also exist, but most of they
    code is generic to all

    The major issue with image data is orientation. This is how we handle it.

    A volume's data has an original shape (dimensions)
    However it may be re-oriented to a different shape by permuting/flipping axes
    using an affine matrix. This raises two issues: behaviour on load and behaviour
    on save.

    On load, we get the affine from the file as best we can (NIFTI: get_best_affine())
    We re-orient the data as required, but also save the original data shape and the
    list of transpositions and axis flips we performed. Internally data is always oriented 
    in RAS dimensions.

    On save, we want to make sure that data loaded from a file is saved identically.
    So we need to undo the transformations on the data and then use the original affine.

    Data created internally poses an issue - we could reasonably save it using a diagonal
    affine and without transposing anything, however this may make non-compilant viewers
    complain because the raw axes order looks different. So instead we inherit
    the affine and transformations from the main volume so everything looks consistent.

    Then there is the issue of expanded dimensions, e.g. 2D volumes expanded to 3d
    for internal use. We keep a list of expanded dimensions so they can be squeezed out
    on save. Note that this list needs to be updated during re-orientation although typically
    this does not do anything as the expanding is normally called after re-orientation.

    Finally we have file that have broken affines. So, if an overlay or ROI does not
    match the main data shape after re-orientation, we check if the original shape did
    match, and if so we can offer the user the option of ignoring the file orientation and
    treating it as if the data was created internally. This will result in the file being
    'fixed' on save.
    """
    
    def __init__(self, name, data=None, fname=None, affine=None):
        self.fname = fname
        if fname is not None:
            self.dir, self.basename = os.path.split(fname)
        else:
            self.dir, self.basename = None, None
        self.name = name
        self.data = data
        self.voxel_sizes = None
        self.nifti_header = None
        self.affine = affine
        self.dim_expand = []

        if self.data is not None and self.fname is not None:
            raise RuntimeError("Creating volume, given both data and filename!")
        elif self.fname is not None:
            self.load()
        elif self.data is None:
            raise RuntimeError("Creating volume, must be given either data or filename")
        self.remove_nans()

        self.ndim = self.data.ndim
        self.shape = self.data.shape
        self.orig_shape = self.data.shape
        if self.voxel_sizes is None: self.voxel_sizes = [1.0, ] * self.ndim
        if self.affine is None: self.affine = np.identity(4)
        self._reorient()

        self.range = [np.min(self.data), np.max(self.data)]
        self.dps = self._calc_dps()
        
    def _calc_dps(self):
        """
        Return appropriate number of decimal places for presenting data values
        """
        if self.range[1] == self.range[0]:
            # Pathological case where data is uniform
            return 0
        else:
            # Look at range of data and allow decimal places to give at least 1% steps
            return max(1, 3-int(math.log(self.range[1]-self.range[0], 10)))

    def force_ndim(self, n, multi=True):
        """
        Force this volume into n dimensions if it isn't already

        If multi=True, assume last dimension is multiple volumes (e.g. time series) 
        and pad other dimensions only
        """
        #print("Forcing to %i dims, multi=%s, current shape=%s" % (n, str(multi), str(self.shape)))
        self.multi = multi
        if self.ndim > n:
            raise RuntimeError("Can't force volume to %i dims since ndim > %i" % (n, n))
        elif multi:
            for i in range(n-self.ndim):
                self.data = np.expand_dims(self.data, self.ndim-1)
                self.dim_expand.append(self.ndim-1+i)
                self.voxel_sizes.insert(self.ndim-1, 1.0)
        else:
            for i in range(n-self.ndim):
                self.data = np.expand_dims(self.data, self.ndim)
                self.dim_expand.append(self.ndim+i)
                self.voxel_sizes.insert(self.ndim, 1.0)
        self.shape = self.data.shape
        self.ndim = n

    def save_nifti(self, fname):
        data = self.data
        # Remove axes that were added to pad to 4d
        for dim in self.dim_expand:
            #print("Squeezing axis", dim)
            data = np.squeeze(data, dim)
        
        # Invert axis transformations
        order, flip = self._get_transform(invert=True)
        data, shape, voxel_sizes = self._transform(order, flip, data)

        if not hasattr(self, "nifti_header"): self.nifti_header = None
        img = nib.Nifti1Image(data, self.affine, header=self.nifti_header)
        img.update_header()
        img.to_filename(fname)
        self.fname = fname

    def _init_from_nifti(self, image):
        # NB: np.asarray appears to convert to an array instead of a numpy memmap.
        # Appears to improve speed drastically as well as stop a bug with accessing the subset of the array
        # memmap has been designed to save space on ram by keeping the array on the disk but does
        # horrible things with performance, and analysis especially when the data is on the network.
        self.data = np.asarray(image.get_data())
        self.voxel_sizes = list(image.get_header().get_zooms())
        self.nifti_header = image.get_header()
        if self.affine is None:
            self.affine = self.nifti_header.get_best_affine()

    def load(self):
        if os.path.isdir(self.fname):
            # A directory. It ought to contain DICOMs. Convert them to a Nifti
            sys.stdout.write("Converting DICOMS in %s..." % (os.path.basename(self.fname)))
            sys.stdout.flush()
            src_dcms = glob.glob('%s/*.dcm' % self.fname)
            stacks = dcmstack.parse_and_stack(src_dcms)
            stack = stacks.values()[0]
            nii = stack.to_nifti()
            # FIXME should we do this?
            if nii.shape[-1] == 1:
                nii = squeeze_image(nii)
            self._init_from_nifti(nii)
            sys.stdout.write("DONE\n")
            sys.stdout.flush()
        elif self.fname.endswith(".nii") or self.fname.endswith(".nii.gz"):
            # File is a nifti
            image = nib.load(self.fname)
            self._init_from_nifti(image)     
        elif self.fname.endswith(".nrrd"):
            # file is a nrrd
            self.data = nrrd.read(self.fname)
        else:
            raise RuntimeError("%s: Unrecognized file type" % self.fname)

    def value_str(self, pos):
        """ Return the data value at pos as a string to an appropriate
        number of decimal places"""
        return str(np.around(self.data[tuple(pos[:self.ndim])], self.dps))

    def _get_transform(self, invert=False):
        """
        Returns dim_order, dim_flip transformations
        to turn data into RAS order
        """
        affine = self.affine
        if invert: affine = affine.transpose()
        space_affine = affine[:3,:3]
        space_pos = np.absolute(space_affine)
        #print(space_affine)
        #print(space_pos)
        dim_order, dim_flip = [], []
        for d in range(3):
            newd = np.argmax(space_pos[:,d])
            dim_order.append(newd)
            if space_affine[newd, d] < 0:
                dim_flip.append(d)
        if self.ndim == 4: dim_order.append(3)
        return dim_order, dim_flip
        #print(dims, flip)

    def _transform(self, dim_order, dim_flip, data=None):
        """
        Permute and flip axes

        returns modified data, shape and voxel sizes
        """
        try:
            if data is None: data = self.data
            #print("Re-orienting shape ", self.shape, self.voxel_sizes)
            new_data = np.transpose(data, dim_order)
            for d in dim_flip:
                new_data = np.flip(new_data, d)
            new_voxel_sizes = [self.voxel_sizes[dim_order[i]] for i in range(self.ndim)]
            #print("Re-oriented to dim order ", dim_order)
            #print("New shape", new_data.shape, new_voxel_sizes)
            return new_data, new_data.shape, new_voxel_sizes
        except:
            # If something goes wrong here, just leave the data
            # as it is. It probably means the affine transformation
            # is nothing like orthogonal and therefore the dimension
            # order is not a permutation
            warnings.warn("Failed to re-orient - non-orthogonal affine?")
            return self.data, self.shape, self.voxel_sizes

    def _reorient(self):
        self.data, self.shape, self.voxel_sizes = self._transform(*self._get_transform())

    def slice(self, *axes):
        """ 
        Get a slice

        axes is a sequence of tuples of (axis number, position)
        """
        sl = [slice(None)] * self.data.ndim
        for axis, pos in axes:
            sl[axis] = pos
        return self.data[sl]

    def check_shape(self, shape):
        ndim = min(self.ndim, len(shape))
        if (list(self.shape[:ndim]) != list(shape[:ndim])):
            raise RuntimeError("First %i Dimensions of must be %s - they are %s" % (ndim, shape[:ndim], self.shape[:ndim]))

    def remove_nans(self):
        """
        Check for and remove nans from images
        """
        nans = np.isnan(self.data)
        if nans.sum() > 0:
            warnings.warn("Image contains nans")
            self.data[nans] = 0

    def copy_orientation(self, vol):
        """
        Copy size and orientation information from another volume.

        Used for overlays and ROIs so they save an orientation consistent with the main volume
        """
        if hasattr(vol, "nifti_header"): 
            self.nifti_header = vol.nifti_header.copy()
            self.nifti_header.set_data_shape(self.orig_shape)
            self.nifti_header.set_data_dtype(self.data.dtype)

        self.affine = vol.affine
        self.voxel_sizes = vol.voxel_sizes

class Overlay(Volume):
    def __init__(self, name, data=None, fname=None, **kwargs):
        super(Overlay, self).__init__(name, data, fname, **kwargs)
        
class Roi(Volume):
    def __init__(self, name, data=None, fname=None, **kwargs):
        super(Roi, self).__init__(name, data, fname, **kwargs)
        if self.range[0] < 0 or self.range[1] > 2**32:
            raise RuntimeError("ROI must contain values between 0 and 2**32")

        if not np.equal(np.mod(self.data, 1), 0).any():
            msgBox = QtGui.QMessageBox()
            msgBox.setText("WARNING: ROI contains non-integer values. These will be truncated to integers")
            msgBox.setStandardButtons(QMessageBox.Ok | QMessageBox.Cancel)
            if msgBox.exec_() == QMessageBox.Cancel:
                raise RuntimeError("ROI not loaded")

        # patch to fix roi loading when a different type.
        self.data = self.data.astype(np.int32)
        self.regions = np.unique(self.data)
        self.regions = self.regions[self.regions > 0]
        #print("ROI: Regions", self.regions)
        self.lut = self.get_lut()
        self.dps = 0
        #print("ROI: LUT=", self.lut)

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
            nonzero = np.any(self.data, axis=tuple(ax))
            s1, s2 = np.where(nonzero)[0][[0, -1]]
            slices[d] = slice(s1, s2)
        
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

        mx = max(self.regions)
        lut = [[int(255 * rgb1) for rgb1 in cmap(float(v)/mx)[:3]] for v in range(mx+1)]
        lut = np.array(lut, dtype=np.ubyte)

        if alpha is not None:
            # add transparency
            alpha1 = np.ones((lut.shape[0], 1))
            alpha1 *= alpha
            alpha1[0] = 0
            lut = np.hstack((lut, alpha1))

        return lut

class ImageVolumeManagement(QtCore.QAbstractItemModel):
    """
    ImageVolumeManagement
    1) Holds all image volumes used in analysis
    2) Better support for switching volumes instead of having a single volume hardcoded

    Has to inherit from a Qt base class that supports signals
    Note that the correct QT Model/View structure has not been set up but is intended in future
    """
    # Signals

    # Change to main volume
    sig_main_volume = QtCore.Signal(Volume)

    # Change to current overlay
    sig_current_overlay = QtCore.Signal(Overlay)

    # Change to set of overlays (e.g. new one added)
    sig_all_overlays = QtCore.Signal(list)

    # Change to current ROI
    sig_current_roi = QtCore.Signal(Roi)

    # Change to set of ROIs (e.g. new one added)
    sig_all_rois = QtCore.Signal(list)

    def __init__(self):
        super(ImageVolumeManagement, self).__init__()
        self.reset()

    def reset(self):
        """
        Reset to empty, signalling any connected widgets
        """
        # Main background image
        self.vol = None

        self.voxel_sizes = [1.0, 1.0, 1.0]
        self.shape = []

        # Map from name to overlay object
        self.overlays = {}

        # Current overlay object
        self.current_overlay = None

        # Map from name to ROI object
        self.rois = {}

        # Processing artifacts
        self.artifacts = {}

        # Current ROI object
        self.current_roi = None

        # Current position of the cross hair as an array
        self.cim_pos = np.array([0, 0, 0, 0], dtype=np.int)

        self.sig_main_volume.emit(self.vol)
        self.sig_current_overlay.emit(self.current_overlay)
        self.sig_current_roi.emit(self.current_roi)
        self.sig_all_rois.emit(self.rois.keys())
        self.sig_all_overlays.emit(self.overlays.keys())

    def check_shape(self, shape):
        ndim = min(len(self.shape), len(shape))
        if (list(self.shape[:ndim]) != list(shape[:ndim])):
            raise RuntimeError("First %i Dimensions must be %s - they are %s" % (ndim, self.shape[:ndim], shape[:ndim]))

    def update_shape(self, shape):
        self.check_shape(shape)
        for d in range(len(self.shape), min(len(shape), 4)):
            self.shape.append(shape[d])

    def set_main_volume(self, name):
        self._overlay_exists(name)
        
        self.vol = self.overlays[name]
        self.voxel_sizes = self.vol.voxel_sizes
        print("Voxel sizes are: ", self.voxel_sizes)
        self.update_shape(self.vol.shape)

        #print(self.cim_pos)
        self.cim_pos = [int(d/2) for d in self.vol.shape]
        if self.vol.ndim == 3: self.cim_pos.append(0)
        self.sig_main_volume.emit(self.vol)

    def add_overlay(self, ov, make_current=False, make_main=False, signal=True):
        ov.force_ndim(max(3, ov.ndim), multi=(ov.ndim == 4))
        self.update_shape(ov.shape)

        self.overlays[ov.name] = ov
        if signal:
            self.sig_all_overlays.emit(self.overlays.keys())

        if make_current:
            self.set_current_overlay(ov.name, signal)

        if make_main or self.vol is None:
            self.set_main_volume(ov.name)

    def _vol_exists(self):
        if self.vol is None:
            raise RuntimeError("Main volume not loaded")

    def _overlay_exists(self, name, invert=False):
        if name not in self.overlays:
            raise RuntimeError("Overlay %s does not exist" % name)

    def _roi_exists(self, name):
        if name not in self.rois:
            raise RuntimeError("ROI %s does not exist" % name)

    def set_current_overlay(self, name, signal=True):
        self._overlay_exists(name)
        self.current_overlay = self.overlays[name]
        if signal: self.sig_current_overlay.emit(self.current_overlay)

    def rename_overlay(self, name, newname, signal=True):
        self._overlay_exists(name)
        ovl = self.overlays[name]
        ovl.name = newname
        self.overlays[newname] = ovl
        del self.overlays[name]
        if signal: self.sig_all_overlays.emit(self.overlays.keys())

    def rename_roi(self, name, newname, signal=True):
        self._roi_exists(name)
        roi = self.rois[name]
        roi.name = newname
        self.rois[newname] = roi
        del self.rois[name]
        if signal: self.sig_all_rois.emit(self.rois.keys())

    def delete_overlay(self, name, signal=True):
        self._overlay_exists(name)
        del self.overlays[name]
        if signal: self.sig_all_overlays.emit(self.overlays.keys())
        if self.current_overlay.name == name:
            self.current_overlay = None
            if signal: self.sig_current_overlay.emit(None)

    def delete_roi(self, name, signal=True):
        self._roi_exists(name)
        del self.rois[name]
        if signal: self.sig_all_rois.emit(self.rois.keys())
        if self.current_roi.name == name:
            self.current_roi = None
            if signal: self.sig_current_roi.emit(None)

    def add_roi(self, roi, make_current=False, signal=True):
        
        roi.force_ndim(3, multi=False)
        self.update_shape(roi.shape)
        self.rois[roi.name] = roi

        if signal:
            self.sig_all_rois.emit(self.rois.keys())
        if make_current:
            self.set_current_roi(roi.name, signal)

    def set_current_roi(self, name, signal=True):
        self._roi_exists(name)
        self.current_roi = self.rois[name]
        if signal:
            self.sig_current_roi.emit(self.current_roi)

    def get_overlay_value_curr_pos(self):
        """
        Get all the overlay values at the current position
        """
        overlay_value = {}

        # loop over all loaded overlays and save values in a dictionary
        for name, ovl in self.overlays.items():
            if ovl.ndim == 3:
                overlay_value[name] = ovl.data[self.cim_pos[0], self.cim_pos[1], self.cim_pos[2]]

        return overlay_value

    def get_current_enhancement(self):
        """
        Return enhancement curves for all 4D overlays whose 4th dimension matches that of the main volume
        """
        if self.vol is None: return [], {}
        if self.vol.ndim != 4: raise RuntimeError("Main volume is not 4D")

        main_sig = self.vol.data[self.cim_pos[0], self.cim_pos[1], self.cim_pos[2], :]
        ovl_sig = {}

        for ovl in self.overlays.values():
            if ovl.ndim == 4 and (ovl.shape[3] == self.vol.shape[3]):
                ovl_sig[ovl.name] = ovl.data[self.cim_pos[0], self.cim_pos[1], self.cim_pos[2], :]

        return main_sig, ovl_sig

    def add_artifact(self, name, obj):
        """
        Add an 'artifact', which can be any result of a process which
        is not voxel data, e.g. a number, table, etc.

        Artifacts are only required to support str() conversion so they
        can be written to a file
        """
        self.artifacts[name] = obj

    def set_blank_annotation(self):
        """
        - Initialise the annotation overlay
        - Set the annotation overlay to be the current overlay
        """
        self._vol_exists()

        ov = Overlay("annotation", np.zeros(self.vol.shape[:3]))
        # little hack to normalise the image from 0 to 10 by listing possible labels in the corner
        for ii in range(11):
            ov.data[0, ii] = ii

        self.add_overlay(ov, make_current=True, signal=True)

