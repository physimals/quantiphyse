"""
Quantiphyse - Rag-bag of utility functions - should be moved into specific modules

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
    try:
        try:
            a = np.loadtxt(filename)
        except ValueError:
            a = np.loadtxt(filename, delimiter=",")
    except ValueError as exc:
        raise QpException("Invalid matrix data: %s" % str(exc))

    a = np.atleast_2d(a)
    if a.ndim != 2:
        raise QpException("Matrix data was not 1D or 2D")

    return a, a.shape[0], a.shape[1]

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
