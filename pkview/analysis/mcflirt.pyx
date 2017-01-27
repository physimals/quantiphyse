"""
Author: Martin Craig <martin.craig@eng.ox.ac.uk>
Copyright (c) 2017 University of Oxford, Martin Craig
"""

# Cython interface file for wrapping the object

import numpy as np
cimport numpy as np

from libcpp.vector cimport vector
from libcpp.string cimport string

cdef extern from "mcflirt.h":
    vector[float] mcflirt_run (vector[float] &vol, vector[int] &extent, vector[float] &voxeldims, vector[string] &opts)

def mcflirt(vol, voxeldims):
    """
    Wrapper for the c++ MCFLIRT motion correction function

    Args:
        vol: Timeseries image

    Returns:
        new volume
    """

    if vol is None:
        raise RuntimeError("Volume data is None")
    if len(vol.shape) != 4:
        raise RuntimeError("Volume must be 4D")
    if len(voxeldims) != 4:
        raise RuntimeError("Must provide 4 voxel dimensions")

    # FSL volumes use column-major order for some reason (FORTRAN order).
    # This seems to work as conversion, basically reverse the order of the
    # axes and then turn to contiguous array and flatten.
    # Strangely np.asfortranarray() did not work!

    origshape = np.copy(vol.shape)
    vol = np.moveaxis(vol, -1, 0)
    vol = np.moveaxis(vol, -1, 1)
    vol = np.moveaxis(vol, -1, 2)

    shape = vol.shape
    flatvol = np.ascontiguousarray(vol.flatten())
    opts = ["-report",]
    mcvol = mcflirt_run(flatvol, origshape, voxeldims, opts)

    # Must remember to change back before returning!
    mcvol = np.reshape(mcvol, shape)
    mcvol = np.moveaxis(mcvol, 0, -1)
    mcvol = np.moveaxis(mcvol, 0, -2)
    mcvol = np.moveaxis(mcvol, 0, -3)
    mcvol = np.ascontiguousarray(mcvol)

    return mcvol

