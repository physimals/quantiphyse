import os
import unittest
import traceback

import numpy as np

from quantiphyse.processes import Process
from quantiphyse.test import ProcessTest

from .processes import CalcVolumesProcess

class AnalysisProcessTest(ProcessTest):
    
    def testCalcVolumes(self):
        yaml = """       
  - CalcVolumes:
        roi: mask
        output-name: mask_vol

  - SaveExtras: 
        mask_vol: mask_vol.tsv
"""
        self.run_yaml(yaml)
        self.assertEqual(self.status, Process.SUCCEEDED)
        self.assertTrue("mask_vol" in self.ivm.extras)
        self.assertTrue(os.path.exists(os.path.join(self.output_dir, "case", "mask_vol.tsv")))

    def testSummaryStats(self):
        yaml = """
  - OverlayStats:
        data: data_3d
        output-name: testdata_stats

  - SaveExtras: 
        testdata_stats: testdata_stats.tsv
"""
        self.run_yaml(yaml)
        self.assertEqual(self.status, Process.SUCCEEDED)
        self.assertTrue("testdata_stats" in self.ivm.extras)
        self.assertTrue(os.path.exists(os.path.join(self.output_dir, "case", "testdata_stats.tsv")))

    def testRadialProfile(self):
        yaml = """ 
  - RadialProfile:
        data: data_3d
        centre: 2, 2, 2
        output-name: testdata_rp

  - SaveExtras: 
        testdata_rp: testdata_rp.tsv
"""
        self.run_yaml(yaml)
        self.assertEqual(self.status, Process.SUCCEEDED)
        self.assertTrue("testdata_rp" in self.ivm.extras)
        self.assertTrue(os.path.exists(os.path.join(self.output_dir, "case", "testdata_rp.tsv")))

    def testHistogram(self):
        yaml = """
  - Histogram:
        data: data_3d
        bins: 10
        output-name: testdata_hist
        roi: mask

  - SaveExtras: 
        testdata_hist: testdata_hist.tsv
"""
        self.run_yaml(yaml)
        self.assertEqual(self.status, Process.SUCCEEDED)
        self.assertTrue("testdata_hist" in self.ivm.extras)
        self.assertTrue(os.path.exists(os.path.join(self.output_dir, "case", "testdata_hist.tsv")))

if __name__ == '__main__':
    unittest.main()
