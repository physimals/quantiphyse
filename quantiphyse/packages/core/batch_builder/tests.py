import unittest
import time

import numpy as np

from quantiphyse.processes import Process
from quantiphyse.test.widget_test import WidgetTest

from .widget import BatchBuilderWidget

SV = """
  - Supervoxels:
      data: data_4d
      roi: mask
      n-supervoxels: 4
      output-name: sv
"""
class BatchBuilderWidgetTest(WidgetTest):

    def widget_class(self):
        return BatchBuilderWidget

    def testNoData(self):
        self.assertTrue(self.w.proc_edit.toPlainText() == "")
        if self.w.run_box.runBtn.isEnabled():
            self.w.run_box.runBtn.clicked.emit()
        self.processEvents()
        self.assertFalse(self.error)

    def testDataLoaded(self):
        self.ivm.add(self.data_3d, grid=self.grid, name="data_3d")
        self.processEvents()
        self.assertTrue(self.w.proc_edit.toPlainText() != "")

        self.w.run_box.runBtn.clicked.emit()
        self.processEvents()
        self.assertFalse(self.error)

    def testAddProcess(self):
        self.ivm.add(self.data_3d, grid=self.grid, name="data_4d")
        self.ivm.add(self.mask, grid=self.grid, name="mask")
        self.processEvents()
        yaml = self.w.proc_edit.toPlainText()
        add_str = "# Additional processing steps go here\n"
        add_idx = yaml.find(add_str)
        self.assertTrue(add_idx > 0)
        add_idx += len(add_str)
        pre = yaml[:add_idx]
        post = yaml[add_idx:]
        self.w.proc_edit.setPlainText(pre + SV + post)
        self.processEvents()
        
        self.w.run_box.runBtn.clicked.emit()
        while not self.error and not hasattr(self.w.run_box, "log"):
            self.processEvents()
            time.sleep(2)
            
        self.assertEqual(self.w.process.status, Process.SUCCEEDED)
        self.assertFalse(self.error)
        self.assertTrue("sv" in self.ivm.rois)

if __name__ == '__main__':
    unittest.main()
