"""
Run supervoxel extraction
"""

import nibabel as nib
import numpy as np

from pkview.utils import yaml_loader, save_file
from pkview.analysis.perfusionslic import PerfSLIC

def perfslic(yaml_file):

    # Load config from yaml
    c1_main = yaml_loader(yaml_file)

    # Loop over each case
    for ii in c1_main.keys():

        c1 = c1_main[ii]

        img = nib.load(c1['Folder'] + c1['File'])
        hdr = img.get_header()
        n_components = c1['Settings']['n_components']
        compactness = c1['Settings']['compactness']
        segment_size = c1['Settings']['segment_size']

        vox_size = np.ones(3) # FIXME

        print("Initialise the perf slic class")
        ps1 = PerfSLIC(img.get_data(), vox_size)
        print("Normalising image...")
        ps1.normalise_curves()
        print("Extracting features...")
        ps1.feature_extraction(n_components=n_components)
        print("Extracting supervoxels...")
        segments = ps1.supervoxel_extraction(compactness=compactness, segment_size=segment_size)
        ovl = np.array(segments, dtype=np.int)
        save_file(c1['Settings']['Out_file'], hdr, ovl)


