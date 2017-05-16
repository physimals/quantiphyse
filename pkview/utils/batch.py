"""
Implements the batch processing system for Quantiphyse
"""
import sys
import os
import os.path
import errno
import traceback
import yaml

from pkview.analysis import Process
from pkview.analysis.fab import FabberProcess
from pkview.analysis.reg import RegProcess, McflirtProcess
from pkview.analysis.pk import PkModellingProcess
from pkview.analysis.t10 import T10Process
from pkview.analysis.sv import SupervoxelsProcess
from pkview.analysis.misc import CalcVolumesProcess

from pkview.volumes.volume_management import ImageVolumeManagement
from pkview.volumes.io import load, save

processes = {"Fabber"      : FabberProcess,
             "MCFlirt"     : McflirtProcess,
             "T10"         : T10Process,
             "Supervoxels" : SupervoxelsProcess,
             "PkModelling" : PkModellingProcess,
             "Reg"         : RegProcess,
             "Moco"        : RegProcess,
             "CalcVolumes" : CalcVolumesProcess}

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
        self.debug = self.get("Debug", False)
        self.folder = self.get("Folder", "")
        self.outdir = os.path.join(self.get("OutputFolder", ""), id)
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
                print("  - WARNING: Output directory %s already exists" % self.outdir)
            else:
                raise

    def load_volume(self):
        # Load main volume      
        vol_file = self.get("Volume", None)
        if vol_file is None:
            raise RuntimeError("No main volume defined")

        vol = load(self.get_filepath(vol_file))
        multi = True
        if vol.ndim == 2:
                multi = False
        if vol.ndim == 3:
            multi = self.get("MultiVolumes", False)
        elif vol.ndim != 4:
            raise RuntimeError("Main volume is invalid number of dimensions: %i" % vol.ndim)
        self.ivm.add_overlay(vol.md.name, vol, make_main=True)

    def load_overlays(self):
        # Load case overlays followed by any root overlays not overridden by case
        overlays = self.case.get("Overlays", {})
        overlays.update(self.root.get("Overlays", {}))
        for key in overlays:
            filepath = self.get_filepath(overlays[key])
            if self.debug: print("  - Loading overlay '%s' from %s" % (key, filepath))
            ovl = load(filepath)
            self.ivm.add_overlay(key, ovl, make_current=True)
        
    def load_rois(self):
        # Load case ROIs followed by any root ROIs not overridden by case
        rois = self.case.get("Rois", {})
        rois.update(self.root.get("Rois", {}))
        for key in rois:
            filepath = self.get_filepath(rois[key])
            if self.debug: print("  - Loading ROI '%s' from %s" % (key, filepath))
            roi = load(filepath)
            self.ivm.add_roi(key, roi, make_current=True)
        
    def run_processing_steps(self):
        # Run processing steps
        for process in self.root.get("Processing", []):
            name = process.keys()[0]
            params = process[name]
            params.update(self.case.get(name, {}))
            self.run_process(name, params)

    def run_process(self, name, params):
        proc = processes.get(name, None)
        if proc is None:
            print("  - WARNING: skipping unknown process: %s" % name)
        else:
            try:
                if self.debug:
                    for key, value in params.items():
                        print("      %s=%s" % (key, str(value)))
                process = proc(self.ivm, sync=True)
                process.debug = self.debug
                process.workdir = self.folder
                process.outdir = self.outdir
                #process.sig_progress.connect(self.progress)
                sys.stdout.write("  - Running %s   0%%" % name)
                process.run(params)
                print("\b\b\b\bDONE")
                if process.status == Process.SUCCEEDED:
                    self.save_text(process.log, name, "log")
                else:
                    raise process.output
            except:
                print("  - WARNING: process %s failed to run" % name)
                traceback.print_exc()

    def progress(self, complete):
        sys.stdout.write("\b\b\b\b%3i%%" % int(complete*100))

    def save_text(self, text, fname, ext="txt"):
        fname = os.path.join(self.outdir, "%s.%s" % (fname, ext))
        with open(fname, "w") as f:
            f.write(text)

    def save_output(self):
        if "SaveVolume" in self.root:
            fname = self.root["SaveVolume"]
            if not fname: fname = self.ivm.vol.md.name
            self.save_data(self.ivm.vol, fname)

        for name, fname in self.get("SaveOverlays", {}).items():
            if not fname: fname = name
            if name in self.ivm.overlays:
                self.save_data(self.ivm.overlays[name], fname)
            else:
                print("  - WARNING: overlay %s not found - not saving" % name)

        for name, fname in self.get("SaveRois", {}).items():
            if not fname: fname = name
            if name in self.ivm.rois:
                self.save_data(self.ivm.rois[name], fname)
            else:
                print("  - WARNING: ROI %s not found - not saving" % name)

        for name, fname in self.get("SaveArtifacts", {}).items():
            if not fname: fname = name
            if name in self.ivm.artifacts:
                self.save_text(str(self.ivm.artifacts[name]), fname)
            else:
                print("  - WARNING: Artifact %s not found - not saving" % name)

    def save_data(self, vol, fname):
        if not fname.endswith(".nii"): 
            fname += ".nii"
        if not os.path.isabs(fname):
            fname = os.path.join(self.outdir, fname)
        print("  - Saving %s" % fname)
        save(vol, fname)

    def run(self):
        print("Processing case: %s" % self.id)
        self.create_outdir()
        self.load_volume()
        self.load_overlays()
        self.load_rois()
        self.run_processing_steps()
        self.save_output()
        