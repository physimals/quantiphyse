"""
Quantiphyse - Histogram process tests

Copyright (c) 2013-2018 University of Oxford
"""
import os
import unittest

from quantiphyse.processes import Process
from quantiphyse.test import ProcessTest

class HistogramProcessTest(ProcessTest):

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
