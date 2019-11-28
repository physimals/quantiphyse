"""
Quantiphyse - Rag-bag of utility functions - should be moved into specific modules

Copyright (c) 2013-2018 University of Oxford
"""

from __future__ import division, print_function

import sys
import tempfile
import logging

from matplotlib import cm
import numpy as np
import pandas as pd

try:
    from PySide import QtGui, QtCore, QtGui as QtWidgets
except ImportError:
    from PySide2 import QtGui, QtCore, QtWidgets

from quantiphyse.data.extras import DataFrameExtra
from .exceptions import QpException
from .logger import LogSource
from .plugins import get_plugins
from .local import set_default_save_dir, default_save_dir, get_local_file, get_local_shlib, get_icon, set_local_file_path, local_file_from_drop_url

__all__ = ["QpException", "LogSource", "get_plugins", "get_local_file", "get_local_shlib", "get_icon", "set_local_file_path", "local_file_from_drop_url",]

DEFAULT_SIG_FIG = 4
LOG = logging.getLogger(__name__)

def norecurse(fn):
    """
    Decorator which prevents recursive calling of an object method
    """
    def _wrapper(*args):
        self = args[0]
        if not self.updating:
            try:
                self.updating = True
                return fn(*args)
            finally:
                self.updating = False
    return _wrapper

def ifnone(obj, alt):
    """
    Convenience function to return an alternative if an object is None

    Why isn't this in the standard library!

    :param obj: Object
    :param alt: Alternative
    :return: obj if not None, otherwise alt
    """
    if obj is None:
        return alt
    else:
        return obj

def show_help(section="", base='http://quantiphyse.readthedocs.io/en/latest/'):
    """
    Open the help page at a specified page

    :param section: Section ID, if not specified open main index page
    :param base: Base URL for documentation, may be version dependent
    """ 
    if section != "" and not section.endswith(".html") and not section.endswith("/"): 
        section += ".html"
    link = base + section
    QtGui.QDesktopServices.openUrl(QtCore.QUrl(link, QtCore.QUrl.TolerantMode))

def load_matrix(filename):
    """
    Load a file containing a matrix of numbers in ASCII text

    :return: Matrix of numbers (list of list, not Numpy array), number of rows, number of columns
    """
    with open(filename, "r") as matrix_file:
        return text_to_matrix(matrix_file.read())

def text_to_matrix(text):
    """
    Convert ASCII text into a matrix of numbers
    
    :return: Matrix of numbers (list of list, not Numpy array), number of rows, number of columns
    """
    fvals = []
    ncols = -1
    lines = text.splitlines()
    for line in lines:
        # Discard comments
        line = line.split("#", 1)[0].strip()
        # Split by commas or spaces
        vals = line.replace(",", " ").split()
        # Ignore empty lines
        if not vals: continue
        # Check correct number of columns
        if ncols < 0: ncols = len(vals)
        elif len(vals) != ncols:
            raise QpException("File must contain a matrix of numbers with fixed size (rows/columns)")
        # Check all data is numeric
        for val in vals:
            try:
                float(val)
            except:
                raise QpException("Non-numeric value '%s' found in matrix" % val)
        fvals.append([float(v) for v in vals])     
    
    return fvals, len(fvals), ncols

def write_temp_matrix(prefix, matrix):
    """
    Write a matrix to a temporary file, returning the filename
    """
    temp_file = tempfile.NamedTemporaryFile(prefix=prefix, delete=False)
    LOG.debug("matrix: %s", prefix)
    for row in matrix:
        line = " ".join([str(v) for v in row]) + "\n"
        LOG.debug(line)
        temp_file.write(line)
    temp_file.close()
    return temp_file.name

def get_version():
    """
    :return: Quantiphyse version number
    """
    try:
        from .._version import __version__
        return __version__
    except ImportError:
        LOG.warn(sys.exc_info()[1])
        return "<version not found>"

def table_to_extra(tabmod, name):
    """ 
    Turn a QT table model into a DataFrameExtra
    """
    cols = range(tabmod.columnCount())
    rows = range(tabmod.rowCount())
    columns = [tabmod.horizontalHeaderItem(col).text().replace("\n", " ") for col in cols]
    index = [tabmod.verticalHeaderItem(row).text() for row in rows] 

    rowdata = []
    for row in rows:
        rowdata.append([tabmod.item(row, col).text() for col in cols])

    df = pd.DataFrame(rowdata, index=index, columns=columns)
    return DataFrameExtra(name, df)

def copy_table(tabmod):
    """ Copy a QT table model to the clipboard in a form suitable for paste into Excel etc """
    clipboard = QtGui.QApplication.clipboard()
    tsv = str(table_to_extra(tabmod, ""))
    clipboard.setText(tsv)

def sf(num, sig_fig=None):
    """ Format a number as a string to a given number of sig figs """
    if sig_fig is None: 
        global DEFAULT_SIG_FIG
        sig_fig = DEFAULT_SIG_FIG
    fmt = "%%.%ig" % sig_fig
    return fmt % float(num)

def remove_nans(data, fillvalue=0):
    """
    Check for and remove nans from data arrays
    """
    notnans = np.isfinite(data)
    if not np.all(notnans):
        data[np.logical_not(notnans)] = fillvalue

def get_col(cmap, idx, out_of):
    """ Get RGB color for an index within a range, using a Matplotlib colour map """
    if out_of == 0: 
        return [255, 0, 0]
    else:
        return [int(255 * rgbf) for rgbf in cmap(float(idx)/out_of)[:3]]

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
    try:
        max_region = max(roi.regions.keys())
    except:
        # No nonzero regions!
        max_region = 1
    if max_region < 3: max_region = 3
    lut = [[0, 0, 0],] + [[int(255 * rgb1) for rgb1 in cmap(float(v+1)/max_region)[:3]] for v in range(max_region-1, -1, -1)]
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
KELLY_COLORS = [
    ("off_white", (230, 230, 230)),
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
    ("dark_olive_green", (35, 44, 22)),
]

def get_kelly_col(idx, wrap=True):
    """
    Get the Kelly colour for a given index

    :param idx: Index
    :param wrap: If True, wrap index to number of Kelly colours
    :return: (RGB) tuple in range 0-255
    """
    baseidx = idx % len(KELLY_COLORS)
    basecol = KELLY_COLORS[baseidx][1]
    if not wrap:
        raise RuntimeError("Not implemented yet")
    return basecol
