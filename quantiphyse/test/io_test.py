import os

from quantiphyse.processes import Process
from quantiphyse.test import ProcessTest

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
        
