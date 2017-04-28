import sys
import os
import warnings
import traceback

import numpy as np

from pkview.volumes.volume_management import Volume, Roi, Overlay
from pkview.analysis import Process, BackgroundProcess
from pkview.analysis.deeds import deedsReg
from pkview.analysis.mcflirt import mcflirt

def deeds_reg(regdata, refdata, options):
    return deedsReg(regdata, refdata, **options)

# Known registration methods (case-insensitive)
methods = {"deeds" : deeds_reg}

def _run_moco(id, queue, method, options, regdata, refdata, refidx=None):
    try:
        mocovols = np.zeros(regdata.shape)
        reg_fn = methods[method.lower()]

        full_log = ""
        for t in range(regdata.shape[-1]):
            print("Registering slice %i of %i" % (t, regdata.shape[-1]))
            regvol = regdata[:,:,:,t]
            if t == refidx:
                mocovols[:,:,:,t] = regvol
            else:
                mocovol, log = reg_fn(regvol, refdata, options)
                mocovols[:,:,:,t] = mocovol
                full_log += log
            queue.put(t)
        return id, True, (mocovols, full_log)
    except:
        return id, False, sys.exc_info()[1]

def _run_reg(id, queue, method, options, regdata, refdata):
    try:
        reg_fn = methods[method]
        registered, log = reg_fn(regdata, refdata, options)
        return id, True, (registered, log)
    except:
        return id, False, sys.exc_info()[1]

class MocoProcess(BackgroundProcess):
    """
    Asynchronous background process to run motion correction
    """
    def __init__(self, ivm, **kwargs):
        BackgroundProcess.__init__(self, ivm, _run_moco, **kwargs)

    def run(self, options):
        self.replace = options.pop("replace-vol", False)
        self.method = options.pop("method", "deeds")
        self.output_name = options.pop("output-name", "moco")
        #self.refvol = options.pop("vol", self.ivm.vol.name)
        moco_vols = self.ivm.vol.data
        self.nvols = moco_vols.shape[-1]

        refidx = None
        if moco_vols.ndim == 4:
            self.refvol = options.pop("ref-vol", "median")
            if self.refvol == "median":
                refidx = moco_vols.shape[-1]/2
                refdata = moco_vols[:,:,:,refidx]
            elif self.refvol == "mean":
                raise RuntimeException("Not yet implemented")
            else:
                refidx = self.refvol
                refdata = moco_vols[:,:,:,refidx]
        else:
            raise RuntimeException("Can only motion correct 4D data")

        # Function input data must be passed as list of arguments for multiprocessing
        self.start(1, [self.method, options, moco_vols, refdata, refidx])

    def timeout(self):
        if self.queue.empty(): return
        while not self.queue.empty():
            done = self.queue.get()
        complete = float(done+1)/self.nvols
        self.sig_progress.emit(complete)

    def finished(self):
        """ Add output data to the IVM and set the log """
        self.log = ""
        if self.status == Process.SUCCEEDED:
            output = self.output[0]
            if self.replace:
                self.ivm.set_main_volume(Volume(self.output_name, data=output[0]), replace=True)
            else:
                self.ivm.add_overlay(Overlay(self.output_name, data=output[0]), make_current=False)
                self.log = output[1]

class McflirtProcess(Process):
    """
    Process to run MCFLIRT motion correction
    """
    def __init__(self, ivm, **kwargs):
        Process.__init__(self, ivm, **kwargs)

    def run(self, options):
        try:
            replace = options.pop("replace-vol", False)
            name = options.pop("output-name", "moco")
            debug = options.pop("Debug", False)
            folder = options.pop("Folder", "")
            folder = options.pop("OutputFolder", "")
            
            refvol = options.pop("ref-vol", "median")
            if refvol == "mean":
                options["meanvol"] = ""
            elif refvol != "median":
                options["refvol"] = refvol

            retdata, self.log = mcflirt(self.ivm.vol.data, self.ivm.vol.voxel_sizes, **options)
            if replace:
                if debug: print("Replacing main volume")
                self.ivm.set_main_volume(Volume(self.ivm.vol.name, data=retdata), replace=True)
            else:
                if debug: print("Adding new overlay")
                ovl = Overlay(name, data=retdata)
                self.ivm.add_overlay(ovl, make_current=True)
            self.status = Process.SUCCEEDED
            self.output = [retdata, ]
        except:
            self.output = sys.exc_info()[1]
            self.status = Process.FAILED

        self.sig_finished.emit(self.status,self.output, self.log)

class RegProcess(BackgroundProcess):
    """
    Asynchronous background process to run registration
    """
    def __init__(self, ivm, **kwargs):
        BackgroundProcess.__init__(self, ivm, _run_reg, **kwargs)

    def run(self, options):
        self.method = options.pop("method", "deeds")
        refvol = self.ivm.overlays[options.pop("ref")]
        regvol = self.ivm.overlays[options.pop("reg")]
        self.output_name = options.pop("output-name",regvol.name + "_reg")

        # Function input data must be passed as list of arguments for multiprocessing
        self.start(1, [self.method, refvol.data, regvol.data, options])

    def finished(self):
        """ Add output data to the IVM and set the log """
        self.log = ""
        if self.status == Process.SUCCEEDED:
            output = self.output[0]
            self.ivm.add_overlay(Overlay(self.output_name, data=output[0]), make_current=True)
            self.log = output[1]
