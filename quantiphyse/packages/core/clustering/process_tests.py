"""
Quantiphyse - Clustering process tests

Copyright (c) 2013-2018 University of Oxford
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
