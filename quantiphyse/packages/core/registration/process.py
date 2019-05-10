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
import multiprocessing

import six
import numpy as np

from quantiphyse.data import NumpyData, QpData
from quantiphyse.data.extras import Extra
from quantiphyse.utils import get_plugins, set_local_file_path, QpException
from quantiphyse.processes import Process

LOG = logging.getLogger(__name__)

def get_reg_method(method_name):
    """
    Get a named registration method (case insensitive)
    """
    methods = get_plugins("reg-methods")
    LOG.debug("Known methods: %s", str(methods))
    for method_class in methods:
        method = method_class(None)
        if method.name.lower() == method_name.lower():
            return method
    return None

def _normalize_output(reg_data, output_data, output_suffix):
    if reg_data.roi:
        # This is not correct for multi-level ROIs - this would basically require support
        # from within the registration algorithm for roi (integer only) data
        data = np.rint(output_data.raw()).astype(np.int)
        output_data = NumpyData(data, grid=output_data.grid, name=output_data.name, roi=True)
    output_data.name = reg_data.name + output_suffix
    return output_data

def _reg_3d(worker_id, method, reg_data, ref_data, options, queue):
    """
    Register single volume data, may be more than one registration target
    """
    out_data = []
    log = "Running 3D registration\n\n"
    output_suffix = options.pop("output-suffix", "_reg")
    registered, transform, reg_log = method.reg_3d(reg_data[0], ref_data, dict(options), queue)
    registered = _normalize_output(reg_data[0], registered, output_suffix)
    log += reg_log
    out_data.append(registered)
    for idx, add_data in enumerate(reg_data[1:]):
        log += "\nApplying transformation to additional data %i\n\n" % (idx+1)
        registered, apply_log = method.apply_transform(add_data, transform, dict(options), queue)
        registered = _normalize_output(add_data, registered, output_suffix)
        log += apply_log
        out_data.append(registered)
    return worker_id, True, (out_data, transform, log)

def _reg_4d(worker_id, method, reg_data, ref_data, options, queue):
    """
    Register multi-volume data, can only be one registration target
    """
    if len(reg_data) > 1:
        raise QpException("Cannot have additional registration targets with 4D registration data")
    
    log = "Running 4D registration\n\n"
    output_suffix = options.pop("output-suffix", "_reg")
    out_data, transforms, reg_log = method.reg_4d(reg_data[0], ref_data, dict(options), queue)
    out_data = _normalize_output(reg_data[0], out_data, output_suffix)
    log += reg_log
    return worker_id, True, ([out_data], transforms, log)

def _reg_moco(worker_id, method, reg_data, ref_data, options, queue):
    """
    Motion correction mode
    """
    if len(reg_data) > 1:
        raise QpException("Cannot have additional registration targets with motion correction")
    
    log = "Running motion correction\n\n"
    output_suffix = options.pop("output-suffix", "_moco")
    out_data, transforms, moco_log = method.moco(reg_data[0], ref_data, dict(options), queue)
    out_data = _normalize_output(reg_data[0], out_data, output_suffix)
    log += moco_log
    return worker_id, True, ([out_data], transforms, log)

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
            return _reg_moco(worker_id, method, reg_data, ref_data, options, queue)
        elif reg_data[0].ndim == 3:
            return _reg_3d(worker_id, method, reg_data, ref_data, options, queue)
        else:
            return _reg_4d(worker_id, method, reg_data, ref_data, options, queue)
    except:
        traceback.print_exc()
        return worker_id, False, sys.exc_info()[1]

class RegProcess(Process):
    """
    Asynchronous background process to run registration / motion correction
    """

    PROCESS_NAME = "Reg"

    def __init__(self, ivm, **kwargs):
        Process.__init__(self, ivm, worker_fn=_run_reg, **kwargs)

    def run(self, options):
        self.debug("Run")
        method_name = options.pop("method")
        mode = options.pop("mode", "reg")
        self._save_transform = options.pop("save-transform", None)

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
        self._output_name = options.pop("output-name", regdata.name + options.get("output-suffix", "_reg"))

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
        add_reg = options.pop("add-reg", options.pop("warp-rois", options.pop("warp-roi", ())))

        # Handle case where additional registation targets are given as a string
        if isinstance(add_reg, six.string_types):
            add_reg = (add_reg,)

        for name in add_reg:
            qpdata = self.ivm.data.get(name, None)
            if not qpdata:
                self.warn("Removing non-existant data set from additional registration list: %s" % name)
            else:
                reg_data.append(qpdata.resample(reg_grid, suffix=""))
        
        self.debug("Have %i registration targets" % len(reg_data))

        # Function input data must be passed as list of arguments for multiprocessingmethod = get_reg_method(method_name)
        options_pass = dict(options)
        options.clear()
        self.start_bg([method_name, mode, reg_data, ref_data, options_pass])

    def timeout(self, queue):
        if queue.empty(): return
        while not queue.empty():
            complete = queue.get()
        self.sig_progress.emit(complete)

    def finished(self, worker_output):
        """ Add output data to the IVM and set the log """
        if self.status == Process.SUCCEEDED:
            registered_data, transform, log = worker_output[0]
            # Output name applies to the registration input data
            registered_data[0].name = self._output_name
            self.log(log)

            first_roi, first_data = True, True
            for data in registered_data:
                if data.roi:
                    self.ivm.add(data, make_current=first_roi)
                    first_roi = False
                else:
                    self.ivm.add(data, make_current=first_data)
                    first_data = False

            if self._save_transform:
                if isinstance(transform, QpData):
                    self.ivm.add(transform, name=self._save_transform)
                elif isinstance(transform, Extra):
                    transform.name = self._save_transform
                    self.ivm.add_extra(self._save_transform, transform)
                else:
                    # FIXME what to do about moco - sequence of transforms?
                    pass

class ApplyTransformProcess(Process):
    """
    Asynchronous background process to run registration / motion correction
    """

    PROCESS_NAME = "ApplyTransform"

    def run(self, options):
        self.debug("Run")
        data = self.get_data(options)
        trans_name = options.pop("transform")
        output_name = options.pop("output-name", data.name + "_reg")

        transform = self.ivm.data.get(trans_name, None)
        if transform is None or "QpReg" not in transform.metadata:
            transform = self.ivm.extras.get(trans_name, None)

        if transform is None or "QpReg" not in transform.metadata:
            raise QpException("Transform not found: %s" % trans_name)

        method = get_reg_method(transform.metadata["QpReg"])
        if method is None:
            raise QpException("Registration method not found: %s" % transform.metadata["QpReg"])

        # Fake queue - we ignore progress reports as this process is not asynchronous
        queue = multiprocessing.Queue()

        self.log("Applying transformation to data: %s" % data.name)
        registered, apply_log = method.apply_transform(data, transform, dict(options), queue)
        registered = _normalize_output(data, registered, "_reg")
        self.log(apply_log)
        self.ivm.add(registered, name=output_name, make_current=True)
        
class MocoProcess(RegProcess):
    """
    Explicit motion correction process for backwards compat
    """

    PROCESS_NAME = "Moco"

    def run(self, options):
        options["mode"] = "moco"
        return RegProcess.run(self, options)
