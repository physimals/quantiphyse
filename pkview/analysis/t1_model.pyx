"""

Author: Benjamin Irving (benjamin.irv@gmail.com)
Copyright (c) 2013-2015 University of Oxford, Benjamin Irving

"""

import numpy as np
cimport numpy as np

from libcpp.vector cimport vector

cdef extern from "T10_calculation.h":
    vector[double] T10mapping (vector[vector[double]] & favols, vector[double] & fa, double TR)


def t10_map(fa_vols, fa, TR):

    """
    Wrapper for the c++ T10 mapping function

    Args:
        favols: List of volumes
        fa: Corresponding flip angles of each volume
        TR:

    Returns:

    """

    fa_vols2 = []

    shp1 = fa_vols[0].shape

    for ii in fa_vols:
        fa_vols2.append(np.ascontiguousarray(fa_vols.flatten()))

    T10array = T10mapping(fa_vols2, fa, TR)

    T10vol = np.reshape(T10array, shp1)

    return T10vol





