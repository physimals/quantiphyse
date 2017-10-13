
"""
Main file

To compile the resources, run:
$ pyside-rcc resource -o resource.py
from inside quantiphyse/resources
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
    args = parser.parse_args()

    set_debug(args.debug)
    if args.debug: pg.systemInfo()

    # Check whether any batch processing arguments have been called
    if (args.batch is not None):
        #app = QtCore.QCoreApplication(sys.argv)
        #timer = threading.Timer(1, get_run_batch(args.batch))
        #timer.daemon = True
        #timer.start()
        #QtCore.QTimer.singleShot(0, get_run_batch(args.batch))
        #t = BatchThread(args.batch)
        #t.start()
        run_batch(args.batch)
        #sys.exit(app.exec_())
    else:
        # OS specific changes
        if sys.platform.startswith("darwin"):
            QtGui.QApplication.setGraphicsSystem('native')
            
        app = QtGui.QApplication(sys.argv)
        QtCore.QCoreApplication.setOrganizationName("ibme-qubic")
        QtCore.QCoreApplication.setOrganizationDomain("eng.ox.ac.uk")
        QtCore.QCoreApplication.setApplicationName("Quantiphyse")
        sys.excepthook = my_catch_exceptions
        # Handle CTRL-C correctly
        signal.signal(signal.SIGINT, signal.SIG_DFL)

        # Set the local file path, used for finding icons, etc
        local_file_path = ""
        if hasattr(sys, 'frozen'):
            # File is frozen (packaged apps)
            print("Frozen executable")
            if hasattr(sys, '_MEIPASS'):
                local_file_path = sys._MEIPASS
            elif hasattr(sys, '_MEIPASS2'):
                local_file_path = sys._MEIPASS2
            elif sys.frozen == 'macosx_app':
                local_file_path = os.getcwd() + '/quantiphyse'
            else:
                local_file_path = os.path.dirname(sys.executable)
            os.environ["FABBERDIR"] = os.path.join(local_file_path, "fabber")
        else:
            # Running from a script
            local_file_path = os.path.dirname(__file__)
            
        if local_file_path == "":
            # Use local working directory otherwise
            warn("Reverting to current directory as local path")
            local_file_path = os.getcwd()

        debug("Local directory: ", local_file_path)
        set_local_file_path(local_file_path)

        # Create window and start main loop
        app.setStyle('plastique') # windows, motif, cde, plastique, windowsxp, macintosh
        win = MainWindow(load_data=args.data, load_roi=args.roi)
        set_main_window(win)

        sys.exit(app.exec_())

