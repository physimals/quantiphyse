"""
Quantiphyse - Subclasses of QpData for loading and saving data in different formats

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

from quantiphyse.utils import QpException
from .qpdata import DataGrid, QpData, NumpyData
from .nifti import NiftiData, save as save_nifti
from .dicoms import DicomFolder

LOG = logging.getLogger(__name__)

def load(fname):
    """
    Load a data file

    :return: QpData instance
    """
    if os.path.isdir(fname):
        return DicomFolder(fname)
    elif fname.endswith(".nii") or fname.endswith(".nii.gz"):
        return NiftiData(fname)
    else:
        raise QpException("%s: Unrecognized file type" % fname)

def save(data, fname, grid=None, outdir=""):
    """
    Save data to a file
    
    :param data: QpData instance
    :param fname: File name
    :param grid: If specified, grid to save the data on
    :param outdir: Optional output directory if fname is not absolute
    """
    save_nifti(data, fname, grid, outdir)
