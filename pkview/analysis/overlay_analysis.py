"""

Author: Benjamin Irving (benjamin.irv@gmail.com)
Copyright (c) 2013-2015 University of Oxford, Benjamin Irving

Library for simple analysis of the overlay parameters

Benjamin Irving

"""

import numpy as np


class OverlayAnalyis(object):
    """
    Class for analysing the imported overlay
    """

    def __init__(self):

        self.ivm = None

    def add_image_management(self, image_volume_management):
        """

        Imports the image volume management object to access data

        """
        self.ivm = image_volume_management

    def get_roi_stats(self):
        """
        Return:
        @m1 mean for each ROI
        @m2 median for each ROI
        @m3 standard deviation for each ROI
        @roi_labels label of each ROI
        """

        # Checks if either ROI or overlay is None
        if (self.ivm.roi is None) or (self.ivm.overlay is None):
            stat1 = {'mean': [0], 'median': [0], 'std': [0], 'max': [0], 'min': [0]}
            roi_labels = np.array([0])
            return stat1, roi_labels, np.array([0, 0]), np.array([0, 1])

        roi_labels = np.unique(self.ivm.roi)
        roi_labels = roi_labels[roi_labels > 0]

        stat1 = {'mean': [], 'median': [], 'std': [], 'max': [], 'min': []}
        hist1 = []
        hist1x = []

        for ii in roi_labels:

            # Overlay for a single label of the roi
            vroi1 = self.ivm.overlay[self.ivm.roi == ii]

            stat1['mean'].append(np.mean(vroi1))
            stat1['median'].append(np.median(vroi1))
            stat1['std'].append(np.std(vroi1))
            stat1['max'].append(np.max(vroi1))
            stat1['min'].append(np.min(vroi1))
            y, x = np.histogram(vroi1, bins=20)
            hist1.append(y)
            hist1x.append(x)

        return stat1, roi_labels, hist1, hist1x

    def get_roi_stats_ss(self):
        """
        Return:
        @m1 mean for each ROI
        @m2 median for each ROI
        @m3 standard deviation for each ROI
        @roi_labels label of each ROI
        """

        # Checks if either ROI or overlay is None
        if (self.ivm.roi is None) or (self.ivm.overlay is None):
            stat1 = {'mean': [0], 'median': [0], 'std': [0], 'max': [0], 'min': [0]}
            roi_labels = np.array([0])
            return stat1, roi_labels, np.array([0, 0]), np.array([0, 1])

        slice1 = self.ivm.cim_pos[2]

        overlay_slice = self.ivm.overlay[:, :, slice1]
        roi_slice = self.ivm.roi[:, :, slice1]

        roi_labels = np.unique(roi_slice)
        roi_labels = roi_labels[roi_labels > 0]

        stat1 = {'mean': [], 'median': [], 'std': [], 'max': [], 'min': []}
        hist1 = []
        hist1x = []

        for ii in roi_labels:

            # Overlay for a single label of the roi
            vroi1 = overlay_slice[roi_slice == ii]

            stat1['mean'].append(np.mean(vroi1))
            stat1['median'].append(np.median(vroi1))
            stat1['std'].append(np.std(vroi1))
            stat1['max'].append(np.max(vroi1))
            stat1['min'].append(np.min(vroi1))
            y, x = np.histogram(vroi1, bins=20)
            hist1.append(y)
            hist1x.append(x)

        return stat1, roi_labels, hist1, hist1x

