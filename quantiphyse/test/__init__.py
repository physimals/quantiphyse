"""
Quantiphyse - Self-test framework

Copyright (c) 2013-2018 University of Oxford
"""

import unittest

from quantiphyse.utils import get_plugins

def run_tests():
    """
    Run all unit tests defined by packages and plugins
    """
    suite = unittest.TestSuite()

    tests = get_plugins("widget-tests")
    for test in tests:
        suite.addTests(unittest.defaultTestLoader.loadTestsFromTestCase(test))
   
    unittest.TextTestRunner().run(suite)
