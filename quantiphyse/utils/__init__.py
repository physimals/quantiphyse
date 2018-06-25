"""
Quantiphyse - Rag-bag of utility functions - some should probably be moved
into more specific modules

Copyright (c) 2013-2018 University of Oxford
"""

from __future__ import division, print_function

import os 
import sys
import glob
import importlib
import traceback
import tempfile
import logging

from matplotlib import cm
import numpy as np

from PySide import QtCore, QtGui

from .exceptions import QpException

LOCAL_FILE_PATH = ""
DEBUG = False
PLUGIN_MANIFEST = None

DEFAULT_SIG_FIG = 4

# This is a generic logger for the application. Intention is to move to
# per-widget loggers but in the interim this is what we use for calls to debug() etc
logging.basicConfig(format='%(asctime)s %(levelname)s %(name)s %(message)s', datefmt='%H:%M:%S')
GENERIC_LOGGER = logging.getLogger("quantiphyse")

def set_debug(enable_debug):
    """
    Set the generic debug level

    .. deprecated:: 0.8
    """
    global DEBUG, GENERIC_LOGGER
    DEBUG = enable_debug
    if enable_debug:
        GENERIC_LOGGER.setLevel(logging.DEBUG)
    else:
        GENERIC_LOGGER.setLevel(logging.WARN)

def get_debug():
    """
    Get the generic debug level

    .. deprecated:: 0.8
    """
    global DEBUG
    return DEBUG
    
def debug(*msgs):
    """
    Generic debug message

    .. deprecated:: 0.8
    """
    msg = " ".join([str(msg) for msg in msgs])
    GENERIC_LOGGER.debug(msg)

def warn(msg):
    """
    Generic warning message

    .. deprecated:: 0.8
    """
    GENERIC_LOGGER.warn(str(msg))

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
    
def set_local_file_path():
    """
    Initialize the file path to use when looking for local files, e.g. icons, plugins, etc

    This depends on whether we are in a frozen executable or running from a script so 
    various possibilities
    """
    global LOCAL_FILE_PATH
    LOCAL_FILE_PATH = ""
    if hasattr(sys, 'frozen'):
        # File is frozen (packaged apps)
        debug("Frozen executable")
        if hasattr(sys, '_MEIPASS'):
            LOCAL_FILE_PATH = sys._MEIPASS
        elif hasattr(sys, '_MEIPASS2'):
            LOCAL_FILE_PATH = sys._MEIPASS2
        elif sys.frozen == 'macosx_app':
            LOCAL_FILE_PATH = os.getcwd() + '/quantiphyse'
        else:
            LOCAL_FILE_PATH = os.path.dirname(sys.executable)
    else:
        # Running from a script
        LOCAL_FILE_PATH = os.path.join(os.path.dirname(__file__), os.pardir)
        
    if LOCAL_FILE_PATH == "":
        # Use local working directory otherwise
        warn("Reverting to current directory as local path")
        LOCAL_FILE_PATH = os.getcwd()

    debug("Local directory: ", LOCAL_FILE_PATH)

def get_local_file(name, loc=None):
    """
    Get path to a file relative to the main Quantiphyse folder

    If location is not None, use it to determine the local root folder 
    (e.g. use __file__ to get file local to a python plugin module)
    """
    if loc is None:
        global LOCAL_FILE_PATH
        loc = LOCAL_FILE_PATH
    else:
        loc = os.path.dirname(loc)
    return os.path.abspath(os.path.join(loc, name))

def local_file_from_drop_url(url):
    """
    Get the local file path associated with a drag/drop URL

    This is platform-dependent so put into it's own function

    :return: Local file path
    """
    if sys.platform.startswith("darwin"):
        # OSx specific changes to allow drag and drop
        from Cocoa import NSURL
        return str(NSURL.URLWithString_(str(url.toString())).filePathURL().path())
    else:
        return str(url.toLocalFile())

def get_icon(name, icon_dir=None):
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
    if icon_dir is not None: 
        tries.append(os.path.join(icon_dir, "%s%s" % (name, extension)))
    tries.append(os.path.join(LOCAL_FILE_PATH, "icons", "%s%s" % (name, extension)))
    for icon_file in tries:
        if os.path.isfile(icon_file): return icon_file

def get_lib_fname(name):
    """ Get file name for named shared library on current platform """
    if sys.platform.startswith("win"):
        return "%s.dll" % name
    elif sys.platform.startswith("darwin"):
        return "lib%s.dylib" % name
    else:
        return "lib%s.so" % name

def get_local_shlib(name, loc):
    """
    Get a named shared library which is stored locally to another file
    """
    return get_local_file(get_lib_fname(name), loc)
    
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
    debug("matrix: %s" % prefix)
    for row in matrix:
        line = " ".join([str(v) for v in row]) + "\n"
        debug(line)
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
        warn(sys.exc_info()[1])
        return "<version not found>"

def table_to_str(tabmod):
    """ 
    Turn a QT table model into a TSV string
    """
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
        max_region = max(roi.regions())
    except ValueError:
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

def _possible_module(mod_file):
    if mod_file.endswith("__init__.py"): 
        return None
    elif os.path.isdir(mod_file): 
        return os.path.basename(mod_file)
    elif mod_file.endswith(".py") or mod_file.endswith(".dll") or mod_file.endswith(".so"):
        return os.path.basename(mod_file).rsplit(".", 1)[0]

def _load_plugins_from_dir(dirname, pkgname, manifest):
    """
    Beginning of plugin system - load modules dynamically from the specified directory

    Then check in module for widgets and/or processes to return
    """
    debug("Loading plugins from ", dirname)
    submodules = glob.glob(os.path.join(os.path.abspath(dirname), "*"))
    done = set()
    sys.path.append(dirname)
    for mod_file in submodules:
        mod = _possible_module(mod_file)
        if mod is not None and mod not in done:
            done.add(mod)
            try:
                debug("Trying to import", mod)
                module = importlib.import_module(mod, pkgname)
                if hasattr(module, "QP_WIDGETS"):
                    debug("Widgets found:", mod, module.QP_WIDGETS)
                    manifest["widgets"] = manifest.get("widgets", []) + module.QP_WIDGETS
                if hasattr(module, "QP_PROCESSES"):
                    debug("Processes found:", mod, module.QP_PROCESSES)
                    manifest["processes"] = manifest.get("processes", []) + module.QP_PROCESSES
                if hasattr(module, "QP_MANIFEST"):
                    for key, val in module.QP_MANIFEST.items():
                        debug("%s found:" % key, mod, val)
                        manifest[key] = manifest.get(key, []) + val
            except ImportError:
                warn("Error loading plugin: %s" % mod)
                traceback.print_exc()

def get_plugins(key=None, class_name=None):
    """
    Beginning of plugin system - load widgets dynamically from specified plugins directory
    """
    global LOCAL_FILE_PATH, PLUGIN_MANIFEST
    if PLUGIN_MANIFEST is None:
        PLUGIN_MANIFEST = {}

        core_dir = os.path.join(LOCAL_FILE_PATH, "packages", "core")
        _load_plugins_from_dir(core_dir, "quantiphyse.packages.core", PLUGIN_MANIFEST)

        plugin_dir = os.path.join(LOCAL_FILE_PATH, "packages", "plugins")
        _load_plugins_from_dir(plugin_dir, "quantiphyse.packages.plugins", PLUGIN_MANIFEST)
    
    if key is not None:
        plugins = PLUGIN_MANIFEST.get(key, [])
        if class_name is not None: 
            plugins = [p for p in plugins if p.__name__ == class_name]
    else:
        plugins = PLUGIN_MANIFEST
    return plugins
