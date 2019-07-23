import unittest
import re

import numpy as np

try:
    from PySide import QtGui, QtCore, QtGui as QtWidgets
except ImportError:
    from PySide2 import QtGui, QtCore, QtWidgets

from quantiphyse.data import DataGrid
from quantiphyse.test.widget_test import WidgetTest

from .widgets import DataStatistics, MultiVoxelAnalysis, VoxelAnalysis, MeasureWidget

class DataStatisticsTest(WidgetTest):

    def widget_class(self):
        return DataStatistics

    def testNoData(self):
        """ User clicks the show buttons with no data"""
        self.harmless_click(self.w.butgen)
        self.harmless_click(self.w.butgenss)

    def test3dData(self):
        self.ivm.add(self.data_3d, grid=self.grid, name="data_3d")
        self.w.data.value = ["data_3d",]
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
        self.ivm.add(self.data_3d, grid=self.grid, name="data_3d")
        self.ivm.add(self.data_4d, grid=self.grid, name="data_4d")
        # Select 'all data'
        self.w.data.value = ["data_3d", "data_4d"]
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
        self.ivm.add(self.data_3d, grid=self.grid, name="data_3d")
        self.w.data.value = ["data_3d",]
        self.harmless_click(self.w.butgen)
        self.harmless_click(self.w.copy_btn)
        cb = QtGui.QApplication.clipboard()
        rows = [row.split("\t") for row in cb.text().split("\n")]
        self.assertEquals(rows[0][0], "")
        self.assertEquals(rows[0][1].strip(), "data_3d")
        numbers = [float(row[1]) for row in rows[1:] if len(row) > 1]
        self.assertTrue(len(numbers) == 5)
        
    def testSliceStats(self):
        self.ivm.add(self.data_3d, grid=self.grid, name="data_3d")
        self.w.data.value = ["data_3d",]
        self.harmless_click(self.w.butgenss)
        self.ivl.set_focus([0, 0, 2, 0])
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
        self.ivl.set_focus([0, 4, 0, 0])
        self.processEvents()
        self.assertEquals(self.w.sscombo.currentText(), "Coronal")
        self.assertAlmostEquals(float(model.item(0, 0).text()), np.mean(self.data_3d[:,4,:]), delta=0.01)
        self.assertAlmostEquals(float(model.item(1, 0).text()), np.median(self.data_3d[:,4,:]), delta=0.01)
        self.assertAlmostEquals(float(model.item(2, 0).text()), np.std(self.data_3d[:,4,:]), delta=0.01)
        self.assertAlmostEquals(float(model.item(3, 0).text()), np.min(self.data_3d[:,4,:]), delta=0.01)
        self.assertAlmostEquals(float(model.item(4, 0).text()), np.max(self.data_3d[:,4,:]), delta=0.01)
        
        self.w.sscombo.setCurrentIndex(2) # Sagittal slice (R/L)
        self.ivl.set_focus([3, 0, 0, 0])
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
     
class MultiVoxelAnalysisTest(WidgetTest):

    def widget_class(self):
        return MultiVoxelAnalysis

    def testClick(self):
        self.ivm.add(self.data_4d, grid=self.grid, name="data_4d")
        pt = (2, 2, 2, 0)
        self.ivl._pick(0, pt)
        self.processEvents()
        sig = self.data_4d[2,2,2,:]
        self.assertTrue(pt in self.w.plots)
        plot = self.w.plots[pt]
        for v1, v2 in zip(sig, plot.yvalues):
            self.assertAlmostEquals(v1, v2)
        self.assertTrue(plot in self.w.plot.items)

    def testMultiClick(self):
        self.ivm.add(self.data_4d, grid=self.grid, name="data_4d")
        pt1 = (2, 2, 2, 0)
        sig1 = self.data_4d[2,2,2,:]
        self.ivl._pick(0, pt1)
        self.processEvents()
        pt2 = (3, 3, 3, 0)
        sig2 = self.data_4d[3,3,3,:]
        self.ivl._pick(0, pt2)
        self.processEvents()

        self.assertTrue(pt1 in self.w.plots)
        plot = self.w.plots[pt1]
        for v1, v2 in zip(sig1, plot.yvalues):
            self.assertAlmostEquals(v1, v2)
        self.assertTrue(plot in self.w.plot.items)

        self.assertTrue(pt2 in self.w.plots)
        plot = self.w.plots[pt2]
        for v1, v2 in zip(sig2, plot.yvalues):
            self.assertAlmostEquals(v1, v2)
        self.assertTrue(plot in self.w.plot.items)

    def testMultiClickChangeColor(self):
        self.ivm.add(self.data_4d, grid=self.grid, name="data_4d")
        self.w.options.option("col").value = "red"
        self.processEvents()

        pt1 = (2, 2, 2, 0)
        self.ivl._pick(0, pt1)
        self.processEvents()

        self.assertTrue(pt1 in self.w.plots)
        plot = self.w.plots[pt1]
        self.assertEquals(plot.line_col, self.w.colors['red'])

        self.w.options.option("col").value = "blue"
        self.processEvents()

        pt2 = (3, 3, 3, 0)
        self.ivl._pick(0, pt2)
        self.processEvents()

        self.assertTrue(pt2 in self.w.plots)
        plot = self.w.plots[pt2]
        self.assertEquals(plot.line_col, self.w.colors['blue'])

    def testShowMeanCurves(self):
        """
        Select two points, show mean curves=On.
        """
        self.ivm.add(self.data_4d, grid=self.grid, name="data_4d")
        self.w.options.option("col").value = "red"
        self.processEvents()
        self.w.options.option("mean").value = True
        self.processEvents()

        pt1 = (2, 2, 2, 0)
        self.ivl._pick(0, pt1)
        self.processEvents()

        self.assertTrue(pt1 in self.w.plots)
        plot = self.w.plots[pt1]

        pt2 = (3, 3, 3, 0)
        self.ivl._pick(0, pt2)
        self.processEvents()

        plot = self.w.mean_plots[self.w.colors["red"]]
        self.assertTrue(plot in self.w.plot.items)

        self.w.options.option("mean").value = False
        self.processEvents()
        self.assertEqual(len(plot.graphics_items), 0)

    def testShowIndividualCurves(self):
        self.ivm.add(self.data_4d, grid=self.grid, name="data_4d")
        self.w.options.option("indiv").value = False
        self.processEvents()

        pt1 = (2, 2, 2, 0)
        self.ivl._pick(0, pt1)
        self.processEvents()

        pt2 = (3, 3, 3, 0)
        self.ivl._pick(0, pt2)
        self.processEvents()

        self.assertTrue(pt1 in self.w.plots)
        plot = self.w.plots[pt1]
        self.assertEqual(len(plot.graphics_items), 0)

        self.assertTrue(pt2 in self.w.plots)
        plot = self.w.plots[pt2]
        self.assertEqual(len(plot.graphics_items), 0)

        self.w.options.option("indiv").value = True
        self.processEvents()

        plot = self.w.plots[pt1]
        self.assertTrue(plot in self.w.plot.items)

        plot = self.w.plots[pt2]
        self.assertTrue(plot in self.w.plot.items)

class VoxelAnalysisTest(WidgetTest):

    def widget_class(self):
        return VoxelAnalysis

    def test3dDataOnly(self):
        self.ivm.add(self.data_4d, grid=self.grid, name="data_3d")
        pt = (2, 2, 2, 0)
        self.ivl._pick(0, pt)
        self.processEvents()
        self.assertFalse(self.error)

class MeasureWidgetTest(WidgetTest):

    def widget_class(self):
        return MeasureWidget

    def testDistance1d(self):
        self.ivm.add(self.data_3d, grid=self.grid, name="data_3d")
        self.harmless_click(self.w._dist_btn)
        self.processEvents()
        self.ivl._pick(0, (2, 2, 2, 0))
        self.processEvents()
        self.ivl._pick(0, (2, 2, 3, 0))
        self.processEvents()
        self.assertFalse(self.error)

        regex = re.compile("distance.*\s+(\d+(\.\d+)?)\s*mm", re.IGNORECASE)
        m = re.match(regex, self.w._label.text())
        self.assertTrue(m is not None)
        self.assertAlmostEquals(float(m.groups()[0]), 1.0, delta=0.01)

    def testDistance2d(self):
        self.ivm.add(self.data_3d, grid=self.grid, name="data_3d")
        self.harmless_click(self.w._dist_btn)
        self.processEvents()
        self.ivl._pick(0, (2, 2, 2, 0))
        self.processEvents()
        self.ivl._pick(0, (2, 3, 3, 0))
        self.processEvents()
        self.assertFalse(self.error)

        regex = re.compile("distance.*\s+(\d+(\.\d+)?)\s*mm", re.IGNORECASE)
        m = re.match(regex, self.w._label.text())
        self.assertTrue(m is not None)
        self.assertAlmostEquals(float(m.groups()[0]), 1.41421, delta=0.01)

    def testDistance3d(self):
        self.ivm.add(self.data_3d, grid=self.grid, name="data_3d")
        self.harmless_click(self.w._dist_btn)
        self.processEvents()
        self.ivl._pick(0, (2, 2, 2, 0))
        self.processEvents()
        self.ivl._pick(0, (4, 3, 3, 0))
        self.processEvents()
        self.assertFalse(self.error)

        regex = re.compile("distance.*\s+(\d+(\.\d+)?)\s*mm", re.IGNORECASE)
        m = re.match(regex, self.w._label.text())
        self.assertTrue(m is not None)
        self.assertAlmostEquals(float(m.groups()[0]), 2.4495, delta=0.01)

    def testDistance3dNonSquiffy(self):
        """
        Distance with non-squiffy grid
        """
        affine = np.identity(4)
        affine[1, 1] = 2
        affine[2, 2] = 3
        grid = DataGrid(self.data_3d.shape, affine)

        self.ivm.add(self.data_3d, grid=grid, name="data_3d")
        self.harmless_click(self.w._dist_btn)
        self.processEvents()
        self.ivl._pick(0, (2, 2, 2, 0))
        self.processEvents()
        self.ivl._pick(0, (4, 3, 3, 0))
        self.processEvents()
        self.assertFalse(self.error)

        regex = re.compile("distance.*\s+(\d+(\.\d+)?)\s*mm", re.IGNORECASE)
        m = re.match(regex, self.w._label.text())
        self.assertTrue(m is not None)
        self.assertAlmostEquals(float(m.groups()[0]), 4.1231, delta=0.01)

    def testAngleStraight(self):
        self.ivm.add(self.data_3d, grid=self.grid, name="data_3d")
        self.harmless_click(self.w._angle_btn)
        self.processEvents()
        self.ivl._pick(0, (2, 2, 2, 0))
        self.processEvents()
        self.ivl._pick(0, (2, 2, 3, 0))
        self.processEvents()
        self.ivl._pick(0, (2, 2, 4, 0))
        self.processEvents()
        self.assertFalse(self.error)

        regex = re.compile("angle.*\s+(\d+(\.\d+)?).*", re.IGNORECASE)
        m = re.match(regex, self.w._label.text())
        self.assertTrue(m is not None)
        self.assertAlmostEquals(float(m.groups()[0]), 180, delta=0.01)

    def testAngleOrtho(self):
        self.ivm.add(self.data_3d, grid=self.grid, name="data_3d")
        self.harmless_click(self.w._angle_btn)
        self.processEvents()
        self.ivl._pick(0, (2, 2, 2, 0))
        self.processEvents()
        self.ivl._pick(0, (2, 2, 3, 0))
        self.processEvents()
        self.ivl._pick(0, (2, 3, 3, 0))
        self.processEvents()
        self.assertFalse(self.error)

        regex = re.compile("angle.*\s+(\d+(\.\d+)?).*", re.IGNORECASE)
        m = re.match(regex, self.w._label.text())
        self.assertTrue(m is not None)
        self.assertAlmostEquals(float(m.groups()[0]), 90, delta=0.01)

    def testAngle45(self):
        self.ivm.add(self.data_3d, grid=self.grid, name="data_3d")
        self.harmless_click(self.w._angle_btn)
        self.processEvents()
        self.ivl._pick(0, (2, 2, 2, 0))
        self.processEvents()
        self.ivl._pick(0, (2, 3, 3, 0))
        self.processEvents()
        self.ivl._pick(0, (2, 2, 3, 0))
        self.processEvents()
        self.assertFalse(self.error)

        regex = re.compile("angle.*\s+(\d+(\.\d+)?).*", re.IGNORECASE)
        m = re.match(regex, self.w._label.text())
        self.assertTrue(m is not None)
        self.assertAlmostEquals(float(m.groups()[0]), 45, delta=0.01)

    def testAngle45Squiffy(self):
        affine = np.identity(4)
        affine[1, 1] = 2
        affine[2, 2] = 3
        grid = DataGrid(self.data_3d.shape, affine)
        self.ivm.add(self.data_3d, grid=grid, name="data_3d")
        self.harmless_click(self.w._angle_btn)
        self.processEvents()
        self.ivl._pick(0, (2, 2, 2, 0))
        self.processEvents()
        self.ivl._pick(0, (4, 3, 2, 0))
        self.processEvents()
        self.ivl._pick(0, (2, 3, 2, 0))
        self.processEvents()
        self.assertFalse(self.error)

        regex = re.compile("angle.*\s+(\d+(\.\d+)?).*", re.IGNORECASE)
        m = re.match(regex, self.w._label.text())
        self.assertTrue(m is not None)
        self.assertAlmostEquals(float(m.groups()[0]), 45, delta=0.01)

    def testAngleOrthoSquifffy(self):
        affine = np.identity(4)
        affine[1, 1] = 2
        affine[2, 2] = 3
        grid = DataGrid(self.data_3d.shape, affine)

        self.ivm.add(self.data_3d, grid=grid, name="data_3d")
        self.harmless_click(self.w._angle_btn)
        self.processEvents()
        self.ivl._pick(0, (2, 2, 2, 0))
        self.processEvents()
        self.ivl._pick(0, (2, 2, 3, 0))
        self.processEvents()
        self.ivl._pick(0, (2, 3, 3, 0))
        self.processEvents()
        self.assertFalse(self.error)

        regex = re.compile("angle.*\s+(\d+(\.\d+)?).*", re.IGNORECASE)
        m = re.match(regex, self.w._label.text())
        self.assertTrue(m is not None)
        self.assertAlmostEquals(float(m.groups()[0]), 90, delta=0.01)

if __name__ == '__main__':
    unittest.main()
