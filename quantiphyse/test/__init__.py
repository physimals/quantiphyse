import unittest

from quantiphyse.utils import get_plugins

def run_tests():

    suite = unittest.TestSuite()

    tests = get_plugins("widget-tests")
    for test in tests:
        suite.addTests(unittest.defaultTestLoader.loadTestsFromTestCase(test))
   
    unittest.TextTestRunner().run(suite)
