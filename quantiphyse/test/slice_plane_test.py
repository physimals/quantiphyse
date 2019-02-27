"""
Quantiphyse - Tests for OrthoSlice class

Copyright (c) 2013-2018 University of Oxford
"""
import unittest

import numpy as np

from quantiphyse.data import DataGrid, NumpyData, OrthoSlice

GRIDSIZE = 5
SLICEPOS = 2
XAXIS, YAXIS, ZAXIS = 0, 1, 2

class OrthoSliceTest(unittest.TestCase):

    def testOrthoY(self):
        grid = DataGrid((GRIDSIZE, GRIDSIZE, GRIDSIZE), np.identity(4))
        YD, XD, ZD = np.meshgrid(range(GRIDSIZE), range(GRIDSIZE), range(GRIDSIZE))

        plane = OrthoSlice(grid, YAXIS, SLICEPOS)
        self.assertEquals(tuple(plane.origin), (0, SLICEPOS, 0))
        self.assertEquals(len(plane.basis), 2)
        self.assertTrue((1, 0, 0) in plane.basis)
        self.assertTrue((0, 0, 1) in plane.basis)
        
    def testOrthoX(self):
        grid = DataGrid((GRIDSIZE, GRIDSIZE, GRIDSIZE), np.identity(4))
        plane = OrthoSlice(grid, XAXIS, SLICEPOS)
        self.assertEquals(tuple(plane.origin), (SLICEPOS, 0, 0))
        self.assertEquals(len(plane.basis), 2)
        self.assertTrue((0, 1, 0) in plane.basis)
        self.assertTrue((0, 0, 1) in plane.basis)
        
    def testOrthoZ(self):
        grid = DataGrid((GRIDSIZE, GRIDSIZE, GRIDSIZE), np.identity(4))
        plane = OrthoSlice(grid, ZAXIS, SLICEPOS)
        self.assertEquals(tuple(plane.origin), (0, 0, SLICEPOS))
        self.assertEquals(len(plane.basis), 2)
        self.assertTrue((0, 1, 0) in plane.basis)
        self.assertTrue((1, 0, 0) in plane.basis)
        
    def testGenericX(self):
        trans = np.array([
            [0.3, 0.2, 1.7, 0],
            [0.1, 2.1, 0.11, 0],
            [2.2, 0.7, 0.3, 0],
            [0, 0, 0, 1]
        ])

        grid = DataGrid((GRIDSIZE, GRIDSIZE, GRIDSIZE), trans)
        origin = list(SLICEPOS * trans[:3,0])
        plane = OrthoSlice(grid, XAXIS, SLICEPOS)
        self.assertAlmostEquals(list(plane.origin), origin)
        self.assertEquals(len(plane.basis), 2)
        self.assertTrue(tuple(trans[:3, 2]) in plane.basis)
        self.assertTrue(tuple(trans[:3, 1]) in plane.basis)

    def testGenericY(self):
        trans = np.array([
            [0.3, 0.2, 1.7, 0],
            [0.1, 2.1, 0.11, 0],
            [2.2, 0.7, 0.3, 0],
            [0, 0, 0, 1]
        ])

        grid = DataGrid((GRIDSIZE, GRIDSIZE, GRIDSIZE), trans)
        origin = list(SLICEPOS * trans[:3,1])
        plane = OrthoSlice(grid, YAXIS, SLICEPOS)
        self.assertAlmostEquals(list(plane.origin), origin)
        self.assertEquals(len(plane.basis), 2)
        self.assertTrue(tuple(trans[:3, 0]) in plane.basis)
        self.assertTrue(tuple(trans[:3, 2]) in plane.basis)

    def testGenericZ(self):
        trans = np.array([
            [0.3, 0.2, 1.7, 0],
            [0.1, 2.1, 0.11, 0],
            [2.2, 0.7, 0.3, 0],
            [0, 0, 0, 1]
        ])

        grid = DataGrid((GRIDSIZE, GRIDSIZE, GRIDSIZE), trans)
        origin = list(SLICEPOS * trans[:3,2])
        plane = OrthoSlice(grid, ZAXIS, SLICEPOS)
        self.assertAlmostEquals(list(plane.origin), origin)
        self.assertEquals(len(plane.basis), 2)
        self.assertTrue(tuple(trans[:3, 0]) in plane.basis)
        self.assertTrue(tuple(trans[:3, 1]) in plane.basis)
    """
    def testSliceIdenticalZ(self):
        grid = DataGrid((GRIDSIZE, GRIDSIZE, GRIDSIZE), np.identity(4))
        plane = OrthoSlice(grid, ZAXIS, SLICEPOS)
        data = np.random.rand(*grid.shape)
        plane.slice_data(data, grid)

    def testSliceIdenticalY(self):
        grid = DataGrid((GRIDSIZE, GRIDSIZE, GRIDSIZE), np.identity(4))
        plane = OrthoSlice(grid, YAXIS, SLICEPOS)
        data = np.random.rand(*grid.shape)
        plane.slice_data(data, grid)
    """
    def testHighRes(self):
        grid = DataGrid((GRIDSIZE, GRIDSIZE, GRIDSIZE), np.identity(4))
        plane = OrthoSlice(grid, YAXIS, SLICEPOS)
        data = np.random.rand(GRIDSIZE*2, GRIDSIZE*2, GRIDSIZE*2)
        datagrid = DataGrid((GRIDSIZE*2, GRIDSIZE*2, GRIDSIZE*2), np.identity(4)/2)
        qpd = NumpyData(data, name="test", grid=datagrid)
        qpd.slice_data(plane)

    def testOrtho(self):
        grid = DataGrid((GRIDSIZE, GRIDSIZE, GRIDSIZE), np.identity(4))
        YD, XD, ZD = np.meshgrid(range(GRIDSIZE), range(GRIDSIZE), range(GRIDSIZE))
        
        plane = OrthoSlice(grid, YAXIS, SLICEPOS)
        xdata, _, _, _ = NumpyData(XD, name="test", grid=grid).slice_data(plane)
        ydata, _, _, _ = NumpyData(YD, name="test", grid=grid).slice_data(plane)
        zdata, _, _, _ = NumpyData(ZD, name="test", grid=grid).slice_data(plane)

        self.assertTrue(np.all(ydata == SLICEPOS))
        for x in range(GRIDSIZE):
           self.assertTrue(np.all(xdata[x,:] == x))
           self.assertTrue(np.all(zdata[:,x] == x))

    def testOrthoSwapAxis(self):
        grid = DataGrid((GRIDSIZE, GRIDSIZE, GRIDSIZE), np.identity(4))
        plane = OrthoSlice(grid, YAXIS, SLICEPOS)

        # Swap Y and Z axes
        affine = np.array([
            [1, 0, 0, 0],
            [0, 0, 1, 0],
            [0, 1, 0, 0],
            [0, 0, 0, 1]
        ])
        datagrid = DataGrid((GRIDSIZE, GRIDSIZE, GRIDSIZE), affine)
        YD, XD, ZD = np.meshgrid(range(GRIDSIZE), range(GRIDSIZE), range(GRIDSIZE))

        xdata, _, _, _ = NumpyData(XD, name="test", grid=datagrid).slice_data(plane)
        ydata, _, _, _ = NumpyData(YD, name="test", grid=datagrid).slice_data(plane)
        zdata, _, _, _ = NumpyData(ZD, name="test", grid=datagrid).slice_data(plane)

        self.assertTrue(np.all(zdata == SLICEPOS))
        for x in range(GRIDSIZE):
            self.assertTrue(np.all(xdata[x,:] == x))
            self.assertTrue(np.all(ydata[:,x] == x))

    def testOrthoReversed(self):
        grid = DataGrid((GRIDSIZE, GRIDSIZE, GRIDSIZE), np.identity(4))
        plane = OrthoSlice(grid, YAXIS, SLICEPOS)

        # Invert Z axis
        affine = np.array([
            [1, 0, 0, 0],
            [0, 1, 0, 0],
            [0, 0, -1, GRIDSIZE-1],
            [0, 0, 0, 1]
        ])
        datagrid = DataGrid((GRIDSIZE, GRIDSIZE, GRIDSIZE), affine)
        YD, XD, ZD = np.meshgrid(range(GRIDSIZE), range(GRIDSIZE), range(GRIDSIZE))

        xdata, _, _, _ = NumpyData(XD, name="test", grid=datagrid).slice_data(plane)
        ydata, _, _, _ = NumpyData(YD, name="test", grid=datagrid).slice_data(plane)
        zdata, _, transv, offset = NumpyData(ZD, name="test", grid=datagrid).slice_data(plane)
        
        # Reversal is reflected in the transformation
        self.assertTrue(np.all(transv == [[1, 0], [0, -1]]))

        self.assertTrue(np.all(ydata == SLICEPOS))
        for x in range(GRIDSIZE):
            self.assertTrue(np.all(xdata[x,:] == x))
            self.assertTrue(np.all(zdata[:,x] == x))

    def testOrthoOffset(self):
        grid = DataGrid((GRIDSIZE, GRIDSIZE, GRIDSIZE), np.identity(4))
        plane = OrthoSlice(grid, YAXIS, SLICEPOS)

        # Offset X axis
        affine = np.array([
            [1, 0, 0, 2],
            [0, 1, 0, 0],
            [0, 0, 1, 0],
            [0, 0, 0, 1]
        ])
        datagrid = DataGrid((GRIDSIZE, GRIDSIZE, GRIDSIZE), affine)
        YD, XD, ZD = np.meshgrid(range(GRIDSIZE), range(GRIDSIZE), range(GRIDSIZE))

        xdata, _, _, _ = NumpyData(XD, name="test", grid=datagrid).slice_data(plane)
        ydata, _, _, _ = NumpyData(YD, name="test", grid=datagrid).slice_data(plane)
        zdata, _, transv, offset = NumpyData(ZD, name="test", grid=datagrid).slice_data(plane)

        self.assertTrue(np.all(ydata == SLICEPOS))
        for x in range(GRIDSIZE):
            self.assertTrue(np.all(xdata[x,:] == x))
            self.assertTrue(np.all(zdata[:,x] == x))

if __name__ == '__main__':
    unittest.main()
