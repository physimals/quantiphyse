"""
Quantiphyse - Analysis process tests

Copyright (c) 2013-2018 University of Oxford
"""
import os
import unittest

import numpy as np
import pandas as pd

from quantiphyse.processes import Process
from quantiphyse.test import ProcessTest

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

    def testSummaryStatsOldName(self):
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

    def testSummaryStats(self):
        yaml = """
  - DataStatistics:
        data: data_3d
        output-name: testdata_stats

  - SaveExtras: 
        testdata_stats: testdata_stats.tsv
"""
        self.run_yaml(yaml)
        self.assertEqual(self.status, Process.SUCCEEDED)
        self.assertTrue("testdata_stats" in self.ivm.extras)

        fname = os.path.join(self.output_dir, "case", "testdata_stats.tsv")
        self.assertTrue(os.path.exists(fname))
        df = pd.read_csv(fname, sep='\t')
        data = df.values
        self.assertEquals(data.shape[0], 5)
        self.assertEquals(data.shape[1], 2)
        self.assertAlmostEquals(data[0, 1], np.mean(self.data_3d), delta=0.01)
        self.assertAlmostEquals(data[1, 1], np.median(self.data_3d), delta=0.01)
        self.assertAlmostEquals(data[2, 1], np.std(self.data_3d), delta=0.01)
        self.assertAlmostEquals(data[3, 1], np.min(self.data_3d), delta=0.01)
        self.assertAlmostEquals(data[4, 1], np.max(self.data_3d), delta=0.01)

    def testSummaryStatsMultiple(self):
        yaml = """
  - DataStatistics:
        data: [data_3d, data_4d]
        output-name: testdata_stats

  - SaveExtras: 
        testdata_stats: testdata_stats.tsv
"""
        self.run_yaml(yaml)
        self.assertEqual(self.status, Process.SUCCEEDED)
        self.assertTrue("testdata_stats" in self.ivm.extras)

        fname = os.path.join(self.output_dir, "case", "testdata_stats.tsv")
        self.assertTrue(os.path.exists(fname))
        df = pd.read_csv(fname, sep='\t')
        data = df.values
        self.assertEquals(data.shape[0], 5)
        self.assertEquals(data.shape[1], 3)
        self.assertAlmostEquals(data[0, 1], np.mean(self.data_3d), delta=0.01)
        self.assertAlmostEquals(data[1, 1], np.median(self.data_3d), delta=0.01)
        self.assertAlmostEquals(data[2, 1], np.std(self.data_3d), delta=0.01)
        self.assertAlmostEquals(data[3, 1], np.min(self.data_3d), delta=0.01)
        self.assertAlmostEquals(data[4, 1], np.max(self.data_3d), delta=0.01)
        self.assertAlmostEquals(data[0, 2], np.mean(self.data_4d), delta=0.01)
        self.assertAlmostEquals(data[1, 2], np.median(self.data_4d), delta=0.01)
        self.assertAlmostEquals(data[2, 2], np.std(self.data_4d), delta=0.01)
        self.assertAlmostEquals(data[3, 2], np.min(self.data_4d), delta=0.01)
        self.assertAlmostEquals(data[4, 2], np.max(self.data_4d), delta=0.01)

    def testSummaryStatsRoi(self):
        yaml = """
  - KMeans:
        data: data_3d
        n-clusters: 3
        output-name: clusters
        
  - DataStatistics:
        data: [data_3d, data_4d]
        roi: clusters
        output-name: testdata_stats

  - SaveExtras: 
        testdata_stats: testdata_stats.tsv
"""
        self.run_yaml(yaml)
        self.assertEqual(self.status, Process.SUCCEEDED)
        self.assertTrue("testdata_stats" in self.ivm.extras)

        fname = os.path.join(self.output_dir, "case", "testdata_stats.tsv")
        self.assertTrue(os.path.exists(fname))
        df = pd.read_csv(fname, sep='\t')
        data = df.values
        self.assertEquals(data.shape[0], 5)
        self.assertEquals(data.shape[1], 7)
        clusters = self.ivm.data["clusters"].raw()

        for roi_region in range(3):
            data_3d = self.data_3d[clusters == roi_region+1]
            data_4d = self.data_4d[clusters == roi_region+1]
            self.assertAlmostEquals(data[0, 1+roi_region], np.mean(data_3d), delta=0.01)
            self.assertAlmostEquals(data[1, 1+roi_region], np.median(data_3d), delta=0.01)
            self.assertAlmostEquals(data[2, 1+roi_region], np.std(data_3d), delta=0.01)
            self.assertAlmostEquals(data[3, 1+roi_region], np.min(data_3d), delta=0.01)
            self.assertAlmostEquals(data[4, 1+roi_region], np.max(data_3d), delta=0.01)
            self.assertAlmostEquals(data[0, 4+roi_region], np.mean(data_4d), delta=0.01)
            self.assertAlmostEquals(data[1, 4+roi_region], np.median(data_4d), delta=0.01)
            self.assertAlmostEquals(data[2, 4+roi_region], np.std(data_4d), delta=0.01)
            self.assertAlmostEquals(data[3, 4+roi_region], np.min(data_4d), delta=0.01)
            self.assertAlmostEquals(data[4, 4+roi_region], np.max(data_4d), delta=0.01)

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

    def testExecMultiply(self):
        yaml = """
  - Exec:
      test1: data_3d * 3.14159265  
"""
        self.run_yaml(yaml)
        self.assertEqual(self.status, Process.SUCCEEDED)
        self.assertTrue("test1" in self.ivm.data)

    def testExecDemean(self):
        yaml = """
  - Exec:
      test1: data_3d - np.mean(data_3d)
"""
        self.run_yaml(yaml)
        self.assertEqual(self.status, Process.SUCCEEDED)
        self.assertTrue("test1" in self.ivm.data)

    def testExecSubtractVolume(self):
        yaml = """
  - Exec:
      test1: data_3d - data_4d[..., 0]
"""
        self.run_yaml(yaml)
        self.assertEqual(self.status, Process.SUCCEEDED)
        self.assertTrue("test1" in self.ivm.data)

if __name__ == '__main__':
    unittest.main()
