"""
Quantiphyse - Subclasses of QpData for handling different data sources

A subclass of QpData must implement the raw() method to return the actual
data on its original grid. This may be stored internally or retrieved on-demand.
We use the latter for NIFTI files since it avoids keeping the data in memory
when we use the standard grid data for viewing and analysis

NumpyData is used for data generated internally on the current grid and stored
as a Numpy array

Copyright (c) 2013-2018 University of Oxford
"""
from __future__ import division, print_function

import sys
import os
import warnings
import glob
import logging

import nibabel as nib
import numpy as np
import nrrd

from quantiphyse.utils import QpException
from .qpdata import DataGrid, QpData

HAVE_DCMSTACK = True
try:
    import dcmstack, dicom
except:
    HAVE_DCMSTACK = False
    warnings.warn("DCMSTACK not found - may not be able to read DICOM folders")

QP_NIFTI_EXTENSION_CODE = 42
LOG = logging.getLogger(__name__)

class NumpyData(QpData):
    def __init__(self, data, grid, name, **kwargs):
        # Unlikely but possible that first data is added from the console
        if grid is None:
            grid = DataGrid(data.shape[:3], np.identity(4))

        if data.dtype.kind in np.typecodes["AllFloat"]:
            # Use float32 rather than default float64 to reduce storage
            data = data.astype(np.float32)
        self.rawdata = data
        
        if data.ndim > 3:
            nvols = data.shape[3]
            if nvols == 1:
                self.rawdata = np.squeeze(self.rawdata, axis=-1)
        else:
            nvols = 1

        QpData.__init__(self, name, grid, nvols, **kwargs)
    
    def raw(self):
        return self.rawdata

class NiftiData(QpData):
    def __init__(self, fname):
        self.nii = nib.load(fname)
        shape = list(self.nii.shape)
        while len(shape) < 3:
            shape.append(1)

        if len(shape) > 3:
            nvols = shape[3]
        else:
            nvols = 1

        self.rawdata = None
        self.voldata = None
        self.nifti_header = self.nii.header
        metadata = None
        for ext in self.nifti_header.extensions:
            if ext.get_code() == QP_NIFTI_EXTENSION_CODE:
                import yaml
                self.debug("Found QP metadata: %s" % ext.get_content())
                metadata = yaml.load(ext.get_content())
                self.debug(metadata)

        grid = DataGrid(shape[:3], self.nii.header.get_best_affine())
        QpData.__init__(self, fname, grid, nvols, fname=fname, metadata=metadata)

    def raw(self):
        # NB: np.asarray convert data to an in-memory array instead of a numpy file memmap.
        # Appears to improve speed drastically as well as stop a bug with accessing the subset of the array
        # memmap has been designed to save space on ram by keeping the array on the disk but does
        # horrible things with performance, and analysis especially when the data is on the network.
        if self.rawdata is None:
            self.rawdata = np.asarray(self.nii.get_data())
            self.rawdata = self._correct_dims(self.rawdata)

        self.voldata = None
        return self.rawdata
        
    def volume(self, vol):
        vol = min(vol, self.nvols-1)
        if self.nvols == 1:
            return self.raw()
        elif self.rawdata is not None:
            return self.rawdata[:, :, :, vol]
        else:
            if self.voldata is None:
                self.voldata = [None,] * self.nvols
            if self.voldata[vol] is None:
                self.voldata[vol] = self._correct_dims(self.nii.dataobj[..., vol])

        return self.voldata[vol]

    def _correct_dims(self, arr):
        while arr.ndim < 3:
            arr = np.expand_dims(arr, -1)

        if self.raw_2dt and arr.ndim == 3:
            # Single-slice, interpret 3rd dimension as time
            arr = np.expand_dims(arr, 2)

        if arr.ndim == 4 and arr.shape[3] == 1:
            arr = np.squeeze(arr, axis=-1)
        return arr

class DicomFolder(QpData):
    def __init__(self, fname):
        # A directory containing DICOMs. Convert them to Nifti
        print("Converting DICOMS in %s..." % (os.path.basename(fname)))
        src_dcms = glob.glob('%s/*' % fname)
        nii = None
        try:
            if HAVE_DCMSTACK:
                # Give DCMSTACK a chance to do its thing
                stacks = dcmstack.parse_and_stack(src_dcms)
                stack = stacks.values()[0]
                nii = stack.to_nifti()
        except:
            warnings.warn("DCMSTACK failed - trying our method")
        if nii is None:
            # Try our top-secret in-house method
            nii = self.fallback_dcmstack(src_dcms)

        print("DONE\n")
        if len(nii.shape) > 3:
            nvols = nii.shape[3]
        else:
            nvols = 1

        grid = DataGrid(nii.shape[:3], nii.header.get_best_affine())
        self.dcmdata = nii.get_data()
        QpData.__init__(self, fname, grid, nvols, fname=fname)

    def raw(self):
        return self.dcmdata

    def fallback_dcmstack(self, fnames):
        """
        Create NIFTI from DCM files. Quick and dirty method
        for when DCMSTACK does not exist or fails.

        Basically we determine the sequence using the InstanceNumber tag
        but make sure we put slices together into volumes using the SliceLocation tag
        """
        import nibabel.nicom.dicomwrappers as nib_dcm
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
        
        if len(slices) < 0:
            raise QpException("This doesn't seem to be a DICOM folder")
            
        n_vols = int(len(dcms) / len(slices))
        if n_vols * len(slices) != len(dcms):
            raise QpException("Could not parse DICOMS - unable to determine fixed number of volumes")

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
        raise QpException("%s: Unrecognized file type" % fname)

def save(data, fname, grid=None, outdir=""):
    if grid is None:
        grid = data.grid
        arr = data.raw()
    else:
        arr = data.resample(grid).raw()
        
    if hasattr(data, "nifti_header"):
        header = data.nifti_header.copy()
    else:
        header = None

    img = nib.Nifti1Image(arr, grid.affine, header=header)
    img.update_header()
    if data.metadata:
        import yaml
        yaml_metadata = yaml.dump(data.metadata, default_flow_style=False)
        LOG.debug("Writing metadata: %s", yaml_metadata)
        ext = nib.nifti1.Nifti1Extension(QP_NIFTI_EXTENSION_CODE, yaml_metadata)
        img.header.extensions.append(ext)

    if not fname:
        fname = data.name
        
    _, extension = os.path.splitext(fname)
    if extension == "":
        fname += ".nii"
        
    if not os.path.isabs(fname):
        fname = os.path.join(outdir, fname)

    dirname = os.path.dirname(fname)
    if not os.path.exists(dirname):
        os.makedirs(dirname)

    LOG.debug("Saving %s as %s" % (data.name, fname))
    img.to_filename(fname)
    data.fname = fname
