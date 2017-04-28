"""
Implements the batch processing system for Quantiphyse
"""
import os
import os.path
import errno
import traceback
import yaml

from pkview.volumes.volume_management import ImageVolumeManagement, Volume, Overlay, Roi

from pkview.analysis import Process
from pkview.analysis.fab import FabberProcess
from pkview.analysis.reg import MocoProcess, RegProcess, McflirtProcess
from pkview.analysis.pk import PkModellingProcess
from pkview.analysis.t10 import T10Process
from pkview.analysis.sv import SupervoxelsProcess

processes = {"Fabber"      : FabberProcess,
             "MCFlirt"     : McflirtProcess,
             "T10"         : T10Process,
             "Supervoxels" : SupervoxelsProcess,
             "PkModelling" : PkModellingProcess,
             "Reg"         : RegProcess,
             "Moco"        : MocoProcess}

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
                print("WARNING: Output directory %s already exists" % self.outdir)
            else:
                raise

    def load_volume(self):
        # Load main volume      
        vol_file = self.get("Volume", None)
        if vol_file is None:
            raise RuntimeError("No main volume defined")

        vol = Volume(os.path.basename(vol_file), fname=self.get_filepath(vol_file))
        multi = True
        if vol.ndims == 2:
                multi = False
        if vol.ndims == 3:
            multi = self.get("MultiVolumes", False)
        elif vol.ndims != 4:
            raise RuntimeError("Main volume is invalid number of dimensions: %i" % vol.ndims)
        vol.force_ndims(4, multi=multi)
        self.ivm.set_main_volume(vol)

    def load_overlays(self):
        # Load case overlays followed by any root overlays not overridden by case
        overlays = self.case.get("Overlays", {})
        overlays.update(self.root.get("Overlays", {}))
        for key in overlays:
            filepath = self.get_filepath(overlays[key])
            if self.debug: print("  - Loading overlay '%s' from %s" % (key, filepath))
            self.ivm.add_overlay(Overlay(key, fname=filepath), make_current=True)
        
    def load_rois(self):
        # Load case ROIs followed by any root ROIs not overridden by case
        rois = self.case.get("Rois", {})
        rois.update(self.root.get("Rois", {}))
        for key in rois:
            filepath = self.get_filepath(rois[key])
            if self.debug: print("  - Loading ROI '%s' from %s" % (key, filepath))
            self.ivm.add_roi(Roi(key, fname=filepath), make_current=True)
        
    def run_processing_steps(self):
        # Run processing steps
        for process in self.root.get("Processing", []):
            name = process.keys()[0]
            params = {"Debug" : self.debug, "Folder" : self.folder, "OutputFolder" : self.outdir}
            params.update(process[name])
            params.update(self.case.get(name, {}))
            self.run_process(name, params)

    def run_process(self, name, params):
        proc = processes.get(name, None)
        if proc is None:
            print("  - WARNING: skipping unknown process: %s" % name)
        else:
            print("  - Running %s" % name)
        if self.debug:
            for key, value in params.items():
                print("      %s=%s" % (key, str(value)))
        try:
            process.run(params)
            if process.status == Process.SUCCEEDED:
                self.write_log(process.log, name)
            else:
                raise process.output
        except:
            print("  - WARNING: process %s failed to run" % name)
            traceback.print_exc()

    def write_log(self, log, procname):
        fname = os.path.join(self.outdir, "%s.log" % procname)
        with open(fname, "w") as f:
            f.write(log)

    def save_output(self):
        print(self.root)
        if "SaveVolume" in self.root:
            fname = self.root["SaveVolume"]
            if not fname: fname = self.ivm.vol.name
            self.save_data(self.ivm.vol, fname)

        for name, fname in self.get("SaveOverlays", {}).items():
            if not fname: fname = name
            self.save_data(self.ivm.overlays[name], fname)

        for name, fname in self.get("SaveRois", {}).items():
            if not fname: fname = name
            self.save_data(self.ivm.rois[name], fname)

    def save_data(self, vol, fname):
        if not fname.endswith(".nii"): 
            fname += ".nii"
        if not os.path.isabs(fname):
            fname = os.path.join(self.outdir, fname)
        print("  - Saving %s" % fname)
        vol.save_nifti(fname)

    def run(self):
        print("Processing case: %s" % self.id)
        self.create_outdir()
        self.load_volume()
        self.load_overlays()
        self.load_rois()
        self.run_processing_steps()
        self.save_output()
        