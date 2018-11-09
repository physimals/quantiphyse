"""
Quantiphyse - Classes for interacting with external command line programs

Copyright (c) 2013-2018 University of Oxford
"""

import os
import sys
import shlex
import subprocess
import tempfile
import re
import shutil
import logging
import six

from quantiphyse.data import load, save
from quantiphyse.utils import QpException
from quantiphyse.processes import Process

LOG = logging.getLogger(__name__)

class OutputStreamMonitor(object):
    """
    Simple file-like object which listens to the output
    of a command and sends each line to a Queue
    """
    def __init__(self, queue, suppress_duplicates=True):
        self._queue = queue
        self._suppress_duplicates = suppress_duplicates
        self._last_line = None

    def write(self, text):
        """ Handle output from the process - send each line to the queue """
        lines = text.splitlines(True)
        for line in lines:
            if line != self._last_line:
                self._queue.put(line)
            if self._suppress_duplicates:
                self._last_line = line

    def flush(self):
        """ Ignore flush requests """
        pass

def _get_files(workdir):
    """
    Get a list of files currently in a working directory
    """
    dir_files = []
    for _, _, files in os.walk(workdir):
        for dir_file in files:
            if os.path.isfile(dir_file):
                dir_files.append(dir_file)
    return dir_files

def _run_cmd(worker_id, queue, workdir, cmdline, expected_data):
    """
    Multiprocessing worker to run a command in the background
    """
    try:
        pre_run_files = _get_files(workdir)

        cmd_args = shlex.split(cmdline, posix=not sys.platform.startswith("win"))
        os.chdir(workdir)
        log = ""
        proc = subprocess.Popen(cmd_args, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
        while 1:
            # This returns None while subprocess is running
            retcode = proc.poll() 
            line = proc.stdout.readline()
            log += line
            if queue: queue.put(line)
            if retcode is not None: break

        if retcode != 0:
            LOG.debug("External program failed: %s", cmdline)
            LOG.debug(log)
            raise QpException("Failed to execute %s: return code %i" % (cmd_args[0], retcode), detail=log)

        post_run_files = _get_files(workdir)
        new_files = [f for f in post_run_files if f not in pre_run_files]
        LOG.debug("New files: %s", new_files)
        data = []

        for new_file in new_files:
            basename = new_file.split(".", 1)[0]
            LOG.debug("Checking if we need to output: %s %s", basename, expected_data)
            if basename in expected_data or not expected_data:
                LOG.debug("Adding output file %s", new_file)
                if basename in expected_data:
                    data.append(new_file)
                else:
                    data.append(new_file)

        return worker_id, True, (log, data)
    except Exception as exc:
        import traceback
        traceback.print_exc(exc)
        return worker_id, False, exc

def apply_backspaces(s):
    while True:
        # if you find a character followed by a backspace, remove both
        t = re.sub('.\b', '', s, count=1)
        if len(s) == len(t):
            # now remove any backspaces from beginning of string
            return re.sub('\b+', '', t)
        s = t

class LogProcess(Process):
    """
    Process which produces a log stream which can be used to 
    monitor progress
    """
    def __init__(self, ivm, **kwargs):
        Process.__init__(self, ivm, **kwargs)
        self.expected_steps = []
        self.current_step = 0
        self.allow_skipping_steps = kwargs.pop("allow_skipping_steps", True)

    def timeout(self, queue):
        """ 
        Monitor queue for updates and send sig_progress 
        """
        if queue.empty(): return
        while not queue.empty():
            line = queue.get()
            # FIXME Some commands may use backspaces to show updating progress!
            self.log(line)
            self.debug(line.rstrip("\n"))
            check_step = self.current_step
            while check_step < len(self.expected_steps):
                # Expected steps can be string regexes, or tuple of (regex, description)
                expected, desc = self.expected_steps[check_step], None
                if not isinstance(expected, six.string_types):
                    expected, desc = expected

                if expected is not None and re.match(expected, line):
                    complete = float(check_step) / len(self.expected_steps)
                    self.current_step = check_step + 1
                    self.sig_progress.emit(complete)
                    if desc:
                        self.sig_step.emit(desc)
                    break
                if self.allow_skipping_steps:
                    check_step += 1

class CommandProcess(LogProcess):
    """
    Process which runs an external command in the background
    """
    def __init__(self, ivm, workdir=None, path=(), **kwargs):
        LogProcess.__init__(self, ivm, worker_fn=_run_cmd, **kwargs)
        self.path = path
        self._current_data = None
        self._current_roi = None

        if workdir is None:
            self.workdir = tempfile.mkdtemp(prefix="qp")
            self.workdir_istemp = True
        else:
            self.workdir = workdir
            self.workdir_istemp = False

    def __del__(self):
        if hasattr(self, "workdir_istemp") and self.workdir_istemp:
            try:
                shutil.rmtree(self.workdir)
            except:
                LOG.warn("Failed to remove temporary directory: %s", self.workdir)

    def add(self, data_name):
        """
        Add a data item to the working directory from the IVM
        """
        fname = os.path.join(self.workdir, data_name)
        save(self.ivm.data[data_name], fname)

    def finished(self, worker_output):
        """ 
        Add data to IVM and set log 

        Note that we need to call ``qpdata.raw()`` to make sure
        data is all loaded into memory as the files may be temporary
        """
        if self.status == Process.SUCCEEDED:
            log, data_files = worker_output[0]
            self.log(log)
            self.debug("Loading data: %s", data_files)
            for data_file in data_files:
                qpdata = load(os.path.join(self.workdir, data_file))
                qpdata.name = self.ivm.suggest_name(data_file.split(".", 1)[0], ensure_unique=False)
                qpdata.raw()
                self.ivm.add(qpdata, make_current=(data_file == self._current_data))

    def _get_cmdline(self, options):
        cmd = options.pop("cmd", None)
        if cmd is None:
            raise QpException("No command provided")

        cmdline = options.pop("cmdline", None)
        argdict = options.pop("argdict", {})
        if cmdline is None and not argdict:
            raise QpException("No command arguments provided")
            
        for arg, value in argdict.items():
            if value != "": 
                cmdline += " --%s=%s" % (arg, value)
            else:
                cmdline += " --%s" % arg
                
        cmd = self._find(cmd)
        cmdline = cmd + " " + cmdline
        LOG.debug(cmdline)
        return cmdline

    def run(self, options):
        """ 
        Run a program
        """
        cmdline = self._get_cmdline(options)

        expected_data = options.pop("output-data", [])

        self.expected_steps = options.pop("expected-steps", [None,])
        self.current_step = 0
        self._current_data = options.pop("set-current-data", None)
        self._current_roi = options.pop("set-current-roi", None)

        LOG.debug("Working directory: %s", self.workdir)
        self._add_data_from_cmdline(cmdline)

        worker_args = [self.workdir, cmdline, expected_data]
        self.start_bg(worker_args)
  
    def _find(self, cmd):
        """ 
        Find the program, either in the 'local' directory, or in $FSLDEVDIR/bin or $FSLDIR/bin 
        This is called each time the program is run so the caller can control where programs
        are searched for at any time
        """
        for bindir in self.path:
            ex = os.path.join(bindir, cmd)
            LOG.debug("Checking %s", ex)
            if os.path.isfile(ex) and os.access(ex, os.X_OK):
                return ex
            elif sys.platform.startswith("win"):
                ex += ".exe"
                if os.path.isfile(ex) and os.access(ex, os.X_OK):
                    return ex
            
        LOG.warn("Failed to find command line program: %s", cmd)
        return cmd
    
    def _add_data_from_cmdline(self, cmdline):
        """
        Add any data/roi item which match an argument to the working directory
        """
        for arg in re.split(r"\s+|=|,|\n|\t", cmdline):
            if arg in self.ivm.data:
                LOG.debug("Adding data from command line args: %s", arg)
                self.add(arg)
