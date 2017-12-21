import unittest
import os
import sys
import numpy as np
from PySide import QtGui

TEST_DIR = os.path.dirname(os.path.realpath(__file__))
qpdir = os.path.join(TEST_DIR, os.pardir, os.pardir)
sys.path.append(TEST_DIR)
sys.path.append(qpdir)

from quantiphyse.volumes.volume_management import ImageVolumeManagement
from quantiphyse.volumes.io import load
from quantiphyse.utils import set_local_file_path, set_debug
from quantiphyse.utils.exceptions import QpException

from quantiphyse.gui.ViewOptions import ViewOptions
from quantiphyse.gui.ImageView import ImageView

APP = None

class WidgetTest(unittest.TestCase):
    """
    Base class for a test module for a QP WidgetTest

    Note that it is necessary to physically show the widget during testing. This is ugly
    but enables checking of visible/invisible components
    """
    def setUp(self):
        global APP
        if APP is None:
            APP = QtGui.QApplication(sys.argv)
        self.app = APP

        set_local_file_path()
        set_debug("--debug" in sys.argv)
        self.qpe, self.error = False, False
        sys.excepthook = self.exc

        self.ivm = ImageVolumeManagement()
        self.opts = ViewOptions(None, self.ivm)
        self.ivl = ImageView(self.ivm, self.opts)

        self.datadir = os.path.join(TEST_DIR, os.pardir, "data_autogen")
        self.data_3d = load(os.path.join(self.datadir, "testdata_3d.nii.gz"))
        self.data_4d = load(os.path.join(self.datadir, "testdata_4d.nii.gz"))
        self.mask = load(os.path.join(self.datadir, "testdata_mask.nii.gz"))
        wclass = self.widget_class()
        if wclass is not None:
            self.w = wclass(ivm=self.ivm, ivl=self.ivl, opts=self.opts)
            self.w.init_ui()
            self.w.activate()
            self.w.show()
        else:
            raise unittest.SkipTest("Plugin not found")

    def harmless_click(self, btn):
        """ Click a button and check that it produces no error"""
        if btn.isEnabled():
            btn.clicked.emit()
        self.assertFalse(self.error)

    def exc(self, exc_type, exc, tb):
        """ Flag whether a user-exception or an error has been caught """
        self.qpe = issubclass(exc_type, QpException)
        self.error = not self.qpe
        
        