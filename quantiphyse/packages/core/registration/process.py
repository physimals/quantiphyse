import sys
import os
import traceback

import numpy as np

from quantiphyse.utils import debug, warn, get_plugins
from quantiphyse.utils.exceptions import QpException

from quantiphyse.analysis import Process, BackgroundProcess

# Known registration methods (case-insensitive)
REG_METHODS = {}

"""
Registration function for asynchronous process - used for moco and registration
"""
def _run_reg(id, queue, method, options, regdata, refdata, warp_rois, ignore_idx=None):
    try:
        full_log = ""
        if regdata.ndim == 3: 
            regdata = np.expand_dims(regdata, -1)
            data_4d = False
        else:
            data_4d = True
        regdata_out = np.zeros(regdata.shape)

        if warp_rois is not None: 
            warp_rois_out = np.zeros(warp_rois.shape)
            full_log += "Warp ROIs max=%f\n" % np.max(warp_rois)
        else: warp_rois_out = None
        method = REG_METHODS[method.lower()]

        for t in range(regdata.shape[-1]):
            full_log += "Registering volume %i of %i\n" % (t+1, regdata.shape[-1])
            regvol = regdata[:,:,:,t]
            if t == ignore_idx:
                regdata_out[:,:,:,t] = regvol
            else:
                outvol, roivol, log = method.reg(regvol, refdata, warp_rois, options)
                full_log += log
                regdata_out[:,:,:,t] = outvol
                if warp_rois is not None: 
                    warp_rois_out = roivol
                    full_log += "add data max=%f\n" % np.max(roivol)
            queue.put(t)
        if not data_4d: 
            regdata_out = np.squeeze(regdata_out, -1)
            if warp_rois is not None: 
                warp_rois_out = (warp_rois_out > 0.5).astype(np.int)
            
        return id, True, (regdata_out, warp_rois_out, full_log)
    except:
        return id, False, sys.exc_info()[1]

class RegProcess(BackgroundProcess):
    """
    Asynchronous background process to run registration / motion correction
    """

    PROCESS_NAME = "Reg"

    def __init__(self, ivm, **kwargs):
        BackgroundProcess.__init__(self, ivm, _run_reg, **kwargs)
        global REG_METHODS
        methods = get_plugins("reg-methods")
        for m in methods:
            method = m()
            REG_METHODS[method.name.lower()] = method

    def run(self, options):
        self.replace = options.pop("replace-vol", False)
        self.method = options.pop("method", "deeds")
        regdata_name = options.pop("reg", self.ivm.main.name)
        reg_data = self.ivm.data[regdata_name].std()

        self.output_name = options.pop("output-name", "reg_%s" % regdata_name)
        if reg_data.ndim == 4: self.nvols = reg_data.shape[-1]
        else: self.nvols = 1

        # Reference data defaults to same as reg data so MoCo can be
        # supported as self-registration
        refdata_name = options.pop("ref", regdata_name)
        ref_vols = self.ivm.data[refdata_name]

        if ref_vols.nvols > 1:
            self.refvol = options.pop("ref-vol", "median")
            if self.refvol == "median":
                refidx = ref_vols.nvols/2
                refdata = ref_vols.std()[:,:,:,refidx]
            elif self.refvol == "mean":
                raise RuntimeException("Not yet implemented")
            else:
                refidx = self.refvol
                refdata = ref_vols.std()[:,:,:,refidx]
        else:
            refdata = ref_vols.std()

        # Linked ROIS can be specified which will be warped in the same way as the main 
        # registration data. Useful for masks defined on an unregistered volume.
        # We handle multiple warp ROIs by building 4D data in which each volume is
        # a separate ROI. This is then unpacked at the end.
        self.warp_roi_names = dict(options.pop("warp-rois", {}))
        warp_roi_name = options.pop("warp-roi", None)
        if warp_roi_name is not None:  self.warp_roi_names[warp_roi_name] = warp_roi_name + "_warp"

        for roi_name in self.warp_roi_names.keys():
            if roi_name not in self.ivm.rois:
                warn("removing non-existant ROI: %s" % roi_name)
                del self.warp_roi_names[roi_name]

        if len(self.warp_roi_names) > 0:
            warp_rois = np.zeros(list(refdata.shape) + [len(self.warp_roi_names)])
            for idx, roi_name in enumerate(self.warp_roi_names):
                roi = self.ivm.rois[roi_name].std()
                if roi.shape != refdata.shape:
                    raise RuntimeError("Warp ROI %s has different shape to registration data" % roi_name)
                warp_rois[:,:,:,idx] = roi
            debug("Have %i warped ROIs" % len(self.warp_roi_names))
        else:
            warp_rois = None
        debug(self.warp_roi_names)

        # Function input data must be passed as list of arguments for multiprocessing
        self.start(1, [self.method, options, reg_data, refdata, warp_rois])

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
            self.ivm.add_data(output[0], name=self.output_name, make_current=True)
            if output[1] is not None: 
                for idx, roi_name in enumerate(self.warp_roi_names):
                    roi = output[1][:,:,:,idx]
                    debug("Adding warped ROI: %s" % self.warp_roi_names[roi_name])
                    self.ivm.add_roi(roi, name=self.warp_roi_names[roi_name], make_current=False)
            self.log = output[2]

class MocoProcess(RegProcess):
    """
    MoCo is identical to registration but has different batch name
    """

    PROCESS_NAME = "Moco"
