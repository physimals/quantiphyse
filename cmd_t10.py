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
c1 = yaml_loader('cmd_t10config.yaml')

# Just running on a single patient for the meanwhile
c1 = c1['RIT005']

fa_vols = []
fa_angles = []

for fa1 in c1['Files']:

    img = nib.load(c1['Folder'] + fa1['File'])
    hdr = img.get_header()
    fa_vols.append(img.get_data())
    fa_angles.append(fa1['FA'])

T10 = t10_map(fa_vols, fa_angles, TR=c1['Settings']['TR'])

save_file(c1['Settings']['Out_file_path'], hdr, T10)



