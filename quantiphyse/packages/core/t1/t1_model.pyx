"""
Quantiphyse - Wrapper for C++ T1 mapping code

Copyright (c) 2013-2018 University of Oxford
"""

import numpy as np
cimport numpy as np

from libcpp.vector cimport vector

cdef extern from "T10_calculation.h":
    vector[double] T10mapping (vector[vector[double]] & favols, vector[double] & fa, double TR)
    vector[double] T10mapping (vector[vector[double]] & favols, vector[double] & fa, double TR,
                               vector[vector[double]] & afi_vols, double fa, vector[double] & TR)

def t10_map(fa_vols, fa, TR, afi_vols=None, fa_afi=None, TR_afi=None):

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

    for fa1 in fa_vols:
        fa_vols2.append(np.ascontiguousarray(fa1.flatten()))

    if afi_vols is None:
        T10array = T10mapping(fa_vols2, fa, TR)

    else:
        afi_vols2 = []

        for afi1 in afi_vols:
            afi_vols2.append(np.ascontiguousarray(afi1.flatten()))

        T10array = T10mapping(fa_vols2, fa, TR, afi_vols2, fa_afi, TR_afi)

    T10vol = np.reshape(T10array, shp1)

    return T10vol





