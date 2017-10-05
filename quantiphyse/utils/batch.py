"""
Implements the batch processing system for Quantiphyse
"""
import sys
import os
import os.path
import errno
import traceback
import yaml

from ..analysis import Process
from ..analysis.fab import FabberProcess
from ..analysis.reg import RegProcess, McflirtProcess
from ..analysis.pk import PkModellingProcess
from ..analysis.t10 import T10Process
from ..analysis.sv import SupervoxelsProcess, Supervoxels4DProcess
from ..analysis.io import *
from ..analysis.misc import *
from ..analysis.kmeans import KMeansPCAProcess, KMeans3DProcess

from ..volumes.volume_management import ImageVolumeManagement
from ..volumes.io import load, save

from . import debug, warn, set_debug

processes = {"Fabber"      : FabberProcess,
             "MCFlirt"     : McflirtProcess,
             "T10"         : T10Process,
             "Supervoxels" : SupervoxelsProcess,
             "PkModelling" : PkModellingProcess,
             "Reg"         : RegProcess,
             "Moco"        : RegProcess,
             "CalcVolumes" : CalcVolumesProcess,
             "OverlayStats" : OverlayStatisticsProcess,
             "RadialProfile" : RadialProfileProcess,
             "Histogram" : HistogramProcess,
             "KMeansPCA"   : KMeansPCAProcess,
             "KMeans3D"   : KMeans3DProcess,
             "MeanValues"   : MeanValuesProcess,
             "RenameData"   : RenameDataProcess,
             "RenameRoi"   : RenameRoiProcess,
             "SimpleMaths" : ExecProcess,
             "Exec" : ExecProcess,
             "RoiCleanup" : RoiCleanupProcess,
             "Load" : LoadProcess,
             "Save" : SaveProcess,
             "SaveAndDelete" : SaveDeleteProcess,
             "LoadData" : LoadDataProcess,
             "LoadRois" : LoadRoisProcess,
             "SaveArtifacts" : SaveArtifactsProcess}

def run_batch(batchfile):
    """ Run a YAML batch file """
    with open(batchfile, "r") as f:
        root = yaml.load(f)
        for id, case in root["Cases"].items():
            c = BatchCase(id, root, case)
            c.run()

class BatchCase:
    def __init__(self, id, root, case):
        self.id = id
        self.root = root
        self.case = case
        if self.get("Debug", False): set_debug(True) # Don't override command line debug flag
        self.folder = self.get("Folder", "")
        self.output_id = self.get("OutputId", id)
        self.outdir = os.path.join(self.get("OutputFolder", ""), self.output_id)
        self.ivm = ImageVolumeManagement()
        
    def get_filepath(self, fname, folder=None):
        if os.path.isabs(fname):
            return fname
        else:
            if folder is None: folder = self.folder
            return os.path.abspath(os.path.join(folder, fname))

    def get(self, param, default=None):
        return self.case.get(param, self.root.get(param, default))

    def create_outdir(self):
        try:
            os.makedirs(self.outdir)
        except OSError as exc:
            if exc.errno == errno.EEXIST and os.path.isdir(self.outdir):
                warn("Output directory %s already exists" % self.outdir)
            else:
                raise

    def load_volume(self):
        # Load main volume      
        vol_file = self.get("Volume", None)
        if vol_file is not None:
            vol = load(self.get_filepath(vol_file)).get_data()
            multi = True
            if vol.ndim == 2:
                    multi = False
            if vol.ndim == 3:
                multi = self.get("MultiVolumes", False)
            elif vol.ndim != 4:
                raise RuntimeError("Main volume is invalid number of dimensions: %i" % vol.ndim)
            self.ivm.add_overlay(self.ivm.suggest_name(vol.md.basename), vol, make_main=True)

    def load_overlays(self):
        # Load case overlays followed by any root overlays not overridden by case
        overlays = self.case.get("Overlays", {})
        overlays.update(self.root.get("Overlays", {}))
        for key in overlays:
            filepath = self.get_filepath(overlays[key])
            debug("  - Loading data '%s' from %s" % (key, filepath))
            try:
                ovl = load(filepath)
                ovl.name = key
                self.ivm.add_data(ovl, make_current=True)
            except:
                warn("Failed to load data: %s" % filepath)
                
    def load_rois(self):
        # Load case ROIs followed by any root ROIs not overridden by case
        rois = self.case.get("Rois", {})
        rois.update(self.root.get("Rois", {}))
        for key in rois:
            filepath = self.get_filepath(rois[key])
            debug("  - Loading ROI '%s' from %s" % (key, filepath))
            try:
                roi = load(filepath)
                roi.name = key
                self.ivm.add_roi(roi, make_current=True)
            except:
                warn("Failed to load ROI: %s" % filepath)

    def run_processing_steps(self):
        # Run processing steps
        for process in self.root.get("Processing", []):
            name = process.keys()[0]
            params = process[name]
            if params is None: params = {}
            params = dict(params) # Make copy so process does not mess up shared config
            params.update(self.case.get(name, {}))
            self.run_process(name, params)

    def run_process(self, name, params):
        proc = processes.get(name, None)
        if proc is None:
            warn("Skipping unknown process: %s" % name)
        else:
            try:
                for key, value in params.items():
                    debug("      %s=%s" % (key, str(value)))
                process = proc(self.ivm, sync=True)
                process.workdir = self.folder
                process.outdir = self.outdir
                process.name = params.get("name", name)
                #process.sig_progress.connect(self.progress)
                sys.stdout.write("  - Running %s..." % process.name)
                process.run(params)
                if process.status == Process.SUCCEEDED:
                    print("DONE")
                    self.save_text(process.log, process.name, "log")
                else:
                    raise process.output
            except:
                print("FAILED")
                warn(str(sys.exc_info()[1]))
                debug(traceback.format_exc())
                
    def progress(self, complete):
        sys.stdout.write("\b\b\b\b%3i%%" % int(complete*100))

    def save_text(self, text, fname, ext="txt"):
        if len(text) > 0:
            if "." not in fname: fname = "%s.%s" % (fname, ext)
            fname = os.path.join(self.outdir, fname)
            with open(fname, "w") as f:
                f.write(text)

    def save_output(self):
        if "SaveVolume" in self.root:
            fname = self.root["SaveVolume"]
            if not fname: fname = self.ivm.main.name
            self.save_data(self.ivm.main, fname)

        for name, fname in self.get("SaveOverlays", {}).items():
            if not fname: fname = name
            if name in self.ivm.data:
                self.save_data(self.ivm.data[name], fname)
            else:
                warn("Overlay %s not found - not saving" % name)

        for name, fname in self.get("SaveRois", {}).items():
            if not fname: fname = name
            if name in self.ivm.rois:
                self.save_data(self.ivm.rois[name], fname)
            else:
                warn("ROI %s not found - not saving" % name)

        for name, fname in self.get("SaveArtifacts", {}).items():
            if not fname: fname = name
            if name in self.ivm.artifacts:
                self.save_text(str(self.ivm.artifacts[name]), fname)
            else:
                warn("Artifact %s not found - not saving" % name)

    def save_data(self, vol, fname):
        if not fname.endswith(".nii"): 
            fname += ".nii"
        if not os.path.isabs(fname):
            fname = os.path.join(self.outdir, fname)
        print("  - Saving %s" % fname)
        save(vol, fname, self.ivm.main.rawgrid)

    def run(self):
        print("Processing case: %s" % self.id)
        self.create_outdir()
        self.load_volume()
        self.load_overlays()
        self.load_rois()
        self.run_processing_steps()
        self.save_output()
        