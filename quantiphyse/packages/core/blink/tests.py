import unittest

from quantiphyse.test.widget_test import WidgetTest

from .widget import BlinkWidget

class BlinkWidgetTest(WidgetTest):

    def widget_class(self):
        return BlinkWidget

    def testDefaults(self):
        self.assertFalse(self.w.running)
        self.assertEqual(self.w.visible_view, 0)
        self.assertEqual(self.w.button.text(), "Toggle")
        self.assertEqual(self.w.options.option("mode").value, "Manual")

    def testManualToggle(self):
        self.ivm.add(self.data_3d, grid=self.grid, name="data1")
        self.ivm.add(self.data_3d, grid=self.grid, name="data2")
        self.w.options.option("data1").value = "data1"
        self.w.options.option("data2").value = "data2"
        self.processEvents()
        self.w.button.clicked.emit()
        self.processEvents()
        self.assertEqual(self.w.ivm.current_data.name, "data2")
        self.w.button.clicked.emit()
        self.processEvents()
        self.assertEqual(self.w.ivm.current_data.name, "data1")
        self.w.button.clicked.emit()
        self.processEvents()
        self.assertEqual(self.w.ivm.current_data.name, "data2")

if __name__ == '__main__':
    unittest.main()
