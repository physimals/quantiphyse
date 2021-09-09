"""
Main program entry point for Quantiphyse

Copyright (c) 2013-2020 University of Oxford

Licensed under the Apache License, Version 2.0 (the "License");
you may not use this file except in compliance with the License.
You may obtain a copy of the License at

    http://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and
limitations under the License.
"""
import sys
import warnings
if "--debug" not in sys.argv:
    # Avoid ugly warnings from some third party packages unless we are debugging
    warnings.simplefilter("ignore")

import argparse
import multiprocessing
import signal
import traceback
import logging

from PySide2 import QtGui, QtCore, QtWidgets

from quantiphyse.test import run_tests

from quantiphyse.utils import QpException, set_local_file_path
from quantiphyse.utils.batch import BatchScript
from quantiphyse.utils.logger import set_base_log_level
from quantiphyse.utils.local import get_icon

from quantiphyse.gui import register
from quantiphyse.gui.main_window import MainWindow
from quantiphyse.gui.dialogs import error_dialog, set_main_window

# Required to use resources in theme. Check if 2 or 3.
if sys.version_info[0] > 2:
    from .resources import resource_py3
else:
    from .resources import resource_py2

def my_catch_exceptions(exc_type, exc, tb):
    """
    Catch exceptions and format appropriately

    QpException can occur due to bad user input so scary tracebacks are not included.
    Other exception types are bugs so give full traceback
    """
    if issubclass(exc_type, QpException):
        detail = exc.detail
    else:
        detail = traceback.format_exception(exc_type, exc, tb)
    error_dialog(str(exc), title="Error", detail=detail)

def main():
    """
    Parse any input arguments and run the application
    """

    # Enable multiprocessing on windows frozen binaries. Does nothing on other systems
    multiprocessing.freeze_support()

    # Parse input arguments to pass info to GUI
    parser = argparse.ArgumentParser()
    parser.add_argument('data', help='Load data files', nargs="*", type=str)
    parser.add_argument('--batch', help='Run batch file', default=None, type=str)
    parser.add_argument('--debug', help='Activate debug mode', action="store_true")
    parser.add_argument('--test-all', help='Run all tests', action="store_true")
    parser.add_argument('--test', help='Specify test suite to be run (default=run all)', default=None)
    parser.add_argument('--test-fast', help='Run only fast tests', action="store_true")
    parser.add_argument('--qv', help='Activate quick-view mode', action="store_true")
    parser.add_argument('--register', help='Force display of registration dialog', action="store_true")
    args = parser.parse_args()

    # Apply global options
    if args.debug:
        set_base_log_level(logging.DEBUG)
    else:
        set_base_log_level(logging.WARN)

    # Set the local file path, used for finding icons, plugins, etc
    set_local_file_path()

    # Handle CTRL-C correctly
    signal.signal(signal.SIGINT, signal.SIG_DFL)

    if args.batch is not None:
        # Batch runs need a QCoreApplication to avoid initializing the GUI - this
        # would fail when running on a displayless system 
        app = QtCore.QCoreApplication(sys.argv)
        runner = BatchScript()
        # Add delay to make sure script is run after the main loop starts, in case
        # batch script is completely synchronous
        QtCore.QTimer.singleShot(200, lambda: runner.execute({"yaml-file" : args.batch}))
        sys.exit(app.exec_())
    else:
        # Otherwise we need a QApplication and to initialize the GUI
        # Note that organization info is not up to date but we will 
        # leave IBME in there as otherwise any previous QSettings (including
        # registration) will be lost.
        app = QtWidgets.QApplication(sys.argv)
        app.setStyle('plastique')
        QtCore.QCoreApplication.setOrganizationName("ibme-qubic")
        QtCore.QCoreApplication.setOrganizationDomain("eng.ox.ac.uk")
        QtCore.QCoreApplication.setApplicationName("Quantiphyse")
        QtWidgets.QApplication.setWindowIcon(QtGui.QIcon(get_icon("main_icon.png")))

        if args.debug:
            import pyqtgraph as pg
            pg.systemInfo()

        if args.test_all or args.test:
            # Run tests
            run_tests(args.test)
            sys.exit(0)
        else:
            # Create window and start main loop
            pixmap = QtGui.QPixmap(get_icon("quantiphyse_splash.png"))
            splash = QtWidgets.QSplashScreen(pixmap)
            splash.show()
            app.processEvents()

            win = MainWindow(load_data=args.data, widgets=not args.qv)
            splash.finish(win)
            sys.excepthook = my_catch_exceptions
            set_main_window(win)
            if args.register:
                register.set_license_accepted(0)
            register.check_register()
            sys.exit(app.exec_())
