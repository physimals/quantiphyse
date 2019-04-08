"""
Quantiphyse - tests for QpData classes

Copyright (c) 2013-2018 University of Oxford
"""

import os
import unittest
import tempfile

import numpy as np

from quantiphyse.data import NumpyData, DataGrid
import quantiphyse.data.nifti as nifti

GRIDSIZE = 5
NVOLS = 4

class NumpyDataTest(unittest.TestCase):
    """ Tests for the NumpyData subclass of QpData """

    def setUp(self):
        self.shape = [GRIDSIZE, GRIDSIZE, GRIDSIZE]
        self.grid = DataGrid(self.shape, np.identity(4))
        self.floats = np.random.rand(*self.shape)
        self.ints = np.random.randint(0, 10, self.shape)
        self.floats4d = np.random.rand(*(self.shape + [NVOLS,]))

    def test3d(self):
        qpd = NumpyData(self.floats, grid=self.grid, name="test")
        self.assertEqual(qpd.name, "test")
        self.assertEqual(qpd.nvols, 1)
        self.assertEqual(qpd.ndim, 3)
        self.assertFalse(qpd.roi)
        
    def test3dints(self):
        qpd = NumpyData(self.ints, grid=self.grid, name="test", roi=True)
        self.assertEqual(qpd.name, "test")
        self.assertEqual(qpd.nvols, 1)
        self.assertEqual(qpd.ndim, 3)
        self.assertTrue(qpd.roi)
        
    def test4d(self):
        qpd = NumpyData(self.floats4d, grid=self.grid, name="test")
        self.assertEqual(qpd.name, "test")
        self.assertEqual(qpd.nvols, NVOLS)
        self.assertEqual(qpd.ndim, 4)
        self.assertFalse(qpd.roi)
        
    def testRandomName(self):
        name = "sdkfjhsdfi4"
        qpd = NumpyData(self.floats4d, grid=self.grid, name=name)
        self.assertEqual(qpd.name, name)
        
    def testRoiFloats(self):
        """ Check that ROIs can contain float data so long as the numbers are really integers """
        qpd = NumpyData(self.ints.astype(np.float), grid=self.grid, name="test", roi=True)
        self.assertTrue(issubclass(qpd.raw().dtype.type, np.floating))
        self.assertTrue(qpd.roi)
        
    def testRoiRegions(self):
        qpd = NumpyData(self.ints, grid=self.grid, name="test", roi=True)
        self.assertTrue(qpd.roi)
        regions = [v for v in np.unique(self.ints) if v != 0]
        self.assertEqual(regions, list(qpd.regions.keys()))

    def testRange(self):
        qpd = NumpyData(self.floats, grid=self.grid, name="test")
        mx, mn = np.max(self.floats), np.min(self.floats)
        self.assertAlmostEqual(qpd.range()[0], mn)
        self.assertAlmostEqual(qpd.range()[1], mx)
        
    def testSet2dt(self):
        qpd = NumpyData(self.floats, grid=self.grid, name="test")
        qpd.set_2dt()
        self.assertEqual(qpd.nvols, GRIDSIZE)
        self.assertEqual(qpd.ndim, 4)
        d = qpd.raw()
        for idx in range(GRIDSIZE):
            vol = d[..., idx]
            self.assertEqual(vol.shape[0], GRIDSIZE)
            self.assertEqual(vol.shape[1],  GRIDSIZE)
            self.assertEqual(vol.shape[2], 1)
            self.assertTrue(np.allclose(np.squeeze(vol), self.floats[:, :, idx]))

    def testVolume(self):
        qpd = NumpyData(self.floats4d, grid=self.grid, name="test")
        for idx in range(NVOLS):
            self.assertTrue(np.allclose(qpd.volume(idx), self.floats4d[..., idx]))
        
    def testValue3d(self):
        qpd = NumpyData(self.floats, grid=self.grid, name="test")
        POS = [2, 3, 4]
        self.assertAlmostEqual(qpd.value(POS), self.floats[POS[0], POS[1], POS[2]])
           
    def testValue3d4dPos(self):
        qpd = NumpyData(self.floats, grid=self.grid, name="test")
        POS = [2, 3, 4, 1]
        self.assertAlmostEqual(qpd.value(POS), self.floats[POS[0], POS[1], POS[2]])
     
    def testValue4d(self):
        qpd = NumpyData(self.floats4d, grid=self.grid, name="test")
        POS = [2, 3, 4, 1]
        self.assertAlmostEqual(qpd.value(POS), self.floats4d[POS[0], POS[1], POS[2], POS[3]])
        
    def testValue4d3dPos(self):
        qpd = NumpyData(self.floats4d, grid=self.grid, name="test")
        POS = [2, 3, 4]
        self.assertAlmostEqual(qpd.value(POS), self.floats4d[POS[0], POS[1], POS[2], 0])
        
class NiftiDataTest(unittest.TestCase):
    """ Tests for the NiftiData subclass of QpData """

    def setUp(self):
        self.shape = [GRIDSIZE, GRIDSIZE, GRIDSIZE]
        self.grid = DataGrid(self.shape, np.identity(4))
        self.floats = np.random.rand(*self.shape)
        self.ints = np.random.randint(0, 10, self.shape)
        self.floats4d = np.random.rand(*(self.shape + [NVOLS,]))

    def testSaveLoadMetadata(self):
        tempdir = tempfile.mkdtemp(prefix="qp")
        fname = os.path.join(tempdir, "test.nii.gz")
        md = {
            "flibble" : 2.3,
            "flobble" : 4,
            "fishcakes" : ["a", "b", "c"],
            "fluntycaps" : {
                "gfruffle" : "def",
                "gfable" : 8,
            }
        }
        qpd = NumpyData(self.floats4d, grid=self.grid, name="test", metadata=md)
        nifti.save(qpd, fname)

        nifti_data = nifti.NiftiData(fname)
        for key, value in md.items():
            self.assertTrue(key in nifti_data.metadata)
            self.assertEqual(nifti_data.metadata[key], value)

    def testLoadSaveSameName(self):
        qpd = NumpyData(self.floats4d, grid=self.grid, name="test")

        tempdir = tempfile.mkdtemp(prefix="qp")
        fname = os.path.join(tempdir, "test.nii")
        nifti.save(qpd, fname)

        nifti_data = nifti.NiftiData(fname)
        nifti.save(nifti_data, fname)

if __name__ == '__main__':
    unittest.main()
