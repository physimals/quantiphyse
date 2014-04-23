"""

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
            return [0], [0], [0], [0], np.array([0, 0]), np.array([0, 1])

        roi_labels = np.unique(self.ivm.roi)
        roi_labels = roi_labels[roi_labels > 0]

        m1, m2, m3 = [], [], []
        hist1 = []
        hist1x = []

        for ii in roi_labels:

            # Overlay for a single label of the roi
            vroi1 = self.ivm.overlay[self.ivm.roi == ii]

            m1.append(np.mean(vroi1))
            m2.append(np.median(vroi1))
            m3.append(np.std(vroi1))
            y, x = np.histogram(vroi1, bins=20)
            hist1.append(y)
            hist1x.append(x)

        return m1, m2, m3, roi_labels, hist1, hist1x

