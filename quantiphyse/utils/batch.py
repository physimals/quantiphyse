"""
Quantiphyse - Implements the batch processing system

The ``Script`` class defines a processing pipeline. It consists
of a series of ``Process`` objects and, optionally, a series of ``BatchCase``
objects, each of which describes a separate execution of the same process
pipeline. It is also in itself a ``Process``.

``Script`` can be used as a means of defining a macro process but is also
used as the basis of the batch processing system. The pipeline can be
defined programatically or via a YAML document.

``BatchScript`` is a subclass of ``Script`` which adds human-readable 
output suitable for command line batch execution.

Copyright (c) 2013-2018 University of Oxford
"""

import sys
import os
import os.path
import traceback
import time
import collections
import logging

import six
import yaml
import numpy as np

from PySide import QtCore

from quantiphyse.processes import Process
from quantiphyse.processes.io import *
from quantiphyse.processes.misc import *
from quantiphyse.utils.logger import set_base_log_level
from quantiphyse.data import ImageVolumeManagement, load, save

from . import get_plugins, ifnone
from .exceptions import QpException

# Default basic processes - all others are imported from packages
BASIC_PROCESSES = {
    "RenameData"   : RenameProcess,
    "RenameRoi"   : RenameProcess,
    "Rename"   : RenameProcess,
    "Delete"   : DeleteProcess,
    "RoiCleanup" : RoiCleanupProcess,
    "Load" : LoadProcess,
    "Save" : SaveProcess,
    "SaveAllExcept" : SaveAllExceptProcess,
    "SaveAndDelete" : SaveDeleteProcess,
    "LoadData" : LoadDataProcess,
    "LoadRois" : LoadRoisProcess,
    "SaveArtifacts" : SaveArtifactsProcess,
    "SaveExtras" : SaveArtifactsProcess
}

def to_yaml(processes, indent=""):
    """
    Turn a process list into YAML

    The reason for using this function instead of the built-in PyYAML
    dump functions is to get the flow we want and also handle Numpy 
    arrays. In particular, we want lists to be inline but dictionaries
    to be in block format.

    This only supports a small subset of YAML types:
    
     - The processes must either be a list of dictionaries, or a single dictionary.
     - Dictionary keys must be strings
     - Dictionary values must be strings, numbers, lists, Numpy arrays or dictionaries
    
    Anything else will throw a ValueError. While the list of supported types might
    increase in the future, part of the intention is to constrain the types that
    processes can use in for options, so it will not change much.

    This does not affect the parsing of YAML code which uses PyYAML and can use
    any supported YAML code.
    """
    def _dict_to_yaml(stream, valdict, indent="", prefix=""):
        for key, value in valdict.items():
            if not isinstance(key, six.string_types):
                raise ValueError("Keys must be strings")

            if value is None:
                continue

            stream.write("%s%s: " % (prefix, key))
            if isinstance(value, six.string_types):
                stream.write("%s\n" % value)
            elif isinstance(value, (int, float, list, np.floating, np.integer)):
                stream.write("%s\n" % str(value))
            elif isinstance(value, np.ndarray):
                stream.write("%s\n" % str(value.tolist()))
            elif isinstance(value, collections.Sequence):
                stream.write("%s\n" % str(list(value)))
            elif isinstance(value, collections.Mapping):
                stream.write("\n")
                indent += "  "
                _dict_to_yaml(stream, value, indent, prefix=indent)
            else:
                raise ValueError("Unsupported option value type: %s" % type(value))            

    if isinstance(processes, dict):
        processes = [processes,]

    yaml_str = six.StringIO()
    for process in processes:
        _dict_to_yaml(yaml_str, process, indent=indent + "    ", prefix="  - ")
        yaml_str.write("\n")
    return yaml_str.getvalue()

class Script(Process):
    """
    A processing script. It consists of three types of information:

     - Generic options (e.g. debug mode)
     - A single pipeline of processing steps
     - Optional list of BatchCase objects to apply these steps to

    A batch script can be run on a specified IVM, or it can be
    run on its cases. In this case a new IVM is created for
    each case
    """

    PROCESS_NAME = "Script"

    IGNORE = 1
    NEXT_CASE = 2
    FAIL = 3

    sig_start_case = QtCore.Signal(object)
    sig_done_case = QtCore.Signal(object)
    sig_start_process = QtCore.Signal(object, dict)
    sig_process_progress = QtCore.Signal(float)
    sig_done_process = QtCore.Signal(object, dict)

    def __init__(self, ivm=None, **kwargs):
        """
        fname: File name containing YAML code to load from
        code: YAML code as a string
        yamlroot: Parsed YAML code as Python objects
        """
        super(Script, self).__init__(ivm, **kwargs)
        
        self._current_ivm = None
        self._current_process = None
        self._current_params = None
        self._process_num = 0
        self._process_start = None
        self._current_case = None
        self._case_num = 0
        self._pipeline = []
        self._cases = []
        self._generic_params = {}
        self._error_action = kwargs.get("error_action", Script.IGNORE)
        self._embed_log = kwargs.get("embed_log", False)
        self._output_items = []

        # Find all the process implementations
        self.known_processes = dict(BASIC_PROCESSES)
        plugin_processes = get_plugins("processes")
        for process in plugin_processes:
            self.known_processes[process.PROCESS_NAME] = process

    def run(self, options):
        """
        Run the script

        The pipeline is created first, either from supplied
        YAML code, a filename or a set of parsed objects

        If no ``Case`` are included, a single default ``Case``
        is created. The completed pipeline is then run on all
        cases.

        Runs are asynchronous - initially we start the first
        process of the first case, and connect to the 'process finished'
        signal. When the slot is called, we start the next process, 
        or the next case as required. So the ``run()`` method returns
        as soon as the first process is started. 
        """
        if "parsed-yaml" in options:
            root = dict(options.pop("parsed-yaml"))
        elif "yaml" in options:
            root = yaml.load(options.pop("yaml"))
        elif "yaml-file" in options:
            with open(options.pop("yaml-file"), "r") as yaml_file:
                root = yaml.load(yaml_file)
        else:
            raise RuntimeError("Neither filename nor YAML code provided")

        if root is None: 
            # Handle special case of empty content
            root = {}

        # Can set mode=check to just validate the YAML
        self._load_yaml(root)
        self.debug(self._pipeline)
        self._output_items = []
        mode = options.pop("mode", "run")
        if mode == "run":
            self.status = Process.RUNNING
            self._case_num = 0
            self._next_case()
        elif mode != "check":
            raise QpException("Unknown mode: %s" % mode)

    def cancel(self):
        if self._current_process is not None:
            self._current_process.cancel()
    
    def _load_yaml(self, root=None):
        """
        Load YAML content
        """
        self._pipeline = []
        for process in root.pop("Processing", []):
            name = list(process.keys())[0]
            proc = self.known_processes.get(name, None)
            params = process[name]
            if params is None: params = {}

            if proc is None:
                raise QpException("Unknown process: %s" % name)
            else:
                params["id"] = params.get("id", name)
                params["__impl"] = proc
                self._pipeline.append(params)

        # Cases can be expressed as list or dict
        self._cases = []
        yaml_cases = root.pop("Cases", [])
        if isinstance(yaml_cases, dict):
            for case_id in sorted(yaml_cases.keys()):
                self._cases.append(Case(case_id, yaml_cases[case_id]))
        else:
            for case in yaml_cases:
                case_id = list(case.keys())[0]
                self._cases.append(Case(case_id, case.get(case_id, {})))
        
        # Create default case if we have not been specified any
        if not self._cases:
            self._cases.append(Case("case", {}))
        # After removing processes and cases, remainder is the generic options
        self._generic_params = root
    
    def _next_case(self):
        if self.status != self.RUNNING:
            return
        
        if self._case_num < len(self._cases):
            case = self._cases[self._case_num]
            self._case_num += 1
            self.sig_start_case.emit(case)
            self.debug("Starting case %s", case.case_id)
            self._start_case(case)
        else:
            self.debug("All cases complete")
            self.status = Process.SUCCEEDED
            self._complete()

    def _start_case(self, case):
        if self.ivm is not None:
            self._current_ivm = self.ivm
        else:
            self._current_ivm = ImageVolumeManagement()
        self._current_case = case
        self._process_num = 0
        self._next_process()

    def _next_process(self):
        if self.status != self.RUNNING:
            return
        
        if self._process_num < len(self._pipeline):
            process = self._pipeline[self._process_num]
            self._process_num += 1
            self._start_process(process)
        else:
            self.debug("All processes complete")
            if len(self._cases) > 1:
                self.log("CASE COMPLETE\n")
            self.sig_done_case.emit(self._current_case)
            self._next_case()

    def _start_process(self, proc_params):
        # Make copy so process does not mess up shared config
        proc_params = dict(proc_params)
        generic_params = dict(self._generic_params)

        # Override values which are defined in the individual case
        if self._current_case is not None:
            case_params = dict(self._current_case.params)
            override = case_params.pop(proc_params["id"], {})
            proc_params.update(override)
            generic_params.update(case_params)
            # OutputId defaults to the case ID if not specified
            if "OutputId" not in generic_params:
                generic_params["OutputId"] = self._current_case.case_id

        # Set debug level for this individual process based on whether logging
        # was enabled generically, for this case, and for this process
        if "--debug" in sys.argv or proc_params.get("Debug", generic_params.get("Debug", False)):
            set_base_log_level(logging.DEBUG)
        else:
            set_base_log_level(logging.WARN)

        try:
            outdir = os.path.abspath(os.path.join(ifnone(generic_params.get("OutputFolder", ""), ""), 
                                                  ifnone(generic_params.get("OutputId", ""), ""),
                                                  ifnone(generic_params.get("OutputSubFolder", ""), "")))
            indir = os.path.abspath(os.path.join(ifnone(generic_params.get("InputFolder", generic_params.get("Folder", "")), ""), 
                                                 ifnone(generic_params.get("InputId", ""), ""),
                                                 ifnone(generic_params.get("InputSubFolder", ""), "")))
            
            proc_id = proc_params.pop("id")
            process = proc_params.pop("__impl")(self._current_ivm, indir=indir, outdir=outdir, proc_id=proc_id)
            
            self._current_process = process
            self._current_params = proc_params
            process.sig_finished.connect(self._process_finished)
            process.sig_progress.connect(self._process_progress)
            process.sig_log.connect(self._process_log)
            
            self._process_start = time.time()
            if len(self._pipeline) > 1:
                self.log("Running %s\n\n" % process.proc_id)
            for key, value in proc_params.items():
                self.debug("      %s=%s" % (key, str(value)))

            self.sig_start_process.emit(process, dict(proc_params))
            process.execute(proc_params)
        
        except Exception as exc:
            # Could not create process - treat as process failure
            self._process_finished(Process.FAILED, "Process failed to start: " + str(exc), exc)
        finally:
            pass

    def _process_finished(self, status, log, exception):
        self.debug("Process finished: %s", self._current_process.proc_id)
        self._current_process.sig_finished.disconnect(self._process_finished)
        self._current_process.sig_progress.disconnect(self._process_progress)
        self._current_process.sig_log.disconnect(self._process_log)
        if self.status != self.RUNNING:
            return

        end = time.time()
        self.sig_done_process.emit(self._current_process, dict(self._current_params))
        
        if status == Process.SUCCEEDED:
            if len(self._pipeline) > 1:
                self.log("\nDONE (%.1fs)\n" % (end - self._process_start))
            self._output_items.extend(self._current_process.output_data_items())
            self._next_process()
        else:
            self.log("\nFAILED: %i\n" % status)
            if self._error_action == Script.IGNORE:
                self.debug("Process failed - ignoring")
                self._next_process()
            elif self._error_action == Script.FAIL:
                self.debug("Process failed - stopping script")
                self.status = status
                self.exception = exception
                self._current_process = None
                self._current_params = None
                self._complete()
            elif self._error_action == Script.NEXT_CASE:
                self.debug("Process failed - going to next case")
                self.log("CASE FAILED\n")
                self.sig_done_case.emit(self._current_case)
                self._next_case()

    def _process_progress(self, complete):
        self.sig_process_progress.emit(complete)
        script_complete = ((self._case_num-1)*len(self._pipeline) + 
                           (self._process_num - 1 + complete)) / (len(self._pipeline)*len(self._cases))
        self.sig_progress.emit(script_complete)

    def _process_log(self, msg):
        self.log(msg)
        
    def output_data_items(self):
        return self._output_items

class Case(object):
    """
    An individual case (e.g. patient scan) which a processing pipeline is applied to
    """
    def __init__(self, case_id, params):
        self.case_id = case_id
        if params is None:
            params = {}
        self.params = params
        # This would break compatibility so not for now
        #self.params["InputId"] = self.params.get("InputId", self.case_id)

class BatchScript(Script):
    """
    A Script which sends human readable output to a log stream. It also
    saves the logs of the processes to a file in the output folder.

    This is used as the runner for batch scripts started from the console
    or from the ``BatchBuilder`` widget.
    """
    def __init__(self, ivm=None, stdout=sys.stdout, **kwargs):
        Script.__init__(self, ivm, **kwargs)
        self.stdout = stdout
        self.start = None
        self._quit_on_exit = kwargs.get("quit_on_exit", True)

        self.sig_start_case.connect(self._log_start_case)
        self.sig_done_case.connect(self._log_done_case)
        self.sig_start_process.connect(self._log_start_process)
        self.sig_process_progress.connect(self._log_process_progress)
        self.sig_done_process.connect(self._log_done_process)
        self.sig_progress.connect(self._log_progress)
        self.sig_finished.connect(self._log_done_script)

    def _log_start_case(self, case):
        self.stdout.write("Processing case: %s\n" % case.case_id)

    def _log_done_case(self, case):
        pass

    def _log_start_process(self, process, params):
        self.start = time.time()
        self.stdout.write("  - Running %s...  0%%" % process.proc_id)
        for key, value in params.items():
            self.debug("      %s=%s" % (key, str(value)))
                
    def _log_done_process(self, process, params):
        if process.status == Process.SUCCEEDED:
            end = time.time()
            self.stdout.write(" DONE (%.1fs)\n" % (end - self.start))
            fname = os.path.join(process.outdir, "%s.log" % process.proc_id)
            self._save_text(process.get_log(), fname)
            if params:
                self.warn("Unused parameters")
                for key, val in params.items():
                    self.warn("%s=%s", str(key), str(val))
        else:
            self.stdout.write(" FAILED: %i\n" % process.status)
            self.warn(str(process.exception))
            self.debug(traceback.format_exc(process.exception))

    def _log_progress(self, complete):
        #self.stdout.write("%i%%\n" % int(100*complete))
        pass

    def _log_process_progress(self, complete):
        percent = int(100*complete)
        self.stdout.write("\b\b\b\b%3i%%" % percent)
        self.stdout.flush()

    def _log_done_script(self):
        self.stdout.write("Script finished\n")
        if self._quit_on_exit:
            QtCore.QCoreApplication.instance().quit()

    def _save_text(self, text, fname, ext="txt"):
        if text:
            if "." not in fname: fname = "%s.%s" % (fname, ext)
            dirname = os.path.dirname(fname)
            if not os.path.exists(dirname): os.makedirs(dirname)
            with open(fname, "w") as text_file:
                text_file.write(text)
