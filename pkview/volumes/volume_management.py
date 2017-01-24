"""

Author: Benjamin Irving (benjamin.irv@gmail.com)
Copyright (c) 2013-2015 University of Oxford, Benjamin Irving

- Data management framework

"""

from __future__ import division, print_function

from PySide import QtCore, QtGui
from matplotlib import cm
import nibabel as nib
import numpy as np
import warnings
import nrrd

import os

class Volume(object):
    def __init__(self, name, data=None, fname=None):
        self.fname = fname
        self.name = name
        self.data = data
        self.voxel_sizes = None
        self.nifti_header = None
        if self.data is not None and self.fname is not None:
            raise RuntimeError("Creating volume, given both data and filename!")
        elif self.fname is not None:
            self.load()
        elif self.data is None:
            raise RuntimeError("Creating volume, must be given either data or filename")
        self.remove_nans()

        self.shape = self.data.shape
        self.ndims = len(self.shape)
        self.range = [np.min(self.data), np.max(self.data)]
        if self.voxel_sizes is None:
            self.voxel_sizes = [1.0, ] * self.ndims

    def save_nifti(self, fname):
        if self.nifti_header is None:
            warnings.warn("No NIFTI header information available")
            img = nib.Nifti1Image(ov.data, np.identity(self.ndims))
        else:
            img = nib.Nifti1Image(ov.data, self.nifti_header.get_base_affine(), header=self.nifti_header)
        img.to_filename(fname)
        self.fname = fname

    def load(self):
        if self.fname.endswith(".nii") or self.fname.endswith(".nii.gz"):
            # File is a nifti
            image = nib.load(self.fname)

            # NB: np.asarray appears to convert to an array instead of a numpy memmap.
            # Appears to improve speed drastically as well as stop a bug with accessing the subset of the array
            # memmap has been designed to save space on ram by keeping the array on the disk but does
            # horrible things with performance, and analysis especially when the data is on the network.
            self.data = np.asarray(image.get_data())
            self.voxel_sizes = image.get_header().get_zooms()
            self.nifti_header = image.get_header()
        elif self.fname.endswith(".nrrd"):
            # else if the file is a nrrd
            self.data = nrrd.read(self.fname)
        else:
            raise RuntimeError("%s: Unrecognized file type" % self.fname)

    def check_shape(self, shape):
        ndims = min(self.ndims, len(shape))
        if (list(self.shape[:ndims]) != list(shape[:ndims])):
            raise RuntimeError("First %i Dimensions of must be %s - they are %s" % (ndims, shape[:ndims], self.shape[:ndims]))

    def remove_nans(self):
        """
        Check for and remove nans from images
        """
        nans = np.isnan(self.data)
        if nans.sum() > 0:
            warnings.warn("Image contains nans")
            self.data[nans] = 0

class Overlay(Volume):
    def __init__(self, name, data=None, fname=None):
        super(Overlay, self).__init__(name, data, fname)
        self.data_roi = data
        self.range_roi = self.range

    def set_roi(self, roi):
        # Get data inside the ROI
        self.data_roi = np.copy(self.data)

        if self.ndims == 3:
            roidata = roi.data
        else:
            roidata = np.expand_dims(roi.data, 3).repeat(self.shape[3], 3)

        within_roi = self.data_roi[np.array(roidata, dtype=bool)]
        self.range_roi = [np.min(within_roi), np.max(within_roi)]
        # Set region outside the ROI to be slightly lower than the minimum value inside the ROI
        # FIXME what if range is zero?
        self.roi_fillvalue = -0.01 * (self.range_roi[1] - self.range_roi[0]) + self.range_roi[0]
        self.data_roi[np.logical_not(roidata)] = self.roi_fillvalue

class Roi(Volume):
    def __init__(self, name, data=None, fname=None):
        super(Roi, self).__init__(name, data, fname)
        if self.range[0] < 0 or self.range[1] > 255:
            raise RuntimeError("ROI must contain values between 0 and 255")

        if not np.equal(np.mod(self.data, 1), 0).any():
            msgBox = QtGui.QMessageBox()
            msgBox.setText("WARNING: ROI contains non-integer values. These will be truncated to integers")
            msgBox.setStandardButtons(QMessageBox.Ok | QMessageBox.Cancel)
            if msgBox.exec_() == QMessageBox.Cancel:
                raise RuntimeError("ROI not loaded")

        # patch to fix roi loading when a different type.
        self.data = self.data.astype(np.int8)
        self.regions = np.unique(self.data)
        self.regions = self.regions[self.regions > 0]
        #print("ROI: Regions", self.regions)
        self.lut = self.get_lut()
        #print("ROI: LUT=", self.lut)

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
        #print([float(v)/mx for v in range(mx)])
        #print([cmap(float(v)/mx) for v in range(mx)])

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

        self.init()

    def init(self):
        """
        Initilises all the volumes.
        *** NB Allows reinitialisation when loading a new image ***
        """
        # Main background image
        self.vol = None

        # Map from name to overlay object
        self.overlays = {}

        # Current overlay object
        self.current_overlay = None

        # List of known overlay types that can be loaded
        self.overlay_label_all = ['loaded', 'Ktrans', 'kep', 've', 'vp', 'offset', 'residual', 'T10', 'annotation',
                                  'segmentation', 'clustering']

        # Map from name to ROI object
        self.rois = {}

        # Current ROI object
        self.current_roi = None

        # Estimated volume from pk modelling
        self.estimated = None

        # Current position of the cross hair as an array
        self.cim_pos = np.array([0, 0, 0, 0], dtype=np.int)

    def set_main_volume(self, vol):
        if self.vol is not None:
            raise RuntimeError("Main volume already loaded")

        self.vol = vol

        # 90% of the image range
        # FIXME unclear what the purpose of this is. If for viewing, should be done on ImageView histogram widget
        #self.img_range = [self.image.min(), 0.5 * self.image.max()]

        self.sig_main_volume.emit(self.vol)

    def add_overlay(self, ov, make_current=False, signal=True, std_only=False):
        if self.vol is None:
            raise RuntimeError("Cannot add overlay with no main volume")

        if std_only and ov.name not in self.overlay_label_all:
            raise RuntimeError("Overlay name is not a known type")

        ov.check_shape(self.vol.shape)
        if self.vol.nifti_header is not None:
            header = self.vol.nifti_header.copy()
            header.set_data_shape(ov.shape)
            header.set_data_dtype(ov.data.dtype)
            ov.nifti_header = header

        self.overlays[ov.name] = ov
        if signal:
            self.sig_all_overlays.emit(self.overlays.keys())
        if make_current:
            self.set_current_overlay(ov.name, signal)

    def set_current_overlay(self, name, signal=True):
        if name in self.overlays:
            self.current_overlay = self.overlays[name]
            if self.current_roi is not None:
                self.current_overlay.set_roi(self.current_roi)
        else:
            raise RuntimeError("set_current_overlay: overlay %s does not exist" % name)

        if signal:
            self.sig_current_overlay.emit(self.current_overlay)

    def add_roi(self, roi, make_current=False, signal=True):
        if roi.ndims != 3:
            raise RuntimeError("ROI must be 3D")

        roi.check_shape(self.vol.shape)
        if self.vol.nifti_header is not None:
            header = self.vol.nifti_header.copy()
            header.set_data_shape(roi.shape)
            header.set_data_dtype(roi.data.dtype)
            roi.nifti_header = header

        self.rois[roi.name] = roi

        if signal:
            self.sig_all_rois.emit(self.rois.keys())
        if make_current:
            self.set_current_roi(roi.name, signal)

    def set_current_roi(self, name, signal=True):
        if name in self.rois:
            self.current_roi = self.rois[name]
            if self.current_overlay is not None:
                self.current_overlay.set_roi(self.current_roi)
        else:
            raise RuntimeError("set_current_roi: ROI %s does not exist" % name)

        if signal:
            self.sig_current_roi.emit(self.current_roi)

    def get_overlay_value_curr_pos(self):
        """
        Get all the overlay values at the current position
        """
        # initialise python dictionary
        overlay_value = {}

        # loop over all loaded overlays and save values in a dictionary
        for ii in self.overlays.keys():
            overlay_value[ii] = self.overlays[ii].data[self.cim_pos[0], self.cim_pos[1], self.cim_pos[2]]

        return overlay_value

    def get_current_enhancement(self):
        """
        Return enhancement curve
        """
        if self.vol is None: raise RuntimeError("No volume loaded")

        main_sig = self.vol.data[self.cim_pos[0], self.cim_pos[1], self.cim_pos[2], :]
        ovl_sig = {}

        for ovl in self.overlays.values():
            if ovl.ndims == 4:
                ovl_sig[ovl.name] = ovl.data[self.cim_pos[0], self.cim_pos[1], self.cim_pos[2], :]

        return main_sig, ovl_sig

    def set_blank_annotation(self):
        """
        - Initialise the annotation overlay
        - Set the annotation overlay to be the current overlay
        """
        if self.vol is not None:
            ov = Overlay("annotation", np.zeros(self.vol.shape[:3]))
            # little hack to normalise the image from 0 to 10 by listing possible labels in the corner
            for ii in range(11):
                ov.data[0, ii] = ii

            self.add_overlay(ov, make_current=True, signal=True)
        else:
            print("Please load an image first")
