"""
Processing labels in an efficient way using Cython
"""

from libc.float cimport DBL_MAX
import numpy as np
cimport numpy as cnp

def createlab(Py_ssize_t[:, :, ::1] slic_reg, double[::1] label_prob):
    """
    Create a labelled image based on the labels assigned to each region
    @param slic_reg: Regions to relabel
    @param label_prob: New label to assign. The indices of this label vector correspond to the
    supervoxel label in slic_reg
    @return:
    """

    cdef double[:, :, ::1] label_img_prob = np.zeros_like(slic_reg, dtype=np.double)
    cdef Py_ssize_t[:, :, ::1] subset = np.zeros_like(slic_reg, dtype=np.intp)

    a1 = np.shape(slic_reg)

    #Loop over each voxel and assign new label
    for xx in range(a1[0]):
        for yy in range(a1[1]):
            for zz in range(a1[2]):
                label_img_prob[xx, yy, zz] = label_prob[slic_reg[xx, yy, zz]]

    # Output new labelled array
    return np.asarray(label_img_prob)


def grouplab(Py_ssize_t[:, :, ::1] slic_reg, double[::1] label_prob, double[:,:,:,::1] img_feat):
    """
    Extract region matching a list of labels
    @param slic_reg: Regions to relabel
    @param label_prob: New label to assign
    @return:
    """

    a1 = np.shape(slic_reg)

    #Loop over each voxel and assign new label
    cdef int dd = 0
    for xx in range(a1[0]):
        for yy in range(a1[1]):
            for zz in range(a1[2]):
                if slic_reg[xx, yy, zz] in label_prob:
                    dd += 1

    sf1 = np.shape(img_feat)[-1]

    cdef Py_ssize_t[:, ::1] reg_inert = np.zeros((dd, 3), dtype=np.intp)
    cdef double[:, ::1] feat_inert = np.zeros((dd, sf1), dtype=np.double)

    #Loop over each voxel and assign new label
    cdef int cc = 0
    for xx in range(a1[0]):
        for yy in range(a1[1]):
            for zz in range(a1[2]):

                if slic_reg[xx, yy, zz] in label_prob:
                    reg_inert[cc, 0] = xx
                    reg_inert[cc, 1] = yy
                    reg_inert[cc, 2] = zz

                    for ii in range(sf1):
                        feat_inert[cc, ii] = img_feat[xx, yy, zz, ii]

                    cc += 1

    # Output new labelled array
    return np.asarray(reg_inert), np.asarray(feat_inert)

