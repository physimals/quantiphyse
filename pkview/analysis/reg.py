import sys
import os
import warnings
import traceback

import numpy as np

from . import Process, BackgroundProcess
from .deeds import deedsReg
from .mcflirt import mcflirt

def deeds_reg(regdata, refdata, options):
    return deedsReg(regdata, refdata, **options)

def mcflirt_reg(regdata, refdata, options):
    # MCFLIRT wants to do motion correction so we stack the reg and ref
    # data together and tell it to use the second as the reference.
    data = np.stack((regdata, refdata), -1)
    options["refvol"] = 1
    # FIXME voxel sizes?
    retdata, log = mcflirt(data, [1.0,] * data.ndim, **options)
    return retdata[:,:,:,0], log

# Known registration methods (case-insensitive)
methods = {"deeds" : deeds_reg,
           "mcflirt" : mcflirt_reg}

"""
Registration function for asynchronous process - used for moco and registration
"""
def _run_reg(id, queue, method, options, regdata, refdata, ignore_idx=None):
    try:
        if regdata.ndim == 3: 
            regdata = np.expand_dims(regdata, -1)
            data_4d = False
        else:
            data_4d = True
        outdata = np.zeros(regdata.shape)
        reg_fn = methods[method.lower()]

        full_log = ""
        for t in range(regdata.shape[-1]):
            print("Registering volume %i of %i" % (t+1, regdata.shape[-1]))
            regvol = regdata[:,:,:,t]
            if t == ignore_idx:
                outdata[:,:,:,t] = regvol
            else:
                outvol, log = reg_fn(regvol, refdata, options)
                outdata[:,:,:,t] = outvol
                full_log += log
            queue.put(t)
        if not data_4d: outdata = np.squeeze(outdata, -1)
        return id, True, (outdata, full_log)
    except:
        return id, False, sys.exc_info()[1]

    try:
        reg_fn = methods[method]
        registered, log = reg_fn(regdata, refdata, options)
        return id, True, (registered, log)
    except:
        return id, False, sys.exc_info()[1]

class RegProcess(BackgroundProcess):
    """
    Asynchronous background process to run registration / motion correction
    """
    def __init__(self, ivm, **kwargs):
        BackgroundProcess.__init__(self, ivm, _run_reg, **kwargs)

    def run(self, options):
        self.replace = options.pop("replace-vol", False)
        self.method = options.pop("method", "deeds")
        regdata_name = options.pop("reg", self.ivm.vol.name)
        if regdata_name == self.ivm.vol.name:
            reg_vols = self.ivm.vol
        else:
            reg_vols = self.ivm.overlays[regdata_name]

        self.output_name = options.pop("output-name", "reg_%s" % regdata_name)
        self.nvols = reg_vols.shape[-1]

        # Reference data defaults to same as reg data so MoCo can be
        # supported as self-registration
        refdata_name = options.pop("ref", regdata_name)
        if refdata_name == self.ivm.vol.name:
            ref_vols = self.ivm.vol
        else:
            ref_vols = self.ivm.overlays[refdata_name]

        if ref_vols.ndim == 4:
            self.refvol = options.pop("ref-vol", "median")
            if self.refvol == "median":
                refidx = ref_vols.shape[-1]/2
                refdata = ref_vols[:,:,:,refidx]
            elif self.refvol == "mean":
                raise RuntimeException("Not yet implemented")
            else:
                refidx = self.refvol
                refdata = ref_vols[:,:,:,refidx]
        else:
            refdata = ref_vols

        # Function input data must be passed as list of arguments for multiprocessing
        self.start(1, [self.method, options, reg_vols, refdata])

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
            self.ivm.add_overlay(self.output_name, output[0], make_current=True)
            self.log = output[1]

class McflirtProcess(Process):
    """
    Process to run MCFLIRT motion correction DEPRECATED
    """
    def __init__(self, ivm, **kwargs):
        Process.__init__(self, ivm, **kwargs)

    def run(self, options):
        try:
            replace = options.pop("replace-vol", False)
            name = options.pop("output-name", "moco")
            refvol = options.pop("ref-vol", "median")
            if refvol == "mean":
                options["meanvol"] = ""
            elif refvol != "median":
                options["refvol"] = refvol

            retdata, self.log = mcflirt(self.ivm.vol, self.ivm.voxel_sizes, **options)
            if self.debug: print("Adding new overlay")
            self.ivm.add_overlay(name, retdata, make_current=True, make_main=replace)
            self.status = Process.SUCCEEDED
            self.output = [retdata, ]
        except:
            self.output = sys.exc_info()[1]
            self.status = Process.FAILED

        self.sig_finished.emit(self.status,self.output, self.log)
