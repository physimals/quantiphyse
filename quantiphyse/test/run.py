import unittest

from quantiphyse.utils import get_plugins

from .ivm_test import IVMTest
from .qpd_test import NumpyDataTest, NiftiDataTest
from .slice_plane_test import OrthoSliceTest
from .io_test import IoProcessTest

class_tests = [IVMTest, NumpyDataTest, NiftiDataTest, OrthoSliceTest, IoProcessTest,]

def run_tests(test_filter=None):
    """
    Run all unit tests defined by packages and plugins

    :param test_filter: Specifies name of test set to be run, None=run all
    """
    suite = unittest.TestSuite()

    for test in class_tests:
        if test_filter is None or test.__name__.lower().startswith(test_filter.lower()):
            suite.addTests(unittest.defaultTestLoader.loadTestsFromTestCase(test))

    tests = get_plugins("widget-tests")
    for test in tests:
        if test_filter is None or test.__name__.lower().startswith(test_filter.lower()):
            suite.addTests(unittest.defaultTestLoader.loadTestsFromTestCase(test))

    tests = get_plugins("process-tests")
    for test in tests:
        if test_filter is None or test.__name__.lower().startswith(test_filter.lower()):
            suite.addTests(unittest.defaultTestLoader.loadTestsFromTestCase(test))
   
    unittest.TextTestRunner(verbosity=2).run(suite)
