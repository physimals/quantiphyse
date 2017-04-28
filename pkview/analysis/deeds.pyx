"""
Author: Martin Craig <martin.craig@eng.ox.ac.uk>
Copyright (c) 2017 University of Oxford, Martin Craig
"""

import numpy as np
cimport numpy as np

from libcpp.string cimport string

cdef extern from "deedsMSTssc.h":
    string deeds(float* im1, float* im1b, int M, int N, int O, float *retbuf,
                 float alpha, int randsamp, int maxlevel)

def run_deeds_c(np.ndarray[np.float32_t, ndim=1] vol, 
                np.ndarray[np.float32_t, ndim=1] refvol, 
                np.ndarray[np.float32_t, ndim=1] retvol,
                shape, alpha, randsamp, maxlevel):
    return deeds(&vol[0], &refvol[0], shape[0], shape[1], shape[2], &retvol[0],
                 alpha, randsamp, maxlevel)

def deedsReg(vol, refvol, **kwargs):
    shape = vol.shape

    # DEEDS works on flattened arrays in Fortran order
    vol = vol.flatten(order='F').astype(np.float32)
    refvol = refvol.flatten(order='F').astype(np.float32)
    retvol = np.zeros(vol.shape, dtype=np.float32)

    log = run_deeds_c(vol, refvol, retvol, shape,
                      kwargs["alpha"], kwargs["randsamp"], kwargs["levels"])
    retvol = np.reshape(retvol, shape, order='F')

    return retvol, log

