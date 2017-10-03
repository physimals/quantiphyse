import os

from PySide import QtGui

from . import Process
from ..utils import debug, warn
from ..volumes.io import load, save

class LoadProcess(Process):
    """
    Load data into the IVM
    """
    def __init__(self, ivm, **kwargs):
        Process.__init__(self, ivm, **kwargs)

    def run(self, options):
        rois = options.pop('rois', {})
        data = options.pop('data', {})

        for fname, name in rois.items():
            qpdata = self._load_file(fname, name)
            if qpdata is not None: self.ivm.add_roi(qpdata, make_current=True)

        for fname, name in data.items():
            qpdata = self._load_file(fname, name)
            if qpdata is not None: self.ivm.add_data(qpdata, make_current=True)

        self.status = Process.SUCCEEDED

    def _load_file(self, fname, name):
        filepath = self._get_filepath(fname)
        if name is None:
            name = self.ivm.suggest_name(os.path.split(fname)[1].split(".", 1)[0])
        debug("  - Loading data '%s' from %s" % (name, filepath))
        try:
            data = load(filepath)
            data.name = name
            return data
        except:
            warn("Failed to load data: %s" % filepath)

    def _get_filepath(self, fname, folder=None):
        if os.path.isabs(fname):
            return fname
        else:
            if folder is None: folder = self.workdir
            return os.path.abspath(os.path.join(folder, fname))

class LoadDataProcess(LoadProcess):
    def run(self, options):
        LoadProcess.run(self, {'data' : options})

class LoadRoisProcess(LoadProcess):
    def run(self, options):
        LoadProcess.run(self, {'rois' : options})

class SaveProcess(Process):
    """
    Save data to file
    """
    def __init__(self, ivm, **kwargs):
        Process.__init__(self, ivm, **kwargs)

    def run(self, options):
        for name, fname in options.items():
            try:
                if fname is None: fname = name
                qpdata = self.ivm.data.get(name, self.ivm.rois.get(name, None))
                if qpdata is not None:
                    if not fname.endswith(".nii"): 
                        fname += ".nii"
                    if not os.path.isabs(fname):
                        fname = os.path.join(self.outdir, fname)
                    debug("Saving %s as %s" % (name, fname))
                    save(qpdata, fname, self.ivm.main.rawgrid)
                else:
                    warn("Failed to save %s - no such data or ROI found" % name)
            except:
                warn("Failed to save %s" % name)
                raise

        self.status = Process.SUCCEEDED
