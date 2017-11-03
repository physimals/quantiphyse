"""
Author: Martin Craig <martin.craig@eng.ox.ac.uk>
Copyright (c) 2013-2015 University of Oxford,  Martin Craig
"""

import numpy as np
cimport numpy as np
import ctypes

from libcpp.string cimport string

cdef extern from "model.h" namespace "VESENC":
    cdef enum LocationInference:
        INFER_NONE=0,
        INFER_XY,
        INFER_AFFINE,
        INFER_RIGID
        
LOC_INFER = {None : INFER_NONE, "xy" : INFER_XY, "affine" : INFER_AFFINE, "rigid" : INFER_RIGID}

cdef extern from "veaslc.h":
    string veaslc(float *data, float *mask, 
                  int x, int y, int z, int v, 
                  string vesloc, string encdef, string modmat,
                  string imlist, int nfpc, LocationInference infer_loc, int infer_v,
                  float *flowout, float *classout)


def run_veaslc(np.ndarray[np.float32_t, ndim=1] data, 
               np.ndarray[np.float32_t, ndim=1] roi, 
               shape, vesloc, encdev, modmat, 
               imlist, nfpc, infer_loc, infer_v,
               np.ndarray[np.float32_t, ndim=1] flowout, 
               np.ndarray[np.float32_t, ndim=1] probout):
    return veaslc(&data[0], &roi[0], shape[0], 
                  shape[1], shape[2], shape[3], 
                  vesloc, encdev, modmat, 
                  imlist, nfpc, infer_loc, infer_v,
                  &flowout[0], &probout[0])


def veaslc_wrapper(data, roi, vesloc, encdef, modmat, nsources, imlist, nfpc, infer_loc, infer_v):
    """
    Wrapper for the c++ VEASL function
    """
    print("veaslc_wrapper")

    # We will pass flattened arrays in Fortran order because this is 
    # compatible with the FSL volume class
    shape = data.shape
    data = data.flatten(order='F').astype(np.float32)
    roi = roi.flatten(order='F').astype(np.float32)

    # Create data buffers to catch returned data
    ret_shape = list(shape)
    ret_shape[3] = nsources
    flow = np.zeros(ret_shape, dtype=np.float32).flatten()
    prob = np.zeros(ret_shape, dtype=np.float32).flatten()

    print("running veaslc")
    log = run_veaslc(data, roi, shape, vesloc, encdef, modmat, imlist, nfpc, LOC_INFER[infer_loc], infer_v, flow, prob)
    print("run veaslc")

    # Reshape output arrays
    flow = np.reshape(flow, ret_shape, order='F')
    prob = np.reshape(prob, ret_shape, order='F')

    return flow, prob, log
