"""
Quantiphyse - Subclass of QpData for handling Nifti data

Copyright (c) 2013-2018 University of Oxford
"""
from __future__ import division, print_function

import os
import logging
import traceback

import nibabel as nib
import numpy as np

from .qpdata import DataGrid, QpData, NumpyData

LOG = logging.getLogger(__name__)

QP_NIFTI_EXTENSION_CODE = 42

class NiftiData(QpData):
    """
    QpData from a Nifti file
    """
    def __init__(self, fname):
        nii = nib.load(fname)
        shape = list(nii.shape)
        while len(shape) < 3:
            shape.append(1)

        if len(shape) > 3:
            nvols = shape[3]
        else:
            nvols = 1

        self.rawdata = None
        self.voldata = None
        self.nifti_header = nii.header
        metadata = None
        for ext in self.nifti_header.extensions:
            if ext.get_code() == QP_NIFTI_EXTENSION_CODE:
                import yaml
                LOG.debug("Found QP metadata: %s", ext.get_content())
                try:
                    metadata = yaml.load(ext.get_content())[0]["QpMetadata"]
                    LOG.debug(metadata)
                except (KeyError, yaml.YAMLError):
                    LOG.warn("Failed to read Quantiphyse metadata")
                    LOG.warn(ext.get_content())
                    traceback.print_exc()

        xyz_units, vol_units = "mm", None
        units = nii.header.get_xyzt_units()
        if units:
            xyz_units = units[0]
            if len(units) > 1:
                vol_units = units[1]

        vol_scale = 1.0
        zooms = nii.header.get_zooms()
        if zooms and len(zooms) > 3:
            vol_scale = zooms[3]

        grid = DataGrid(shape[:3], nii.header.get_best_affine(), units=xyz_units)
        QpData.__init__(self, fname, grid, nvols, vol_unit=vol_units, vol_scale=vol_scale, fname=fname, metadata=metadata)

    def raw(self):
        # NB: copy() converts data to an in-memory array instead of a numpy file memmap.
        # Appears to improve speed drastically as well as stop a bug with accessing the subset of the array
        # memmap has been designed to save space on ram by keeping the array on the disk but does
        # horrible things with performance, and analysis especially when the data is on the network.
        if self.rawdata is None:
            nii = nib.load(self.fname)
            #self.rawdata = nii.get_data().copy()
            self.rawdata = nii.get_data()
            self.rawdata = self._correct_dims(self.rawdata)

        self.voldata = None
        return self.rawdata
        
    def volume(self, vol, qpdata=False):
        vol = min(vol, self.nvols-1)
        if self.nvols == 1:
            ret = self.raw()
        elif self.rawdata is not None:
            ret = self.rawdata[:, :, :, vol]
        else:
            if self.voldata is None:
                self.voldata = [None,] * self.nvols
            if self.voldata[vol] is None:
                nii = nib.load(self.fname)
                self.voldata[vol] = self._correct_dims(nii.dataobj[..., vol])
            ret = self.voldata[vol]

        if qpdata:
            return NumpyData(ret, grid=self.grid, name="%s_vol_%i" % (self.name, vol))
        else:
            return ret

    def _correct_dims(self, arr):
        while arr.ndim < 3:
            arr = np.expand_dims(arr, -1)

        if self.metadata.get("raw_2dt", False) and arr.ndim == 3:
            # Single-slice, interpret 3rd dimension as time
            arr = np.expand_dims(arr, 2)

        if arr.ndim == 4 and arr.shape[3] == 1:
            arr = np.squeeze(arr, axis=-1)
        return arr

def save(data, fname, grid=None, outdir=""):
    """
    Save data to a file
    
    :param data: QpData instance
    :param fname: File name
    :param grid: If specified, grid to save the data on
    :param outdir: Optional output directory if fname is not absolute
    """
    if grid is None:
        grid = data.grid
        arr = data.raw().copy()
    else:
        arr = data.resample(grid).raw().copy()
        
    if hasattr(data, "nifti_header"):
        header = data.nifti_header.copy()
    else:
        header = None

    img = nib.Nifti1Image(arr, grid.affine, header=header)
    img.update_header()
    if data.metadata:
        from quantiphyse.utils.batch import to_yaml
        yaml_metadata = to_yaml({"QpMetadata" : data.metadata})
        LOG.debug("Writing metadata: %s", yaml_metadata)
        extensions = nib.nifti1.Nifti1Extensions([ext for ext in img.header.extensions if ext.get_code() != QP_NIFTI_EXTENSION_CODE])
        extensions.append(nib.nifti1.Nifti1Extension(QP_NIFTI_EXTENSION_CODE, yaml_metadata.encode('utf-8')))
        img.header.extensions = extensions

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

    LOG.debug("Saving %s as %s", data.name, fname)
    img.to_filename(fname)
    data.fname = fname
