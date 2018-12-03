"""
Quantiphyse - tests for ImageVolumeManagement

Copyright (c) 2013-2018 University of Oxford
"""

import unittest
import numpy as np

from quantiphyse.data import ImageVolumeManagement, NumpyData, DataGrid

GRIDSIZE = 5

class IVMTest(unittest.TestCase):

    def setUp(self):
        self.ivm = ImageVolumeManagement()

    def testEmptyCreate(self):
        self.assertEqual(len(self.ivm.data), 0)
        self.assertEqual(len(self.ivm.rois), 0)
        self.assertTrue(self.ivm.current_data is None)
        self.assertTrue(self.ivm.current_roi is None)
        self.assertTrue(self.ivm.main is None)
        
    def testAdd(self):
        shape = [GRIDSIZE, GRIDSIZE, GRIDSIZE]
        grid = DataGrid(shape, np.identity(4))
        qpd = NumpyData(np.random.rand(*shape), name="test", grid=grid)
        self.ivm.add(qpd)
        self.assertEqual(len(self.ivm.data), 1)
        self.assertEqual(len(self.ivm.rois), 0)
        self.assertTrue(self.ivm.current_data is None)
        self.assertTrue(self.ivm.current_roi is None)
        self.assertEqual(self.ivm.main, qpd)
        self.assertEqual(self.ivm.data["test"], qpd)

    def testAddRoi(self):
        shape = [GRIDSIZE, GRIDSIZE, GRIDSIZE]
        grid = DataGrid(shape, np.identity(4))
        qpd = NumpyData(np.random.randint(0, 10, size=shape), name="test", grid=grid, roi=True)
        self.assertTrue(qpd.roi)
        self.ivm.add(qpd)
        self.assertEqual(len(self.ivm.data), 1)
        self.assertEqual(len(self.ivm.rois), 1)
        self.assertTrue(self.ivm.current_data is None)
        self.assertTrue(self.ivm.current_roi is None)
        self.assertEqual(self.ivm.main, qpd)
        self.assertEqual(self.ivm.data["test"], qpd)

    def testAddTwo(self):
        shape = [GRIDSIZE, GRIDSIZE, GRIDSIZE]
        grid = DataGrid(shape, np.identity(4))
        qpd = NumpyData(np.random.rand(*shape), name="test", grid=grid)
        qpd2 = NumpyData(np.random.rand(*shape), name="test2", grid=grid)
        self.ivm.add(qpd)
        self.ivm.add(qpd2)
        self.assertEqual(len(self.ivm.data), 2)
        self.assertEqual(len(self.ivm.rois), 0)
        self.assertEqual(self.ivm.main, qpd)
        self.assertEqual(self.ivm.current_data, qpd2)
        self.assertTrue(self.ivm.current_roi is None)
        self.assertEqual(self.ivm.data["test"], qpd)
        self.assertEqual(self.ivm.data["test2"], qpd2)

    def testAddTwoRois(self):
        shape = [GRIDSIZE, GRIDSIZE, GRIDSIZE]
        grid = DataGrid(shape, np.identity(4))
        qpd = NumpyData(np.random.randint(0, 10, size=shape), name="test", grid=grid, roi=True)
        qpd2 = NumpyData(np.random.randint(0, 10, size=shape), name="test2", grid=grid, roi=True)
        self.assertTrue(qpd.roi)
        self.assertTrue(qpd2.roi)
        self.ivm.add(qpd)
        self.ivm.add(qpd2)
        self.assertEqual(len(self.ivm.data), 2)
        self.assertEqual(len(self.ivm.rois), 2)
        self.assertEqual(self.ivm.main, qpd)
        self.assertEqual(self.ivm.current_roi, qpd2)
        self.assertTrue(self.ivm.current_data is None)
        self.assertEqual(self.ivm.data["test"], qpd)
        self.assertEqual(self.ivm.data["test2"], qpd2)
        self.assertEqual(self.ivm.rois["test"], qpd)
        self.assertEqual(self.ivm.rois["test2"], qpd2)

    def testAddTwoMixed1(self):
        shape = [GRIDSIZE, GRIDSIZE, GRIDSIZE]
        grid = DataGrid(shape, np.identity(4))
        qpd = NumpyData(np.random.rand(*shape), name="test", grid=grid)
        qpd2 = NumpyData(np.random.randint(0, 10, size=shape), name="test2", grid=grid, roi=True)
        self.assertFalse(qpd.roi)
        self.assertTrue(qpd2.roi)
        self.ivm.add(qpd)
        self.ivm.add(qpd2)
        self.assertEqual(len(self.ivm.data), 2)
        self.assertEqual(len(self.ivm.rois), 1)
        self.assertEqual(self.ivm.main, qpd)
        self.assertEqual(self.ivm.current_roi, qpd2)
        self.assertTrue(self.ivm.current_data is None)
        self.assertEqual(self.ivm.data["test"], qpd)
        self.assertEqual(self.ivm.data["test2"], qpd2)
        self.assertEqual(self.ivm.rois["test2"], qpd2)

    def testAddTwoMixed2(self):
        shape = [GRIDSIZE, GRIDSIZE, GRIDSIZE]
        grid = DataGrid(shape, np.identity(4))
        qpd = NumpyData(np.random.rand(*shape), name="test", grid=grid)
        qpd2 = NumpyData(np.random.randint(0, 10, size=shape), name="test2", grid=grid, roi=True)
        self.assertFalse(qpd.roi)
        self.assertTrue(qpd2.roi)
        self.ivm.add(qpd2)
        self.ivm.add(qpd)
        self.assertEqual(len(self.ivm.data), 2)
        self.assertEqual(len(self.ivm.rois), 1)
        self.assertEqual(self.ivm.main, qpd2)
        self.assertEqual(self.ivm.current_data, qpd)
        self.assertTrue(self.ivm.current_roi is None)
        self.assertEqual(self.ivm.data["test"], qpd)
        self.assertEqual(self.ivm.data["test2"], qpd2)
        self.assertEqual(self.ivm.rois["test2"], qpd2)

    def testAddThreeMixed(self):
        shape = [GRIDSIZE, GRIDSIZE, GRIDSIZE]
        grid = DataGrid(shape, np.identity(4))
        qpd = NumpyData(np.random.rand(*shape), name="test", grid=grid)
        qpd2 = NumpyData(np.random.rand(*shape), name="test2", grid=grid)
        qpd3 = NumpyData(np.random.randint(0, 10, size=shape), name="test3", grid=grid, roi=True)
        self.assertFalse(qpd.roi)
        self.assertFalse(qpd2.roi)
        self.assertTrue(qpd3.roi)
        self.ivm.add(qpd)
        self.ivm.add(qpd2)
        self.ivm.add(qpd3)
        self.assertEqual(len(self.ivm.data), 3)
        self.assertEqual(len(self.ivm.rois), 1)
        self.assertEqual(self.ivm.main, qpd)
        self.assertEqual(self.ivm.current_data, qpd2)
        self.assertEqual(self.ivm.current_roi, qpd3)
        self.assertEqual(self.ivm.data["test"], qpd)
        self.assertEqual(self.ivm.data["test2"], qpd2)
        self.assertEqual(self.ivm.data["test3"], qpd3)
        self.assertEqual(self.ivm.rois["test3"], qpd3)

    def testDelete(self):
        shape = [GRIDSIZE, GRIDSIZE, GRIDSIZE]
        grid = DataGrid(shape, np.identity(4))
        qpd = NumpyData(np.random.rand(*shape), name="test", grid=grid)
        self.ivm.add(qpd)
        self.assertEqual(len(self.ivm.data), 1)
        self.assertEqual(len(self.ivm.rois), 0)
        self.assertTrue(self.ivm.current_data is None)
        self.assertTrue(self.ivm.current_roi is None)
        self.assertEqual(self.ivm.main, qpd)
        self.assertEqual(self.ivm.data["test"], qpd)
        self.ivm.delete(qpd.name)
        self.assertEqual(len(self.ivm.data), 0)
        self.assertEqual(len(self.ivm.rois), 0)
        self.assertTrue(self.ivm.current_data is None)
        self.assertTrue(self.ivm.current_roi is None)
        self.assertTrue(self.ivm.main is None)
      
    def testRename(self):
        shape = [GRIDSIZE, GRIDSIZE, GRIDSIZE]
        grid = DataGrid(shape, np.identity(4))
        qpd = NumpyData(np.random.rand(*shape), name="test", grid=grid)
        self.ivm.add(qpd)
        self.ivm.rename("test", "test2")
        self.assertEqual(len(self.ivm.data), 1)
        self.assertEqual(len(self.ivm.rois), 0)
        self.assertTrue(self.ivm.current_data is None)
        self.assertTrue(self.ivm.current_roi is None)
        self.assertEqual(self.ivm.main, self.ivm.data["test2"])
        self.assertTrue(np.all(self.ivm.data["test2"].raw() == qpd.raw()))

if __name__ == '__main__':
    unittest.main()
