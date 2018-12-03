"""
Quantiphyse - Tests for supervoxel clustering widget

Copyright (c) 2013-2018 University of Oxford
"""
import unittest 

import numpy as np

from quantiphyse.processes import Process
from quantiphyse.test import WidgetTest, ProcessTest

from .widgets import PerfSlicWidget

NUM_SV = 4
NAME = "test_sv"
NUM_PCA = 3
SIGMA = 0.5
COMP = 0.2

class PerfSlicWidgetTest(WidgetTest):

    def widget_class(self):
        return PerfSlicWidget

    def testNoData(self):
        """ User clicks the generate buttons with no data"""
        self.harmless_click(self.w.gen_btn)

    def test3dData(self):
        self.ivm.add(self.data_3d, grid=self.grid, name="data_3d")
        self.w.ovl.setCurrentIndex(0)
        self.processEvents()
        self.assertFalse(self.w.n_comp.spin.isVisible())

        self.w.compactness.spin.setValue(COMP)
        self.w.sigma.spin.setValue(SIGMA)
        self.w.n_supervoxels.spin.setValue(NUM_SV)
        self.w.output_name.setText(NAME)

        self.harmless_click(self.w.gen_btn)
        self.processEvents()

        self.assertTrue(NAME in self.ivm.rois)
        self.assertEquals(self.ivm.current_roi.name, NAME)
        # Don't check regions as we know this doesn't work. Really you shouldn't be running
        # supervoxels without an ROI, we are just checking it handles it gracefully if you do
        #self.assertEquals(len(self.ivm.rois[NAME].regions, NUM_SV)
        self.assertFalse(self.error)

    def test3dDataMask(self):
        self.ivm.add(self.mask, grid=self.grid, name="mask", roi=True)
        self.w.ovl.setCurrentIndex(0)
        self.test3dData()
        self.assertEquals(len(self.ivm.rois[NAME].regions), NUM_SV)
        # Supervoxel value is always zero outside the ROI
        sv = self.ivm.rois[NAME].raw()
        self.assertTrue(np.all(sv[self.mask == 0] == 0))
        self.assertFalse(self.error)

    def test4dData(self):
        self.ivm.add(self.data_4d, grid=self.grid, name="data_4d")
        self.w.ovl.setCurrentIndex(0)
        self.w.roi.setCurrentIndex(0)
        self.processEvents()
        self.assertTrue(self.w.n_comp.spin.isEnabled())

        self.w.compactness.spin.setValue(COMP)
        self.w.n_comp.spin.setValue(NUM_PCA)
        self.w.sigma.spin.setValue(SIGMA)
        self.w.n_supervoxels.spin.setValue(NUM_SV)
        self.w.output_name.setText(NAME)

        self.harmless_click(self.w.gen_btn)
        self.processEvents()

        self.assertTrue(NAME in self.ivm.rois)
        self.assertEquals(self.ivm.current_roi.name, NAME)
        # Don't check regions as we know this doesn't work. Really you shouldn't be running
        # supervoxels without an ROI, we are just checking it handles it gracefully if you do
        #self.assertEquals(len(self.ivm.rois[NAME].regions, NUM_SV)
        self.assertFalse(self.error)

    def test4dDataMask(self):
        self.ivm.add(self.mask, grid=self.grid, name="mask", roi=True)
        self.w.ovl.setCurrentIndex(0)
        self.w.roi.setCurrentIndex(0)
        self.test4dData()
        self.assertEquals(len(self.ivm.rois[NAME].regions), NUM_SV)
        # Supervoxel value is always zero outside the ROI
        sv = self.ivm.rois[NAME].raw()
        self.assertTrue(np.all(sv[self.mask == 0] == 0))
        self.assertFalse(self.error)

class MeanValuesProcessTest(ProcessTest):

    def test3d(self):
        yaml = """
  - MeanValues:
        data: data_3d
        roi: mask
        output-name: data_roi_mean
"""
        self.run_yaml(yaml)
        self.assertEqual(self.status, Process.SUCCEEDED)
        self.assertTrue("data_roi_mean" in self.ivm.data)

class SupervoxelsProcessTest(ProcessTest):

    def test3d(self):
        yaml = """
  - Supervoxels:
      data: data_3d
      output-name: sv_3d
      compactness: 0.01
      n-supervoxels: 20
"""
        self.run_yaml(yaml)
        self.assertEqual(self.status, Process.SUCCEEDED)
        self.assertTrue("sv_3d" in self.ivm.rois)

    def test4d(self):
        yaml = """

  - Supervoxels:
      data: data_4d
      output-name: sv_4d
      n-components: 3
      compactness: 0.02
      n-supervoxels: 30
"""
        self.run_yaml(yaml)
        self.assertEqual(self.status, Process.SUCCEEDED)
        self.assertTrue("sv_4d" in self.ivm.rois)

if __name__ == '__main__':
    unittest.main()
