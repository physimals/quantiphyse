# Generate AIF, mask and T1 map from QIBA data

import sys
import math

import numpy as np

import nibabel as nib 

if len(sys.argv) != 3:
    sys.stderr.write("Usage: get_qiba_info.py <qiba data> <time subsample factor>")
    sys.exit(1)

fname = sys.argv[1]
subsample_factor = int(sys.argv[2])

# Create a notional T1 map with fixed value of 1.0s
t1 = np.full([50, 80, 1], 1.0)
img = nib.Nifti1Image(t1, np.identity(4))
img.to_filename("qiba_t1.nii.gz")

mask = np.ones([50, 80, 1])
img = nib.Nifti1Image(mask, np.identity(4))
img.to_filename("qiba_mask.nii.gz")

img = nib.load(fname)
data = img.get_data()
data_subsampled = data[..., ::subsample_factor]
print("Original data shape: %s" % str(data.shape))
print("New data shape: %s" % str(data_subsampled.shape))
img_subsampled = nib.Nifti1Image(data_subsampled, img.header.get_best_affine(), header=img.header)
img_subsampled.to_filename("qiba_subsampled.nii.gz")

# Extract the AIF and output as signal and concentration curves
aif = data[25, 5, 0, :]

# Data parameters
TR = 0.005
FA = math.radians(30)
s0 = float(aif[0])
T10 = 1.4
Rg = 4.5
R10 = 1.0/T10
E10 = math.exp(-TR/T10)
B = (1.0-E10) / (1.0-math.cos(FA) * E10)
HCT = 0.45
M0 = s0 / (B*math.sin(FA))
M00 = 50000

aif_sig, aif_conc = [], []
for t, v in enumerate(aif):
    s = float(v)

    # Convert signal to concentration
    CA = s/s0
    v = math.log((1-CA*B)/(1-CA*B*math.cos(FA)))
    roft = (-1/TR)*v
    cb = (roft - R10)/Rg
    cb /= (1-HCT)

    aif_sig.append(s)
    aif_conc.append(cb)

aif_sig = aif_sig[::subsample_factor]
aif_conc = aif_conc[::subsample_factor]
print("AIF as signal curve")
print(" ".join([str(v) for v in aif_sig]))
print("AIF as concentration curve")
print(" ".join([str(v) for v in aif_conc]))
