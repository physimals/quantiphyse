
"""
Main file

To compile the resources, run:
$ pyside-rcc resource -o resource.py
from inside pkview/resources
"""

if __name__ == '__main__':
    from pkview import pkviewer
    pkviewer.main()

