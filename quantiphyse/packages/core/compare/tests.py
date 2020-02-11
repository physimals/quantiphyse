import unittest

import numpy as np

from quantiphyse.test.widget_test import WidgetTest

from .widget import CompareDataWidget

SAMPLE_SIZE=2314

class CompareDataWidgetTest(WidgetTest):

    def widget_class(self):
        return CompareDataWidget

    def testNoData(self):
        """ Run button disabled with no data"""
        self.assertFalse(self.w.run_btn.isEnabled())
        self.assertEqual(len(self.w.plot.listDataItems()), 0)

    def test3dDataVsItself(self):
        self.ivm.add(self.data_3d, grid=self.grid, name="data_3d")
        self.w.d1_combo.setCurrentIndex(0)
        self.w.d2_combo.setCurrentIndex(0)
        self.processEvents()
        self.assertTrue(self.w.run_btn.isEnabled())

        self.w.run_btn.clicked.emit()
        self.assertFalse(self.error)

        self.assertEqual(len(self.w.plot.listDataItems()), 1)

        # Data all matches
        self.assertTrue(np.all(self.w.d1 == self.w.d2))

    def test4dDataVsItself(self):
        self.ivm.add(self.data_4d, grid=self.grid, name="data_4d")
        self.w.d1_combo.setCurrentIndex(0)
        self.w.d2_combo.setCurrentIndex(0)
        self.processEvents()
        self.assertTrue(self.w.run_btn.isEnabled())

        self.w.run_btn.clicked.emit()
        self.assertFalse(self.error)

        self.assertEqual(len(self.w.plot.listDataItems()), 1)

        # Data all matches
        self.assertTrue(np.all(self.w.d1 == self.w.d2))

    def test3dVs4d(self):
        self.ivm.add(self.data_4d, grid=self.grid, name="data_4d")
        self.ivm.add(self.data_3d, grid=self.grid, name="data_3d")
        self.w.d1_combo.setCurrentIndex(0)
        self.w.d2_combo.setCurrentIndex(1)
        self.processEvents()
        self.assertTrue(self.w.run_btn.isEnabled())

        self.w.run_btn.clicked.emit()
        self.assertFalse(self.error)

        self.assertEqual(len(self.w.plot.listDataItems()), 1)

        # Data does not all match
        self.assertTrue(np.any(self.w.d1 != self.w.d2))

    def testCurrentVolume(self):
        data_4d = np.ones(list(self.grid.shape) + [2,])
        data_4d[..., 1] = 2

        data_3d = np.ones(self.grid.shape)
        data_3d[...] = 3

        self.ivm.add(data_3d, grid=self.grid, name="data_3d")
        self.ivm.add(data_4d, grid=self.grid, name="data_4d")
        self.processEvents()

        focus = self.ivl.focus()
        focus[3] = 1
        self.ivl.set_focus(list(focus))
        self.processEvents()

        self.w.d1_combo.setCurrentIndex(self.w.d1_combo.findText("data_3d"))
        self.w.d2_combo.setCurrentIndex(self.w.d2_combo.findText("data_4d"))
        self.processEvents()
        self.assertTrue(self.w.run_btn.isEnabled())

        self.w.run_btn.clicked.emit()
        self.assertFalse(self.error)

        self.assertEqual(len(self.w.plot.listDataItems()), 1)

        # Data is all from volume 2 for 4d dataset
        self.assertTrue(np.all(self.w.d1 == 3))
        self.assertTrue(np.all(self.w.d2 == 2))

    def testSampleSize(self):
        self.ivm.add(self.data_3d, grid=self.grid, name="data_3d")
        self.w.d1_combo.setCurrentIndex(0)
        self.w.d2_combo.setCurrentIndex(0)
        self.processEvents()

        self.w.sample_spin.setValue(SAMPLE_SIZE)
        self.processEvents()
        self.assertTrue(self.w.run_btn.isEnabled())

        self.w.run_btn.clicked.emit()
        self.assertFalse(self.error)

        self.assertEqual(len(self.w.plot.listDataItems()), 1)

        # Data all matches
        self.assertEqual(len(self.w.d1), SAMPLE_SIZE)
        self.assertEqual(len(self.w.d2), SAMPLE_SIZE)
        self.assertTrue(np.all(self.w.d1 == self.w.d2))

    def testSampleSizeOff(self):
        self.ivm.add(self.data_3d, grid=self.grid, name="data_3d")
        self.w.d1_combo.setCurrentIndex(0)
        self.w.d2_combo.setCurrentIndex(0)
        self.processEvents()

        self.w.sample_spin.setValue(SAMPLE_SIZE)
        self.w.sample_cb.setChecked(False)
        self.processEvents()
        self.assertTrue(self.w.run_btn.isEnabled())

        self.w.run_btn.clicked.emit()
        self.assertFalse(self.error)

        self.assertEqual(len(self.w.plot.listDataItems()), 1)

        # Data all matches
        self.assertEqual(len(self.w.d1), self.data_3d.size)
        self.assertEqual(len(self.w.d2), self.data_3d.size)
        self.assertTrue(np.all(self.w.d1 == self.w.d2))

    def testWithinRoi(self):
        data_3d = np.ones(self.grid.shape)
        roi = np.random.choice(a=[False, True], size=self.grid.shape)
        data_3d[roi] = 3
        self.ivm.add(data_3d, grid=self.grid, name="data_3d")
        self.ivm.add(roi, grid=self.grid, roi=True, name="roi")
        self.processEvents()

        self.w.d1_combo.setCurrentIndex(0)
        self.w.d2_combo.setCurrentIndex(0)
        self.w.roi_combo.setCurrentIndex(self.w.roi_combo.findText("roi"))
        self.processEvents()
        self.assertTrue(self.w.run_btn.isEnabled())

        self.w.run_btn.clicked.emit()
        self.assertFalse(self.error)

        self.assertEqual(len(self.w.plot.listDataItems()), 1)

        # Data is all from volume 2 for 4d dataset
        self.assertTrue(np.all(self.w.d1 == 3))
        self.assertTrue(np.all(self.w.d2 == 3))

    def testIdLine(self):
        self.ivm.add(self.data_3d, grid=self.grid, name="data_3d")
        self.w.d1_combo.setCurrentIndex(0)
        self.w.d2_combo.setCurrentIndex(0)
        self.processEvents()

        self.w.id_cb.setChecked(True)
        self.processEvents()
        self.assertTrue(self.w.run_btn.isEnabled())

        self.w.run_btn.clicked.emit()
        self.assertFalse(self.error)

        self.assertEqual(len(self.w.plot.listDataItems()), 2)

if __name__ == '__main__':
    unittest.main()
