"""
Quantiphyse - Wrapper for C++ based DCE modelling code

Copyright (c) 2013-2018 University of Oxford
"""

# Cython interface file for wrapping the object

import numpy as np
cimport numpy as np

from libcpp.vector cimport vector
from libcpp.string cimport string

# c++ interface to cython
cdef extern from "pkrun2.h" namespace "pkmodellingspace":
  cdef cppclass Pkrun2:
        Pkrun2(vector[double] &, vector[vector[double]] &, vector[double] &) except +
        void set_bounds(vector[double] & ub1, vector[double] & lb1)
        void set_parameters(double R1in, double R2in, double dce_flip_anglein,
                            double dce_TRin, double dce_TEin, double Dosein)
        string rinit(int model1, double injtmins)
        string run(int pause1)
        vector[vector[double] ] get_parameters()
        vector[vector[double] ] get_fitted_curve()
        vector[double] get_residual()

# creating a cython wrapper class
cdef class PyPk:
    cdef Pkrun2 *thisptr      # hold a C++ instance which we're wrapping
    def __cinit__(self, vector [double] t1, vector[vector[double]] y1, vector[double] T101):
        self.thisptr = new Pkrun2(t1, y1, T101)
    def __dealloc__(self):
        del self.thisptr
    def set_bounds(self, ub1, lb1):
        self.thisptr.set_bounds(ub1, lb1)
    def set_parameters(self, R1in, R2in, dce_flip_anglein, dce_TRin, dce_TEin, Dosein):
        self.thisptr.set_parameters(R1in, R2in, dce_flip_anglein, dce_TRin, dce_TEin, Dosein)
    def rinit(self, model1, injtmins):
        return self.thisptr.rinit(model1, injtmins)
    def run(self, pause1):
        return self.thisptr.run(pause1)
    def get_parameters(self):
        return self.thisptr.get_parameters()
    def get_fitted_curve(self):
        return self.thisptr.get_fitted_curve()
    def get_residual(self):
        return self.thisptr.get_residual()
