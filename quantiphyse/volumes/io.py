
from __future__ import division, print_function

import sys
import os
import math
import warnings
import glob
import types

import nibabel as nib
import nibabel.nicom.dicomwrappers as nib_dcm
import numpy as np
import nrrd

from ..volumes import DataGrid, QpData

HAVE_DCMSTACK = True
try:
    import dcmstack, dicom
except:
    HAVE_DCMSTACK = False
    warnings.warn("DCMSTACK not found - may not be able to read DICOM folders")

class NiftiData(QpData):
    def __init__(self, fname):
        self.nii = nib.load(fname)
        
        # NB: np.asarray appears to convert to an array instead of a numpy memmap.
        # Appears to improve speed drastically as well as stop a bug with accessing the subset of the array
        # memmap has been designed to save space on ram by keeping the array on the disk but does
        # horrible things with performance, and analysis especially when the data is on the network.
        data = np.asarray(self.nii.get_data())
        shape = list(self.nii.shape)
        while data.ndim < 3:
            shape.append(1)
            data = np.expand_dims(data, -1)
            
        grid = DataGrid(shape[:3], self.nii.header.get_best_affine())
        QpData.__init__(self, fname, data, grid, fname=fname)

class DicomFolder(QpData):
    def __init__(self, fname):
        # A directory containing DICOMs. Convert them to Nifti
        print("Converting DICOMS in %s..." % (os.path.basename(fname)))
        src_dcms = glob.glob('%s/*' % fname)
        self.nii = None
        try:
            if HAVE_DCMSTACK:
                # Give DCMSTACK a chance to do its thing
                raise "no"
                stacks = dcmstack.parse_and_stack(src_dcms)
                stack = stacks.values()[0]
                self.nii = stack.to_nifti()
        except:
            warnings.warn("DCMSTACK failed - trying our method")
        if self.nii is None:
            # Try our top-secret in-house method
            self.nii = self.fallback_dcmstack(src_dcms)

        print("DONE\n")
        grid = DataGrid(self.nii.shape[:3], self.nii.header.get_best_affine())
        QpData.__init__(self, fname, self.nii.get_data(), grid, fname=fname)

    def fallback_dcmstack(self, fnames):
        """
        Create NIFTI from DCM files. Quick and dirty method
        for when DCMSTACK does not exist or fails.

        Basically we determine the sequence using the InstanceNumber tag
        but make sure we put slices together into volumes using the SliceLocation tag
        """
        ignored_files = []
        first = True
        dcms = []
        slices = set()
        ss, rs, ri = 1, 1, 0 # Pixel value scaling
        sys.stdout.write("  0%")
        for idx, fname in enumerate(fnames):
            try:
                dcm = dicom.read_file(fname)
            except:
                ignored_files.append(fname)
                continue
            slices.add(float(dcm.SliceLocation))
            dcms.append(dcm)

            if first:
                dcm1 = nib_dcm.wrapper_from_file(fname)
                dcm_affine = dcm1.get_affine()
                print(dcm_affine)
                try:
                    # Need all three of these to be of use
                    ss = dcm[0x2005,0x100e].value
                    rs = dcm[0x2005,0x140a].value
                    ri = dcm[0x2005,0x1409].value
                except:
                    pass
                first = False

            percent = 100*float(idx+1) / len(fnames)
            sys.stdout.write("\b\b\b\b%3i%%" % int(percent))
            sys.stdout.flush()
        
        n_vols = int(len(dcms) / len(slices))
        if n_vols * len(slices) != len(dcms):
            raise RuntimeError("Could not parse DICOMS - unable to determine fixed number of volumes")

        print("\n")
        print("%i Volumes" % n_vols)
        print("Ignored (non-DICOM) files: %i" % len(ignored_files))
        print("Slice locations are: " + ", ".join([str(s) for s in slices]))
        print("RescaleSlope: %f" % rs)
        print("RescaleIntercept: %f" % ri)
        print("ScaleSlope: %f" % ss)
        for sidx, s in enumerate(sorted(slices)):
            for idx, dcm in enumerate(sorted([d for d in dcms if d.SliceLocation == s], key=lambda x: x.InstanceNumber)):
                dcm.GlobalIndex = sidx + len(slices) * idx
            
        print("Creating NIFTI...")
        data = np.zeros([dcm1.image_shape[0], dcm1.image_shape[1], len(slices), int(n_vols)])
        sidx, vidx = 0, 0
        for dcm in sorted(dcms, key=lambda x: x.GlobalIndex):
            data[:,:,sidx, vidx] = (np.squeeze(dcm.pixel_array)*rs + ri)/ss
            sidx += 1
            if sidx == len(slices):
                sidx = 0
                vidx += 1

        # FIXME do this or not?
        #for d in range(3): data = np.flip(data, d)

        nii = nib.Nifti1Image(data, dcm_affine)
        nii.update_header()
        print("DONE")
        return nii
        
class NttrData(QpData):
    def __init__(self, fname):
        raise RuntimeError("NRRD support not currently enabled")

def load(fname):
    if os.path.isdir(fname):
        return DicomFolder(fname)
    elif fname.endswith(".nii") or fname.endswith(".nii.gz"):
        return NiftiData(fname)
    elif fname.endswith(".nrrd"):
        return NttrData(fname)
    else:
        raise RuntimeError("%s: Unrecognized file type" % fname)

def save(data, fname):
    img = nib.Nifti1Image(data.raw, data.rawgrid.affine)
    img.update_header()
    img.to_filename(fname)
    data.fname = fname
