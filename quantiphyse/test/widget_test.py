"""
Quantiphyse - Base class for widget self-test framework

Copyright (c) 2013-2018 University of Oxford
"""

import sys
import math
import unittest
import traceback

import numpy as np
import scipy

from PySide import QtCore

from quantiphyse.data import DataGrid, ImageVolumeManagement
from quantiphyse.gui import ViewOptions, ImageView
from quantiphyse.utils import QpException, get_plugins

class WidgetTest(unittest.TestCase):
    """
    Base class for a test module for a QP WidgetTest

    Note that it is necessary to physically show the widget during testing. This is ugly
    but enables checking of visible/invisible components.

    The philosophy of widget testing is 'white box', so we feel entitled to use our knowledge
    of the names given to widget components and other internal structure. This means tests
    are likely to go out of date very quickly if not maintained in line with the widgets
    themselves. However it is difficult to test GUI logic otherwise.

    Because of this, widget test classes should be stored in their respective packages and
    exposed to the test framework using the ``widget-tests`` key in ``QP_MANIFEST``. Tests are then
    run using ``quantiphyse --test-all``
    """
    def setUp(self):
        self.qpe, self.error = False, False
        sys.excepthook = self._exc

        self.ivm = ImageVolumeManagement()
        self.opts = ViewOptions(None, self.ivm)
        self.ivl = ImageView(self.ivm, self.opts)

        get_plugins()
        wclass = self.widget_class()
        if wclass is not None:
            self.w = wclass(ivm=self.ivm, ivl=self.ivl, opts=self.opts)
            self.w.init_ui()
            self.w.activate()
            self.w.show()
        else:
            raise unittest.SkipTest("Plugin not found")

        from . import create_test_data
        create_test_data(self)
        
    def tearDown(self):
        if hasattr(self, "w"):
            self.w.hide()
            
    def processEvents(self):
        """
        Process outstanding QT events, i.e. let handlers for widget
        events that we have triggered run

        This must be run every time a test triggers widget events
        in order for the test to detect the effects
        """
        QtCore.QCoreApplication.instance().processEvents()

    def harmless_click(self, btn):
        """ 
        Click a button and check that it produces no error
        """
        if btn.isEnabled():
            btn.clicked.emit()
        self.processEvents()
        self.assertFalse(self.error)

    def _exc(self, exc_type, value, tb):
        """ 
        Exception handler which simply flags whether a user-exception or an error has been caught 
        """
        self.qpe = issubclass(exc_type, QpException)
        self.error = not self.qpe
        if self.error or "--debug" in sys.argv:
            traceback.print_exception(exc_type, value, tb)
        
