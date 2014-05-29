"""
- Data management framework

"""

from __future__ import division, print_function

from PySide import QtCore
import nibabel as nib
import numpy as np


class ImageVolumeManagement(QtCore.QAbstractItemModel):
    """
    ImageVolumeManagement
    1) Holds all image volumes used in analysis
    2) Better support for switching volumes instead of having a single volume hardcoded

    Has to inherit from a Qt base class that supports signals
    Note that the correct QT Model/View structure has not been set up but is intended in future
    """

    #Signalse
    sig_current_overlay = QtCore.Signal(str)
    sig_all_overlays = QtCore.Signal(list)

    def __init__(self):
        super(ImageVolumeManagement, self).__init__()

        # Main background image
        self.image_file1 = None
        self.image = np.zeros((1, 1, 1))
        #Current image position and size
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
        self.overlay_label_all = ['loaded', 'ktrans', 'kep', 've', 'vp']

        # All overlays
        self.overlay_all = {}

        # ROI image
        self.roi = None
        self.roi_all = []  # All rois
        self.roi_dims = None
        self.roi_file1 = None
        # Number of ROIs
        self.num_roi = 0

        # Current position of the cross hair
        self.cim_pos = [0, 0, 0, 0]

    def get_roi(self):
        return self.roi

    def get_image(self):
        return self.image

    def get_overlay(self):
        return self.overlay

    def get_image_shape(self):
        return self.image.shape

    def set_roi(self, x):
        self.roi = x

    def set_image(self, x):
        self.image = x

    def set_overlay(self, choice1, ovreg):
        """
        Set an overlay for storage
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
        img = nib.load(self.image_file1)
        # NB: np.array appears to convert to an array instead of a numpy memmap.
        # Appears to improve speed drastically as well as stop a bug with accessing the subset of the array
        # memmap has been designed to save space on ram by keeping the array on the disk but does
        # horrible things with performance, and analysis especially when the data is on the network.
        self.image = np.array(img.get_data())
        self.img_dims = self.image.shape
        self.voxel_size = img.get_header().get_zooms()

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
        roi = nib.load(self.roi_file1)
        # NB: np.array appears to convert to an array instead of a numpy memmap.
        # Appears to improve speed drastically as well as stop a bug with accessing the subset of the array
        # memmap has been designed to save space on ram by keeping the array on the disk but does
        # horrible things with performance, and analysis especially when the data is on the network.
        self.roi = np.array(roi.get_data())
        self.roi_all.append(self.roi)
        self.roi_dims = self.roi.shape

        if (self.roi_dims != self.img_dims[:3]) or (len(self.roi_dims) > 3):
            print("First 3 Dimensions of the ROI must be the same as the image, "
                  "and ROI must be 3D")
            self.roi = None
            self.roi_dims = None

        else:
            self.num_roi += 1

    def load_ovreg(self, file1):
        """
        Loads and checks Overlay region image
        """

        if self.image.shape[0] == 1:
            print("Please load an image first")
            return

        #Setting Overlay region data
        self.ovreg_file1 = file1
        ovreg = nib.load(self.ovreg_file1)
        # NB: np.array appears to convert to an array instead of a numpy memmap.
        # Appears to improve speed drastically as well as stop a bug with accessing the subset of the array
        overlay_load = np.array(ovreg.get_data())

        # add the loaded overlay
        self.set_overlay('loaded', overlay_load)

        # set the loaded overlay to be the current overlay
        self.set_current_overlay('loaded')








