import sys
import os
import math
import shutil

import numpy as np
import scipy.ndimage
import nibabel as nib

TEST_SHAPE = [10, 10, 10]
TEST_NT = 20
MOTION_SCALE = 0.5

def test_fn(x, y, z, t=None):
    f = math.exp(-(x**2 + 2*y**2 + 3*z**2))
    if t is not None:
        f *= 1-math.cos(t*2*math.pi)
    return f

centre = [float(v)/2 for v in TEST_SHAPE]
script_dir = os.path.abspath(os.path.dirname(__file__))
output_dir = os.path.join(script_dir, "test_data")

testdata_3d = np.zeros(TEST_SHAPE, dtype=np.float32)
testdata_4d = np.zeros(TEST_SHAPE + [TEST_NT,], dtype=np.float32)
testdata_4d_moving = np.zeros(TEST_SHAPE + [TEST_NT,], dtype=np.float32)
testdata_mask = np.zeros(TEST_SHAPE, dtype=np.int)

for x in range(TEST_SHAPE[0]):
    for y in range(TEST_SHAPE[1]):
        for z in range(TEST_SHAPE[2]):
            nx = 2*float(x-centre[0])/TEST_SHAPE[0]
            ny = 2*float(y-centre[1])/TEST_SHAPE[1]
            nz = 2*float(z-centre[2])/TEST_SHAPE[2]
            d = math.sqrt(nx**2 + ny**2 + nz**2)
            testdata_3d[x,y,z] = test_fn(nx, ny, nz)
            testdata_mask[x, y, z] = int(d < 0.5)
            for t in range(TEST_NT):
                nt = float(t)/TEST_NT
                testdata_4d[x, y, z, t] = test_fn(nx, ny, nz, nt)
   
for t in range(TEST_NT):
    tdata = testdata_4d[:,:,:,t]
    shift = np.random.normal(scale=MOTION_SCALE, size=3)
    odata = scipy.ndimage.interpolation.shift(tdata, shift)
    testdata_4d_moving[:,:,:,t] = odata

try:
    shutil.rmtree(output_dir)
except:
    pass
os.makedirs(output_dir)

nii_3d = nib.Nifti1Image(testdata_3d, np.identity(4))
nii_3d.to_filename(os.path.join(output_dir, "testdata_3d.nii.gz"))

nii_4d = nib.Nifti1Image(testdata_4d, np.identity(4))
nii_4d.to_filename(os.path.join(output_dir, "testdata_4d.nii.gz"))

nii_4d_moving = nib.Nifti1Image(testdata_4d_moving, np.identity(4))
nii_4d_moving.to_filename(os.path.join(output_dir, "testdata_4d_moving.nii.gz"))

nii_mask = nib.Nifti1Image(testdata_mask, np.identity(4))
nii_mask.to_filename(os.path.join(output_dir, "testdata_mask.nii.gz"))


