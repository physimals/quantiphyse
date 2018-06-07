"""
Quantiphyse - Analysis processes for registration and motion correction

Copyright (c) 2013-2018 University of Oxford
"""

import sys

import numpy as np

from quantiphyse.utils import debug, warn, get_plugins, set_local_file_path, QpException
from quantiphyse.processes import Process

def get_reg_method(method_name):
    """
    Get a named registration method (case insensitive)
    """
    methods = get_plugins("reg-methods")
    debug("Known methods: ", methods)
    for method_class in methods:
        method = method_class()
        if method.name.lower() == method_name.lower():
            return method
    return None

def _run_reg(worker_id, queue, method_name, mode, reg_data, reg_grid, ref_data, ref_grid, options):
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
            out_data, transforms, moco_log = method.moco(reg_data[0], reg_grid, ref_data, ref_grid, options, queue)
            log += moco_log
            return worker_id, True, ([out_data], transforms, log)
        elif reg_data[0].ndim == 3: 
            # Register single volume data, may be more than one registration target
            out_data = []
            log = "Running 3D registration\n\n"
            registered, transform, reg_log = method.reg_3d(reg_data[0], reg_grid, ref_data, ref_grid, options, queue)
            log += reg_log
            out_data.append(registered)
            for idx, add_data in enumerate(reg_data[1:]):
                log += "\nApplying transformation to additional data %i\n\n" % (idx+1)
                registered, apply_log = method.apply_transform(add_data, reg_grid, ref_data, ref_grid, transform, queue)
                log += apply_log
                out_data.append(registered)
            return worker_id, True, (out_data, transform, log)
        else:
            # Register multi-volume data, can only be one registration target
            if len(reg_data) > 1:
                raise QpException("Cannot have additional registration targets with 4D registration data")
            
            log = "Running 4D registration\n\n"
            out_data, transforms, reg_log = method.reg_4d(reg_data[0], reg_grid, ref_data, ref_grid, options, queue)
            log += reg_log
            return worker_id, True, ([out_data], transforms, log)
    except:
        return worker_id, False, sys.exc_info()[1]

class RegProcess(Process):
    """
    Asynchronous background process to run registration / motion correction
    """

    PROCESS_NAME = "Reg"

    def __init__(self, ivm, **kwargs):
        Process.__init__(self, ivm, worker_fn=_run_reg, **kwargs)
        self.grid = None
        self.output_names = None

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
        self.grid = regdata.grid
        reg_data = [regdata.raw(), ]


        # Names of input / output data
        self.input_names = [regdata_name,]
        if options.pop("replace-vol", False):
            self.output_names = [regdata_name,]
        else:
            self.output_names = [options.pop("output-name", "reg_%s" % regdata_name), ]

        # Reference data. Defaults to same as reg data so MoCo can be
        # supported as self-registration
        refdata_name = options.pop("ref", regdata_name)
        ref_data = self.ivm.data[refdata_name]
        ref_grid = ref_data.grid
        if ref_data.nvols > 1:
            refvol = options.pop("ref-vol", "median")
            if refvol == "median":
                refidx = int(ref_data.nvols/2)
            elif refvol == "mean":
                raise NotImplementedError("Not yet implemented")
            else:
                refidx = refvol
            ref_data = ref_data.volume(refidx)
        else:
            ref_data = ref_data.raw()

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
                warn("Removing non-existant data set from additional registration list: %s" % name)
            else:
                if not output_name:
                    output_name = name + "_reg"
                reg_data.append(qpdata.resample(self.grid).raw())
                self.input_names.append(name)
                self.output_names.append(output_name)
        
        debug("Have %i registration targets" % len(reg_data))

        # Function input data must be passed as list of arguments for multiprocessingmethod = get_reg_method(method_name)
        self.start_bg([method_name, mode, reg_data, self.grid.affine, ref_data, ref_grid.affine, options])

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
            for input_name, output_name, data in zip(self.input_names, self.output_names, registered_data):
                if input_name in self.ivm.rois:
                    # This is not correct for multi-level ROIs - this would basically require support
                    # from within the registration algorithm for roi (integer only) data
                    data = (data > 0.5).astype(np.int)
                    self.ivm.add_roi(data, name=output_name, grid=self.grid, make_current=first_roi)
                    first_roi = False
                else:
                    self.ivm.add_data(data, name=output_name, grid=self.grid, make_current=first_data)
                    first_data = False
