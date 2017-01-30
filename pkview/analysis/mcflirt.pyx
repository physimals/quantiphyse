"""
Author: Martin Craig <martin.craig@eng.ox.ac.uk>
Copyright (c) 2017 University of Oxford, Martin Craig
"""

import numpy as np
cimport numpy as np

from libcpp.vector cimport vector
from libcpp.string cimport string

cdef extern from "mcflirt.h":
    void mcflirt_run (float *vol, vector[int] &extent, vector[float] &voxeldims, vector[string] &opts)

def run_mcflirt_c(np.ndarray[np.float32_t, ndim=1, mode="fortran"] mcvol, shape, voxeldims, opts):
    mcflirt_run(&mcvol[0], shape, voxeldims, opts)
    print(mcvol[0])
    print(mcvol[64*64*42])

def mcflirt(vol, voxeldims, **kwargs):
    opts = ["-report",]
    for key, value in kwargs.items():
        opts.append("-%s" % key)
        if value is not None and len(value) > 0: opts.append(value)

    # FSL volumes use data in Fortran order
    mcvol = vol.flatten(order='F').astype(np.float32)

    run_mcflirt_c(mcvol, vol.shape, voxeldims, opts)
    print(mcvol[0])
    print(mcvol[64*64*42])

    mcvol = np.reshape(mcvol, vol.shape, order='F')
    print(mcvol[0,0,0,0])
    print(mcvol[0,0,0,1])

    return mcvol

