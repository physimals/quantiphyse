"""
Quantiphyse - Clustering process tests

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

class KmeansProcessTest(ProcessTest):
    
    def testKmeans3d(self):
        yaml = """       
  - KMeans:
        data: testdata_3d
        n-clusters: 3
        output-name: test_clusters_3d
        
  - Save:
        test_clusters_3d:
"""
        self.run_yaml(yaml)
        self.assertEqual(self.status, Process.SUCCEEDED)
        self.assertTrue("test_clusters_3d" in self.ivm.data)
        self.assertTrue(os.path.exists(os.path.join(self.output_dir, "case", "test_clusters_3d.nii.gz")))

    def testKmeans4d(self):
        yaml = """
  - KMeans:
        data: testdata_4d
        n-clusters: 4
        n-pca: 5
        output-name: test_clusters_4d
        
  - Save:
        test_clusters_4d:
"""
        self.run_yaml(yaml)
        self.assertEqual(self.status, Process.SUCCEEDED)
        self.assertTrue("test_clusters_4d" in self.ivm.data)
        self.assertTrue(os.path.exists(os.path.join(self.output_dir, "case", "test_clusters_4d.nii.gz")))

if __name__ == '__main__':
    unittest.main()
