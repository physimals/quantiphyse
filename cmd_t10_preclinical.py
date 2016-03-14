"""
Run T10 calculation from VFA images

- Loading from cmd_t0config.yaml
- Load files
- Run T10
- Save T10

"""

import nibabel as nib
from pkview.utils import yaml_loader, save_file
from pkview.analysis.t1_model import t10_map

# Load config from yaml
c1 = yaml_loader('cmd_t10config_preclinical.yaml')

# TODO Just running on a single patient for the meanwhile
c1 = c1['EG1']

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

print("Saving T10")
save_file(c1['Settings']['Out_file_path'], hdr, T10)



