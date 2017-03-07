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

    def get_roi_stats(self, hist_bins=20, hist_range=None):
        """
        Return:
        @m1 mean for each ROI
        @m2 median for each ROI
        @m3 standard deviation for each ROI
        @roi_labels label of each ROI
        """

        # Checks if either ROI or overlay is None
        if (self.ivm.current_roi is None) or (self.ivm.current_overlay is None):
            stat1 = {'mean': [0], 'median': [0], 'std': [0], 'max': [0], 'min': [0]}
            roi_labels = np.array([0])
            return stat1, roi_labels, np.array([0, 0]), np.array([0, 1])

        roi = self.ivm.current_roi
        ovl = self.ivm.current_overlay
        roi_labels = roi.regions
        roi_labels = roi_labels[roi_labels > 0]

        stat1 = {'mean': [], 'median': [], 'std': [], 'max': [], 'min': []}
        hist1 = []
        hist1x = []

        for ii in roi_labels:

            # Overlay for a single label of the roi
            vroi1 = ovl.data[roi.data == ii]

            stat1['mean'].append(np.mean(vroi1))
            stat1['median'].append(np.median(vroi1))
            stat1['std'].append(np.std(vroi1))
            stat1['max'].append(np.max(vroi1))
            stat1['min'].append(np.min(vroi1))
            y, x = np.histogram(vroi1, bins=hist_bins, range=hist_range)
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
        if (self.ivm.current_roi is None) or (self.ivm.current_overlay is None):
            stat1 = {'mean': [0], 'median': [0], 'std': [0], 'max': [0], 'min': [0]}
            roi_labels = np.array([0])
            return stat1, roi_labels, np.array([0, 0]), np.array([0, 1])

        slice1 = self.ivm.cim_pos[2]

        roi = self.ivm.current_roi
        ovl = self.ivm.current_overlay
        overlay_slice = ovl.data[:, :, slice1]
        roi_slice = roi.data[:, :, slice1]

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

    def get_radial_profile(self, bins=30):
        """
        Generate a radial profile curve within an ROI
        """
        if (self.ivm.current_roi is None) or (self.ivm.current_overlay is None):
            return []

        data = self.ivm.current_overlay.data
        voxel_sizes = self.ivm.vol.voxel_sizes
        roi = self.ivm.current_roi.data
        centre = self.ivm.cim_pos

        # If overlay is 4d, get current 3d volume
        if len(data.shape) == 4:
            print("4d data")
            data = data[:, :, :, centre[3]]

        # Generate an array whose entries are integer values of the distance
        # from the centre. Set masked values to distance of -1
        x, y, z = np.indices((data.shape[:3]))
        r = np.sqrt(voxel_sizes[0]*(x - centre[0])**2 + voxel_sizes[1]*(y - centre[1])**2 + voxel_sizes[2]*(z - centre[2])**2)
        r[roi==0] = -1

        # Generate histogram by distance, weighted by data and corresponding histogram
        # of distances only (i.e. the number of voxels in each bin)
        minv = r[roi>0].min()
        rpd, edges = np.histogram(r, weights=data, bins=bins, range=(minv, r.max()))
        rpv, junk = np.histogram(r, bins=bins, range=(minv, r.max()))

        # Divide by number of voxels in each bin to get average value by distance.
        # Prevent divide by zero, if there are no voxels in a bin, this is OK because
        # there will be no data either
        rpv[rpv==0] = 1
        rp = rpd / rpv
        return rp, edges
