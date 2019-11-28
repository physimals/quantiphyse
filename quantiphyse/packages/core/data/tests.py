import unittest

import numpy as np

from quantiphyse.data import DataGrid
from quantiphyse.test.widget_test import WidgetTest
from quantiphyse.processes import Process
from quantiphyse.test import ProcessTest

from .widgets import ResampleDataWidget

NAME = "resampled"
ORDER = 0

class ResampleDataWidgetTest(WidgetTest):

    def widget_class(self):
        return ResampleDataWidget

    def testNoData(self):
        """ User clicks the run button with no data"""
        self.w.run.btn.clicked.emit()
        self.processEvents()
        self.assertFalse(self.error)
        self.assertTrue(self.qpe)

    def testResampleToSelf3d(self):
        """ 3d data resampled to self"""
        self.ivm.add(self.data_3d, grid=self.grid, name="data_3d")
        self.w.order.setCurrentIndex(0)
        self.processEvents()

        self.assertEqual(self.w.data.currentText(), "data_3d")
        self.assertEqual(self.w.grid_data.currentText(), "data_3d")
        self.assertEqual(self.w.output_name.value, "data_3d_res")

        self.w.run.btn.clicked.emit()
        self.processEvents()
        
        self.assertFalse(self.error)
        self.assertTrue("data_3d" in self.ivm.data)
        self.assertTrue("data_3d_res" in self.ivm.data)
        
        # Resampled data should match original data
        self.assertTrue(self.ivm.data["data_3d_res"].grid.matches(self.ivm.data["data_3d"].grid))
        self.assertTrue(np.all(self.ivm.data["data_3d_res"].raw() == self.data_3d))
        
    def testResampleToSelf4d(self):
        """ 4d data resampled to self"""
        self.ivm.add(self.data_4d, grid=self.grid, name="data_4d")
        self.w.order.setCurrentIndex(0)
        self.processEvents()

        self.assertEqual(self.w.data.currentText(), "data_4d")
        self.assertEqual(self.w.grid_data.currentText(), "data_4d")
        self.assertEqual(self.w.output_name.value, "data_4d_res")

        self.w.run.btn.clicked.emit()
        self.processEvents()

        self.assertFalse(self.error)
        self.assertTrue("data_4d" in self.ivm.data)
        self.assertTrue("data_4d_res" in self.ivm.data)
        
        # Resampled data should match original data
        self.assertTrue(self.ivm.data["data_4d_res"].grid.matches(self.ivm.data["data_4d"].grid))
        self.assertTrue(np.all(self.ivm.data["data_4d_res"].raw() == self.data_4d))
        
    def testResampleToHiResNN(self):
        self.ivm.add(self.data_3d, grid=self.grid, name="data_3d")
        hires_shape = [dim*2 for dim in self.data_3d.shape]
        hires_grid = DataGrid(hires_shape, np.identity(4) / 2)
        hires_data = np.tile(self.data_3d, (2, 2, 2))
        self.ivm.add(hires_data, grid=hires_grid, name="hires_data")

        self.w.order.setCurrentIndex(0)
        self.w.data.setCurrentIndex(self.w.data.findText("data_3d"))
        self.w.grid_data.setCurrentIndex(self.w.grid_data.findText("hires_data"))
        self.processEvents()

        self.assertEqual(self.w.output_name.value, "data_3d_res")
        
        self.w.run.btn.clicked.emit()
        self.processEvents()

        self.assertFalse(self.error)
        self.assertTrue("data_3d_res" in self.ivm.data)
        
        # Resampled data should match original data but at twice the resolution
        self.assertTrue(self.ivm.data["data_3d_res"].grid.matches(hires_grid))
        data_res = self.ivm.data["data_3d_res"].raw()
        
        for x in range(data_res.shape[0]):
            for y in range(data_res.shape[1]):
                for z in range(data_res.shape[2]):
                    nx, ny, nz = int(float(x)/2+0.5), int(float(y)/2+0.5), int(float(z)/2+0.5)
                    if nx < self.data_3d.shape[0] and ny < self.data_3d.shape[1] and nz < self.data_3d.shape[2]:
                        self.assertEqual(data_res[x, y, z], self.data_3d[nx, ny, nz])
                    else:
                        self.assertEqual(data_res[x, y, z], 0)
                            
    def testResampleToHiResLinear(self):
        self.ivm.add(self.data_3d, grid=self.grid, name="data_3d")
        hires_shape = [dim*2 for dim in self.data_3d.shape]
        hires_grid = DataGrid(hires_shape, np.identity(4) / 2)
        hires_data = np.tile(self.data_3d, (2, 2, 2))
        self.ivm.add(hires_data, grid=hires_grid, name="hires_data")

        self.w.order.setCurrentIndex(1)
        self.w.data.setCurrentIndex(self.w.data.findText("data_3d"))
        self.w.grid_data.setCurrentIndex(self.w.grid_data.findText("hires_data"))
        self.processEvents()

        self.assertEqual(self.w.output_name.value, "data_3d_res")
        
        self.w.run.btn.clicked.emit()
        self.processEvents()

        self.assertFalse(self.error)
        self.assertTrue("data_3d_res" in self.ivm.data)
        
        # Resampled data should match original data but at twice the resolution
        self.assertTrue(self.ivm.data["data_3d_res"].grid.matches(hires_grid))
        data_res = self.ivm.data["data_3d_res"].raw()
        
        X = range(self.data_3d.shape[0])
        Y = range(self.data_3d.shape[1])
        Z = range(self.data_3d.shape[2])
        
        for x in range(data_res.shape[0]):
            for y in range(data_res.shape[1]):
                for z in range(data_res.shape[2]):
                    gx, gy, gz = float(x)/2, float(y)/2, float(z)/2
                    from scipy.interpolate import interpn
                    d = interpn((X, Y, Z), self.data_3d, (gx, gy, gz), method="linear", bounds_error=False, fill_value=0)
                    self.assertAlmostEqual(data_res[x, y, z], d[0])

    def testDownsample3d(self):
        """ 3d data downsampled"""
        self.ivm.add(self.data_3d, grid=self.grid, name="data_3d")
        self.w.resample_type.value = "down"
        self.w.factor.value = 3
        self.processEvents()

        self.assertEqual(self.w.data.currentText(), "data_3d")
        self.assertEqual(self.w.grid_data.currentText(), "data_3d")
        self.assertEqual(self.w.output_name.value, "data_3d_res")
        self.assertEqual(self.w.resample_type.value, "down")
        self.assertEqual(self.w.factor.value, 3)

        self.w.run.btn.clicked.emit()
        self.processEvents()

        self.assertFalse(self.error)
        self.assertTrue("data_3d" in self.ivm.data)
        self.assertTrue("data_3d_res" in self.ivm.data)
        
        # FIXME check resampled data
        
class ResampleProcessTest(ProcessTest):
    
    def testResample3d(self):
        yaml = """       
  - Resample:
      data: data_3d
      order: 1 # Linear interpolation
      grid: data_3d
      output-name: testdata_resampled
"""
        self.run_yaml(yaml)
        self.assertEqual(self.status, Process.SUCCEEDED)
        self.assertTrue("testdata_resampled" in self.ivm.data)

    def testResample4d(self):
        yaml = """
  - Resample:
      data: data_4d
      order: 3 # Cubic interpolation
      grid: data_4d
      output-name: testdata_resampled
"""
        self.run_yaml(yaml)
        self.assertEqual(self.status, Process.SUCCEEDED)
        self.assertTrue("testdata_resampled" in self.ivm.data)
   
if __name__ == '__main__':
    unittest.main()
