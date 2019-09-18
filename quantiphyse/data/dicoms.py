"""
Quantiphyse - Module for loading / saving DICOM data

Copyright (c) 2013-2018 University of Oxford
"""
from __future__ import division, print_function

import sys
import os
import warnings
import glob
import logging
import shutil
import tempfile
import subprocess

import numpy as np

try:
    from PySide import QtCore
except ImportError:
    from PySide2 import QtCore
  
import nibabel as nib
import pydicom

try:
    import dcmstack
except ImportError:
    dcmstack = None
    warnings.warn("DCMSTACK not found - may not be able to read DICOM folders")

from quantiphyse.utils import QpException
from quantiphyse.utils.local import which
from .qpdata import DataGrid, QpData, NumpyData

LOG = logging.getLogger(__name__)

def _find_dcm2niix():
    settings = QtCore.QSettings()
    if settings.contains("dicom/dcm2niix"):
        # Explicitly set by user - note there is no UI to do this currently!
        return settings.value("dicom/dcm2niix")
    else:
        return which("dcm2niix")

def get_load_methods():
    """
    :return: List of supported DICOM load methods, ordered by priority (best first)
    """
    methods = []
    if _find_dcm2niix():
        methods.append("dcm2niix")
    if dcmstack is not None:
        methods.append("dcmstack")
    methods.append("qp")
    return methods

def _load_dcm2niix(fnames):
    """
    Load DICOMs using the DCM2NIIX executable

    Note code is intended to be Python 2.7 compatible!
    """
    dcm2niix = _find_dcm2niix()
    tmpdir = ""
    try:
        tmpdir = tempfile.mkdtemp()
        for fname in fnames:
            shutil.copy(fname, tmpdir)
        stdout = subprocess.check_output([dcm2niix, "-f", "dcm2niix_out", tmpdir])
        return nib.load(os.path.join(tmpdir, "dcm2niix_out") + ".nii")
    finally:
        if tmpdir:
            shutil.rmtree(tmpdir)

def _load_dcmstack(fnames):
    """
    Load DICOMs using DCMSTACK the standard Python method
    """
    stacks = dcmstack.parse_and_stack(fnames)
    stack = stacks.values()[0]
    return stack.to_nifti()

def _load_qp(fnames):
    """
    Custom Quantiphyse DICOM load method based on code written to stack DICOMs which
    were causing failures using DCM2NIIX. We still prefer DCM2NIIX/DCMSTACK where
    available.

    The algorithm is to determine the sequence using the InstanceNumber tag
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
            dcm = pydicom.read_file(fname)
        except:
            ignored_files.append(fname)
            continue
        if "SliceLocation" not in dcm.dir():
            dcm.SliceLocation = 0.0
        if "InstanceNumber" not in dcm.dir():
            dcm.InstanceNumber = 1

        slices.add(float(dcm.SliceLocation))
        dcms.append(dcm)

        if first:
            dcm1 = nib_dcm.wrapper_from_file(fname)
            dcm_affine = dcm1.get_affine()
            print(dcm_affine)
            try:
                # Need all three of these to be of use
                ss = dcm[0x2005, 0x100e].value
                rs = dcm[0x2005, 0x140a].value
                ri = dcm[0x2005, 0x1409].value
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

    LOG.debug("%i Volumes" % n_vols)
    LOG.debug("Ignored (non-DICOM) files: %i" % len(ignored_files))
    LOG.debug("Slice locations are: " + ", ".join([str(s) for s in slices]))
    LOG.debug("RescaleSlope: %f" % rs)
    LOG.debug("RescaleIntercept: %f" % ri)
    LOG.debug("ScaleSlope: %f" % ss)
    for sidx, s in enumerate(sorted(slices)):
        for idx, dcm in enumerate(sorted([d for d in dcms if d.SliceLocation == s], key=lambda x: x.InstanceNumber)):
            dcm.GlobalIndex = sidx + len(slices) * idx
        
    LOG.debug("Creating NIFTI...")
    data = np.zeros([dcm1.image_shape[0], dcm1.image_shape[1], len(slices), int(n_vols)])
    sidx, vidx = 0, 0
    for dcm in sorted(dcms, key=lambda x: x.GlobalIndex):
        data[:, :, sidx, vidx] = (np.squeeze(dcm.pixel_array)*rs + ri)/ss
        sidx += 1
        if sidx == len(slices):
            sidx = 0
            vidx += 1

    nii = nib.Nifti1Image(data, dcm_affine)
    nii.update_header()
    LOG.debug("DONE")
    return nii

METHOD_IMPLS = {
    "dcm2niix" : _load_dcm2niix,
    "dcmstack" : _load_dcmstack,
    "qp" : _load_qp,
}

def load(dirname, filter="*", methods=None):
    """
    Load DICOM files and attempt to stack them into a 3D/4D data set
    """
    src_dcms = glob.glob(os.path.join(dirname, filter))
    LOG.debug("Loading DICOMS in %s...", str(src_dcms))
    
    if methods is None:
        methods = get_load_methods()

    nii = None
    for method in methods:
        try:
            LOG.debug("Trying using method: %s", method)
            method_impl = globals().get("_load_%s" % method, None)
            if method_impl is None:
                LOG.warn("Unknown DCM load method: %s", method)
            else:
                nii = method_impl(src_dcms)
                LOG.debug("Loaded successfully using method: %s", method)
                break
        except Exception as exc:
            LOG.debug("Failed to load DCMs using method: %s", method)
            LOG.debug(str(exc))

    if nii is None:
        raise QpException("Failed to load DICOMS - no method was successful")

    grid = DataGrid(nii.shape[:3], nii.header.get_best_affine())
    dcmdata = nii.get_data()
    return DicomData(dcmdata, grid, dirname)

def save(data, prefix, grid=None, outdir=""):
    """
    Save a data set as a set of DICOMs

    :param data: QpData instance
    :param prefix: Prefix for DCM filenames. May include a directory component
    :param grid: Optional DataGrid instance for output data
    :param outdir: Optional output directory if prefix is not absolute
    """
    if grid is None:
        grid = data.grid
        arr = data.raw().copy()
    else:
        arr = data.resample(grid).raw().copy()
 
    # Make sure output directory exists
    if not os.path.isabs(prefix):
        prefix = os.path.join(outdir, prefix)

    dirname = os.path.dirname(prefix)
    if not os.path.exists(dirname):
        os.makedirs(dirname)

    # Loop over volumes and slices:
    for vol in range(data.nvols):
        for slc in range(grid.shape[2]):
            fname = prefix + "_%i_%i.dcm" % (vol, slc)
            if data.nvols > 1:
                slicedata = arr[..., vol]
            slicedata = arr[..., slc]
    
            ## This code block was taken from the output of a MATLAB secondary
            ## capture.  I do not know what the long dotted UIDs mean, but
            ## this code works.
            file_meta = pydicom.Dataset()
            file_meta.MediaStorageSOPClassUID = 'Secondary Capture Image Storage'
            file_meta.MediaStorageSOPInstanceUID = '1.3.6.1.4.1.9590.100.1.1.111165684411017669021768385720736873780'
            file_meta.ImplementationClassUID = '1.3.6.1.4.1.9590.100.1.0.100.4.0'
            ds = pydicom.FileDataset(filename, {},file_meta = file_meta,preamble="\0"*128)
            ds.Modality = 'WSD'
            ds.ContentDate = str(datetime.date.today()).replace('-','')
            ds.ContentTime = str(time.time()) #milliseconds since the epoch
            ds.StudyInstanceUID =  '1.3.6.1.4.1.9590.100.1.1.124313977412360175234271287472804872093'
            ds.SeriesInstanceUID = '1.3.6.1.4.1.9590.100.1.1.369231118011061003403421859172643143649'
            ds.SOPInstanceUID =    '1.3.6.1.4.1.9590.100.1.1.111165684411017669021768385720736873780'
            ds.SOPClassUID = 'Secondary Capture Image Storage'
            ds.SecondaryCaptureDeviceManufctur = 'Python 2.7.3'

            ## These are the necessary imaging components of the FileDataset object.
            ds.SamplesPerPixel = 1
            ds.PhotometricInterpretation = "MONOCHROME2"
            ds.PixelRepresentation = 0
            ds.HighBit = 15
            ds.BitsStored = 16
            ds.BitsAllocated = 16
            ds.SmallestImagePixelValue = '\\x00\\x00'
            ds.LargestImagePixelValue = '\\xff\\xff'
            ds.Columns = slicedata.shape[0]
            ds.Rows = slicedata.shape[1]
            if slicedata.dtype != np.uint16:
                slicedata = slicedata.astype(np.uint16)
            ds.PixelData = slicedata.tostring()

            ds.save_as(fname)
    return

class DicomData(NumpyData):
    """
    QpData instance loaded from a collection of DICOM files
    """

    def __init__(self, dcmdata, grid, fname):
        NumpyData.__init__(self, dcmdata, grid, name=fname)
