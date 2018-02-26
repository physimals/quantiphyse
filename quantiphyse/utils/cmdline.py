"""
Quantiphyse - Classes for interacting with external command line programs

Copyright (c) 2013-2018 University of Oxford
"""

import os
import sys
import shlex
import subprocess
import tempfile
import shutil
import re

from quantiphyse.volumes.io import load, save

from quantiphyse.utils import debug, warn
from quantiphyse.utils.exceptions import QpException

class Script:
    """
    Sequence of external programs sharing a common PATH and working directory

    FIXME unfinished, is this useful?
    """
    def __init__(self, ivm, path=[]):
        self.ivm = ivm
        self.path = path
        self.workdir = tempfile.mkdtemp(prefix="qpscript")
        self.cmds = []

    def add(cmd):
        """ 
        Add an ExternalProgram to the script
        """
        self.cmds.add(ExternalProgram(cmd, self.ivm, self.path))

    def __call__(self):
        for cmd in self.cmds:
            pass

class Workspace:
    def __init__(self, ivm, workdir=None, path=[]):
        print(ivm)
        self.ivm = ivm
        self.path = path

        if workdir is None:
            self.workdir = tempfile.mkdtemp(prefix="qp")
            self.workdir_istemp = True
        else:
            self.workdir = workdir
            self.workdir_istemp = False

    def add_data(self, data_name):
        fname = os.path.join(self.workdir, data_name)
        save(self.ivm.data.get(data_name, self.ivm.rois.get(data_name)), fname)

    def _find(self, cmd):
        """ 
        Find the program, either in the 'local' directory, or in $FSLDEVDIR/bin or $FSLDIR/bin 
        This is called each time the program is run so the caller can control where programs
        are searched for at any time
        """
        for d in self.path:
            ex = os.path.join(d, cmd)
            debug("Checking %s" % ex)
            if os.path.isfile(ex) and os.access(ex, os.X_OK):
                return ex
            elif sys.platform.startswith("win"):
                ex += ".exe"
                if os.path.isfile(ex) and os.access(ex, os.X_OK):
                    return ex
            
        warn("Failed to find command line program: %s" % cmd)
        return cmd
    
    def _add_data_from_cmdline(self, cmdline):
        """
        Add any data/roi item which match an argument to the working directory
        """
        print("cmdline=", cmdline)
        for arg in re.split("\s+|=|,|\n|\t", cmdline):
            print("arg=", arg)
            if arg in self.ivm.data or arg in self.ivm.rois:
                print("Adding data ", arg)
                self.add_data(arg)

    def _get_files(self):
        """
        Get a list of files currently in working directory
        """
        files = []
        for _, _, fs in os.walk(self.workdir):
            for f in fs:
                if os.path.isfile(f):
                    files.append(f)
        return files

    def run(self, cmd, argline="", argdict={}, output_data={}, output_rois={}, **kwargs):
        """ Run a program in the workspace """
        cwd = os.getcwd()

        debug("Working directory: %s" % self.workdir)
        os.chdir(self.workdir)
        try:
            cmd = self._find(cmd)
            print(cmd)

            cmd_args = shlex.split(cmd + " " + argline, posix=not sys.platform.startswith("win"))
            print(cmd_args)
            for arg, value in argdict.items():
                cmd_args.append(arg)
                if value != "": cmd_args.append(value)
            cmdline = " ".join(cmd_args)
            debug(cmdline)
            self._add_data_from_cmdline(cmdline)
            pre_run_contents = self._get_files()

            out = ""
            p = subprocess.Popen(cmd_args, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
            while 1:
                # This returns None while subprocess is running
                retcode = p.poll() 
                line = p.stdout.readline()
                out += line
                if retcode is not None: break

            if retcode != 0:
                debug("External program failed: %s" % cmd)
                debug(out)
                raise QpException("Failed to execute %s: return code %i" % (cmd, retcode), detail=out)
            
            post_run_contents = self._get_files()
            new_files = [f for f in post_run_contents if f not in pre_run_contents]
            for f in new_files:
                basename = f.split(".", 1)[0]
                print("Looking for", basename, output_data, output_rois)
                if basename in output_data or basename in output_rois or (len(output_data) == 0 and len(output_rois) == 0):
                    debug("Loading output file %s" % f)
                    try:
                        qpdata = load(f)
                        if basename in output_data:
                            qpdata.name = output_data.get(basename)
                            self.ivm.add_data(qpdata)
                        elif basename in output_rois:
                            qpdata.name = output_rois.get(basename)
                            self.ivm.add_roi(qpdata)
                        else:
                            qpdata.name = basename
                            self.ivm.add_data(qpdata)

                        # Make sure data is loaded as file is temporary
                        qpdata.std()
                    except:
                        warn("Error loading output file %s" % f)
                        traceback.print_exc()

            debug("New files: ", new_files)
        finally:
           os.chdir(cwd)
        
        return out

class ExternalProgram:
    def __init__(self, cmd, ivm, path=[]):
        self.ivm = ivm
        self.cmd = self._find(cmd, path)
        self.workdir_istemp = False

    def _find(self, cmd, path):
        """ 
        Find the program, either in the 'local' directory, or in $FSLDEVDIR/bin or $FSLDIR/bin 
        This is called each time the program is run so the caller can control where programs
        are searched for at any time
        """
        for d in path:
            ex = os.path.join(d, cmd)
            debug("Checking %s" % ex)
            if os.path.isfile(ex) and os.access(ex, os.X_OK):
                return ex
        
        warn("Failed to find command line program: %s" % cmd)
        return cmd
    
    def _prepare_workspace(self, ivm, data=[], path=None):
        if path is None:
            path = tempfile.mkdtemp(prefix="qp")
            istemp = True
        else:
            istemp = False

        for d in data:
            if d in ivm.data:
                save(ivm.data[d], os.path.join(path, "%s.nii.gz" % d), ivm.save_grid)
            elif d in ivm.rois:
                save(ivm.rois[d],  os.path.join(path, "%s.nii.gz" % d), ivm.save_grid)
        return path, istemp

    def __call__(self, argline="", argdict={}, workdir=None, data=[], 
                 outdata={}, outrois={}, outextras={}, **kwargs):
        """ Run, writing output to stdout and returning retcode """
        cwd = os.getcwd()
        workdir, istemp = self._prepare_workspace(self.ivm, data, path=workdir)
        debug("Working directory: %s" % workdir)
        os.chdir(workdir)
        try:
            cmd_args = shlex.split(self.cmd + " " + argline)
            for arg, value in argdict.items():
                cmd_args.append(arg)
                if value != "": cmd_args.append(value)

            out = ""
            debug(" ".join(cmd_args))
            p = subprocess.Popen(cmd_args, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
            while 1:
                # This returns None while subprocess is running
                retcode = p.poll() 
                line = p.stdout.readline()
                out += line
                if retcode is not None: break

            if retcode != 0:
                debug("External program failed: %s" % self.cmd)
                debug(out)
                raise QpException("Failed to execute %s: return code %i" % (self.cmd, retcode), detail=out)
            else:
                for dname, fname in outdata.items():
                    path = os.path.join(workdir, fname)
                    d = load(path)
                    self.ivm.add_data(d, name=dname)
                for dname, fname in outrois.items():
                    path = os.path.join(workdir, fname)
                    d = load(path)
                    self.ivm.add_roi(d, name=dname)
                for dname, fname in outextras.items():
                    path = os.path.join(workdir, fname)
                    with open(path) as f:
                        self.ivm.add_extra(dname, f.read())
                
                return out
        finally:
            if istemp:
                try:
                    shutil.rmtree(workdir)
                except:
                    warn("Failed to delete temp dir: %s" % sys.exc_info()[1])
            os.chdir(cwd)
