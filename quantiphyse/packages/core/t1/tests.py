import unittest 

from quantiphyse.test.widget_test import WidgetTest

from .widgets import T10Widget

class T10WidgetTest(WidgetTest):

    def widget_class(self):
        return T10Widget

    def testSmoothToggled(self):
        self.assertFalse(self.w.sigma.isEnabled())
        self.assertFalse(self.w.truncate.isEnabled())
        self.w.smooth.setChecked(True)
        self.processEvents()
        self.assertTrue(self.w.sigma.isEnabled())
        self.assertTrue(self.w.truncate.isEnabled())
        self.w.smooth.setChecked(False)
        self.processEvents()
        self.assertFalse(self.w.sigma.isEnabled())
        self.assertFalse(self.w.truncate.isEnabled())
        self.assertFalse(self.error)

    def testPreclinToggled(self):
        self.assertFalse(self.w.preclinGroup.isVisible())
        self.w.preclin.setChecked(True)
        self.processEvents()
        self.assertTrue(self.w.preclinGroup.isVisible())
        self.w.preclin.setChecked(False)
        self.processEvents()
        self.assertFalse(self.w.preclinGroup.isVisible())
        self.w.setVisible(False)
        self.assertFalse(self.error)

    def testClampToggled(self):
        self.assertFalse(self.w.clampMin.isEnabled())
        self.assertFalse(self.w.clampMin.isEnabled())
        self.w.clamp.setChecked(True)
        self.processEvents()
        self.assertTrue(self.w.clampMin.isEnabled())
        self.assertTrue(self.w.clampMin.isEnabled())
        self.w.clamp.setChecked(False)
        self.processEvents()
        self.assertFalse(self.w.clampMin.isEnabled())
        self.assertFalse(self.w.clampMin.isEnabled())
        self.assertFalse(self.error)

        # def testGenerateNoVolume(self):
   #     self.assertRaises(Exception, self.w.generate)

if __name__ == '__main__':
    unittest.main()
