"""
Tests for Histogram Widget - empty at present

Copyright (c) 2013-2018 University of Oxford
"""
import unittest

from quantiphyse.test.widget_test import WidgetTest

from .widget import HistogramWidget

class HistogramWidgetTest(WidgetTest):

    def widget_class(self):
        return HistogramWidget

if __name__ == '__main__':
    unittest.main()
