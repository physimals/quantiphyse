#!/bin/env python
"""
Simulate motion to test MC/registration algorithms
"""

import sys

import nibabel as nib
import numpy as np 
import scipy.ndimage

if len(sys.argv) != 4:
    print("Usage: sim_motion.py <input filename> <msize> <output filename>")
    sys.exit(1)

infile, msize, outfile = sys.argv[1:]
msize = float(msize)

f = nib.load(infile)
nvols = f.shape[3]

d = f.get_fdata()
o = np.zeros(d.shape)

for v in range(nvols):
    vdata = d[:,:,:,v]
    shift = np.random.normal(scale=msize, size=3)
    odata = scipy.ndimage.interpolation.shift(vdata, shift)
    o[:,:,:,v] = odata

of = nib.Nifti1Image(o, f.header.get_best_affine())
of.to_filename(outfile)
