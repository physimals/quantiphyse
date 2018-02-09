import unittest
import os
import sys
import numpy as np

from quantiphyse.volumes import DataGrid, SlicePlane

GRIDSIZE = 5
SLICEPOS = 2
XAXIS, YAXIS, ZAXIS = 0, 1, 2

class SlicePlaneTest(unittest.TestCase):

    def setUp(self):
        pass

    def tearDown(self):
        pass

    def testOrtho(self):
        grid = DataGrid((GRIDSIZE, GRIDSIZE, GRIDSIZE), np.identity(4))
        YD, XD, ZD = np.meshgrid(range(GRIDSIZE), range(GRIDSIZE), range(GRIDSIZE))

        plane = SlicePlane(grid, ortho=(YAXIS, SLICEPOS))
        xdata = plane.slice_data(XD)
        ydata = plane.slice_data(YD)
        zdata = plane.slice_data(ZD)

        self.assertTrue(np.all(ydata == SLICEPOS))
        for x in range(GRIDSIZE):
            self.assertTrue(np.all(xdata[x,:] == x))
            self.assertTrue(np.all(zdata[:,x] == x))

    def testFromPlane(self):
        grid = DataGrid((GRIDSIZE, GRIDSIZE, GRIDSIZE), np.identity(4))
        grid2 = DataGrid((20, 20, 20), np.identity(4))

        plane = SlicePlane(grid, ortho=(YAXIS, SLICEPOS))
        plane2 = SlicePlane(grid2, plane=plane)

        print(plane2.origin, plane2.basis_vectors)
        
    def testBasic(self):
        grid = DataGrid((10, 10, 10), np.identity(4))
        YD, XD, ZD = np.meshgrid(range(10), range(10), range(10))

        #plane1 = SlicePlane(grid, ortho=(1, 10))
        #plane2 = SlicePlane(grid, origin=(0, 0, 0), unit_vectors=([1, 0, 0], [0, 0, 1]))
        #plane3 = SlicePlane(grid, origin=(0, 5, 0), unit_vectors=([1, 0, 0], [0, -1, 0]))
        #sdata = plane3.slice_data(XD)
        #print(sdata)
#        print(XD[:,5:,0])
        #plane4 = SlicePlane(grid, origin=(0, 0, 0), unit_vectors=([1, 1, 0.5], [0, 0, 1]))
        #plane5 = SlicePlane(grid, origin=(-3, 0, 0), basis_vectors=([1, 1, 0], [-1, 1, 0]))
        #sdata, smask = plane5.slice_data(XD, include_mask=True)
        #print(sdata)
        #print(smask)

if __name__ == '__main__':
    unittest.main()
