import os
import sys

from widget_test import WidgetTest

from quantiphyse.packages.core.t1 import T10Widget

TEST_VOLUME = "dce"
TEST_OVERLAY = "overlay"
TEST_ROI = "roi"
TEST_NX = 64
TEST_NY = 64
TEST_NZ = 42
TEST_NT = 106

class T10WidgetTest(WidgetTest):

    def widget_class(self):
        return T10Widget

    def testSmoothToggled(self):
        self.assertFalse(self.w.sigma.isEnabled())
        self.assertFalse(self.w.truncate.isEnabled())
        self.w.smooth.setChecked(True)
        self.app.processEvents()
        self.assertTrue(self.w.sigma.isEnabled())
        self.assertTrue(self.w.truncate.isEnabled())
        self.w.smooth.setChecked(False)
        self.app.processEvents()
        self.assertFalse(self.w.sigma.isEnabled())
        self.assertFalse(self.w.truncate.isEnabled())
        self.assertFalse(self.error)

    def testPreclinToggled(self):
        self.assertFalse(self.w.preclinGroup.isVisible())
        self.w.preclin.setChecked(True)
        self.app.processEvents()
        self.assertTrue(self.w.preclinGroup.isVisible())
        self.w.preclin.setChecked(False)
        self.app.processEvents()
        self.assertFalse(self.w.preclinGroup.isVisible())
        self.w.setVisible(False)
        self.assertFalse(self.error)

    def testClampToggled(self):
        self.assertFalse(self.w.clampMin.isEnabled())
        self.assertFalse(self.w.clampMin.isEnabled())
        self.w.clamp.setChecked(True)
        self.app.processEvents()
        self.assertTrue(self.w.clampMin.isEnabled())
        self.assertTrue(self.w.clampMin.isEnabled())
        self.w.clamp.setChecked(False)
        self.app.processEvents()
        self.assertFalse(self.w.clampMin.isEnabled())
        self.assertFalse(self.w.clampMin.isEnabled())
        self.assertFalse(self.error)

        # def testGenerateNoVolume(self):
   #     self.assertRaises(Exception, self.w.generate)

if __name__ == '__main__':
    unittest.main()
