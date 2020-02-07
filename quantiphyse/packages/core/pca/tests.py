import unittest

import numpy as np

from quantiphyse.test.widget_test import WidgetTest

from .widget import PcaWidget

NUM_PCA = 5
NAME = "pca"

class PcaWidgetTest(WidgetTest):

    def widget_class(self):
        return PcaWidget

    def testNoData(self):
        if self.w._run.runBtn.isEnabled():
            self.w._run.runBtn.clicked.emit()
        self.assertFalse(self.error)

    def test3dData(self):
        """ 4D data required """
        self.ivm.add(self.data_3d, grid=self.grid, name="data_3d") 
        self.assertFalse(bool(self.w._options.option("data").value))
        
    def test4dData(self):
        """ 4d clustering """
        self.ivm.add(self.data_4d, grid=self.grid, name="data_4d")
        self.processEvents()            
        self.w._options.option("data").value = "data_4d"
        self.processEvents()            
        self.assertTrue(self.w._run.runBtn.isEnabled())
        self.assertEquals(self.w._options.option("output-name").value, "data_4d_pca")
        
        self.w._options.option("n-components").value = NUM_PCA
        self.w._options.option("output-name").value = NAME
        self.w._run.runBtn.clicked.emit()
        self.processEvents()
        
        for mode in range(NUM_PCA):
            self.assertTrue("%s%i" % (NAME, mode) in self.ivm.data)
        self.assertFalse("%s%i" % (NAME, NUM_PCA+1) in self.ivm.data)

        self.assertEquals(self.ivm.current_data.name, "%s0" % NAME)
        self.assertFalse(self.error)
        
    def test4dDataWithRoi(self):
        """ 4d clustering within an ROI"""
        self.ivm.add(self.data_4d, grid=self.grid, name="data_4d")
        self.ivm.add(self.mask, grid=self.grid, roi=True, name="mask")
        self.w._options.option("data").value = "data_4d"
        self.w._options.option("roi").value = "mask"
        
        self.assertTrue(self.w._run.runBtn.isEnabled())
        self.assertEquals(self.w._options.option("output-name").value, "data_4d_pca")
        
        self.w._options.option("n-components").value = NUM_PCA
        self.w._options.option("output-name").value = NAME
        self.w._run.runBtn.clicked.emit()
        self.processEvents()
        
        for mode in range(NUM_PCA):
            name = "%s%i" % (NAME, mode)
            self.assertTrue(name in self.ivm.data)
            # Data value is always zero outside the ROI
            data = self.ivm.data[name].raw()
            self.assertTrue(np.all(data[self.mask == 0] == 0))
            self.assertFalse(self.error)

        self.assertFalse("%s%i" % (NAME, NUM_PCA+1) in self.ivm.data)
        self.assertEquals(self.ivm.current_data.name, "%s0" % NAME)
        self.assertFalse(self.error)
        
if __name__ == '__main__':
    unittest.main()
