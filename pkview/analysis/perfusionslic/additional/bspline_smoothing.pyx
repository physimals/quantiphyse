"""
Library to speed up B-spline processing of the whole image
"""

from __future__ import division, print_function

import numpy as np
cimport numpy as np
from scipy.interpolate import LSQUnivariateSpline, splrep, splev


def image_bspline_smooth(double[:, :, :, ::1] im4d, double[::1] splpos):

    """
    Apply B-spline smoothing to the whole image
    @param im4d: 4D image
    @param splpos: knot locations - positions in the time domain
    @return:
    """

    cdef Py_ssize_t nx =im4d.shape[0]
    cdef Py_ssize_t ny =im4d.shape[1]
    cdef Py_ssize_t nz =im4d.shape[2]
    cdef Py_ssize_t nt =im4d.shape[3]

    cdef double[::1] vec1 = np.zeros(nt, dtype=np.double)
    cdef double[::1] vec3 = np.zeros(nt, dtype=np.double)
    cdef double[::1] r1 = np.zeros(nt, dtype=np.double)

    cdef Py_ssize_t xx, yy, zz, ii

    for ii in range(nt):
        r1[ii] = ii

    for xx in range(ny):
        print(xx)
        for yy in range(ny):
            for zz in range(nz):

                # populate vector
                for ii in range(nt):
                    r1[ii] = ii
                    vec1[ii] = im4d[xx, yy, zz, ii]

                s = LSQUnivariateSpline(r1, vec1, splpos, k=4)
                #print(s.get_knots())
                vec3 = s(r1)

                for ii in range(nt):
                    im4d[xx, yy, zz, ii] = vec3[ii]

    return np.asarray(im4d)






