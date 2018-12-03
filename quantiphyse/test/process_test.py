"""
Quantiphyse - Base class for process self-test framework

Copyright (c) 2013-2018 University of Oxford
"""

import sys
import os
import math
import unittest
import traceback
import tempfile
import shutil
import time

import numpy as np
import scipy
import nibabel as nib

from PySide import QtCore

from quantiphyse.data import DataGrid, ImageVolumeManagement
from quantiphyse.processes import Process
from quantiphyse.utils.batch import Script
from quantiphyse.utils import QpException

class ProcessTest(unittest.TestCase):
    """
    Base class for a test module for a QP ProcessTest

    Process tests consist of running example batch scripts
    and checking the output. A set of test data files are created 
    in a temporary directory ``self.test_data_path``
    """
    def setUp(self):
        self.qpe, self.error = False, False
        sys.excepthook = self._exc

        self.ivm = ImageVolumeManagement()
        self.input_dir = tempfile.mkdtemp(prefix="qp")
        self.output_dir = tempfile.mkdtemp(prefix="qp")
        self._create_test_data_files()
        self.status, self.log, self.exception = None, None, None

    def tearDown(self):
        shutil.rmtree(self.input_dir)
        shutil.rmtree(self.output_dir)
            
    def run_yaml(self, yaml):
        script = Script(self.ivm)
        script.sig_finished.connect(self._script_finished)

        full_yaml = """
OutputFolder: %s
InputFolder: %s

Processing:
  - Load:
        data:
            data_3d.nii.gz:
            data_4d.nii.gz:
            data_4d_moving.nii.gz:
        rois:
            mask.nii.gz:
"""  % (self.output_dir, self.input_dir) + yaml + """
Cases:
  - case:
"""
        script.execute({"yaml" : full_yaml})
        while script.status == Script.RUNNING:
            self.processEvents()
            time.sleep(1)
        if self.status != Script.SUCCEEDED:
            raise self.exception 

    def _script_finished(self, *args):
        self.status, self.log, self.exception = args

    def processEvents(self):
        """
        Process outstanding QT events, i.e. let handlers for widget
        events that we have triggered run

        This must be run every time a test triggers widget events
        in order for the test to detect the effects
        """
        QtCore.QCoreApplication.instance().processEvents()

    def _create_test_data_files(self):
        """
        Create test data files

        This is done freshly for each test in case the data is modified
        during the process of a test
        """
        from . import create_test_data
        testshape = getattr(self, "testshape", (10, 10, 10))
        create_test_data(self, shape=testshape)

        nii_3d = nib.Nifti1Image(self.data_3d, np.identity(4))
        nii_3d.to_filename(os.path.join(self.input_dir, "data_3d.nii.gz"))

        nii_4d = nib.Nifti1Image(self.data_4d, np.identity(4))
        nii_4d.to_filename(os.path.join(self.input_dir, "data_4d.nii.gz"))

        nii_4d_moving = nib.Nifti1Image(self.data_4d_moving, np.identity(4))
        nii_4d_moving.to_filename(os.path.join(self.input_dir, "data_4d_moving.nii.gz"))

        nii_mask = nib.Nifti1Image(self.mask, np.identity(4))
        nii_mask.to_filename(os.path.join(self.input_dir, "mask.nii.gz"))

    def _exc(self, exc_type, value, tb):
        """ 
        Exception handler which simply flags whether a user-exception or an error has been caught 
        """
        self.qpe = issubclass(exc_type, QpException)
        self.error = not self.qpe
        if self.error or "--debug" in sys.argv:
            traceback.print_exception(exc_type, value, tb)
        
