import sys
import os
import warnings
import traceback

import numpy as np

from pkview.volumes.volume_management import Volume, Roi, Overlay
from pkview.analysis import Process, BackgroundProcess

try:
    if "FSLDIR" in os.environ: sys.path.append("%s/lib/python/" % os.environ["FSLDIR"])
    if "FABBERDIR" in os.environ: sys.path.append("%s/lib/python/" % os.environ["FABBERDIR"])
    from fabber import FabberLib, FabberRunData
except:
    # Stubs to prevent startup error - warning will occur if Fabber is used
    warnings.warn("Failed to import Fabber API - analysis will be disabled")
    traceback.print_exc()

def _make_fabber_progress_cb(id, queue):
    """ 
    Closure which can be used as a progress callback for the C API. Puts the 
    number of voxels processed onto the queue
    """
    def progress_cb(voxel, nvoxels):
        if (voxel % 100 == 0) or (voxel == nvoxels):
            queue.put((id, voxel, nvoxels))
    return progress_cb

def _run_fabber(id, queue, rundata, main_data, roi, *overlays):
    """
    Function to run Fabber in a multiprocessing environment
    """
    try:
        data = {"data" : main_data}
        n = 0
        while n < len(overlays):
            data[overlays[n]] = overlays[n+1]
            n += 2
        lib = FabberLib(rundata=rundata, auto_load_models=True)
        run = lib.run_with_data(rundata, data, roi, progress_cb=_make_fabber_progress_cb(id, queue))
        return id, True, run
    except:
        #print(sys.exc_info()[1])
        return id, False, sys.exc_info()[1]

class FabberProcess(BackgroundProcess):
    """
    Asynchronous background process to run Fabber
    """

    def __init__(self, ivm, **kwargs):
        BackgroundProcess.__init__(self, ivm, _run_fabber, **kwargs)

    def run(self, options):
        # FIXME rundata requires all arguments to be strings!
        rundata = FabberRunData()
        for key, value in options.items():
            if value is not None: rundata[key] = str(value)
            else: rundata[key] = ""
            
        # Pass in input data. To enable the multiprocessing module to split our volumes
        # up automatically we have to pass the arguments as a single list. This consists of
        # rundata, main data, roi and then each of the used overlays, name followed by data
        if self.ivm.current_roi is not None:
            roidata = self.ivm.current_roi.data
        else:
            roidata = None
        input_args = [rundata, self.ivm.vol.data, roidata]
        run_overlays = {}

        # This is not perfect - we just grab all overlays matching an option value
        for key, value in rundata.items():
            if value in self.ivm.overlays:
                input_args.append(value)
                input_args.append(self.ivm.overlays[value].data)

        if rundata["method"] == "spatialvb":
            # Spatial VB will not work properly in parallel
            n = 1
        else:
            # Run one worker for each slice
            n = self.ivm.vol.data.shape[0]

        if roidata is not None: self.voxels_todo = np.count_nonzero(self.ivm.current_roi.data)
        else: self.voxels_todo = self.ivm.vol.data.size

        self.voxels_done = [0, ] * n
        self.start(n, input_args)

    def timeout(self):
        if self.queue.empty(): return
        while not self.queue.empty():
            id, v, nv = self.queue.get()
            self.voxels_done[id] = v
        cv = sum(self.voxels_done)
        if self.voxels_todo > 0: complete = float(cv)/self.voxels_todo
        else: complete = 1
        self.sig_progress.emit(complete)

    def finished(self):
        """ Add output data to the IVM and set the combined log """
        self.log = ""
        if self.status == Process.SUCCEEDED:
            self.log = "\n\n".join([o.log for o in self.output])

            first = True
            for key in self.output[0].data:
                recombined_item = np.concatenate([o.data[key] for o in self.output], 0)
                ovl = Overlay(name=key, data=recombined_item)
                self.ivm.add_overlay(ovl, make_current=first)
                first = False
