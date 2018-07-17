"""
Quantiphyse - Analysis processes for registration and motion correction

Registration is a little complex because it is a plugin which uses other
plugins - registration methods.

A registration method contains methods to do registration on 3d and 4d data,
and also motion correction. There are default base class implementations
of 4d registration and motion correction which simply use the 3d method, but
methods can override these defaults, e.g. the Flirt plugin can use McFlirt
to do motion correction

A registration method can also return the transform and apply it to other
data. Of course only transforms compatible with a registration method
can be used, e.g. rigid body vs fully deformable.

Copyright (c) 2013-2018 University of Oxford
"""

import sys
import logging
import traceback

import numpy as np

from quantiphyse.data import NumpyData
from quantiphyse.utils import get_plugins, set_local_file_path, QpException
from quantiphyse.processes import Process

LOG = logging.getLogger(__name__)

def get_reg_method(method_name):
    """
    Get a named registration method (case insensitive)
    """
    methods = get_plugins("reg-methods")
    LOG.debug("Known methods: %s", methods)
    for method_class in methods:
        method = method_class()
        if method.name.lower() == method_name.lower():
            return method
    return None

def _run_reg(worker_id, queue, method_name, mode, reg_data, ref_data, options):
    """
    Generic registration function for asynchronous process
    """
    try:
        set_local_file_path()
        method = get_reg_method(method_name)
        if method is None: 
            raise QpException("Unknown registration method: %s (known: %s)" % (method_name, str(get_plugins("reg-methods"))))

        if not reg_data:
            raise QpException("No registration data")
        elif mode == "moco":
            # Motion correction mode
            if len(reg_data) > 1:
                raise QpException("Cannot have additional registration targets with motion correction")
            
            log = "Running motion correction\n\n"
            out_data, transforms, moco_log = method.moco(reg_data[0], ref_data, options, queue)
            log += moco_log
            return worker_id, True, ([out_data], transforms, log)
        elif reg_data[0].ndim == 3: 
            # Register single volume data, may be more than one registration target
            out_data = []
            log = "Running 3D registration\n\n"
            registered, transform, reg_log = method.reg_3d(reg_data[0], ref_data, options, queue)
            log += reg_log
            out_data.append(registered)
            for idx, add_data in enumerate(reg_data[1:]):
                log += "\nApplying transformation to additional data %i\n\n" % (idx+1)
                registered, apply_log = method.apply_transform(add_data, ref_data, transform, queue)
                log += apply_log
                out_data.append(registered)
            return worker_id, True, (out_data, transform, log)
        else:
            # Register multi-volume data, can only be one registration target
            if len(reg_data) > 1:
                raise QpException("Cannot have additional registration targets with 4D registration data")
            
            log = "Running 4D registration\n\n"
            out_data, transforms, reg_log = method.reg_4d(reg_data[0], ref_data, options, queue)
            log += reg_log
            return worker_id, True, ([out_data], transforms, log)
    except:
        print(log)
        traceback.print_exc()
        return worker_id, False, sys.exc_info()[1]

class RegProcess(Process):
    """
    Asynchronous background process to run registration / motion correction
    """

    PROCESS_NAME = "Reg"

    def __init__(self, ivm, **kwargs):
        Process.__init__(self, ivm, worker_fn=_run_reg, **kwargs)
        self.output_names = {}

    def run(self, options):
        method_name = options.pop("method")
        mode = options.pop("mode", "reg")

        # Registration data. Need to know the reg data grid and number of volumes so progress
        # and output data can be interpreted correctly
        regdata_name = options.pop("reg", options.pop("data", None))
        if not regdata_name:
            raise QpException("No registration data specified")
        elif regdata_name not in self.ivm.data:
            raise QpException("Registration data not found: %s" % regdata_name)
        regdata = self.ivm.data[regdata_name]
        reg_grid = regdata.grid
        reg_data = [regdata, ]

        # Names of input / output data
        if options.pop("replace-vol", False):
            self.output_names[regdata_name] = regdata_name
        else:
            self.output_names[regdata_name] = options.pop("output-name", "reg_%s" % regdata_name)

        # Reference data. Defaults to same as reg data so MoCo can be
        # supported as self-registration
        refdata_name = options.pop("ref", regdata_name)
        ref_data = self.ivm.data[refdata_name]
        if ref_data.nvols > 1:
            refvol = options.pop("ref-vol", "median")
            if refvol == "median":
                refidx = int(ref_data.nvols/2)
            elif refvol == "mean":
                raise NotImplementedError("Not yet implemented")
            else:
                refidx = refvol
            ref_data = NumpyData(ref_data.volume(refidx), ref_data.grid, "refdata")

        # Additional registration targets can be specified which will be transformed
        # in the same way as the main registration data. 
        # 
        # Useful for masks defined on an unregistered volume.
        add_reg = dict(options.pop("add-reg", options.pop("warp-rois", {})))
        
        # Deprecated
        warp_roi_name = options.pop("warp-roi", None)
        if warp_roi_name:  
            add_reg[warp_roi_name] = warp_roi_name + "_reg"

        for name, output_name in add_reg.items():
            qpdata = self.ivm.data.get(name, self.ivm.rois.get(name, None))
            if not qpdata:
                self.warn("Removing non-existant data set from additional registration list: %s" % name)
            else:
                if not output_name:
                    output_name = name + "_reg"
                reg_data.append(qpdata.resample(reg_grid))
                self.output_names[name] = output_name
        
        self.debug("Have %i registration targets" % len(reg_data))

        # Function input data must be passed as list of arguments for multiprocessingmethod = get_reg_method(method_name)
        self.start_bg([method_name, mode, reg_data, ref_data, options])

    def timeout(self):
        if self.queue.empty(): return
        while not self.queue.empty():
            complete = self.queue.get()
        self.sig_progress.emit(complete)

    def finished(self):
        """ Add output data to the IVM and set the log """
        self.log = ""
        if self.status == Process.SUCCEEDED:
            registered_data, transforms, self.log = self.worker_output[0]

            first_roi, first_data = True, True
            for data in registered_data:
                output_name = self.output_names[data.name]
                if data.roi:
                    # This is not correct for multi-level ROIs - this would basically require support
                    # from within the registration algorithm for roi (integer only) data
                    data = NumpyData((data.raw() > 0.5).astype(np.int), grid=data.grid, name=data.name)
                    self.ivm.add_roi(data, name=output_name, make_current=first_roi)
                    first_roi = False
                else:
                    self.ivm.add_data(data, name=output_name, make_current=first_data)
                    first_data = False
