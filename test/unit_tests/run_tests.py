import unittest

import volume_management_test
import t10_widget_test

if __name__ == '__main__':

    suite = unittest.TestSuite()
    suite.addTests(unittest.defaultTestLoader.loadTestsFromModule(volume_management_test))
    suite.addTests(unittest.defaultTestLoader.loadTestsFromModule(t10_widget_test))

    unittest.TextTestRunner().run(suite)
