"""
Quantiphyse - Histogram process tests

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
