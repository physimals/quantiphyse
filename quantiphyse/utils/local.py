"""
Quantiphyse - Functions for querying and reading locally installed files

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
    else:
        # Running from a script
        LOCAL_FILE_PATH = os.path.join(os.path.dirname(__file__), os.pardir)
        
    if LOCAL_FILE_PATH == "":
        # Use local working directory otherwise
        LOG.warn("Reverting to current directory as local path")
        LOCAL_FILE_PATH = os.getcwd()

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
        url = str(url.toString()).replace(" ", "%20")
        url_obj = NSURL.URLWithString_(url)
        if url_obj:
            return str(url_obj.filePathURL().path())
        else:
            LOG.warn("Failed to convert local file URL: %s", url)
            return None
    else:
        path = str(url.toLocalFile())
        if sys.platform.startswith("win"):
            # QT bug with UNC paths. We can't fix this generally but we want
            # the WSL specific case to work, so detect that at least
            wslpath = "\\\\wsl$\\" + path
            if not os.path.exists(path) and os.path.exists(wslpath):
                return wslpath
        return path

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

def get_local_shlib(name, loc):
    """
    Get a named shared library which is stored locally to another file
    """
    return get_local_file(get_lib_fname(name), loc)
    
def default_save_dir():
    return DEFAULT_SAVE_DIR

def set_default_save_dir(save_dir):
    global DEFAULT_SAVE_DIR
    DEFAULT_SAVE_DIR = save_dir