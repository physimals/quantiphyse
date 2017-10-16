"""

Author: Benjamin Irving (benjamin.irv@gmail.com)
Copyright (c) 2013-2015 University of Oxford, Benjamin Irving

"""
import os.path
import glob
import importlib

from PySide import QtGui

from ..utils import debug, warn, get_icon

def _merge_into_dict(d1, d2):
    for key, values in d2.items():
        if key not in d1: d1[key] = []
        d1[key] += values

def _possible_module(f):
    if f.endswith("__init__.py"): 
        return None
    elif os.path.isdir(f): 
        return os.path.basename(f)
    elif f.endswith(".py") or f.endswith(".dll") or f.endswith(".so"):
        return os.path.basename(f).rsplit(".", 1)[0]

def _load_plugins(dirname, pkgname):
    """
    Beginning of plugin system - load modules dynamically from the specified directory

    Then check in module for widgets and/or processes to return
    """
    submodules = glob.glob(os.path.join(dirname, "*"))
    widgets, processes = [], []
    done = set()
    for f in submodules:
        mod = _possible_module(f)
        if mod is not None and mod not in done:
            done.add(mod)
            modname = "%s.%s" % (pkgname, mod)
            try:
                m = importlib.import_module(modname)
                if hasattr(m, "QP_WIDGETS"):
                    debug(modname, m.QP_WIDGETS)
                    widgets += m.QP_WIDGETS
                if hasattr(m, "QP_PROCESSES"):
                    debug(modname, m.QP_PROCESSES)
                    processes += m.QP_PROCESSES
            except:
                warn("Error loading widget: %s" % modname)
                raise
    debug(widgets)
    debug(processes)
    return widgets, processes

def get_known_widgets():
    """
    Beginning of plugin system - load widgets dynamically from specified plugins directory
    """
    widgets = []

    base_dir = os.path.dirname(__file__)
    base_widgets, base_processes = _load_plugins(base_dir, "quantiphyse.widgets")
    widgets += base_widgets
    
    plugin_dir = os.path.join(base_dir, os.pardir, "plugins")
    plugin_widgets, plugin_processes = _load_plugins(plugin_dir, "quantiphyse.plugins")
    widgets += plugin_widgets
    
    return widgets

class QpWidget(QtGui.QWidget):
    """
    Base class for a Quantiphyse widget

    The following properties are set automatically from keyword args or defaults:
      self.ivm - Image Volume Management instance
      self.ivl - ImageView instance
      self.icon - QIcon for the menu/tab
      self.name - Name for the menu
      self.description - Longer description (for tooltip)
      self.tabname - Name for the tab
    """

    def __init__(self, **kwargs):
        super(QpWidget, self).__init__()
        self.name = kwargs.get("name", "")
        self.description = kwargs.get("desc", self.name)
        self.icon = QtGui.QIcon(get_icon(kwargs.get("icon", "")))
        self.tabname = kwargs.get("tabname", self.name.replace(" ", "\n"))
        self.ivm = kwargs.get("ivm", None)
        self.ivl = kwargs.get("ivl", None)
        self.opts = kwargs.get("opts", None)
        self.group = kwargs.get("group", "")
        self.position = kwargs.get("position", 999)
        self.visible = False
        if self.opts:
                self.opts.sig_options_changed.connect(self.options_changed)

    def init_ui(self):
        """
        Called when widget is first shown. Widgets should ideally override this to build their
        UI widgets when required, rather than in the constructor which is called at startup
        """
        pass

    def activate(self):
        """
        Called when widget is made active, so can for example connect signals to the 
        volume management or view classes, and update it's current state
        """
        pass

    def deactivate(self):
        """
        Called when widget is made inactive, so should for example disconnect signals and remove 
        any related selections from the view
        """
        pass

    def options_changed(self):
        """
        Override to respond to global option changes
        """
        pass

