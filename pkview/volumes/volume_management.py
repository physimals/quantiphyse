"""

Author: Benjamin Irving (benjamin.irv@gmail.com)
Copyright (c) 2013-2015 University of Oxford, Benjamin Irving

- Data management framework

"""

from __future__ import division, print_function

from PySide import QtCore, QtGui
import nibabel as nib
import numpy as np
import warnings
import nrrd


class ImageVolumeManagement(QtCore.QAbstractItemModel):
    """
    ImageVolumeManagement
    1) Holds all image volumes used in analysis
    2) Better support for switching volumes instead of having a single volume hardcoded

    Has to inherit from a Qt base class that supports signals
    Note that the correct QT Model/View structure has not been set up but is intended in future
    """

    # Signals
    sig_current_overlay = QtCore.Signal(str)
    # Signal all overlays
    sig_all_overlays = QtCore.Signal(list)
    sig_current_roi = QtCore.Signal(str)
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
        self.image_file1 = None
        self.image = None #np.zeros((1, 1, 1))
        # Current image position and size
        self.img_dims = None #self.image.shape
        #Voxel size initialisation
        self.voxel_size = [1.0, 1.0, 1.0]
        # Range of image
        self.img_range = [0, 1]

        # Current overlay
        self.overlay = None
        self.ovreg_dims = None
        self.ovreg_file1 = None
        # Type of the current overlay
        self.overlay_label = None

        # List of default overlays that can be loaded
        self.overlay_label_all = ['loaded', 'Ktrans', 'kep', 've', 'vp', 'offset', 'residual', 'T10', 'annotation',
                                  'segmentation', 'clustering']

        # Current overlay range
        self.ov_range = [0.0, 1.0]

        # All overlays
        self.overlay_all = {}

        # Current ROI image
        self.roi = None
        self.roi_dims = None
        self.roi_file1 = None
        # Number of ROIs
        self.rois = {}
        self.num_roi = 0

        #Estimated volume from pk modelling
        self.estimated = None

        # Current position of the cross hair as an array
        self.cim_pos = np.array([0, 0, 0, 0], dtype=np.int)

        # Current color map
        self.cmap = None

    def get_roi(self):
        return self.roi

    def get_image(self):
        return self.image

    def get_overlay(self):
        return self.overlay

    def get_T10(self):

        if 'T10' in self.overlay_all:
            return self.overlay_all['T10']
        else:
            return None

    def get_image_shape(self):
        if self.image is None:
            return None
        else:
            return self.image.shape

    def get_current_enhancement(self):
        """
        Return enhancement curve
        """

        vec_sig = self.image[self.cim_pos[0], self.cim_pos[1], self.cim_pos[2], :]

        if self.estimated is not None:
            vec_sig_est = self.estimated[self.cim_pos[0], self.cim_pos[1], self.cim_pos[2], :]
        else:
            vec_sig_est = np.zeros(vec_sig.shape)

        return vec_sig, vec_sig_est

    def get_overlay_value_curr_pos(self):
        """
        Get all the overlay parameters at the current position
        """
        # initialise python dictionary
        overlay_value = {}

        # loop over all loaded overlays and save values in a dictionary
        for ii in self.overlay_all.keys():
            overlay_value[ii] = self.overlay_all[ii][self.cim_pos[0], self.cim_pos[1], self.cim_pos[2]]

        return overlay_value

    def set_roi(self, x):
        self.roi = x

    def set_image(self, x):
        self.image = x

    def set_T10(self, x):
        self.overlay_all['T10'] = x

    def set_estimated(self, x):
        self.estimated = x

    def set_blank_annotation(self):
        """
        - Initialise the annotation overlay
        - Set the annotation overlay to be the current overlay
        """
        if self.image is not None:
            self.overlay_all['annotation'] = np.zeros(self.image.shape[:3])

            # little hack to normalise the image from 0 to 10 by listing possible labels in the corner
            for ii in range(11):
                self.overlay_all['annotation'][0, ii] = ii
        else:
            print("Please load an image first")

        # update overlay list
        self.sig_all_overlays.emit(self.overlay_all.keys())
        # set current overlay
        self.set_current_overlay('annotation', broadcast_change=True)

    def set_overlay(self, choice1, ovreg, force=False):
        """

        Set an overlay for storage

        Choices:

        ['loaded', 'Ktrans', 'kep', 've', 'vp', 'offset', 'residual', 'T10']

        """

        if (ovreg.shape[:3] != self.img_dims[:3]) or (len(ovreg.shape) > 4):
            print("First 3 Dimensions of the overlay region must be the same as the image, "
                  "and overlay region must be 3D (or 4D for RGBa images)")
            return

        if (choice1 not in self.overlay_label_all) and (force is False):
            print("Warning: Label choice is incorrect")
            return

        self.overlay_all[choice1] = ovreg
        self.overlay_label = choice1

        # emit all overlays (QtCore)
        self.sig_all_overlays.emit(self.overlay_all.keys())

    def set_current_overlay(self, choice1, broadcast_change=True):
        """

        Set the current overlay

        """

        if choice1 in self.overlay_all.keys():
            self.overlay_label = choice1
            self.overlay = self.overlay_all[choice1]
            self.ovreg_dims = self.overlay.shape
        else:
            print("Warning: Label choice is incorrect")

        # emit current overlay (QtCore)
        if broadcast_change:
            self.sig_current_overlay.emit(self.overlay_label)

    def load_image(self, image_file1):
        """

        Loading nifti image

        self.img: variable storing numpy volume
        self.img_dims: dimensions of the image

        """

        self.image_file1 = image_file1
        self.image, self.voxel_size, self.hdr = self._load_med_file(self.image_file1)

        self.image = self._remove_nans(self.image)

        self.img_dims = self.image.shape

        # 90% of the image range
        self.img_range = [self.image.min(), 0.5*self.image.max()]

        print("Image dimensions: ", self.img_dims)
        print("Voxel size: ", self.voxel_size)
        print("Image range: ", self.img_range)

    def load_roi(self, file1):
        """

        Loads and checks roi image
        Initialise viewing windows

        """

        if self.image.shape[0] == 1:
            print("Please load an image first")
            return

        #Setting ROI data
        roi, voxel_size, _ = self._load_med_file(file1)
        roi = self._remove_nans(roi)

        # patch to fix roi loading when a different type.
        roi = roi.astype(np.float64)

        dims = roi.shape
        if (dims != self.img_dims[:3]) or (len(dims) > 3):

            warnings.warn("First 3 Dimensions of the ROI must be the same as the image, and ROI must be 3D")

            # Checking if data already exists
            msgBox = QtGui.QMessageBox()
            msgBox.setText("First 3 Dimensions of the ROI must be the same as the image, and ROI must be 3D")
            ret = msgBox.exec_()
        else:
            self.rois[file1] = roi
            self.num_roi += 1
            self.sig_all_rois.emit(self.rois.keys())  
            self.set_current_roi(file1)      

    def set_current_roi(self, roi_file, broadcast_change=True):
        """ 
        Set the current ROI to the specified file.
        """
        print("Setting current ROI to: " + roi_file)
        self.roi_file1 = roi_file
        self.roi = self.rois[roi_file]
        self.roi_dims = self.roi.shape
        if broadcast_change:
            self.sig_current_roi.emit(roi_file)        

    def load_ovreg(self, file1, type1='loaded'):
        """

        Loads and checks Overlay region image

        """
        if self.image.shape[0] == 1:
            print("Please load an image first")
            return

        #Setting Overlay region data
        self.ovreg_file1 = file1
        overlay_load, self.voxel_size, _ = self._load_med_file(self.ovreg_file1)
        overlay_load = self._remove_nans(overlay_load)

        if type1 == 'model_curves':
            self.set_estimated(overlay_load)

        else:
            # add the loaded overlay
            self.set_overlay(type1, overlay_load)
            # set the loaded overlay to be the current overlay
            self.set_current_overlay(type1)

    def save_ovreg(self, file1, type1):
        """

        Save an overlay as a nifti file

        """

        if type1 == 'current':
            data1 = self.overlay
        else:
            data1 = self.overlay_all[type1]

        # get header
        header1 = self.hdr

        # modify header
        shp1 = header1.get_data_shape()
        header1.set_data_shape(shp1[:-1])
        header1.set_data_dtype(data1.dtype)

        # Save the current overlay or save a specific overlay
        img1 = nib.Nifti1Image(data1, header1.get_base_affine(), header=header1)
        # Save image
        img1.to_filename(file1)

    def set_cmap(self, cmap):
        """
        Saves the current colormap
        """
        self.cmap = cmap

    @staticmethod
    def _load_med_file(image_location):
        if image_location.endswith(".nii") or image_location.endswith(".nii.gz"):
            # if the file is a nifti
            image = nib.load(image_location)
            # NB: np.asarray appears to convert to an array instead of a numpy memmap.
            # Appears to improve speed drastically as well as stop a bug with accessing the subset of the array
            # memmap has been designed to save space on ram by keeping the array on the disk but does
            # horrible things with performance, and analysis especially when the data is on the network.
            image1 = np.asarray(image.get_data())

            voxel_size = image.get_header().get_zooms()

            hdr = image.get_header()

        elif image_location.endswith(".nrrd"):
            #else if the file is a nrrd
            image1, options1 = nrrd.read(image_location)
            voxel_size = [0, 0, 0]
            hdr = None

        else:
            image1 = None
            voxel_size = None
            hdr = None

        # otherwise return 0

        return image1, voxel_size, hdr

    @staticmethod
    def _remove_nans(image1):
        """

        Function to check for and remove nans from images

        """

        nan1 = np.isnan(image1)

        if nan1.sum() > 0:
            warnings.warn("Image contains nans")
            image1[nan1] = 0

        return image1








