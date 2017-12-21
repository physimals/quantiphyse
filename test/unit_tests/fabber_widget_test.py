import os
import sys
import time
import unittest

from widget_test import WidgetTest

from quantiphyse.utils import get_plugins

class FabberWidgetTest(WidgetTest):

    def widget_class(self):
        widgets = get_plugins("widgets", "FabberWidget")
        if len(widgets) == 0:
            return None
        else:
            return widgets[0]

    def testNoData(self):
        """ User clicks the run button with no data"""
        if self.w.runBox.runBtn.isEnabled():
            self.w.runBox.runBtn.clicked.emit()
        self.assertFalse(self.error)

    @unittest.skipIf("--fast" in sys.argv,  "Slow test")
    def testJustClickRun(self):
        """ User loads some data and clicks the run button """
        self.ivm.add_data(self.data_4d, name="data_4d")
        self.ivm.add_roi(self.mask, name="mask")
        self.w.runBox.runBtn.clicked.emit()
        while not hasattr(self.w.runBox, "log"):
            self.app.processEvents()
            time.sleep(2)
        #print(self.w.runBox.log)
        self.assertTrue("mean_c0" in self.ivm.data)
        self.assertTrue("mean_c1" in self.ivm.data)
        self.assertTrue("mean_c2" in self.ivm.data)
        self.assertTrue("modelfit" in self.ivm.data)
        self.assertFalse(self.error)

if __name__ == '__main__':
    unittest.main()
