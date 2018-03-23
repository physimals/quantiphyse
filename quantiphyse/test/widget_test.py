import sys
import math
import unittest

import numpy as np
import scipy

from PySide import QtCore

from quantiphyse.volumes.volume_management import ImageVolumeManagement
from quantiphyse.gui.ViewOptions import ViewOptions
from quantiphyse.gui.ImageView import ImageView
from quantiphyse.utils.exceptions import QpException

TEST_SHAPE = [10, 10, 10]
TEST_NT = 20
MOTION_SCALE = 0.5

def _test_fn(x, y, z, t=None):
    f = math.exp(-(x**2 + 2*y**2 + 3*z**2))
    if t is not None:
        f *= 1-math.cos(t*2*math.pi)
    return f

class WidgetTest(unittest.TestCase):
    """
    Base class for a test module for a QP WidgetTest

    Note that it is necessary to physically show the widget during testing. This is ugly
    but enables checking of visible/invisible components.

    The philosophy of widget testing is 'white box', so we feel entitled to use our knowledge
    of the names given to widget components and other internal structure. This means tests
    are likely to go out of date very quickly if not maintained in line with the widgets
    themselves. However it is difficult to test GUI logic otherwise.

    Because of this it may be appropriate to move widget test classes into the widget packages
    themselves and make the whole test system internal (i.e. you can run 
    ``quantiphyse.exe --self-test``)
    """
    def setUp(self):
        self.qpe, self.error = False, False
        sys.excepthook = self.exc

        self.ivm = ImageVolumeManagement()
        self.opts = ViewOptions(None, self.ivm)
        self.ivl = ImageView(self.ivm, self.opts)

        wclass = self.widget_class()
        if wclass is not None:
            self.w = wclass(ivm=self.ivm, ivl=self.ivl, opts=self.opts)
            self.w.init_ui()
            self.w.activate()
            self.w.show()
        else:
            raise unittest.SkipTest("Plugin not found")

        self.create_test_data()
        
    def tearDown(self):
        if hasattr(self, "w"):
            self.w.hide()
            
    def processEvents(self):
        QtCore.QCoreApplication.instance().processEvents()

    def create_test_data(self):
        centre = [float(v)/2 for v in TEST_SHAPE]

        self.data_3d = np.zeros(TEST_SHAPE, dtype=np.float32)
        self.data_4d = np.zeros(TEST_SHAPE + [TEST_NT,], dtype=np.float32)
        self.data_4d_moving = np.zeros(TEST_SHAPE + [TEST_NT,], dtype=np.float32)
        self.mask = np.zeros(TEST_SHAPE, dtype=np.int)

        for x in range(TEST_SHAPE[0]):
            for y in range(TEST_SHAPE[1]):
                for z in range(TEST_SHAPE[2]):
                    nx = 2*float(x-centre[0])/TEST_SHAPE[0]
                    ny = 2*float(y-centre[1])/TEST_SHAPE[1]
                    nz = 2*float(z-centre[2])/TEST_SHAPE[2]
                    d = math.sqrt(nx**2 + ny**2 + nz**2)
                    self.data_3d[x,y,z] = _test_fn(nx, ny, nz)
                    self.mask[x, y, z] = int(d < 0.5)
                    for t in range(TEST_NT):
                        nt = float(t)/TEST_NT
                        self.data_4d[x, y, z, t] = _test_fn(nx, ny, nz, nt)
        
        for t in range(TEST_NT):
            tdata = self.data_4d[:,:,:,t]
            shift = np.random.normal(scale=MOTION_SCALE, size=3)
            odata = scipy.ndimage.interpolation.shift(tdata, shift)
            self.data_4d_moving[:,:,:,t] = odata

    def harmless_click(self, btn):
        """ Click a button and check that it produces no error"""
        if btn.isEnabled():
            btn.clicked.emit()
        self.assertFalse(self.error)

    def exc(self, exc_type, *_):
        """ Flag whether a user-exception or an error has been caught """
        self.qpe = issubclass(exc_type, QpException)
        self.error = not self.qpe
        
