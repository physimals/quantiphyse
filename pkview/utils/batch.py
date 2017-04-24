import yaml
import nibabel as nib
import os.path
import errno
import os
import traceback

from pkview.volumes.volume_management import ImageVolumeManagement, Volume, Overlay, Roi
import pkview.widgets.FabberWidgets as Fabber
import pkview.widgets.MCWidgets as Motion
import pkview.widgets.T10Widgets as T10
import pkview.widgets.PerfSlicWidgets as SV
import pkview.widgets.PharmaWidgets as Pk

processes = {"Fabber" : Fabber.run_batch,
             "MCFlirt": Motion.run_mcflirt_batch,
             "T10" : T10.run_batch,
             "Supervoxels" : SV.run_batch,
             "PkModelling" : Pk.run_batch}

class BatchCase:
    def __init__(self, id, root, case):
        self.id = id
        self.root = root
        self.case = case
        self.debug = self.get("Debug", False)
        self.outdir = os.path.join(self.get("OutputFolder", ""), id)
        self.ivm = ImageVolumeManagement()
        
    def get_filepath(self, fname, folder=None):
        if os.path.isabs(fname):
            return fname
        else:
            if folder is None: folder = self.get("Folder")
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
            params = process[name]
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
            log = proc(self, params)
            self.write_log(log, name)
        except:
            traceback.print_exc()

    def write_log(self, log, procname):
        fname = os.path.join(self.outdir, "%s.log" % procname)
        with open(fname, "w") as f:
            f.write(log)

    def save_output(self):
        # Save Output
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
        
def run_batch(batchfile):
    with open(batchfile, "r") as f:
        root = yaml.load(f)
        for id, case in root["Cases"].items():
            c = BatchCase(id, root, case)
            c.run()
