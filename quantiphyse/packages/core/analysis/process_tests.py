"""
Quantiphyse - Analysis process tests

Copyright (c) 2013-2020 University of Oxford

Licensed under the Apache License, Version 2.0 (the "License");
you may not use this file except in compliance with the License.
You may obtain a copy of the License at

    http://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and
limitations under the License.
"""
import os
import unittest

import numpy as np
import pandas as pd
import scipy

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

    def testSummaryStatsCustom(self):
        yaml = """
  - DataStatistics:
        data: data_3d
        output-name: testdata_stats
        stats: [mean, median, iqr, uq, lq, skewness, kurtosis, n, iqmean, iqn, fwhm, mode]
        exact-median: True

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

        uq, med, lq = np.nanquantile(self.data_3d, [0.75, 0.5, 0.25])
        iqr = uq - lq
        iqd = self.data_3d[self.data_3d > lq]
        iqd = iqd[iqd < uq]

        loc, scale = scipy.stats.norm.fit(self.data_3d)

        self.assertEquals(data.shape[0], 12)
        self.assertEquals(data.shape[1], 2)
        self.assertAlmostEquals(data[0, 1], np.mean(self.data_3d), delta=0.01)
        self.assertAlmostEquals(data[1, 1], np.median(self.data_3d), delta=0.01)
        self.assertAlmostEquals(data[2, 1], iqr, delta=0.01)
        self.assertAlmostEquals(data[3, 1], uq, delta=0.01)
        self.assertAlmostEquals(data[4, 1], lq, delta=0.01)
        self.assertAlmostEquals(data[5, 1], scipy.stats.skew(self.data_3d.flatten()), delta=0.01)
        self.assertAlmostEquals(data[6, 1], scipy.stats.kurtosis(self.data_3d.flatten()), delta=0.01)
        self.assertAlmostEquals(data[7, 1], np.count_nonzero(~np.isnan(self.data_3d)), delta=0.01)
        self.assertAlmostEquals(data[8, 1], np.mean(iqd), delta=0.01)
        self.assertAlmostEquals(data[9, 1], np.count_nonzero(~np.isnan(iqd)), delta=0.01)
        self.assertAlmostEquals(data[10, 1], scale*2.355, delta=0.01)
        self.assertAlmostEquals(data[11, 1], loc, delta=0.01)

    def testSummaryStatsAll(self):
        yaml = """
  - DataStatistics:
        data: data_3d
        output-name: testdata_stats
        stats: all

  - SaveExtras:
        testdata_stats: testdata_stats.tsv
"""
        NUM_ALL_STATS = 15 # Needs updating if we add/remove any!
        self.run_yaml(yaml)
        self.assertEqual(self.status, Process.SUCCEEDED)
        self.assertTrue("testdata_stats" in self.ivm.extras)

        fname = os.path.join(self.output_dir, "case", "testdata_stats.tsv")
        self.assertTrue(os.path.exists(fname))
        df = pd.read_csv(fname, sep='\t')
        data = df.values
        self.assertEquals(data.shape[0], NUM_ALL_STATS)
        self.assertEquals(data.shape[1], 2)

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

    def testSummaryStatsDataLimits(self):
        yaml = """
  - DataStatistics:
        data: data_3d
        output-name: testdata_stats
        data-limits:
          data_3d: [0.25, 0.75]

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

        allowed_data = self.data_3d[self.data_3d >= 0.25]
        allowed_data = allowed_data[allowed_data <= 0.75]
        self.assertAlmostEquals(data[0, 1], np.mean(allowed_data), delta=0.01)
        self.assertAlmostEquals(data[1, 1], np.median(allowed_data), delta=0.01)
        self.assertAlmostEquals(data[2, 1], np.std(allowed_data), delta=0.01)
        self.assertAlmostEquals(data[3, 1], np.min(allowed_data), delta=0.01)
        self.assertAlmostEquals(data[4, 1], np.max(allowed_data), delta=0.01)

if __name__ == '__main__':
    unittest.main()
