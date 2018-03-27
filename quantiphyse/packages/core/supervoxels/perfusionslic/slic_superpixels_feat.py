"""
Quantiphyse - SLIC implementation for supervoxels

Copyright (c) 2013-2018 University of Oxford
"""

# coding=utf-8

from __future__ import division, print_function, absolute_import

import collections as coll
import warnings

import numpy as np
from scipy import ndimage as ndi
from scipy.ndimage.morphology import distance_transform_edt
from skimage.util import img_as_float, regular_grid
from skimage.color import rgb2lab

from ._slic_feat import _slic_feat_cython, _enforce_label_connectivity_cython, _find_adjacency_map, _find_adjacency_map_mask

from .additional.processing import get_mpd

def slic_feat(image, n_segments=100, compactness=10., max_iter=10, sigma=0,
              seed_type='grid', spacing=None, multichannel=True, convert2lab=None,
              enforce_connectivity=False, min_size_factor=0.5, max_size_factor=3,
              slic_zero=False, multifeat=True, return_adjacency=False, mask=None,
              recompute_seeds=False, n_random_seeds=10):

    """Segments image using k-means clustering in Color-(x,y,z) space.

    Parameters
    ----------
    image : 2D, 3D or 4D ndarray
        Input image, which can be 2D or 3D, and grayscale or multichannel
        (see `multichannel` parameter).
    n_segments : int, optional
        The (approximate) number of labels in the segmented output image.
    compactness : float, optional
        Balances color-space proximity and image-space proximity. Higher
        values give more weight to image-space. As `compactness` tends to
        infinity, superpixel shapes become square/cubic. In SLICO mode, this
        is the initial compactness.
    max_iter : int, optional
        Maximum number of iterations of k-means.
    sigma : float or (3,) array-like of floats, optional
        Width of Gaussian smoothing kernel for pre-processing for each
        dimension of the image. The same sigma is applied to each dimension in
        case of a scalar value. Zero means no smoothing.
        Note, that `sigma` is automatically scaled if it is scalar and a
        manual voxel spacing is provided (see Notes section).
    spacing : (3,) array-like of floats, optional
        The voxel spacing along each image dimension. By default, `slic`
        assumes uniform spacing (same voxel resolution along z, y and x).
        This parameter controls the weights of the distances along z, y,
        and x during k-means clustering.
    multichannel : bool, optional
        Whether the last axis of the image is to be interpreted as multiple
        channels or another spatial dimension.
    convert2lab : bool, optional
        Whether the input should be converted to Lab colorspace prior to
        segmentation. The input image *must* be RGB. Highly recommended.
        This option defaults to ``True`` when ``multichannel=True`` *and*
        ``image.shape[-1] == 3``.
    enforce_connectivity: bool, optional (default False)
        Whether the generated segments are connected or not
    min_size_factor: float, optional
        Proportion of the minimum segment size to be removed with respect
        to the supposed segment size ```depth*width*height/n_segments```
    max_size_factor: float, optional
        Proportion of the maximum connected segment size. A value of 3 works
        in most of the cases.
    slic_zero: bool, optional
        Run SLIC-zero, the zero-parameter mode of SLIC. [2]_
    mask: ndarray of bools or 0s and 1s, optional
        Array of same shape as `image`. Supervoxel analysis will only be performed on points at
        which mask == True

    Returns
    -------
    labels : 2D or 3D array
        Integer mask indicating segment labels.

    Raises
    ------
    ValueError
        If ``convert2lab`` is set to ``True`` but the last array
        dimension is not of length 3.

    Notes
    -----
    * If `sigma > 0`, the image is smoothed using a Gaussian kernel prior to
      segmentation.

    * If `sigma` is scalar and `spacing` is provided, the kernel width is
      divided along each dimension by the spacing. For example, if ``sigma=1``
      and ``spacing=[5, 1, 1]``, the effective `sigma` is ``[0.2, 1, 1]``. This
      ensures sensible smoothing for anisotropic images.

    * The image is rescaled to be in [0, 1] prior to processing.

    * Images of shape (M, N, 3) are interpreted as 2D RGB images by default. To
      interpret them as 3D with the last dimension having length 3, use
      `multichannel=False`.

    References
    ----------
    .. [1] Radhakrishna Achanta, Appu Shaji, Kevin Smith, Aurelien Lucchi,
        Pascal Fua, and Sabine Susstrunk, SLIC Superpixels Compared to
        State-of-the-art Superpixel Methods, TPAMI, May 2012.
    .. [2] http://ivrg.epfl.ch/research/superpixels#SLICO

    Examples
    --------
    >>> from skimage.segmentation import slic
    >>> from skimage.data import astronaut
    >>> img = astronaut()
    >>> segments = slic(img, n_segments=100, compactness=10)

    Increasing the compactness parameter yields more square regions:

    >>> segments = slic(img, n_segments=100, compactness=20)

    """
    if enforce_connectivity is None:
        warnings.warn('Deprecation: enforce_connectivity will default to'
                      ' True in future versions.')
        enforce_connectivity = False

    if mask is None and seed_type == 'nrandom':
        warnings.warn('nrandom assignment of seed points should only be used with an ROI. Changing seed type.')
        seed_type = 'grid'

    if seed_type == 'nrandom' and recompute_seeds is False:
        warnings.warn('Seeds should be recomputed when seed points are randomly assigned')

    image = img_as_float(image)
    is_2d = False
    if image.ndim == 2:
        # 2D grayscale image
        image = image[np.newaxis, ..., np.newaxis]
        is_2d = True
    elif image.ndim == 3 and multichannel:
        # Make 2D multichannel image 3D with depth = 1
        image = image[np.newaxis, ...]
        is_2d = True
    elif image.ndim == 3 and not multichannel:
        # Add channel as single last dimension
        image = image[..., np.newaxis]

    if spacing is None:
        spacing = np.ones(3)
    elif isinstance(spacing, (list, tuple)):
        spacing = np.array(spacing, dtype=np.double)

    if not isinstance(sigma, coll.Iterable):
        sigma = np.array([sigma, sigma, sigma], dtype=np.double)
        sigma /= spacing.astype(np.double)
    elif isinstance(sigma, (list, tuple)):
        sigma = np.array(sigma, dtype=np.double)
    if (sigma > 0).any():
        # add zero smoothing for multichannel dimension
        sigma = list(sigma) + [0]
        image = ndi.gaussian_filter(image, sigma)

    if multichannel and (convert2lab or convert2lab is None):
        if image.shape[-1] != 3 and convert2lab:
            raise ValueError("Lab colorspace conversion requires a RGB image.")
        elif image.shape[-1] == 3:
            image = rgb2lab(image)

    if multifeat is True:
        feat_scale = float(image.shape[3])
    else:
        feat_scale = 1.0

    depth, height, width = image.shape[:3]

    if mask is None:
        mask = np.ones(image.shape[:3], dtype=np.bool)
    else:
        mask = np.asarray(mask, dtype=np.bool)

    if seed_type == 'nrandom':

        segments_z = np.zeros(n_random_seeds, dtype=int)
        segments_y = np.zeros(n_random_seeds, dtype=int)
        segments_x = np.zeros(n_random_seeds, dtype=int)

        m_inv = np.copy(mask)

        # SEED STEP 1:  n seeds are placed as far as possible from every other seed and the edge.
        for ii in range(n_random_seeds):

            dtrans = distance_transform_edt(m_inv, sampling=spacing)

            mcoords = np.nonzero(dtrans == np.max(dtrans))

            segments_z[ii] = int(mcoords[2][0])
            segments_y[ii] = int(mcoords[1][0])
            segments_x[ii] = int(mcoords[0][0])

            m_inv[segments_x[ii], segments_y[ii], segments_z[ii]] = False

            # plt.imshow(dtrans[:, :, segments_z[ii]])
            # plt.show()

        segments_color = np.zeros((segments_z.shape[0], image.shape[3]))
        segments = np.concatenate([segments_x[..., np.newaxis],
                                   segments_y[..., np.newaxis],
                                   segments_z[..., np.newaxis],
                                   segments_color], axis=1)

        sx = np.ascontiguousarray(segments_x, dtype=np.int32)
        sy = np.ascontiguousarray(segments_y, dtype=np.int32)
        sz = np.ascontiguousarray(segments_z, dtype=np.int32)

        out1 = get_mpd(sx, sy, sz)
        step_x, step_y, step_z = out1[0], out1[1], out1[2]

    elif seed_type == 'grid':

        # initialize cluster centroids for desired number of segments
        # essentially just outputs the indices of a grid in the x, y and z direction
        grid_z, grid_y, grid_x = np.mgrid[:depth, :height, :width]
        # returns 3 slices (an object representing an array of slices, see builtin slice)
        slices = regular_grid(image.shape[:3], n_segments)
        step_z, step_y, step_x = [int(s.step) for s in slices]  # extract step size from slices
        segments_z = grid_z[slices]  # use slices to extract coordinates for centre points
        segments_y = grid_y[slices]
        segments_x = grid_x[slices]

        # mask_ind = mask[slices].reshape(-1)
        # list of all locations as well as zeros for the color features
        segments_color = np.zeros(segments_z.shape + (image.shape[3],))
        segments = np.concatenate([segments_z[..., np.newaxis],
                                   segments_y[..., np.newaxis],
                                   segments_x[..., np.newaxis],
                                   segments_color],
                                  axis=-1).reshape(-1, 3 + image.shape[3])
    else:
        raise ValueError('seed_type should be nrandom or grid')

    # Only use values in the mask
    # segments = segments[mask_ind, :]

    #print("Number of supervoxels: ", segments.shape[0])
    segments = np.ascontiguousarray(segments)

    # we do the scaling of ratio in the same way as in the SLIC paper
    # so the values have the same meaning
    step = float(max((step_z, step_y, step_x)))
    ratio = 1.0 / compactness

    image = np.ascontiguousarray(image * ratio, dtype=np.double)
    mask = np.ascontiguousarray(mask, dtype=np.int32)

    if recompute_seeds:

        # Seed step 2: Run SLIC to reinitialise seeds
        # Runs the supervoxel method but only uses distance to better initialise the method
        labels = _slic_feat_cython(image, mask, segments, step, max_iter, spacing, slic_zero, feat_scale,
                                   only_dist=True)

        # # Testing
        # fig = plt.figure()
        # ax = fig.add_subplot(111, projection='3d')
        # ax.scatter(segments_old[:, 0], segments_old[:, 1], segments_old[:, 2], c='red', s=80)
        # ax.scatter(segments[:, 0], segments[:, 1], segments[:, 2], c='blue', s=80)
        # plt.show()

    labels = _slic_feat_cython(image, mask, segments, step, max_iter, spacing, slic_zero, feat_scale,
                               only_dist=False)

    if enforce_connectivity:
        segment_size = depth * height * width / n_segments
        min_size = int(min_size_factor * segment_size)
        max_size = int(max_size_factor * segment_size)
        labels = _enforce_label_connectivity_cython(labels,
                                                    mask,
                                                    n_segments,
                                                    min_size,
                                                    max_size)

    # Also return adjacency map
    if return_adjacency:
        labels = np.ascontiguousarray(labels, dtype=np.int32)
        if mask is None:
            adj_mat, border_mat = _find_adjacency_map(labels)
        else:
            adj_mat, border_mat = _find_adjacency_map_mask(labels)

        #print(adj_mat.shape)
        if is_2d:
            labels = labels[0]
        return labels, adj_mat, border_mat

    else:

        if is_2d:
            labels = labels[0]
        return labels
