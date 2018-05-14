"""
Quantiphyse - Self-test framework

Copyright (c) 2013-2018 University of Oxford
"""

import unittest

from quantiphyse.utils import get_plugins

def run_tests(test_filter=None):
    """
    Run all unit tests defined by packages and plugins

    :param test_filter: Specifies name of test set to be run, None=run all
    """
    suite = unittest.TestSuite()

    tests = get_plugins("widget-tests")
    for test in tests:
        if test_filter is None or test.__name__.lower().startswith(test_filter.lower()):
            suite.addTests(unittest.defaultTestLoader.loadTestsFromTestCase(test))
   
    unittest.TextTestRunner().run(suite)
