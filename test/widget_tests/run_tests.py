import sys, os
import unittest

TEST_DIR = os.path.dirname(os.path.realpath(__file__))
qpdir = os.path.join(TEST_DIR, os.pardir, os.pardir)
sys.path.append(TEST_DIR)
sys.path.append(qpdir)

from quantiphyse.utils import set_debug

#import volume_management_test
#import t10_widget_test
#import fabber_widget_test
#import clustering_widget_test
#import stats_widget_test
#import sv_widget_test
import slice_plane_test

if __name__ == '__main__':
    set_debug("--debug" in sys.argv)

    suite = unittest.TestSuite()
    suite.addTests(unittest.defaultTestLoader.loadTestsFromModule(slice_plane_test))
    #suite.addTests(unittest.defaultTestLoader.loadTestsFromModule(volume_management_test))
    #suite.addTests(unittest.defaultTestLoader.loadTestsFromModule(t10_widget_test))
    #suite.addTests(unittest.defaultTestLoader.loadTestsFromModule(fabber_widget_test))
    #suite.addTests(unittest.defaultTestLoader.loadTestsFromModule(clustering_widget_test))
    #suite.addTests(unittest.defaultTestLoader.loadTestsFromModule(stats_widget_test))
    #suite.addTests(unittest.defaultTestLoader.loadTestsFromModule(sv_widget_test))

    unittest.TextTestRunner().run(suite)
