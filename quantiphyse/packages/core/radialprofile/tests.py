"""
Tests for Radial profile widget - empty at present

Copyright (c) 2013-2018 University of Oxford
"""
import unittest

from quantiphyse.test.widget_test import WidgetTest

from .widget import RadialProfileWidget

class RadialProfileWidgetTest(WidgetTest):

    def widget_class(self):
        return RadialProfileWidget

if __name__ == '__main__':
    unittest.main()
