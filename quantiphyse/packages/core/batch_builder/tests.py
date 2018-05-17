import unittest
import time

import numpy as np

from quantiphyse.test.widget_test import WidgetTest

from .widget import BatchBuilderWidget

FABBER = """
  - Fabber:
      data: data_4d
      model: poly
      degree: 2
      method: vb
      noise: white
      save-mean:
      save-model-fit:
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
        self.ivm.add_data(self.data_3d, grid=self.grid, name="data_3d")
        self.processEvents()
        self.assertTrue(self.w.proc_edit.toPlainText() != "")

        self.w.run_box.runBtn.clicked.emit()
        self.processEvents()
        self.assertFalse(self.error)

    def testFabber(self):
        self.ivm.add_data(self.data_3d, grid=self.grid, name="data_4d")
        self.processEvents()
        yaml = self.w.proc_edit.toPlainText()
        add_str = "# Additional processing steps go here\n"
        add_idx = yaml.find(add_str)
        self.assertTrue(add_idx > 0)
        add_idx += len(add_str)
        pre = yaml[:add_idx]
        post = yaml[add_idx:]
        self.w.proc_edit.setPlainText(pre + FABBER + post)
        self.processEvents()
        
        self.w.run_box.runBtn.clicked.emit()
        while not self.error and not hasattr(self.w.run_box, "log"):
            self.processEvents()
            time.sleep(2)

        self.assertFalse(self.error)
        self.assertTrue("mean_c0" in self.ivm.data)
        self.assertTrue("mean_c1" in self.ivm.data)
        self.assertTrue("mean_c2" in self.ivm.data)
        self.assertTrue("modelfit" in self.ivm.data)

if __name__ == '__main__':
    unittest.main()
