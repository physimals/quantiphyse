import sys
import os
import warnings
import traceback

import numpy as np

from quantiphyse.analysis import Process, BackgroundProcess
from quantiphyse.utils import debug, warn
from quantiphyse.utils.exceptions import QpException

try:
    if "FSLDIR" in os.environ: sys.path.append("%s/lib/python/" % os.environ["FSLDIR"])
    if "FABBERDIR" in os.environ: sys.path.append("%s/lib/python/" % os.environ["FABBERDIR"])
    from fabber import find_fabber, FabberLib, FabberRunData, LibRun
except:
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

def _run_fabber(id, queue, rundata, main_data, roi, *add_data):
    """
    Function to run Fabber in a multiprocessing environment
    """
    try:
        if np.count_nonzero(roi) == 0:
            # Ignore runs with no voxel. Return placeholder object
            debug("No voxels")
            return id, True, LibRun({}, "")
    
        data = {"data" : main_data}
        n = 0
        if len(add_data) % 2 != 0:
            raise Exception("Additional data has length %i - should be key then value" % len(add_data))
        while n < len(add_data):
            data[add_data[n]] = add_data[n+1]
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

    PROCESS_NAME = "Fabber"
    FABBER_FOUND = False
    FABBER_EX = None
    FABBER_LIB = None
    
    try:
        FABBER_EX, FABBER_LIB, MODEL_LIBS = find_fabber()
        FABBER_FOUND = FABBER_LIB is not None
    except:
        # Error with fabber logged on import
        pass

    def __init__(self, ivm, **kwargs):
        BackgroundProcess.__init__(self, ivm, _run_fabber, **kwargs)

    def run(self, options):
        data_name = options.pop("data", None)
        if data_name is None:
            if self.ivm.main is None:
                raise QpException("No data loaded")
            data = self.ivm.main.std()
        else:
            data = self.ivm.data[data_name].std()

        roi_name = options.pop("roi", None)
        if roi_name is None:
            if self.ivm.current_roi is not None:
                roidata = self.ivm.current_roi.std()
            else:
                roidata = np.ones(data.shape[:3])
        else:
            roidata = self.ivm.rois[roi_name].std()

        # FIXME rundata requires all arguments to be strings!
        rundata = FabberRunData()
        for key in options.keys():
            value = options.pop(key)
            if value is not None: rundata[key] = str(value)
            else: rundata[key] = ""

        # Pass in input data. To enable the multiprocessing module to split our volumes
        # up automatically we have to pass the arguments as a single list. This consists of
        # rundata, main data, roi and then each of the used additional data items, name followed by data
        input_args = [rundata, data, roidata]

        # This is not perfect - we just grab all data matching an option value
        for key, value in rundata.items():
            if value in self.ivm.data:
                input_args.append(value)
                input_args.append(self.ivm.data[value].std())

        if rundata["method"] == "spatialvb":
            # Spatial VB will not work properly in parallel
            n = 1
        else:
            # Run one worker for each slice
            n = data.shape[0]

        if roidata is not None: self.voxels_todo = np.count_nonzero(roidata)
        else: self.voxels_todo = self.ivm.main.grid.nvoxels

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
        for o in self.output:
            if o is not None and  hasattr(o, "log") and len(o.log) > 0:
                self.log += o.log + "\n\n"

        if self.status == Process.SUCCEEDED:
            first = True
            data_keys = []
            for o in self.output:
                if len(o.data) > 0: data_keys = o.data.keys()
            for key in data_keys:
                debug(key)
                recombined_item = self.recombine_data([o.data.get(key, None) for o in self.output])
                debug("recombined")
                self.ivm.add_data(recombined_item, name=key, make_current=first)
                first = False

