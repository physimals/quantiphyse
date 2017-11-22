import os

from quantiphyse.utils import debug, warn
from quantiphyse.volumes.io import load, save

from . import Process

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
        for key in options.keys(): options.pop(key)

class LoadRoisProcess(LoadProcess):
    def run(self, options):
        LoadProcess.run(self, {'rois' : options})
        for key in options.keys(): options.pop(key)

class SaveProcess(Process):
    """
    Save data to file
    """
    def __init__(self, ivm, **kwargs):
        Process.__init__(self, ivm, **kwargs)

    def run(self, options):
        for name in options.keys():
            try:
                fname = options.pop(name)
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

class SaveAllExceptProcess(Process):
    """
    Save all data to file apart from specified items
    """
    def __init__(self, ivm, **kwargs):
        Process.__init__(self, ivm, **kwargs)

    def run(self, options):
        exceptions = [k for k in options.keys()]
        for k in options.keys(): options.pop(k)

        for name, qpdata in self.ivm.data.items():
            if name in exceptions: 
                continue
            try:
                fname = os.path.join(self.outdir, "%s.nii" % name)
                debug("Saving %s as %s" % (name, fname))
                save(qpdata, fname, self.ivm.main.rawgrid)
            except:
                warn("Failed to save %s" % name)
                raise

        for name, qpdata in self.ivm.rois.items():
            if name in exceptions: 
                continue
            try:
                fname = os.path.join(self.outdir, "%s.nii" % name)
                debug("Saving %s as %s" % (name, fname))
                save(qpdata, fname, self.ivm.main.rawgrid)
            except:
                warn("Failed to save %s" % name)
                raise

        self.status = Process.SUCCEEDED

class SaveDeleteProcess(SaveProcess):
    """
    Save data to file and then delete it
    """
    def __init__(self, ivm, **kwargs):
        Process.__init__(self, ivm, **kwargs)

    def run(self, options):
        SaveProcess.run(self, options)

        for name in options:
            if name in self.ivm.data: self.ivm.delete_data(name)
            if name in self.ivm.rois: self.ivm.delete_roi(name)

        self.status = Process.SUCCEEDED

class SaveArtifactsProcess(Process):
    """
    Save data to file and then delete it
    """
    def __init__(self, ivm, **kwargs):
        Process.__init__(self, ivm, **kwargs)

    def run(self, options):
        for name in options.keys():
            fname = options.pop(name)
            if not fname: fname = name
            if name in self.ivm.artifacts: 
                self._save_text(str(self.ivm.artifacts[name]), fname)
            else:
                warn("Artifact %s not found - not saving" % name)

        self.status = Process.SUCCEEDED

    def _save_text(self, text, fname, ext="txt"):
        if len(text) > 0:
            if "." not in fname: fname = "%s.%s" % (fname, ext)
            fname = os.path.join(self.workdir, fname)
            with open(fname, "w") as f:
                f.write(text)
