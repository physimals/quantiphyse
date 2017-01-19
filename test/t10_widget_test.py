import unittest
import os
import sys
import numpy as np
from PySide import QtGui

TEST_DIR = os.path.dirname(os.path.realpath(__file__))
sys.path.append(os.path.dirname(TEST_DIR))
from pkview.volumes.volume_management import Volume, Overlay, Roi, ImageVolumeManagement
from pkview.widgets.T10Widgets import T10Widget

TEST_VOLUME = "dce"
TEST_OVERLAY = "overlay"
TEST_ROI = "roi"
TEST_NX = 64
TEST_NY = 64
TEST_NZ = 42
TEST_NT = 106

APP = None

class T10WidgetTest(unittest.TestCase):

    def __init__(self, *args, **kwargs):
        super(T10WidgetTest, self).__init__(*args, **kwargs)
        #self.app = QtGui.QApplication(sys.argv)

    def setUp(self):
        self.ivm = ImageVolumeManagement()
        self.w = T10Widget()
        self.w.add_image_management(self.ivm)

    def testSmoothToggled(self):
        self.assertFalse(self.w.sigma.isEnabled())
        self.assertFalse(self.w.truncate.isEnabled())
        self.w.smooth.setChecked(True)
        APP.processEvents()
        self.assertTrue(self.w.sigma.isEnabled())
        self.assertTrue(self.w.truncate.isEnabled())
        self.w.smooth.setChecked(False)
        APP.processEvents()
        self.assertFalse(self.w.sigma.isEnabled())
        self.assertFalse(self.w.truncate.isEnabled())

    def testPreclinToggled(self):
        # Have to make the widget visible to check if the preclin
        # box is hidden correctly!
        self.w.setVisible(True)
        self.assertFalse(self.w.preclinGroup.isVisible())
        self.w.preclin.setChecked(True)
        APP.processEvents()
        self.assertTrue(self.w.preclinGroup.isVisible())
        self.w.preclin.setChecked(False)
        APP.processEvents()
        self.assertFalse(self.w.preclinGroup.isVisible())
        self.w.setVisible(False)

    def testClampToggled(self):
        self.assertFalse(self.w.clampMin.isEnabled())
        self.assertFalse(self.w.clampMin.isEnabled())
        self.w.clamp.setChecked(True)
        APP.processEvents()
        self.assertTrue(self.w.clampMin.isEnabled())
        self.assertTrue(self.w.clampMin.isEnabled())
        self.w.clamp.setChecked(False)
        APP.processEvents()
        self.assertFalse(self.w.clampMin.isEnabled())
        self.assertFalse(self.w.clampMin.isEnabled())

        # def testGenerateNoVolume(self):
   #     self.assertRaises(Exception, self.w.generate)

if __name__ == '__main__':
    APP = QtGui.QApplication(sys.argv)
    unittest.main()
