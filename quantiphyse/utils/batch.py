"""
Implements the batch processing system for Quantiphyse
"""
import sys
import os
import os.path
import errno
import traceback
import yaml
import time

from ..analysis import Process
from ..analysis.io import *
from ..analysis.misc import *

from ..volumes.volume_management import ImageVolumeManagement
from ..volumes.io import load, save

from . import debug, warn, set_debug, get_plugins
from .exceptions import QpException

# Default basic processes - all others are imported from packages
processes = {"RenameData"   : RenameDataProcess,
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

def parse_batch(fname=None, code=None):
    """ Run a YAML batch file """

    # Register packages processes FIXME use this mechanism for all processes
    plugin_procs = get_plugins("processes")
    for p in plugin_procs:
        processes[p.PROCESS_NAME] = p

    if fname is not None:
        with open(fname, "r") as f:
            root = yaml.load(f)
    elif code is not None:
        root = yaml.load(code)
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
        
    def get_filepath(self, fname, folder=None):
        if os.path.isabs(fname):
            return fname
        else:
            if folder is None: folder = self.indir
            return os.path.abspath(os.path.join(folder, fname))

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

    def run(self, checkonly=False):
        print("Processing case: %s" % self.id)
        cwd_prev = self.chdir()
        self.create_outdir()
        self.run_processing_steps()
        os.chdir(cwd_prev)

        