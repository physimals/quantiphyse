"""
Author: Martin Craig <martin.craig@eng.ox.ac.uk>
Copyright (c) 2017 University of Oxford, Martin Craig
"""

import numpy as np
cimport numpy as np

from libcpp.string cimport string

cdef extern from "deedsMSTssc.h":
    string deeds(float* im1, float* im1b, int M, int N, int O, 
                 float *ux, float *vx, float *wx,
                 float alpha, int randsamp, int maxlevel)

    string deeds_warp(float* im, float *ux, float *vx, float *wx, 
                      int M, int N, int O, float *retbuf)

def run_deeds_c(np.ndarray[np.float32_t, ndim=1] vol, 
                np.ndarray[np.float32_t, ndim=1] refvol, 
                np.ndarray[np.float32_t, ndim=1] ux,
                np.ndarray[np.float32_t, ndim=1] vx,
                np.ndarray[np.float32_t, ndim=1] wx,
                shape, alpha, randsamp, maxlevel):
    return deeds(&vol[0], &refvol[0], 
                 shape[0], shape[1], shape[2],
                 &ux[0], &vx[0], &wx[0], 
                 alpha, randsamp, maxlevel)

def run_deeds_warp_c(np.ndarray[np.float32_t, ndim=1] vol, 
                np.ndarray[np.float32_t, ndim=1] ux,
                np.ndarray[np.float32_t, ndim=1] vx,
                np.ndarray[np.float32_t, ndim=1] wx,
                np.ndarray[np.float32_t, ndim=1] retvol,
                shape):
    return deeds_warp(&vol[0], &ux[0], &vx[0], &wx[0], 
                      shape[0], shape[1], shape[2], 
                      &retvol[0])

def deedsReg(vol, refvol, warp_rois, **kwargs):
    shape = vol.shape
    # DEEDS works on flattened arrays in Fortran order
    vol = vol.flatten(order='F').astype(np.float32)
    refvol = refvol.flatten(order='F').astype(np.float32)

    ux = np.zeros(vol.shape, dtype=np.float32).flatten()
    vx = np.zeros(vol.shape, dtype=np.float32).flatten()
    wx = np.zeros(vol.shape, dtype=np.float32).flatten()
    log = run_deeds_c(vol, refvol, ux, vx, wx, shape,
                      kwargs.get("alpha", 2), kwargs.get("randsamp", 50), kwargs.get("levels", 5))
                      
    retvol = np.zeros(vol.shape, dtype=np.float32).flatten().astype(np.float32)
    log += run_deeds_warp_c(vol, ux, vx, wx, retvol, shape)
    retvol = np.reshape(retvol, shape, order='F')
    
    warp_rois_out = None
    if warp_rois is not None:
        num_rois = warp_rois.shape[3]
        warp_rois_out = np.zeros(warp_rois.shape, dtype=np.float32)
        vol_out = np.zeros(warp_rois.shape[:3]).flatten().astype(np.float32)
        for v in range(num_rois):
            warp_roi = warp_rois[:,:,:,v].flatten(order='F').astype(np.float32)
            log += run_deeds_warp_c(warp_roi, ux, vx, wx, vol_out, shape)
            warp_rois_out[:,:,:,v] = np.reshape(vol_out, shape, order='F')
            
    return retvol, warp_rois_out, log

