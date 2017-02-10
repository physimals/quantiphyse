from __future__ import division, print_function, unicode_literals

import matplotlib.pyplot as plt
import matplotlib.animation as animation
import matplotlib.cm as cm
import numpy as np
import scipy.ndimage as ndi

from pkview.analysis.feat_pca import PcaFeatReduce
from . import slic_feat
import warnings

class PerfSLIC(object):

    """
    PerfSLIC
    Object that creates and visualises supervoxels created from 4D perfusion images

    Benjamin Irving
    20141124
    """

    def __init__(self, img1, vox_size, mask=None):
        """

        :param img1: 4D image to load
        :param vox_size: voxel size of loaded image
        :return:
        """

        self.img1 = img1
        # cython is sensitive to the double definition
        self.vox_size = np.asarray(vox_size/vox_size[0], dtype=np.double)
        self.mask = mask

        self.segments = None
        self.adj_mat = None
        self.border_mat = None
        self.feat1_image = None
        self.img_slice = None
        self.zoom_factor = None

    def normalise_curves(self):
        """

        :param use_roi: Normalise within an roi
        :return:
        """

        # ~~~~~~~~~~~~~~~~~~~~~ 1) Normalise enhancement curves (optional) ~~~~~~~~~~~~~~~~~~~~~~

        print("Image norm")
        baseline1 = np.mean(self.img1[:, :, :, :3], axis=-1)
        self.img1 = self.img1 - np.tile(np.expand_dims(baseline1, axis=-1), (1, 1, 1, self.img1.shape[-1]))

    def feature_extraction(self, n_components=5, normalise_input_image=1, norm_type='perc'):
        """

        :param n_components:
        :param normalise_input_image: Normalise the input image
        :param norm_type: 'max' or 'perc'
        :return:
        """

        # ~~~~~~~~~~~~~~~~~~~~~~ 2) Feature extraction ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

        self.n_components = n_components
        self.fe = PcaFeatReduce(self.img1)
        self.feat1_image, _ = self.fe.get_training_features(opt_normdata=1,
                                                            opt_normimage=normalise_input_image,
                                                            feature_volume=True,
                                                            n_components=self.n_components,
                                                            norm_type=norm_type)

    def get_component(self, comp_choice):
        """
        Component to save
        :return:

        """

        return self.feat1_image[:, :, :, comp_choice]


    def zoom(self, zoomfactor=2):
        """
        Experimental
        :param zoomfactor:
        :return:
        """
        self.zoom_factor = zoomfactor
        warnings.warn('Experimental feature')
        self.feat1_image = ndi.interpolation.zoom(self.feat1_image, [zoomfactor, zoomfactor, zoomfactor, 1], order=0)

    def supervoxel_extraction(self, compactness=0.05, sigma=1, seed_type='grid',
                              segment_size=400, recompute_seeds=False, n_random_seeds=10):

        """
        Just a wrapper for the SLIC interface
        :param compactness:
        :param sigma:
        :param seed_type: 'grid', 'nrandom'
                        Type of seed point initiliasation which is either based on a grid of no points or randomly
                        assigned within an roi
        :param segment_size: Mean supervoxel size (assuming no ROI but can be used with an ROI as standard)
        :param recompute_seeds: True or False
                                Recompute the initialisation points based on spatial distance within a ROI
        :param n_random_seeds:
        :return:
        """

        # ~~~~~~~~~~~~~~~~~~~~~~ 3) SLIC ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        print("SLIC")
        n_segments = int(self.feat1_image.shape[0] * self.feat1_image.shape[1] * self.feat1_image.shape[2]/segment_size)
        self.segments, self.adj_mat, self.border_mat = slic_feat(self.feat1_image,
                                                                 n_segments=n_segments,
                                                                 compactness=compactness,
                                                                 sigma=sigma,
                                                                 seed_type=seed_type,
                                                                 multichannel=False, multifeat=True,
                                                                 enforce_connectivity=False,
                                                                 return_adjacency=True,
                                                                 spacing=self.vox_size,
                                                                 mask=self.mask,
                                                                 recompute_seeds=recompute_seeds,
                                                                 n_random_seeds=n_random_seeds)

        return self.segments

    def plot_pca_modes(self):
        self.fe.show_model_stats()
        self.fe.plot_curve_modes(num1=self.n_components)

    def plotstatic(self, img_slice=None, temporal_point=None, visual_zoom=None, linewidths=0.3):
        """
        Plot the image and supervoxels at a particular slice
        :param img_slice: slice to plot supervoxel cross section
        :param temporal_point: (Optional) enhancement point to plot image
        :return:
        """

        if img_slice is None:
            if self.mask is None:
                # Take the midpoint of the entire volume
                img_slice = round(self.img1.shape[2] / 2)
            else:
                # Take the mid point of the mask
                mlist = self.mask.sum(1).sum(0)
                mlistnz = np.nonzero(mlist)[0]
                img_slice = round((mlistnz.max() + mlistnz.min())/2)
        self.img_slice = img_slice

        if temporal_point is None:
            print("Plotting mid enhancement point")
            temporal_point = round(self.img1.shape[3] / 2)

        segment_slice1 = self.segments[:, :, img_slice]
        labels1 = np.unique(self.segments[:, :, img_slice])

        img_disp = self.img1[:, :, img_slice, temporal_point]

        if self.zoom_factor is not None:
            img_disp = ndi.interpolation.zoom(img_disp, [self.zoom_factor, self.zoom_factor], order=0)

        plt.figure()
        plt.imshow(img_disp, cmap=cm.Greys_r, interpolation='nearest')
        for l in labels1:
            plt.contour(segment_slice1 == l, contours=1, colors='green', linewidths=linewidths)
        plt.show()

    def plotdynamic(self, img_slice=None, save_animation=False, interval=200, save_fps=5):
        """
        Plot a single slice with supervoxel contours and animation of perfusion image
        :param img_slice: Z-slice of the volume to plot. If none then plot middle slice.
        :param save_animation: Save the animated slice as a gif
        :return:
        """
        if img_slice is None:
            if self.mask is None:
                # Take the midpoint of the entire volume
                img_slice = round(self.img1.shape[2] / 2)
            else:
                # Take the mid point of the mask
                mlist = self.mask.sum(1).sum(0)
                mlistnz = np.nonzero(mlist)[0]
                img_slice = round((mlistnz.max() + mlistnz.min())/2)
        self.img_slice = img_slice

        segment_slice1 = self.segments[:, :, img_slice]
        labels1 = np.unique(self.segments[:, :, img_slice])

        fig = plt.figure()
        self.x = 0
        pim = self.img1[:, :, img_slice, self.x]

        self.pimplot = plt.imshow(pim, cmap=cm.Greys_r, interpolation='none', alpha=0.6,
                                  vmax=np.percentile(self.img1, 99.5), zorder=-1)

        for l in labels1:
            plt.contour(segment_slice1 == l, contours=1, colors='green', linewidths=0.3)

        ani = animation.FuncAnimation(fig, self._updatefig, interval=interval, blit=True)

        # save animation if requested
        if save_animation:
            ani.save('saved_animation.gif', writer='imagemagick', fps=save_fps)
        plt.show()

    def _updatefig(self, *args):
        """
        Method used to animate figure
        :param args:
        :return:
        """
        self.x += 1
        self.x = self.x % self.img1.shape[3]
        pim = self.img1[:, :, self.img_slice, self.x]
        self.pimplot.set_array(pim)
        return self.pimplot,

    def return_adjacency_matrix(self):
        return self.adj_mat

    def return_border_list(self):
        return np.asarray(self.border_mat, dtype=bool)

    def return_adjacency_as_list(self):
        """
        Ruturn a list of adjacent supervoxels for each supervoxel
        :return:
        """

        # saving nearest neighbour data
        print("Converting neighbour array to list...")
        neigh_store = []
        for pp in range(self.adj_mat.shape[0]):
            n1_ar = np.array(self.adj_mat[int(pp), :] == 1)
            sv_neigh = n1_ar.nonzero()[0]
            neigh_store.append(sv_neigh)

        return neigh_store

