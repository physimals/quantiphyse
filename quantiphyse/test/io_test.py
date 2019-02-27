import os

import pandas as pd

from quantiphyse.processes import Process
from quantiphyse.test import ProcessTest
from quantiphyse.data.extras import DataFrameExtra

class IoProcessTest(ProcessTest):

    def testSaveAllExcept(self):
        yaml = """
  - SaveAllExcept:
        data_3d:
        data_4d_moving:
"""
        self.run_yaml(yaml)
        self.assertEqual(self.status, Process.SUCCEEDED)
        self.assertTrue(os.path.exists(os.path.join(self.output_dir, "case", "data_4d.nii")))
        self.assertTrue(os.path.exists(os.path.join(self.output_dir, "case", "mask.nii")))
        self.assertFalse(os.path.exists(os.path.join(self.output_dir, "case", "data_4d_moving.nii")))
        self.assertFalse(os.path.exists(os.path.join(self.output_dir, "case", "data_3d.nii")))

    def testSaveAll(self):
        yaml = """
  - SaveAllExcept:
"""
        self.run_yaml(yaml)
        self.assertEqual(self.status, Process.SUCCEEDED)
        self.assertTrue(os.path.exists(os.path.join(self.output_dir, "case", "data_4d.nii")))
        self.assertTrue(os.path.exists(os.path.join(self.output_dir, "case", "mask.nii")))
        self.assertTrue(os.path.exists(os.path.join(self.output_dir, "case", "data_4d_moving.nii")))
        self.assertTrue(os.path.exists(os.path.join(self.output_dir, "case", "data_3d.nii")))

    def testSave(self):
        yaml = """
  - Save:
        data_3d:
        data_4d: data_multivol
"""
        self.run_yaml(yaml)
        self.assertEqual(self.status, Process.SUCCEEDED)
        self.assertTrue(os.path.exists(os.path.join(self.output_dir, "case", "data_multivol.nii")))
        self.assertTrue(os.path.exists(os.path.join(self.output_dir, "case", "data_3d.nii")))
        self.assertTrue("data_3d" in self.ivm.data)
        self.assertTrue("data_4d" in self.ivm.data)

    def testSaveDelete(self):
        yaml = """
  - SaveAndDelete:
        data_3d:
        data_4d: data_multivol
"""
        self.run_yaml(yaml)
        self.assertEqual(self.status, Process.SUCCEEDED)
        self.assertTrue(os.path.exists(os.path.join(self.output_dir, "case", "data_multivol.nii")))
        self.assertTrue(os.path.exists(os.path.join(self.output_dir, "case", "data_3d.nii")))
        self.assertFalse("data_3d" in self.ivm.data)
        self.assertFalse("data_4d" in self.ivm.data)
        
    def testSaveExtras(self):
        yaml = """
  - SaveExtras:
        my_extra: saved_file.mat
"""
        df = pd.DataFrame({'one': [1., 2., 3., 4.], 'two': [4., 3., 2., 1.]})
        self.ivm.add_extra("my_extra", DataFrameExtra("my_extra", df))
        self.run_yaml(yaml)
        self.assertEqual(self.status, Process.SUCCEEDED)
        self.assertTrue(os.path.exists(os.path.join(self.output_dir, "case", "saved_file.mat")))
        
