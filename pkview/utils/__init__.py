import os, sys

from PySide import QtCore, QtGui

LOCAL_FILE_PATH=""

def set_local_file_path(path):
    global LOCAL_FILE_PATH
    LOCAL_FILE_PATH = path

def get_icon(name):
    """
    Get path to the named icon
    """
    global LOCAL_FILE_PATH
    name, extension = os.path.splitext(name)
    if extension == "":
        if sys.platform.startswith("win") or sys.platform.startswith("darwin"):
            extension = ".png"
        else:
            extension = ".svg"
    return os.path.join(LOCAL_FILE_PATH, "icons/%s%s" % (name, extension))

def get_local_file(name):
    """
    Get path to the named icon
    """
    global LOCAL_FILE_PATH
    return os.path.join(LOCAL_FILE_PATH, name)

def copy_table(tabmod):
    """ Copy a QT table model to the clipboard in a form suitable for paste into Excel etc """
    tsv = ""
    rows = range(tabmod.rowCount())
    cols = range(tabmod.columnCount())
    colheaders = ["",] + [tabmod.horizontalHeaderItem(col).text().replace("\n", " ") for col in cols]
    tsv += "\t".join(colheaders) + "\n"

    for row in rows:
        rowdata = [tabmod.verticalHeaderItem(row).text(),] 
        rowdata += [tabmod.item(row, col).text() for col in cols]
        tsv += "\t".join(rowdata) + "\n"
    clipboard = QtGui.QApplication.clipboard()
    print(tsv)
    clipboard.setText(tsv)
