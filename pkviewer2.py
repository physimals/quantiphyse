
"""
Main file

To compile the resources, run:
$ pyside-rcc resource -o resource.py
from inside pkview/resources
"""

import multiprocessing

if __name__ == '__main__':
    # Enable multiprocessing on windows frozen binaries
    # Does nothing on other systems
    multiprocessing.freeze_support()

    from pkview import pkviewer
    pkviewer.main()

