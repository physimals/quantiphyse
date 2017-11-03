"""
Rag-bag of utility functions - some should probably be moved
into more specific modules
"""
from __future__ import division, print_function

import os, sys
import glob
import importlib
import traceback
import tempfile

from matplotlib import cm
import numpy as np

from PySide import QtCore, QtGui

LOCAL_FILE_PATH=""
DEBUG = False
WIDGETS = None
PROCESSES = None

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

def get_icon(name, dir=None):
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
    tries = []
    if dir is not None: 
        tries.append(os.path.join(dir, "%s%s" % (name, extension)))
    tries.append(os.path.join(LOCAL_FILE_PATH, "icons", "%s%s" % (name, extension)))
    for t in tries:
        if os.path.isfile(t): return t

def get_local_file(name):
    """
    Get path to the named icon
    """
    global LOCAL_FILE_PATH
    return os.path.join(LOCAL_FILE_PATH, name)

def load_matrix(filename):
    f = open(filename)
    fvals = []
    ncols = -1
    try:
        lines = f.readlines()
        for line in lines:
            # Discard comments
            line = line.split("#", 1)[0].strip()
            # Split by commas or spaces
            vals = line.replace(",", " ").split()
            if ncols < 0: ncols = len(vals)
            elif len(vals) != ncols:
                raise QpException("File must contain a matrix of numbers with fixed size (rows/columns)")

            for val in vals:
                try:
                    fval = float(val)
                except:
                    raise QpException("Non-numeric value '%s' found in file %s" % (val, filename))
            fvals.append([float(v) for v in vals])     
    finally:
        f.close()
    return fvals, len(fvals), ncols

def write_temp_matrix(prefix, matrix):
    """
    Write a matrix to a temporary file, returning the filename
    """
    f = tempfile.NamedTemporaryFile(prefix=prefix, delete=False)
    debug("matrix: %s" % prefix)
    for row in matrix:
        line = " ".join([str(v) for v in row]) + "\n"
        debug(line)
        f.write(line)
    f.close()
    return f.name

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
    debug(tsv)
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

def _possible_module(f):
    if f.endswith("__init__.py"): 
        return None
    elif os.path.isdir(f): 
        return os.path.basename(f)
    elif f.endswith(".py") or f.endswith(".dll") or f.endswith(".so"):
        return os.path.basename(f).rsplit(".", 1)[0]

def _load_plugins_from_dir(dirname, pkgname, widgets, processes):
    """
    Beginning of plugin system - load modules dynamically from the specified directory

    Then check in module for widgets and/or processes to return
    """
    submodules = glob.glob(os.path.join(dirname, "*"))
    done = set()
    sys.path.append(dirname)
    for f in submodules:
        mod = _possible_module(f)
        if mod is not None and mod not in done:
            done.add(mod)
            try:
                debug("Trying to import", mod)
                m = importlib.import_module(mod, pkgname)
                if hasattr(m, "QP_WIDGETS"):
                    debug("Widgets found:", mod, m.QP_WIDGETS)
                    widgets += m.QP_WIDGETS
                if hasattr(m, "QP_PROCESSES"):
                    debug("Processes found:", mod, m.QP_PROCESSES)
                    processes += m.QP_PROCESSES
            except:
                warn("Error loading plugin: %s" % mod)
                traceback.print_exc()

def get_plugins():
    """
    Beginning of plugin system - load widgets dynamically from specified plugins directory
    """
    global LOCAL_FILE_PATH, WIDGETS, PROCESSES
    if WIDGETS is None or PROCESSES is None:
        WIDGETS, PROCESSES = [], []

        core_dir = os.path.join(LOCAL_FILE_PATH, "packages", "core")
        _load_plugins_from_dir(core_dir, "quantiphyse.packages.core", WIDGETS, PROCESSES)

        plugin_dir = os.path.join(LOCAL_FILE_PATH, "packages", "plugins")
        _load_plugins_from_dir(plugin_dir, "quantiphyse.packages.plugins", WIDGETS, PROCESSES)
    
    return WIDGETS, PROCESSES
