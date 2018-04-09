import unittest
import os
import sys
import numpy as np

from quantiphyse.volumes import DataGrid, SlicePlane, OrthoSlice

GRIDSIZE = 5
SLICEPOS = 2
XAXIS, YAXIS, ZAXIS = 0, 1, 2

class OrthoSliceTest(unittest.TestCase):

    def setUp(self):
        pass

    def tearDown(self):
        pass

    def testOrthoY(self):
        grid = DataGrid((GRIDSIZE, GRIDSIZE, GRIDSIZE), np.identity(4))
        YD, XD, ZD = np.meshgrid(range(GRIDSIZE), range(GRIDSIZE), range(GRIDSIZE))

        plane = OrthoSlice(grid, YAXIS, SLICEPOS)
        self.assertEquals(plane.origin, (0, SLICEPOS, 0))
        self.assertEquals(len(plane.basis), 2)
        self.assertTrue((1, 0, 0) in plane.basis)
        self.assertTrue((0, 0, 1) in plane.basis)
        
    def testOrthoX(self):
        grid = DataGrid((GRIDSIZE, GRIDSIZE, GRIDSIZE), np.identity(4))
        plane = OrthoSlice(grid, XAXIS, SLICEPOS)
        self.assertEquals(plane.origin, (SLICEPOS, 0, 0))
        self.assertEquals(len(plane.basis), 2)
        self.assertTrue((0, 1, 0) in plane.basis)
        self.assertTrue((0, 0, 1) in plane.basis)
        
    def testOrthoZ(self):
        grid = DataGrid((GRIDSIZE, GRIDSIZE, GRIDSIZE), np.identity(4))
        plane = OrthoSlice(grid, ZAXIS, SLICEPOS)
        self.assertEquals(plane.origin, (0, 0, SLICEPOS))
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
        origin = tuple(SLICEPOS * trans[:3,0])
        plane = OrthoSlice(grid, XAXIS, SLICEPOS)
        self.assertAlmostEquals(plane.origin, origin)
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
        origin = tuple(SLICEPOS * trans[:3,1])
        plane = OrthoSlice(grid, YAXIS, SLICEPOS)
        self.assertAlmostEquals(plane.origin, origin)
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
        origin = tuple(SLICEPOS * trans[:3,2])
        plane = OrthoSlice(grid, ZAXIS, SLICEPOS)
        self.assertAlmostEquals(plane.origin, origin)
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
        print("testHighRes")
        grid = DataGrid((GRIDSIZE, GRIDSIZE, GRIDSIZE), np.identity(4))
        plane = OrthoSlice(grid, YAXIS, SLICEPOS)
        data = np.random.rand(GRIDSIZE*2, GRIDSIZE*2, GRIDSIZE*2)
        datagrid = DataGrid((GRIDSIZE*2, GRIDSIZE*2, GRIDSIZE*2), np.identity(4)/2)
        plane.slice_data(data, datagrid)

    def testOrtho(self):
        print("testOrtho")
        grid = DataGrid((GRIDSIZE, GRIDSIZE, GRIDSIZE), np.identity(4))
        YD, XD, ZD = np.meshgrid(range(GRIDSIZE), range(GRIDSIZE), range(GRIDSIZE))

        plane = OrthoSlice(grid, YAXIS, SLICEPOS)
        xdata = plane.slice_data(XD, grid)
        ydata = plane.slice_data(YD, grid)
        zdata = plane.slice_data(ZD, grid)

        self.assertTrue(np.all(ydata == SLICEPOS))
        for x in range(GRIDSIZE):
           self.assertTrue(np.all(xdata[x,:] == x))
           self.assertTrue(np.all(zdata[:,x] == x))

    def testOrthoSwapAxis(self):
        print("testOrthoSwapAxis")
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

        xdata = plane.slice_data(XD, datagrid)
        ydata = plane.slice_data(YD, datagrid)
        zdata = plane.slice_data(ZD, datagrid)


        self.assertTrue(np.all(zdata == SLICEPOS))
        for x in range(GRIDSIZE):
            self.assertTrue(np.all(xdata[x,:] == x))
            self.assertTrue(np.all(ydata[:,x] == x))

    def testOrthoReversed(self):
        print("testOrthoReversed")
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

        xdata = plane.slice_data(XD, datagrid)
        ydata = plane.slice_data(YD, datagrid)
        zdata = plane.slice_data(ZD, datagrid)

        self.assertTrue(np.all(ydata == SLICEPOS))
        for x in range(GRIDSIZE):
            self.assertTrue(np.all(xdata[x,:] == x))
            self.assertTrue(np.all(zdata[:,x] == GRIDSIZE-1-x))

    def testOrthoOffset(self):
        print("testOrthoOffset")
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
        data = np.random.rand(GRIDSIZE, GRIDSIZE), range(GRIDSIZE))

        xdata = plane.slice_data(XD, datagrid)
        ydata = plane.slice_data(YD, datagrid)
        zdata = plane.slice_data(ZD, datagrid)
        print(xdata)
        print(ydata)
        print(zdata)

        #self.assertTrue(np.all(ydata == SLICEPOS))
        for x in range(GRIDSIZE):
            self.assertTrue(np.all(xdata[x,:] == max(0, x-2)))
            self.assertTrue(np.all(zdata[:,x] == GRIDSIZE-1-x))

if __name__ == '__main__':
    unittest.main()
