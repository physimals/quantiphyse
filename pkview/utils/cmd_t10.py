"""
Run T10 calculation from VFA images

- Loading from cmd_t0config.yaml
- Load files
- Run T10
- Save T10

"""


import nibabel as nib
from scipy.ndimage.filters import gaussian_filter
import numpy as np

from pkview.utils import yaml_loader, save_file
from pkview.analysis.t1_model import t10_map


def t10(yaml_file):

    # Load config from yaml
    c1_main = yaml_loader(yaml_file)

    # Loop over each case
    for ii in c1_main.keys():

        # print(ii)
        # Just running on a single patient for the meanwhile
        c1 = c1_main[ii]

        fa_vols = []
        fa_angles = []

        for fa1 in c1['Files']:

            img = nib.load(c1['Folder'] + fa1['File'])
            hdr = img.get_header()
            fa_vols.append(img.get_data())
            fa_angles.append(fa1['FA'])

        T10 = t10_map(fa_vols, fa_angles, TR=c1['Settings']['TR'])

        save_file(c1['Settings']['Out_file_path'], hdr, T10)


def t10_preclinical(yaml_file):

    # Load config from yaml
    c1_main = yaml_loader(yaml_file)

    # Loop over each case
    for ii in c1_main.keys():

        print(ii)
        c1 = c1_main[ii]

        fa_vols = []
        afi_vols = []

        img = nib.load(c1['Folder'] + c1['Files']['fa_vol'])
        hdr = img.get_header()
        img1 = img.get_data()

        print("Loading files")
        for ii in range(len(c1['Settings']['FA'])):
            # Need to convert it to a list of volumes to be consistent with clinical data
            fa_vols.append(img1[:, :, :, ii])
        fa_angles = c1['Settings']['FA']

        img = nib.load(c1['Folder'] + c1['Files']['afi_vol'])
        img1 = img.get_data()

        for ii in range(len(c1['Settings']['TR_afi'])):
            # Need to convert it to a list of volumes to be consistent with clinical data
            afi_vols.append(img1[:, :, :, ii])
        afi_angles = c1['Settings']['FA_afi']

        print("Beginning conversion")
        T10 = t10_map(fa_vols, fa_angles, TR=c1['Settings']['TR'],
                      afi_vols=afi_vols, fa_afi=afi_angles, TR_afi=c1['Settings']['TR_afi'])

        if c1['Files']['mask'] is not None:
            mask = nib.load(c1['Folder'] + c1['Files']['mask'])
            T10[np.logical_not(mask.get_data())] = 0

        if c1['Settings']['smooth']:
            print("Smoothing map")
            T10 = gaussian_filter(T10, sigma=0.5, truncate=3)

        print("Saving T10")
        save_file(c1['Files']['Out_file_path'], hdr, T10)




