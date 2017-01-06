from __future__ import print_function, division, absolute_import

import nibabel as nib
import numpy as np


def save_nifti(data, folder1, name1, hdr=None):
    """
    Save as a nifti file
    @param data: Image data
    @param folder1: Folder to save
    @param name1: Saving name
    @param example_nifti: Provide a path to an example Nifti in order to save with correct affine matrix and other info
    @return:
    """

    # 1) Generic header information
    if hdr is None:
        # Default image creation
        img = nib.Nifti1Image(data, np.eye(4))

    # Header information derived from a specific nifti header
    else:
        img = nib.Nifti1Image(data, hdr.get_best_affine(), header=hdr)
        # Harmonise header with data
        img.update_header()

    # 2) check if it has a backslash or not
    if folder1[-1] == '/':
        img.to_filename(folder1 + name1)
    else:
        img.to_filename(folder1 + '/' + name1)

