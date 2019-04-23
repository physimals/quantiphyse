import os
import unittest

import numpy as np

from quantiphyse.processes import Process
from quantiphyse.test import WidgetTest, ProcessTest

from .widgets import ClusteringWidget

NUM_CLUSTERS = 4
NAME = "test_clusters"
NUM_PCA = 3

class ClusteringWidgetTest(WidgetTest):

    def widget_class(self):
        return ClusteringWidget

    def testNoData(self):
        """ User clicks the run button with no data"""
        if self.w.run_btn.isEnabled():
            self.w.run_btn.clicked.emit()
        self.assertFalse(self.error)

    def test3dData(self):
        """ 3d clustering"""
        self.ivm.add(self.data_3d, grid=self.grid, name="data_3d")
        self.w.data_combo.setCurrentIndex(0)
        self.processEvents()
        self.assertFalse(self.w.n_pca.spin.isVisible())

        self.w.n_clusters.spin.setValue(NUM_CLUSTERS)
        self.w.output_name.setText(NAME)
        self.w.run_btn.clicked.emit()
        self.processEvents()
        
        self.assertTrue(NAME in self.ivm.rois)
        self.assertEquals(self.ivm.current_roi.name, NAME)
        self.assertEquals(len(self.ivm.rois[NAME].regions), NUM_CLUSTERS)
        self.assertFalse(self.error)
        
    def test3dDataWithRoi(self):
        """ 3d clustering"""
        self.ivm.add(self.data_3d, grid=self.grid, name="data_3d")
        self.ivm.add(self.mask, grid=self.grid, name="mask")
        self.w.data_combo.setCurrentIndex(0)
        self.w.roi_combo.setCurrentIndex(1)
        self.w.n_clusters.spin.setValue(NUM_CLUSTERS)
        self.w.output_name.setText(NAME)
        self.w.run_btn.clicked.emit()
        self.processEvents()
        
        self.assertTrue(NAME in self.ivm.rois)
        self.assertEquals(self.ivm.current_roi.name, NAME)
        self.assertEquals(len(self.ivm.rois[NAME].regions), NUM_CLUSTERS)
        # Cluster value is always zero outside the ROI
        cl = self.ivm.rois[NAME].raw()
        self.assertTrue(np.all(cl[self.mask == 0] == 0))
        self.assertFalse(self.error)

    def test4dData(self):
        """ 4d clustering """
        self.ivm.add(self.data_4d, grid=self.grid, name="data_4d")
        self.w.data_combo.setCurrentIndex(0)
        self.processEvents()            
        self.assertTrue(self.w.n_pca.spin.isVisible())

        self.w.n_pca.spin.setValue(NUM_PCA)
        self.w.n_clusters.spin.setValue(NUM_CLUSTERS)
        self.w.output_name.setText(NAME)
        self.w.run_btn.clicked.emit()
        self.processEvents()
        
        self.assertTrue(NAME in self.ivm.rois)
        self.assertEquals(self.ivm.current_roi.name, NAME)
        self.assertEquals(len(self.ivm.rois[NAME].regions), NUM_CLUSTERS)
        self.assertFalse(self.error)
        
    def test4dDataWithRoi(self):
        """ 4d clustering within an ROI"""
        self.ivm.add(self.data_4d, grid=self.grid, name="data_4d")
        self.ivm.add(self.mask, grid=self.grid, name="mask")
        self.w.data_combo.setCurrentIndex(0)
        self.w.roi_combo.setCurrentIndex(1)

        self.w.n_pca.spin.setValue(NUM_PCA)
        self.w.n_clusters.spin.setValue(NUM_CLUSTERS)
        self.w.output_name.setText(NAME)
        self.w.run_btn.clicked.emit()
        self.processEvents()
        
        self.assertTrue(NAME in self.ivm.rois)
        self.assertEquals(self.ivm.current_roi.name, NAME)
        self.assertEquals(len(self.ivm.rois[NAME].regions), NUM_CLUSTERS)
        # Cluster value is always zero outside the ROI
        cl = self.ivm.rois[NAME].raw()
        self.assertTrue(np.all(cl[self.mask == 0] == 0))
        self.assertFalse(self.error)

class KMeansProcessTest(ProcessTest):

    def test3d(self):
        yaml = """
  - KMeans:
        data: data_3d
        n-clusters: 3
        output-name: clusters_3d
  
  - Save:
        clusters_3d: clusters.nii.gz
"""
        self.run_yaml(yaml)
        self.assertEqual(self.status, Process.SUCCEEDED)
        self.assertTrue("clusters_3d" in self.ivm.rois)
        self.assertTrue(os.path.exists(os.path.join(self.output_dir, "case", "clusters.nii.gz")))

    def test4d(self):
        yaml = """
  - KMeans:
        data: data_4d
        n-clusters: 3
        n-pca: 
        output-name: clusters_4d
  
  - Save:
        clusters_4d: 4dclusters.nii.gz
"""
        self.run_yaml(yaml)
        self.assertEqual(self.status, Process.SUCCEEDED)
        self.assertTrue("clusters_4d" in self.ivm.rois)
        self.assertTrue(os.path.exists(os.path.join(self.output_dir, "case", "4dclusters.nii.gz")))

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

if __name__ == '__main__':
    unittest.main()
