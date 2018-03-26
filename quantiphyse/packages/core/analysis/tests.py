import unittest

import numpy as np

from PySide import QtGui

from quantiphyse.test.widget_test import WidgetTest

from .widgets import DataStatistics

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
        self.assertTrue(self.w.stats_table.isVisible())
        model = self.w.stats_table.model()
        self.assertEquals(model.rowCount(), 5)
        self.assertEquals(model.columnCount(), 1)
        self.assertAlmostEquals(float(model.item(0, 0).text()), np.mean(self.data_3d), delta=0.01)
        self.assertAlmostEquals(float(model.item(1, 0).text()), np.median(self.data_3d), delta=0.01)
        self.assertAlmostEquals(float(model.item(2, 0).text()), np.std(self.data_3d), delta=0.01)
        self.assertAlmostEquals(float(model.item(3, 0).text()), np.min(self.data_3d), delta=0.01)
        self.assertAlmostEquals(float(model.item(4, 0).text()), np.max(self.data_3d), delta=0.01)
        
    def testAllData(self):
        self.ivm.add_data(self.data_3d, name="data_3d")
        self.ivm.add_data(self.data_4d, name="data_4d")
        # Select 'all data'
        self.w.data_combo.setCurrentIndex(2)
        self.harmless_click(self.w.butgen)
        self.assertTrue(self.w.stats_table.isVisible())
        self.assertEquals(self.w.stats_table.model().rowCount(), 5)
        self.assertEquals(self.w.stats_table.model().columnCount(), 2)

    def testShowHide(self):
        self.harmless_click(self.w.butgen)
        self.assertTrue(self.w.stats_table.isVisible())
        self.harmless_click(self.w.butgen)
        self.assertFalse(self.w.stats_table.isVisible())
     
    def testCopy(self):
        self.ivm.add_data(self.data_3d, name="data_3d")
        self.w.data_combo.setCurrentIndex(0)
        self.harmless_click(self.w.butgen)
        self.harmless_click(self.w.copy_btn)
        cb = QtGui.QApplication.clipboard()
        rows = [row.split("\t") for row in cb.text().split("\n")]
        self.assertEquals(rows[0][0], "")
        self.assertEquals(rows[0][1], "data_3d Region 1")
        numbers = [float(row[1]) for row in rows[1:] if len(row) > 1]
        self.assertTrue(len(numbers) == 5)
        
    def testSliceStats(self):
        self.ivm.add_data(self.data_3d, name="data_3d")
        self.w.data_combo.setCurrentIndex(0)
        self.harmless_click(self.w.butgenss)
        self.ivl.set_focus([0, 0, 2, 0], 0, True)
        model = self.w.stats_table_ss.model()
        self.assertEquals(model.rowCount(), 5)
        self.assertEquals(model.columnCount(), 1)

        self.w.sscombo.setCurrentIndex(0) # Axial slice (I/S)
        self.processEvents()
        self.assertEquals(self.w.sscombo.currentText(), "Axial")
        self.assertAlmostEquals(float(model.item(0, 0).text()), np.mean(self.data_3d[:,:,2]), delta=0.01)
        self.assertAlmostEquals(float(model.item(1, 0).text()), np.median(self.data_3d[:,:,2]), delta=0.01)
        self.assertAlmostEquals(float(model.item(2, 0).text()), np.std(self.data_3d[:,:,2]), delta=0.01)
        self.assertAlmostEquals(float(model.item(3, 0).text()), np.min(self.data_3d[:,:,2]), delta=0.01)
        self.assertAlmostEquals(float(model.item(4, 0).text()), np.max(self.data_3d[:,:,2]), delta=0.01)
          
        self.w.sscombo.setCurrentIndex(1) # Coronal slice (A/P)
        self.ivl.set_focus([0, 4, 0, 0], 0, True)
        self.processEvents()
        self.assertEquals(self.w.sscombo.currentText(), "Coronal")
        self.assertAlmostEquals(float(model.item(0, 0).text()), np.mean(self.data_3d[:,4,:]), delta=0.01)
        self.assertAlmostEquals(float(model.item(1, 0).text()), np.median(self.data_3d[:,4,:]), delta=0.01)
        self.assertAlmostEquals(float(model.item(2, 0).text()), np.std(self.data_3d[:,4,:]), delta=0.01)
        self.assertAlmostEquals(float(model.item(3, 0).text()), np.min(self.data_3d[:,4,:]), delta=0.01)
        self.assertAlmostEquals(float(model.item(4, 0).text()), np.max(self.data_3d[:,4,:]), delta=0.01)
        
        self.w.sscombo.setCurrentIndex(2) # Sagittal slice (R/L)
        self.ivl.set_focus([3, 0, 0, 0], 0, True)
        self.processEvents()
        self.assertEquals(self.w.sscombo.currentText(), "Sagittal")
        self.assertAlmostEquals(float(model.item(0, 0).text()), np.mean(self.data_3d[3,:,:]), delta=0.01)
        self.assertAlmostEquals(float(model.item(1, 0).text()), np.median(self.data_3d[3,:,:]), delta=0.01)
        self.assertAlmostEquals(float(model.item(2, 0).text()), np.std(self.data_3d[3,:,:]), delta=0.01)
        self.assertAlmostEquals(float(model.item(3, 0).text()), np.min(self.data_3d[3,:,:]), delta=0.01)
        self.assertAlmostEquals(float(model.item(4, 0).text()), np.max(self.data_3d[3,:,:]), delta=0.01)
      
    def testSliceShowHide(self):
        self.harmless_click(self.w.butgenss)
        self.assertTrue(self.w.stats_table_ss.isVisible())
        self.harmless_click(self.w.butgenss)
        self.assertFalse(self.w.stats_table_ss.isVisible())
     
    def testHistogramShowHide(self):
        self.harmless_click(self.w.hist_show_btn)
        self.assertTrue(self.w.win1.isVisible())
        self.assertTrue(self.w.regenBtn.isVisible())
        self.assertEquals(self.w.hist_show_btn.text(), "Hide")
        self.harmless_click(self.w.hist_show_btn)
        self.assertFalse(self.w.win1.isVisible())
        self.assertFalse(self.w.regenBtn.isVisible())
        self.assertEquals(self.w.hist_show_btn.text(), "Show")
     
    def testRadialProfileShowHide(self):
        self.harmless_click(self.w.rp_btn)
        self.assertTrue(self.w.rp_win.isVisible())
        self.assertEquals(self.w.rp_btn.text(), "Hide")
        self.harmless_click(self.w.rp_btn)
        self.assertFalse(self.w.rp_win.isVisible())
        self.assertFalse(self.w.regenBtn.isVisible())
     
if __name__ == '__main__':
    unittest.main()
