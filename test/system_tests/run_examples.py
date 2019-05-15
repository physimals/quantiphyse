#!/bin/env python
"""
Run all the example batch scripts
"""

import sys
import os
import glob
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

def create_test_data(output_dir):
    centre = [float(v)/2 for v in TEST_SHAPE]

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

    output_dir = os.path.join(output_dir, "data_autogen")
    if os.path.isdir(output_dir):
        sys.stderr.write("WARNING: test data dir already exists: %s\n" % output_dir)
    else:
        os.makedirs(output_dir)

    nii_3d = nib.Nifti1Image(testdata_3d, np.identity(4))
    nii_3d.to_filename(os.path.join(output_dir, "testdata_3d.nii.gz"))

    nii_4d = nib.Nifti1Image(testdata_4d, np.identity(4))
    nii_4d.to_filename(os.path.join(output_dir, "testdata_4d.nii.gz"))

    nii_4d_moving = nib.Nifti1Image(testdata_4d_moving, np.identity(4))
    nii_4d_moving.to_filename(os.path.join(output_dir, "testdata_4d_moving.nii.gz"))

    nii_mask = nib.Nifti1Image(testdata_mask, np.identity(4))
    nii_mask.to_filename(os.path.join(output_dir, "testdata_mask.nii.gz"))

def main():
    argv = sys.argv
    if len(argv) < 2:
        sys.stderr.write("Usage: run_examples.py <output_dir> [test name] [--debug]\n")
        sys.exit(1)
    outdir = argv[1]
    if "--debug" in argv:
        debug = "--debug"
        argv = [s for s in argv if s != "--debug"]
    else:
        debug = ""

    if len(argv) > 2:
        test_name = argv[2]
    else:
        test_name = ""

    if os.path.isdir(outdir):
        sys.stderr.write("WARNING: output dir already exists\n")
    else:
        os.makedirs(outdir)
    create_test_data(outdir)

    script_dir = os.path.abspath(os.path.dirname(__file__))
    print(script_dir)
    qpdir = os.path.abspath(os.path.join(script_dir, os.pardir, os.pardir))
    print(qpdir)
    examples = glob.glob(os.path.join(qpdir, "examples", "batch_scripts", "*.yaml"))
    os.chdir(outdir)
    for ex in sorted(examples):
        if not test_name or test_name in ex:
            print("**** Running example: %s" % ex)
            os.system("python -u %s/qp.py --batch=%s %s" % (qpdir, ex, debug))

if __name__ == "__main__":
    main()
