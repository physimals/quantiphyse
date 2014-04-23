"""
- Develops the data management framework
- Currently just a skeleton with an interface
- Will allow more flexibility to manage the data for all widgets within this class
"""

from __future__ import division, print_function

import nibabel as nib
import numpy as np


class ImageVolumeManagement(object):

    """
    ImageVolumeManagement
    1) Holds all image volumes used in analysis
    2) Better support for switching volumes instead of having a single volume hardcoded
    """

    def __init__(self):

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
        self.overlay = []
        self.ovreg_dims = None
        self.ovreg_file1 = None

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
        return self.roi

    def set_roi(self, x):
        self.roi = x

    def set_image(self, x):
        self.image = x

    def set_overlay(self, x):
        self.overlay = x

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

        self.img_range = [self.image.min(), self.image.max()]

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
        self.overlay = np.array(ovreg.get_data())
        self.ovreg_dims = self.overlay.shape

        if (self.ovreg_dims != self.img_dims[:3]) or (len(self.ovreg_dims) > 3):
            print("First 3 Dimensions of the overlay region must be the same as the image, "
                  "and overlay region must be 3D")
            self.overlay = None
            self.ovreg_dims = None







