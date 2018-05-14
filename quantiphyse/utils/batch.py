"""
Quantiphyse - Implements the batch processing system for Quantiphyse

Copyright (c) 2013-2018 University of Oxford
"""

import sys
import os
import os.path
import traceback
import time

import yaml

from PySide import QtCore

from quantiphyse.processes import Process
from quantiphyse.processes.io import *
from quantiphyse.processes.misc import *

from quantiphyse.data import ImageVolumeManagement, load, save

from . import debug, warn, get_debug, set_debug, get_plugins
from .exceptions import QpException

# Default basic processes - all others are imported from packages
BASIC_PROCESSES = {"RenameData"   : RenameDataProcess,
                   "RenameRoi"   : RenameRoiProcess,
                   "Delete"   : DeleteProcess,
                   "RoiCleanup" : RoiCleanupProcess,
                   "Load" : LoadProcess,
                   "Save" : SaveProcess,
                   "SaveAllExcept" : SaveAllExceptProcess,
                   "SaveAndDelete" : SaveDeleteProcess,
                   "LoadData" : LoadDataProcess,
                   "LoadRois" : LoadRoisProcess,
                   "SaveArtifacts" : SaveArtifactsProcess,
                   "SaveExtras" : SaveArtifactsProcess}

class Script(Process):
    """
    A processing scripts. It consists of three types of information:

     - Generic options (e.g. debug mode)
     - A single pipeline of processing steps
     - Optional list of BatchCase objects to apply these steps to

    A batch script can be run on a specified IVM, or it can be
    run on its cases. In this case a new IVM is created for
    each case
    """

    sig_start_case = QtCore.Signal(object)
    sig_done_case = QtCore.Signal(object)
    sig_start_process = QtCore.Signal(object, dict)
    sig_process_progress = QtCore.Signal(float)
    sig_done_process = QtCore.Signal(object, dict)

    def __init__(self, fname=None, code=None, yamlroot=None, ivm=None):
        """
        fname: File name containing YAML code to load from
        code: YAML code as a string
        yamlroot: Parsed YAML code as Python objects
        """
        super(Script, self).__init__(ivm)
        if fname is not None:
            with open(fname, "r") as f:
                root = yaml.load(f)
        elif code is not None:
            root = yaml.load(code)
        elif yamlroot is not None:
            root = dict(yamlroot)
        else:
            raise RuntimeError("Neither filename nor YAML code provided")

        if root is None: 
            # Handle special case of empty content
            root = {}

        self.ivm = ivm
        self._current_process = None

        # Find all the process implementations
        processes = dict(BASIC_PROCESSES)
        plugin_processes = get_plugins("processes")
        for process in plugin_processes:
            processes[process.PROCESS_NAME] = process

        self.pipeline = []
        for process in root.pop("Processing", []):
            name = process.keys()[0]
            proc = processes.get(name, None)
            params = process[name]
            if params is None: params = {}

            if proc is None:
                raise QpException("Unknown process: %s" % name)
            else:
                params["id"] = params.get("id", name)
                params["__impl"] = proc
                self.pipeline.append(params)

        # Cases can be expressed as list or dict
        self.cases = []
        yaml_cases = root.pop("Cases", [])
        if isinstance(yaml_cases, dict):
            for case_id in sorted(yaml_cases.keys()):
                self.cases.append(BatchScriptCase(case_id, yaml_cases[case_id]))
        else:
            for case in yaml_cases:
                case_id = case.keys()[0]
                self.cases.append(BatchScriptCase(case_id, case.get(case_id, {})))
        
        # After removing processes and cases, remainder is the generic options
        self.generic_params = root

    def run(self):
        if not self.cases:
            self.cases.append(BatchScriptCase("case", {}))

        self.status = Process.RUNNING
        self._case_num = 0
        self._next_case()

    def cancel(self):
        if self._current_process is not None:
            self._current_process.cancel()
        
    def _next_case(self):
        if self.status != self.RUNNING:
            return
        
        if self._case_num < len(self.cases):
            case = self.cases[self._case_num]
            self._case_num += 1
            self.sig_start_case.emit(case)
            debug("Starting case %s" % case.case_id)
            self._start_case(case)
        else:
            debug("All cases complete")
            self.log += "COMPLETE\n"
            self.status = Process.SUCCEEDED
            self.sig_finished.emit(self.status, self.log, self.exception)

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
        
        if self._process_num < len(self.pipeline):
            process = self.pipeline[self._process_num]
            self._process_num += 1
            self._start_process(process)
        else:
            debug("All processes complete")
            self.log += "CASE COMPLETE\n"
            self.sig_done_case.emit(self._current_case)
            self._next_case()

    def _start_process(self, proc_params):
        # Make copy so process does not mess up shared config
        proc_params = dict(proc_params)
        generic_params = dict(self.generic_params)

        # Override values which are defined in the individual case
        if self._current_case is not None:
            case_params = dict(self._current_case.params)
            override = case_params.pop(proc_params["id"], {})
            proc_params.update(override)
            generic_params.update(case_params)

        #debug_orig = get_debug() FIXME

        # Do not 'turn off' debugging if it has been enabled at higher level
        if generic_params.get("Debug", False): set_debug(True)
        try:
            outdir = os.path.abspath(os.path.join(generic_params.get("OutputFolder", ""), 
                                                  generic_params.get("OutputId", ""),
                                                  generic_params.get("OutputSubFolder", "")))
            indir = os.path.abspath(os.path.join(generic_params.get("InputFolder", generic_params.get("Folder", "")), 
                                                 generic_params.get("InputId", ""),
                                                 generic_params.get("InputSubFolder", "")))
            
            proc_id = proc_params.pop("id")
            process = proc_params.pop("__impl")(self._current_ivm, indir=indir, outdir=outdir, proc_id=proc_id)
            self._current_process = process
            self._current_params = proc_params
            process.sig_finished.connect(self._process_finished)
            process.sig_progress.connect(self._process_progress)
            debug("Executing process %s" % proc_id)
            self.sig_start_process.emit(process, dict(proc_params))
            process.execute(proc_params)
        
        except Exception as e:
            # Could not create process - better abandon everything
            warn("Failed to create process - stopping script")
            traceback.print_exc(e)
            self.status = Process.FAILED
            self.exception = e
            self.sig_finished.emit(self.status, self.log, self.exception)
        finally:
            #set_debug(debug_orig)
            pass

    def _process_finished(self, status, log, exception):
        debug("Process finished", self._current_process.proc_id)
        if self.status != self.RUNNING:
            return

        self._current_process.sig_finished.disconnect(self._process_finished)
        self._current_process.sig_progress.disconnect(self._process_progress)
        self.log += log + "\n\n"
        self.sig_done_process.emit(self._current_process, dict(self._current_params))
        if status == Process.SUCCEEDED:
            self._next_process()
        else:
            debug("Process failed - stopping script")
            self.log += "FAILED\n"
            self.status = status
            self._current_process = None
            self._current_params = None
            self.sig_finished.emit(self.status, self.log, exception)

    def _process_progress(self, complete):
        self.sig_process_progress.emit(complete)
        script_complete = ((self._case_num-1)*len(self.pipeline) + 
                          (self._process_num - 1 + complete)) / (len(self.pipeline)*len(self.cases))
        self.sig_progress.emit(script_complete)

class BatchScriptCase:
    """
    An individual case (e.g. patient scan) which a processing pipeline is applied to
    """
    def __init__(self, case_id, params):
        self.case_id = case_id
        self.params = params
        self.params["OutputId"] = self.params.get("OutputId", self.case_id)
        # This would break compatibility so not for now
        #self.params["InputId"] = self.params.get("InputId", self.case_id)

class BatchScriptRunner:
    """
    Runs a batch script, sending human readable output to a log stream.

    This is used as the runner for batch scripts started from the console
    """

    def __init__(self, fname, verbose=True, log=sys.stdout):
        self.script = Script(fname=fname)
        self.script.sig_start_case.connect(self._start_case)
        self.script.sig_done_case.connect(self._done_case)
        self.script.sig_start_process.connect(self._start_process)
        self.script.sig_process_progress.connect(self._process_progress)
        self.script.sig_done_process.connect(self._done_process)
        self.script.sig_progress.connect(self._progress)
        self.script.sig_finished.connect(self._done_script)
        self.verbose = verbose
        self.log = log

    def run(self):
        self.script.run()

    def _start_case(self, case):
        self.log.write("Processing case: %s\n" % case.case_id)

    def _done_case(self, case):
        pass

    def _start_process(self, process, params):
        self.start = time.time()
        self.log.write("  - Running %s...  0%%" % process.proc_id)
        for key, value in params.items():
            debug("      %s=%s" % (key, str(value)))
                
    def _done_process(self, process, params):
        if process.status == Process.SUCCEEDED:
            end = time.time()
            self.log.write(" DONE (%.1fs)\n" % (end - self.start))
            fname = os.path.join(process.outdir, "%s.log" % process.proc_id)
            self._save_text(process.log, fname)
            if len(params) != 0:
                warn("Unused parameters")
                for k, v in params.items():
                    warn("%s=%s" % (str(k), str(v)))
        else:
            self.log.write("FAILED: %i\n" % process.status)
            warn(str(process.exception))
            debug(traceback.format_exc(process.exception))

    def _progress(self, complete):
        #self.log.write("%i%%\n" % int(100*complete))
        pass

    def _process_progress(self, complete):
        percent = int(100*complete)
        self.log.write("\b\b\b\b%3i%%" % percent)
        self.log.flush()

    def _done_script(self):
        self.log.write("Script finished\n")
        QtCore.QCoreApplication.instance().quit()

    def _save_text(self, text, fname, ext="txt"):
        if len(text) > 0:
            if "." not in fname: fname = "%s.%s" % (fname, ext)
            dirname = os.path.dirname(fname)
            if not os.path.exists(dirname): os.makedirs(dirname)
            with open(fname, "w") as f:
                f.write(text)
