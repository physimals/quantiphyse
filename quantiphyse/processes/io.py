"""
Quantiphyse - Processes for basic loading/saving of data

Copyright (c) 2013-2018 University of Oxford
"""

import os

from quantiphyse.utils import QpException
from quantiphyse.data import load, save

from .process import Process

__all__ = ["LoadProcess", "LoadDataProcess", "LoadRoisProcess", "SaveProcess", "SaveAllExceptProcess", "SaveDeleteProcess", "SaveArtifactsProcess"]

class LoadProcess(Process):
    """
    Load data into the IVM
    """
    def __init__(self, ivm, **kwargs):
        Process.__init__(self, ivm, **kwargs)

    def run(self, options):
        rois = options.pop('rois', {})
        data = options.pop('data', {})
        # Force 3D data to be multiple 2D volumes 
        force_mv = options.pop('force-multivol', False)

        for fname, name in list(data.items()) + list(rois.items()):
            qpdata = self._load_file(fname, name)
            if qpdata is not None: 
                if force_mv and qpdata.nvols == 1 and qpdata.grid.shape[2] > 1: 
                    qpdata.set_2dt()
                qpdata.roi = fname in rois
                self.ivm.add(qpdata, make_current=True)

    def _load_file(self, fname, name):
        filepath = self._get_filepath(fname)
        if name is None:
            name = self.ivm.suggest_name(os.path.split(fname)[1].split(".", 1)[0])
        self.debug("  - Loading data '%s' from %s" % (name, filepath))
        try:
            data = load(filepath)
            data.name = name
            return data
        except QpException as exc:
            self.warn("Failed to load data: %s (%s)" % (filepath, str(exc)))

    def _get_filepath(self, fname, folder=None):
        if os.path.isabs(fname):
            return fname
        else:
            if folder is None: folder = self.indir
            return os.path.abspath(os.path.join(folder, fname))

class LoadDataProcess(LoadProcess):
    """
    Process to load data

    Deprecated: use LoadProcess
    """
    def run(self, options):
        LoadProcess.run(self, {'data' : options})
        for key in list(options.keys()): options.pop(key)

class LoadRoisProcess(LoadProcess):
    """
    Process to load ROIs

    Deprecated: use LoadProcess
    """
    def run(self, options):
        LoadProcess.run(self, {'rois' : options})
        for key in list(options.keys()): options.pop(key)

class SaveProcess(Process):
    """
    Save data to file
    """
    def __init__(self, ivm, **kwargs):
        Process.__init__(self, ivm, **kwargs)

    def run(self, options):
        # Note that output-grid is not a valid data name so will not clash
        output_grid = None
        output_grid_name = options.pop("output-grid", None)
        if output_grid_name is not None:
            output_grid_data = self.ivm.data.get(output_grid_name, self.ivm.rois.get(output_grid_name, None))
            if output_grid_data is None:
                raise QpException("No such data found as source of grid: %s" % output_grid_name)
            else:
                output_grid = output_grid_data.grid

        for name in list(options.keys()):
            try:
                fname = options.pop(name, name)
                qpdata = self.ivm.data.get(name, None)
                if qpdata is not None:
                    save(qpdata, fname, grid=output_grid, outdir=self.outdir)
                else:
                    self.warn("Failed to save %s - no such data or ROI found" % name)
            except QpException as exc:
                self.warn("Failed to save %s: %s" % (name, str(exc)))

class SaveAllExceptProcess(Process):
    """
    Save all data to file apart from specified items
    """
    def __init__(self, ivm, **kwargs):
        Process.__init__(self, ivm, **kwargs)

    def run(self, options):
        exceptions = list(options.keys())
        for k in exceptions: options.pop(k)

        for name, qpdata in self.ivm.data.items():
            if name in exceptions: 
                continue
            try:
                save(qpdata, name, outdir=self.outdir)
            except QpException as exc:
                self.warn("Failed to save %s: %s" % (name, str(exc)))
            except:
                import traceback
                traceback.print_exc()

class SaveDeleteProcess(SaveProcess):
    """
    Save data to file and then delete it
    """
    def __init__(self, ivm, **kwargs):
        SaveProcess.__init__(self, ivm, **kwargs)

    def run(self, options):
        options_save = dict(options)
        SaveProcess.run(self, options)

        for name in options_save:
            if name in self.ivm.data: self.ivm.delete(name)

class SaveArtifactsProcess(Process):
    """
    Save 'extras' (previously known as 'artifacts')
    """
    def __init__(self, ivm, **kwargs):
        Process.__init__(self, ivm, **kwargs)

    def run(self, options):
        for name in list(options.keys()):
            fname = options.pop(name)
            if not fname: fname = name
            if name in self.ivm.extras: 
                self.debug("Saving '%s' to %s" % (name, fname))
                self._save_text(str(self.ivm.extras[name]), fname)
            else:
                self.warn("Extra '%s' not found - not saving" % name)

    def _save_text(self, text, fname, ext="txt"):
        if text:
            if "." not in fname: fname = "%s.%s" % (fname, ext)
            if not os.path.isabs(fname):
                fname = os.path.join(self.outdir, fname)
            dirname = os.path.dirname(fname)
            if not os.path.exists(dirname): os.makedirs(dirname)
            with open(fname, "w") as text_file:
                text_file.write(text)
