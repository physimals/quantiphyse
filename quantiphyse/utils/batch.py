"""
Quantiphyse - Implements the batch processing system for Quantiphyse

Copyright (c) 2013-2018 University of Oxford
"""

import sys
import os
import os.path
import errno
import traceback
import time

import yaml

from PySide import QtCore

from ..analysis import Process
from ..analysis.io import *
from ..analysis.misc import *

from ..volumes.volume_management import ImageVolumeManagement
from ..volumes.io import load, save

from . import debug, warn, get_debug, set_debug, get_plugins
from .exceptions import QpException

# Default basic processes - all others are imported from packages
BASIC_PROCESSES = {"RenameData"   : RenameDataProcess,
                   "RenameRoi"   : RenameRoiProcess,
                   "RoiCleanup" : RoiCleanupProcess,
                   "Load" : LoadProcess,
                   "Save" : SaveProcess,
                   "SaveAllExcept" : SaveAllExceptProcess,
                   "SaveAndDelete" : SaveDeleteProcess,
                   "LoadData" : LoadDataProcess,
                   "LoadRois" : LoadRoisProcess,
                   "SaveArtifacts" : SaveArtifactsProcess,
                   "SaveExtras" : SaveArtifactsProcess}

class Script(QtCore.QThread):
    """
    A processing scripts. It consists of three types of information:

     - Generic options (e.g. debug mode)
     - A single pipeline of processing steps
     - Optional list of BatchCase to apply these steps to

    A batch script can be run on a specified IVM, or it can be
    run on its cases. In this case a new IVM is created for
    each case
    """

    sig_start_case = QtCore.Signal(object)
    sig_done_case = QtCore.Signal(object)
    sig_start_process = QtCore.Signal(object, dict)
    sig_progress = QtCore.Signal()
    sig_done_process = QtCore.Signal(object, dict)
    sig_done = QtCore.Signal()

    def __init__(self, fname=None, code=None, yamlroot=None, ivm=None):
        """
        fname: File name containing YAML code to load from
        code: YAML code as a string
        yamlroot: Parsed YAML code as Python objects
        """
        super(Script, self).__init__()
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
                params["Id"] = params.get("Id", name)
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
                if case[case_id] is None: case[case_id] = {}
                self.cases.append(BatchScriptCase(case_id, yaml_cases[case_id]))
        
        # After removing processes and cases, remainder is the generic options
        self.generic_params = root

    def run(self):
        cases = self.cases
        if not cases:
            cases.append(BatchScriptCase("case", {}))

        try:
            for case in cases:
                self._sync_emit(self.sig_start_case, case)
                ivm = self.ivm
                if ivm is None:
                    ivm = ImageVolumeManagement()
                self.run_pipeline(ivm, case)
                self._sync_emit(self.sig_done_case, case)
        except:
            print("Exceptino")
            print(traceback.format_exc())
        finally:
            self.sig_done.emit()

    def run_pipeline(self, ivm, case):
        """
        Run the pipeline on a specified IVM, with optional case parameters 
        """
        for process in self.pipeline:            
            # Make copy so process does not mess up shared config
            proc_params = dict(process)
            generic_params = dict(self.generic_params)

            # Override values which are defined in the individual case
            if case is not None:
                case_params = dict(case.params)
                override = case_params.pop(proc_params["Id"], {})
                proc_params.update(override)
                generic_params.update(case_params)

            self.run_process(ivm, proc_params, generic_params)

    def run_process(self, ivm, proc_params, generic_params):
        debug_orig = get_debug()
        # Do not 'turn off' debugging if it has been enabled at higher level
        if generic_params.get("Debug", False): set_debug(True)

        try:
            outdir = os.path.abspath(os.path.join(generic_params.get("OutputFolder", ""), 
                                                  generic_params.get("OutputId", ""),
                                                  generic_params.get("OutputSubFolder", "")))
            indir = os.path.abspath(os.path.join(generic_params.get("InputFolder", generic_params.get("Folder", "")), 
                                                 generic_params.get("InputId", ""),
                                                 generic_params.get("InputSubFolder", "")))
            
            proc_id = proc_params.pop("Id")
            process = proc_params.pop("__impl")(ivm, indir=indir, outdir=outdir, proc_id=proc_id, sync=True)
            process.sig_progress.connect(self._process_progress)
            self._sync_emit(self.sig_start_process, process, dict(proc_params))  
            process.run(proc_params)
        except Exception as e:
            process.exception = e
            process.status = Process.FAILED
        finally:
            set_debug(debug_orig)
            self._sync_emit(self.sig_done_process, process, dict(proc_params))
                
    def _process_progress(self):
        pass
    
    def _sync_emit(self, sig, *args):
        """ Very ugly way to emit a signal synchronously """
        TIMEOUT = 200
        loop = QtCore.QEventLoop()
        sig.connect(loop.quit)
        sig.emit(*args)
        QtCore.QTimer.singleShot(TIMEOUT, loop.quit)
        loop.exec_()

class BatchScriptRunner:

    def __init__(self, fname, verbose=True, log=sys.stdout):
        self.script = Script(fname=fname)
        self.script.sig_start_case.connect(self._start_case)
        self.script.sig_done_case.connect(self._done_case)
        self.script.sig_start_process.connect(self._start_process)
        self.script.sig_done_process.connect(self._done_process)
        self.script.sig_done.connect(self._done_script)
        self.verbose = verbose
        self.log = log

    def run(self):
        self.script.start()

    def _start_case(self, case):
        self.log.write("Processing case: %s\n" % case.case_id)

    def _done_case(self, case):
        pass

    def _start_process(self, process, params):
        self.start = time.time()
        self.log.write("  - Running %s..." % process.proc_id)
        for key, value in params.items():
            debug("      %s=%s" % (key, str(value)))
                
    def _done_process(self, process, params):
        if process.status == Process.SUCCEEDED:
            end = time.time()
            self.log.write("DONE (%.1fs)\n" % (end - self.start))
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

class BatchScriptCase:
    def __init__(self, case_id, params):
        self.case_id = case_id
        self.params = params
        self.params["OutputId"] = self.params.get("OutputId", self.case_id)
        # This would break compatibility so not for now
        #self.params["InputId"] = self.params.get("InputId", self.case_id)

def parse_batch(fname=None, code=None, yamlroot=None):
    """ Parse a YAML batch file to return a list of cases and the processing pipeline """

    # Register packages processes FIXME use this mechanism for all processes

    if fname is not None:
        with open(fname, "r") as f:
            root = yaml.load(f)
    elif code is not None:
        root = yaml.load(code)
    elif yamlroot is not None:
        root = yamlroot
    else:
        raise RuntimeError("Neither filename nor YAML code provided")

    if root is None: 
        return []
    
    # Cases can be expressed as list or dict
    cases = root.get("Cases", [])
    ret = []
    if isinstance(cases, dict):
        for id in sorted(cases.keys()):
            ret.append(BatchCase(id, root, cases[id]))
    else:
        for case in cases:
            id = case.keys()[0]
            if case[id] is None: case[id] = {}
            ret.append(BatchCase(id, root, case[id]))
    return ret

def run_batch(fname=None, code=None):
    script = Script(fname=fname, code=code)
    runner = ScriptRunner(script)
    runner.run()

def _run_batch(fname=None, code=None):
    cases = parse_batch(fname=fname, code=code)
    for c in cases:
        c.run()

def check_batch(fname=None, code=None):
    warnings = set()
    cases = parse_batch(fname=fname, code=code)
    for c in cases:
        for w in c.check(): 
            warnings.add(w)
    return warnings

class BatchCase:
    def __init__(self, id, root, case):
        self.id = id
        self.root = root
        self.case = case
        if self.get("Debug", False): set_debug(True) # Don't override command line debug flag

        self.output_id = self.get("OutputId", id)
        self.indir = os.path.abspath(self.get("InputFolder", self.get("Folder", "")))
        self.outdir = os.path.abspath(os.path.join(self.get("OutputFolder", ""), self.output_id))
        self.ivm = ImageVolumeManagement()

    def get(self, param, default=None):
        return self.case.get(param, self.root.get(param, default))

    def chdir(self):
        cwd_prev = os.getcwd()
        if self.indir: os.chdir(self.indir)
        return cwd_prev

    def create_outdir(self):
        try:
            os.makedirs(self.outdir)
        except OSError as exc:
            if exc.errno == errno.EEXIST and os.path.isdir(self.outdir):
                warn("Output directory %s already exists" % self.outdir)
            else:
                raise

    def run_processing_steps(self):
        # Run processing steps
        for process in self.root.get("Processing", []):
            name = process.keys()[0]
            params = process[name]
            if params is None: params = {}
            
            # Make copy so process does not mess up shared config
            params = dict(params)

            # Override values which are defined in the individual case
            params.update(self.case.get(name, {}))

            self.run_process(name, params)

    def check(self):
        # Check specified processes exist
        ret = set()
        for process in self.root.get("Processing", []):
            name = process.keys()[0]
            proc = processes.get(name, None)
            if proc is None:
                ret.add("Unknown process: %s" % name)
        return ret

    def run_process(self, name, params):
        proc = processes.get(name, None)
        if proc is None:
            warn("Skipping unknown process: %s" % name)
        else:
            try:
                for key, value in params.items():
                    debug("      %s=%s" % (key, str(value)))
                process = proc(self.ivm, sync=True, indir=self.indir, outdir=self.outdir, name=params.get("name", name))
                #process.sig_progress.connect(self.progress)
                sys.stdout.write("  - Running %s..." % process.name)
                start = time.time()
                process.run(params)
                if process.status == Process.SUCCEEDED:
                    end = time.time()
                    process.log += "\nTOTAL DURATION: %.1fs" % (end-start)
                    print("DONE (%.1fs)" % (end-start))
                    self.save_text(process.log, process.name, "log")
                    if len(params) != 0:
                        warn("Unused parameters")
                        for k, v in params.items():
                            warn("%s=%s" % (str(k), str(v)))
                else:
                    raise process.exception
            except:
                print("FAILED")
                warn(str(sys.exc_info()[1]))
                debug(traceback.format_exc())
                
    #def progress(self, complete):
    #    sys.stdout.write("\b\b\b\b%3i%%" % int(complete*100))

    def save_text(self, text, fname, ext="txt"):
        if len(text) > 0:
            if "." not in fname: fname = "%s.%s" % (fname, ext)
            fname = os.path.join(self.outdir, fname)
            with open(fname, "w") as f:
                f.write(text)

    def run(self):
        print("Processing case: %s" % self.id)
        cwd_prev = self.chdir()
        self.create_outdir()
        self.run_processing_steps()
        os.chdir(cwd_prev)

        