"""
Author: Martin Craig <martin.craig@eng.ox.ac.uk>
Copyright (c) 2013-2015 University of Oxford,  Martin Craig
"""

import numpy as np
cimport numpy as np

from libcpp.vector cimport vector

cdef extern from "veaslc.h":
    string veaslc(float *data, int *mask, int x, int y, int z, int t)

def veaslc_wrapper(data, roi, encmat, vesloc, modmat, nfpc):
    """
    Wrapper for the c++ VEASL function
    """

    # We will pass flattened arrays in Fortran order because this is 
    # compatible with the FSL volume class
    data = data.flatten(order='F').astype(np.float32)
    roi = roi.flatten(order='F').astype(np.int32)
    x, y, z, t = data.shape

    # Create data buffers to catch returned data
    flow = np.zeros(data.shape, dtype=np.float32).flatten()
    prob = np.zeros(data.shape, dtype=np.float32).flatten()

    log = run_veaslc(&data[0], &roi[0], x, y, z, t)
    return log
