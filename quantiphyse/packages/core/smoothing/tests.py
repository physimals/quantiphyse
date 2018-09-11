"""
Quantiphyse - Tests for supervoxel clustering widget

Copyright (c) 2013-2018 University of Oxford
"""
import unittest 

import numpy as np

from quantiphyse.test.widget_test import WidgetTest

from .widget import SmoothingWidget

NAME = "test_smooth"
SIGMA = 0.5

class SmoothingWidgetTests(WidgetTest):

    def widget_class(self):
        return SmoothingWidget

    def testNoData(self):
        """ User clicks the generate buttons with no data"""
        self.harmless_click(self.w.run_btn)

    def testNoSmoothing(self):
        """ Check that data is unchanged if sigma = 0 """
        self.ivm.add(self.data_3d, grid=self.grid, name="data_3d")
        self.w.data_combo.setCurrentIndex(0)
        self.processEvents()

        self.w.sigma.spin.setValue(0)
        self.w.output_name.setText(NAME)

        self.harmless_click(self.w.run_btn)
        self.processEvents()

        self.assertTrue(NAME in self.ivm.data)
        self.assertEquals(self.ivm.current_data.name, NAME)
        self.assertFalse(self.error)

        d = self.ivm.data[NAME].raw()
        self.assertTrue(np.all(d == self.data_3d))

    def test3dData(self):
        self.ivm.add(self.data_3d, grid=self.grid, name="data_3d")
        self.w.data_combo.setCurrentIndex(0)
        self.processEvents()

        self.w.sigma.spin.setValue(SIGMA)
        self.w.output_name.setText(NAME)

        self.harmless_click(self.w.run_btn)
        self.processEvents()

        self.assertTrue(NAME in self.ivm.data)
        self.assertEquals(self.ivm.current_data.name, NAME)
        self.assertFalse(self.error)

        d = self.ivm.data[NAME].raw()
        self.assertFalse(np.all(d == self.data_3d))

    def test4dData(self):
        self.ivm.add(self.data_4d, grid=self.grid, name="data_4d")
        self.w.data_combo.setCurrentIndex(0)
        self.processEvents()

        self.w.sigma.spin.setValue(SIGMA)
        self.w.output_name.setText(NAME)

        self.harmless_click(self.w.run_btn)
        self.processEvents()

        self.assertTrue(NAME in self.ivm.data)
        self.assertEquals(self.ivm.current_data.name, NAME)
        self.assertEquals(self.ivm.data[NAME].nvols, self.data_4d.shape[3])
        self.assertFalse(self.error)

        d = self.ivm.data[NAME].raw()
        self.assertFalse(np.all(d == self.data_4d))

if __name__ == '__main__':
    unittest.main()
