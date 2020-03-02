"""
Quantiphyse - Tests for the radial profile process

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
