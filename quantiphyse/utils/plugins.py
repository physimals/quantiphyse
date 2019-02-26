"""
Quantiphyse - Functions for loading and querying plugins

Copyright (c) 2013-2018 University of Oxford
"""

import sys
import os
import glob
import importlib
import logging
import traceback

from quantiphyse.utils.local import get_local_file

PLUGIN_MANIFEST = None
LOG = logging.getLogger(__name__)

def _possible_module(mod_file):
    if os.path.basename(mod_file).startswith("_"):
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
    LOG.debug("Loading plugins from %s", dirname)
    submodules = glob.glob(os.path.join(os.path.abspath(dirname), "*"))
    done = set()
    pythonpath = list(sys.path)
    try:
        sys.path.insert(0, dirname)
        for mod_file in submodules:
            mod = _possible_module(mod_file)
            if mod is not None and mod not in done:
                done.add(mod)
                try:
                    LOG.debug("Trying to import %s", mod)
                    module = importlib.import_module(mod, pkgname)
                    LOG.debug("Got %s (%s)", module.__name__, module.__file__)
                    if hasattr(module, "QP_WIDGETS"):
                        LOG.debug("Widgets found: %s %s", mod, module.QP_WIDGETS)
                        manifest["widgets"] = manifest.get("widgets", []) + module.QP_WIDGETS
                    if hasattr(module, "QP_PROCESSES"):
                        LOG.debug("Processes found: %s %s", mod, module.QP_PROCESSES)
                        manifest["processes"] = manifest.get("processes", []) + module.QP_PROCESSES
                    if hasattr(module, "QP_MANIFEST"):
                        # Module directories are added to the global PYTHONPATH
                        for deps_dir in module.QP_MANIFEST.pop("module-dirs", []):
                            deps_path = os.path.join(dirname, mod_file, deps_dir)
                            if os.path.isdir(deps_path):
                                pythonpath.append(deps_path)
                        # Everything else is added to the global manifest
                        for key, val in module.QP_MANIFEST.items():
                            LOG.debug("%s found: %s %s", key, mod, val)
                            manifest[key] = manifest.get(key, []) + val
                except ImportError:
                    LOG.warn("Error loading plugin: %s", mod)
                    traceback.print_exc()
    finally:
        sys.path = pythonpath

def _load_plugins_from_entry_points(manifest, key="quantiphyse_plugins"):
    import pkg_resources
    for ep in pkg_resources.iter_entry_points(key):
        for key, val in ep.load().items():
            LOG.debug("entry points: found: %s %s", key, val)
            manifest[key] = manifest.get(key, []) + val

def get_plugins(key=None, class_name=None):
    """
    Beginning of plugin system - load widgets dynamically from specified plugins directory
    """
    global PLUGIN_MANIFEST
    if PLUGIN_MANIFEST is None:
        PLUGIN_MANIFEST = {}

        plugin_dirs = {
            "quantiphyse.packages.core" : get_local_file("packages/core"), 
            "quantiphyse.packages.plugins" : get_local_file("packages/plugins"),
        }
        for pkg, plugin_dir in plugin_dirs.items():
            #if os.path.exists(plugin_dir):
            #    __import__(pkg)
            _load_plugins_from_dir(plugin_dir, pkg, PLUGIN_MANIFEST)

        _load_plugins_from_entry_points(PLUGIN_MANIFEST)
    
    if key is not None:
        plugins = PLUGIN_MANIFEST.get(key, [])
        if class_name is not None: 
            plugins = [p for p in plugins if p.__name__ == class_name]
    else:
        plugins = PLUGIN_MANIFEST
    return plugins
