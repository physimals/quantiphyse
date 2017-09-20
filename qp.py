
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
import warnings
import traceback

from PySide import QtCore, QtGui
import pyqtgraph as pg

from quantiphyse.qpmain import MainWindow
from quantiphyse.utils.batch import run_batch
from quantiphyse.utils import set_local_file_path
from quantiphyse.QtInherit.dialogs import error_dialog

def my_catch_exceptions(type, value, tb):
    error_dialog(str(value), title="Error", detail=traceback.format_exception(type, value, tb))
        
if __name__ == '__main__':
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
    args = parser.parse_args()
    print(pg.systemInfo())

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
            local_file_path = os.path.join(os.path.dirname(__file__), "quantiphyse")
            
        if local_file_path == "":
            # Use local working directory otherwise
            warnings.warn("Reverting to current directory as local path")
            local_file_path = os.getcwd()

        print("Local directory: ", local_file_path)
        set_local_file_path(local_file_path)

        # Create window and start main loop
        app.setStyle('plastique') # windows, motif, cde, plastique, windowsxp, macintosh
        ex = MainWindow(load_data=args.data, load_roi=args.roi)
        sys.exit(app.exec_())

