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
        if self.w.run_btn.isEnabled():
            self.w.run_btn.clicked.emit()
        self.assertFalse(self.error)

    def test3dData(self):
        """ 4D data required but error should be produced to inform user of reason """
        self.ivm.add(self.data_3d, grid=self.grid, name="data_3d")
        self.w.data_combo.setCurrentIndex(0)
        self.processEvents()            
        self.assertTrue(self.w.run_btn.isEnabled())
        self.assertEquals(self.w.output_name.text(), "data_3d_pca")
        
        self.w.n_comp.spin.setValue(NUM_PCA)
        self.w.output_name.setText(NAME)
        self.w.run_btn.clicked.emit()
        self.processEvents()
        
        self.assertFalse(self.error)
        self.assertTrue(self.qpe)
        
    def test4dData(self):
        """ 4d clustering """
        self.ivm.add(self.data_4d, grid=self.grid, name="data_4d")
        self.w.data_combo.setCurrentIndex(0)
        self.processEvents()            
        self.assertTrue(self.w.run_btn.isEnabled())
        self.assertEquals(self.w.output_name.text(), "data_4d_pca")
        
        self.w.n_comp.spin.setValue(NUM_PCA)
        self.w.output_name.setText(NAME)
        self.w.run_btn.clicked.emit()
        self.processEvents()
        
        for mode in range(NUM_PCA):
            self.assertTrue("%s%i" % (NAME, mode) in self.ivm.data)
        self.assertFalse("%s%i" % (NAME, NUM_PCA+1) in self.ivm.data)

        self.assertEquals(self.ivm.current_data.name, "%s0" % NAME)
        self.assertFalse(self.error)
        
    def test4dDataWithRoi(self):
        """ 4d clustering within an ROI"""
        self.ivm.add(self.data_4d, grid=self.grid, name="data_4d")
        self.ivm.add(self.mask, grid=self.grid, name="mask")
        self.w.data_combo.setCurrentIndex(0)
        self.w.roi_combo.setCurrentIndex(1)

        self.assertTrue(self.w.run_btn.isEnabled())
        self.assertEquals(self.w.output_name.text(), "data_4d_pca")
        
        self.w.n_comp.spin.setValue(NUM_PCA)
        self.w.output_name.setText(NAME)
        self.w.run_btn.clicked.emit()
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
