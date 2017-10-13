from __future__ import division, print_function

import os, sys

from matplotlib import cm
import numpy as np

from PySide import QtCore, QtGui

LOCAL_FILE_PATH=""
DEBUG = False

def set_debug(debug):
    global DEBUG
    DEBUG = debug

def debug(*msgs):
    if DEBUG:
        print(*msgs)

def warn(msg):
    sys.stderr.write("WARNING: %s\n" % str(msg))
    sys.stderr.flush()

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

def get_version():
    try:
        from .._version import __version__
        return __version__
    except:
        warn(sys.exc_info()[1])
        return "<version not found>"

def table_to_str(tabmod):
    """ Turn a QT table model into a TSV string """
    tsv = ""
    rows = range(tabmod.rowCount())
    cols = range(tabmod.columnCount())
    colheaders = ["",] + [tabmod.horizontalHeaderItem(col).text().replace("\n", " ") for col in cols]
    tsv += "\t".join(colheaders) + "\n"

    for row in rows:
        rowdata = [tabmod.verticalHeaderItem(row).text(),] 
        rowdata += [tabmod.item(row, col).text() for col in cols]
        tsv += "\t".join(rowdata) + "\n"
    #print(tsv)
    return tsv

def copy_table(tabmod):
    """ Copy a QT table model to the clipboard in a form suitable for paste into Excel etc """
    clipboard = QtGui.QApplication.clipboard()
    tsv = table_to_str(tabmod)
    clipboard.setText(tsv)

def get_col(cmap, idx, out_of):
    """ Get RGB color for an index within a range, using a Matplotlib colour map """
    if out_of == 0: 
        return [255, 0, 0]
    else:
        return [int(255 * rgbf) for rgbf in cmap(float(idx)/out_of)[:3]]

    return lut

def get_pencol(roi, region):
    """
    Get an RGB pen colour for a given ROI region
    """
    if roi is None:
        return (255, 0, 0)
    else:
        return get_lut(roi)[region]

def get_lut(roi, alpha=None):
    """
    Get the colour look up table for the ROI.
    """
    cmap = getattr(cm, 'jet')
    mx = max(roi.regions)
    if mx < 3: mx = 3
    lut = [[0, 0, 0],] + [[int(255 * rgb1) for rgb1 in cmap(float(v+1)/mx)[:3]] for v in range(mx-1, -1, -1)]
    lut = np.array(lut, dtype=np.ubyte)

    if alpha is not None:
        # add transparency
        alpha1 = np.ones((lut.shape[0], 1))
        alpha1 *= alpha
        alpha1[0] = 0
        lut = np.hstack((lut, alpha1))

    return lut

# Kelly (1965) - set of 20 contrasting colours
# We alter the order a bit to prioritize those that give good contrast to our dark background
# plus we add an 'off white' at the start
KELLY_COLORS = [("off_white", (230, 230, 230)),
                ("vivid_yellow", (255, 179, 0)),
                ("vivid_orange", (255, 104, 0)),
                ("very_light_blue", (166, 189, 215)),
                ("vivid_red", (193, 0, 32)),
                ("grayish_yellow", (206, 162, 98)),
                ("medium_gray", (129, 112, 102)),
                ("strong_purple", (128, 62, 117)),

                # these aren't good for people with defective color vision:
                ("vivid_green", (0, 125, 52)),
                ("strong_purplish_pink", (246, 118, 142)),
                ("strong_blue", (0, 83, 138)),
                ("strong_yellowish_pink", (255, 122, 92)),
                ("strong_violet", (83, 55, 122)),
                ("vivid_orange_yellow", (255, 142, 0)),
                ("strong_purplish_red", (179, 40, 81)),
                ("vivid_greenish_yellow", (244, 200, 0)),
                ("strong_reddish_brown", (127, 24, 13)),
                ("vivid_yellowish_green", (147, 170, 0)),
                ("deep_yellowish_brown", (89, 51, 21)),
                ("vivid_reddish_orange", (241, 58, 19)),
                ("dark_olive_green", (35, 44, 22))
]

def get_kelly_col(idx, wrap=True):
    baseidx = idx % len(KELLY_COLORS)
    basecol = KELLY_COLORS[baseidx][1]
    if not wrap:
        raise RuntimeError("Not implemented yet")
    return basecol
