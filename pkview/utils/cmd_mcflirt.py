"""
Run T10 calculation from VFA images

- Loading from cmd_t0config.yaml
- Load files
- Run T10
- Save T10

"""


import nibabel as nib
import numpy as np

from pkview.utils import yaml_loader, save_file
from pkview.analysis.mcflirt import mcflirt

def mcflirt_batch(yaml_file):

    # Load config from yaml
    c1_main = yaml_loader(yaml_file)

    # Loop over each case
    for ii in c1_main.keys():

        c1 = c1_main[ii]

        img = nib.load(c1['Folder'] + c1['File'])
        hdr = img.get_header()

        print("Running MCFLIRT")
        ret = mcflirt(img.get_data(), hdr.get_zooms())
        print("Run, saving output")
        save_file(c1['Settings']['Out_file'], hdr, ret)
        print("Done")
