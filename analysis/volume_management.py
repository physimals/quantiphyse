"""
- Data management framework

"""

from __future__ import division, print_function

from PySide import QtCore
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

    def __init__(self):
        super(ImageVolumeManagement, self).__init__()

        self.init()

    def init(self):
        """
        Initilises all the volumes.
        Allows reinitialisation when loading a new image.
        """
        # Main background image
        self.image_file1 = None
        self.image = np.zeros((1, 1, 1))
        # Current image position and size
        self.img_dims = self.image.shape
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
        # List of possible overlays that can be loaded
        self.overlay_label_all = ['loaded', 'Ktrans', 'kep', 've', 'vp', 'offset', 'residual', 'T10', 'annotation',
                                  'segmentation']

        # All overlays
        self.overlay_all = {}

        # ROI image
        self.roi = None
        self.roi_all = []  # All rois
        self.roi_dims = None
        self.roi_file1 = None
        # Number of ROIs
        self.num_roi = 0

        #Estimated volume from pk modelling
        self.estimated = None

        # Current position of the cross hair
        self.cim_pos = [0, 0, 0, 0]

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
            self.overlay_all['annotation'] = np.zeros(self.image.shape[:-1])

            #little hack to normalise the image from 0 to 10 by listing possible labels in the corner
            for ii in range(11):
                self.overlay_all['annotation'][0, ii] = ii
        else:
            print("Please load an image first")

        #update overlay list
        self.sig_all_overlays.emit(self.overlay_all.keys())
        #set current overlay
        self.set_current_overlay('annotation', broadcast_change=True)

    def set_overlay(self, choice1, ovreg):
        """

        Set an overlay for storage

        Choices:

        ['loaded', 'Ktrans', 'kep', 've', 'vp', 'offset', 'residual', 'T10']

        """

        if (ovreg.shape != self.img_dims[:3]) or (len(ovreg.shape) > 3):
            print("First 3 Dimensions of the overlay region must be the same as the image, "
                  "and overlay region must be 3D")
            return

        if choice1 not in self.overlay_label_all:
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

        if choice1 in self.overlay_label_all and choice1 in self.overlay_all.keys():
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
        self.image, self.voxel_size = self._load_med_file(self.image_file1)

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
        self.roi_file1 = file1
        self.roi, voxel_size = self._load_med_file(self.roi_file1)

        self.roi = self._remove_nans(self.roi)

        self.roi_all.append(self.roi)
        self.roi_dims = self.roi.shape

        if (self.roi_dims != self.img_dims[:3]) or (len(self.roi_dims) > 3):
            warnings.warn("First 3 Dimensions of the ROI must be the same as the image, and ROI must be 3D")
            self.roi = None
            self.roi_dims = None

        else:
            self.num_roi += 1

    def load_ovreg(self, file1, type1='loaded'):
        """

        Loads and checks Overlay region image

        """

        if self.image.shape[0] == 1:
            print("Please load an image first")
            return

        #Setting Overlay region data
        self.ovreg_file1 = file1

        overlay_load, self.voxel_size = self._load_med_file(self.ovreg_file1)

        overlay_load = self._remove_nans(overlay_load)

        if type1 == 'model_curves':

            self.set_estimated(overlay_load)

        else:

            # add the loaded overlay
            self.set_overlay(type1, overlay_load)

            # set the loaded overlay to be the current overlay
            self.set_current_overlay(type1)

    def set_cmap(self, cmap):
        """
        Saves the current colormap
        """

        self.cmap = cmap

    @staticmethod
    def _load_med_file(image_location):

        ii = image_location.find('.')
        ext1 = image_location[ii+1:]

        if ext1 == 'nii':

            # if the file is a nifti
            image = nib.load(image_location)
            # NB: np.asarray appears to convert to an array instead of a numpy memmap.
            # Appears to improve speed drastically as well as stop a bug with accessing the subset of the array
            # memmap has been designed to save space on ram by keeping the array on the disk but does
            # horrible things with performance, and analysis especially when the data is on the network.
            image1 = np.asarray(image.get_data())

            voxel_size = image.get_header().get_zooms()

        elif ext1 == 'nrrd':

            #else if the file is a nrrd
            image1, options1 = nrrd.read(image_location)
            voxel_size = [0, 0, 0]

        else:

            image1 = None
            voxel_size = None

        # otherwise return 0

        return image1, voxel_size

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








