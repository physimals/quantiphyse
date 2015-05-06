"""

Author: Benjamin Irving (benjamin.irv@gmail.com)
Copyright (c) 2013-2015 University of Oxford, Benjamin Irving


Module for normalising the image prior to features extraction
"""
from __future__ import division, print_function

import numpy as np
from scipy.ndimage.filters import gaussian_filter1d


class ImNorm(object):

    """
    Preprocesses the images to try and establish consistency without converting to Gd concentration

    """

    def __init__(self, img1):

        self.img1 = img1

        # convert to list of enhancement curves
        if np.ndim(self.img1) > 2:
            self.image_input = True
            self.img1_shape = self.img1.shape
            self.img1 = self.img1.reshape((-1, self.img1.shape[-1]))
        else:
            self.image_input = False

        # Injection time
        self.ind1 = 0
        self.injection_time()

    def smooth(self):
        self.img1 = gaussian_filter1d(self.img1, sigma=2.0, axis=-1)
        None

    def injection_time(self):

        """
        Find the injection time as the point of maximum enhancement
        @return:
        """
        m1 = np.mean(self.img1, axis=0)
        d1 = m1[1:] - m1[:-1]
        ind1 = np.argmax(d1)
        ind1 -= 1
        ind1 *= ind1 >= 0
        print("Offset time: ", ind1)

        self.ind1 = ind1

        self.img1 = self.img1[:, ind1:]

        # just taking the first 20 time points for the meanwhile
        self.img1 = self.img1[:, :21]

    def offset_time(self):

        None

    def scale_norm(self, scale_position1=10):

        self.img1 = self.img1 / np.median(self.img1[:, scale_position1])

    def scale_percentile(self):

        perc1 = np.percentile(self.img1, 90)
        self.img1 = self.img1 / perc1

    def scale_indv(self):
        """
        Scale each signal enhancement curve by max and min

        @return:
        """

        min1 = np.tile(np.expand_dims(np.min(self.img1, axis=-1), axis=1), (1, self.img1.shape[-1]))
        self.img1 = self.img1 - min1

        max1 = np.tile(np.expand_dims(np.min(self.img1, axis=-1), axis=1), (1, self.img1.shape[-1]))
        self.img1 = self.img1 / (max1 + 0.001)

    def get_image(self):

        if self.image_input:
            None
        else:
            return self.img1
