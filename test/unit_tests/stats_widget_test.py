import os
import sys
import time

import numpy as np

from widget_test import WidgetTest

from quantiphyse.packages.core.analysis import DataStatistics

NUM_CLUSTERS = 4
NAME = "test_clusters"
NUM_PCA = 3

class DataStatisticsTest(WidgetTest):

    def widget_class(self):
        return DataStatistics

    def testNoData(self):
        """ User clicks the show buttons with no data"""
        self.harmless_click(self.w.butgen)
        self.harmless_click(self.w.butgenss)
        self.harmless_click(self.w.hist_show_btn)
        self.harmless_click(self.w.rp_btn)

    def test3dData(self):
        self.ivm.add_data(self.data_3d, name="data_3d")
        self.w.data_combo.setCurrentIndex(0)
        self.harmless_click(self.w.butgen)
        self.app.processEvents()
        self.assertTrue(self.w.stats_table.isVisible())
        self.assertEquals(self.w.stats_table.model().rowCount(), 5)
        self.assertEquals(self.w.stats_table.model().columnCount(), 1)

    def testAllData(self):
        self.ivm.add_data(self.data_3d, name="data_3d")
        self.ivm.add_data(self.data_4d, name="data_4d")
        # Select 'all data'
        self.w.data_combo.setCurrentIndex(2)
        self.harmless_click(self.w.butgen)
        self.app.processEvents()
        self.assertTrue(self.w.stats_table.isVisible())
        self.assertEquals(self.w.stats_table.model().rowCount(), 5)
        self.assertEquals(self.w.stats_table.model().columnCount(), 2)

if __name__ == '__main__':
    unittest.main()
