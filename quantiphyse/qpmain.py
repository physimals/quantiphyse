"""
Main program entry point for Quantiphyse

Copyright (c) 2013-2018 University of Oxford
"""
import os
import sys
import argparse
import multiprocessing
import signal
import traceback

from PySide import QtCore, QtGui
import pyqtgraph as pg

from .utils.batch import run_batch
from .utils.exceptions import QpException
from .utils import debug, warn, set_local_file_path, set_debug
from .gui.MainWindow import MainWindow
from .gui.QuickWindow import QuickWindow
from .gui.dialogs import error_dialog, set_main_window

# Required to use resources in theme. Check if 2 or 3.
if sys.version_info[0] > 2:
    from .resources import resource_py3
else:
    from .resources import resource_py2

def my_catch_exceptions(exc_type, exc, tb):
    if issubclass(exc_type, QpException):
        detail = exc.detail
    else:
        detail = traceback.format_exception(exc_type, exc, tb)
    error_dialog(str(exc), title="Error", detail=detail)
        
def main():
    """
    Parse any input arguments and run the application
    """
    
    # Enable multiprocessing on windows frozen binaries
    # Does nothing on other systems
    multiprocessing.freeze_support()

    # Parse input arguments to pass info to GUI
    parser = argparse.ArgumentParser()
    parser.add_argument('--data', help='Load data file', default=None, type=str)
    parser.add_argument('--roi', help='Load ROI file', default=None, type=str)
    parser.add_argument('--batch', help='Run batch file', default=None, type=str)
    parser.add_argument('--debug', help='Activate debug mode', action="store_true")
    parser.add_argument('--qv', help='Activate quick-view mode', action="store_true")
    args = parser.parse_args()

    set_debug(args.debug)
    if args.debug: pg.systemInfo()

    # Set the local file path, used for finding icons, plugins, etc
    set_local_file_path()

    # Check whether any batch processing arguments have been called
    if (args.batch is not None):
        #app = QtCore.QCoreApplication(sys.argv)
        #timer = threading.Timer(1, get_run_batch(args.batch))
        #timer.daemon = True
        #timer.start()
        #QtCore.QTimer.singleShot(0, get_run_batch(args.batch))
        #t = BatchThread(args.batch)
        #t.start()
        run_batch(fname=args.batch)
        #sys.exit(app.exec_())
    else:
        # OS specific changes
        if sys.platform.startswith("darwin"):
            QtGui.QApplication.setGraphicsSystem('native')
        elif sys.platform.startswith('linux'):
            # Broken opening of external links with PyInstaller - this is a hack to work around it
            os.environ["XDG_DATA_DIRS"] = "/usr/share/gnome:/usr/local/share/:/usr/share/:" + os.environ.get("XDG_DATA_DIRS", "")

        app = QtGui.QApplication(sys.argv)
        QtCore.QCoreApplication.setOrganizationName("ibme-qubic")
        QtCore.QCoreApplication.setOrganizationDomain("eng.ox.ac.uk")
        QtCore.QCoreApplication.setApplicationName("Quantiphyse")
        sys.excepthook = my_catch_exceptions
        # Handle CTRL-C correctly
        signal.signal(signal.SIGINT, signal.SIG_DFL)

        # Create window and start main loop
        app.setStyle('plastique') # windows, motif, cde, plastique, windowsxp, macintosh
        if args.qv:
            win = QuickWindow(load_data=args.data, load_roi=args.roi)
        else:
            win = MainWindow(load_data=args.data, load_roi=args.roi)
        set_main_window(win)

        sys.exit(app.exec_())

