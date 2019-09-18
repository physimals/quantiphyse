"""
Quantiphyse - Functions for querying and reading locally installed files

Copyright (c) 2013-2018 University of Oxford
"""
import sys
import os
import logging
import warnings

LOCAL_FILE_PATH = ""
DEFAULT_SAVE_DIR = ""
LOG = logging.getLogger(__name__)

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
        LOG.debug("Frozen executable")
        if hasattr(sys, '_MEIPASS'):
            LOCAL_FILE_PATH = sys._MEIPASS
        elif hasattr(sys, '_MEIPASS2'):
            LOCAL_FILE_PATH = sys._MEIPASS2
        elif sys.frozen == 'macosx_app':
            LOCAL_FILE_PATH = os.getcwd() + '/quantiphyse'
        else:
            LOCAL_FILE_PATH = os.path.dirname(sys.executable)
        
        # Frozen packages have Fabber code bundled but allow user override
        if "FABBERDIR" in os.environ:
            warnings.warn("Using user's custom Fabber code in $FABBERDIR=%s" % os.environ["FABBERDIR"])
        else:
            os.environ["FABBERDIR"] = os.path.join(LOCAL_FILE_PATH, "fabberdir")
        
        # If we are on Windows and there is no sign of FSL, look for bundled code
        if "FSLDIR" not in os.environ and sys.platform.startswith("win"):
            os.environ["FSLDIR"] = os.path.join(LOCAL_FILE_PATH, "fsldir")
    else:
        # Running from a script
        LOCAL_FILE_PATH = os.path.join(os.path.dirname(__file__), os.pardir)
        
    if LOCAL_FILE_PATH == "":
        # Use local working directory otherwise
        LOG.warn("Reverting to current directory as local path")
        LOCAL_FILE_PATH = os.getcwd()

    if "FSLOUTPUTTYPE" not in os.environ:
        # Required for FSLMATHS - should really be in FSL widget
        os.environ["FSLOUTPUTTYPE"] = "NIFTI_GZ"

    LOG.debug("Local directory: %s", LOCAL_FILE_PATH)

def local_file_path():
    """
    :return: The path to locally installed files
    """
    return LOCAL_FILE_PATH

def get_local_file(name, loc=None):
    """
    Get path to a file relative to the main Quantiphyse folder

    If location is not None, use it to determine the local root folder 
    (e.g. use __file__ to get file local to a python plugin module)
    """
    if loc is None:
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
    name, extension = os.path.splitext(name)
    if extension == "":
        extension = ".png"
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

def get_exe_fname(name):
    """ Get file name for named executable on current platform """
    if sys.platform.startswith("win"):
        return "%s.exe" % name
    else:
        return  name

def get_local_shlib(name, loc=None):
    """
    Get a named shared library which is stored locally

    :param name: Name of shared library which will be turned into an actual filename
                 in a platform dependent way
    :param loc: Directory to make relative to. If not specified, use 'lib' subdirectory
                of Quantiphyse local file directory
    """
    if loc is None:
        loc = os.path.join(LOCAL_FILE_PATH, "lib")
    return get_local_file(get_lib_fname(name), loc)
    
def get_local_exe(name, loc=None):
    """
    Get a named executable which is stored locally

    :param name: Name of executable which will be turned into an actual filename
                 in a platform dependent way
    :param loc: Directory to make relative to. If not specified, use 'lib' subdirectory
                of Quantiphyse local file directory
    """
    if loc is None:
        loc = os.path.join(LOCAL_FILE_PATH, "bin")
    return get_local_file(get_exe_fname(name), loc)

def default_save_dir():
    return DEFAULT_SAVE_DIR

def set_default_save_dir(save_dir):
    global DEFAULT_SAVE_DIR
    DEFAULT_SAVE_DIR = save_dir

def which(program):
    """
    Find an executable locally or in the user's PATH
    """
    def is_exe(fpath):
        return os.path.isfile(fpath) and os.access(fpath, os.X_OK)

    fpath, fname = os.path.split(program)
    if fpath:
        if is_exe(program):
            return program
    elif is_exe(get_local_exe(program)):
        return get_local_exe(program)
    else:
        for path in os.environ["PATH"].split(os.pathsep):
            exe_file = os.path.join(path, get_exe_fname(program))
            if is_exe(exe_file):
                return exe_file

    return None