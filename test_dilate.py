from __future__ import print_function, division, absolute_import

import numpy as np
import nibabel as nib
from scipy.ndimage import morphology
import scipy.ndimage as ndimage


base_dir = '/netshares/mvlprojects13/Registration_Data2/FILM/'

for ii in range(1, 9):

    pat = 'FILM' + str(ii).zfill(3)

    fname1 = base_dir + pat + '/PRE/dceMRI/nifti/' + pat + '_pre_VOI.nii'

    nifti1 = nib.load(fname1)
    img1 = nifti1.get_data()
    h1 = nifti1.get_header()

    img1_binary = img1 == 1

    struct1 = ndimage.generate_binary_structure(3, 1)

    img1_binary_dilat = morphology.binary_dilation(img1_binary, struct1)

    img1[img1_binary_dilat] = 1

    nifti = nib.Nifti1Image(img1, h1.get_best_affine(), header=h1)
    nifti.update_header()
    fname_out = base_dir + pat + '/PRE/dceMRI/nifti/' + pat + '_pre_VOI_dilate.nii'
    nifti.to_filename(fname_out)

    nifti = nib.Nifti1Image(img1_binary, h1.get_best_affine(), header=h1)
    nifti.update_header()
    fname_out = base_dir + pat + '/PRE/dceMRI/nifti/' + pat + '_pre_VOI_singlelab.nii'
    nifti.to_filename(fname_out)
