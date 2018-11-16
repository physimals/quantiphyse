"""
Quantiphyse - Tests for the radial profile process

Copyright (c) 2013-2018 University of Oxford
"""
import os
import unittest

from quantiphyse.processes import Process
from quantiphyse.test import ProcessTest

class RadialProfileProcessTest(ProcessTest):
    
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

if __name__ == '__main__':
    unittest.main()
