/*
Tofts-Orton model to fit to signal enhancement (SE)
This version also fits offset for each pk model

double Tofts_model_with_orton_aif(double t, const double *x, 
                                params_for_optimisation P1)


Written by:
Benjamin Irving 
2013/08/08

References:
[1] M. R. Orton, J. a d’Arcy, S. Walker-Samuel, D. J. Hawkes, 
D. Atkinson, D. J. Collins, and M. O. Leach, 
“Computationally efficient vascular input function models for 
quantitative kinetic modelling using DCE-MRI.,” 
Physics in medicine and biology, vol. 53, no. 5, pp. 1225–39, Mar. 2008.

*/

#ifndef TOFTSWEINOFFSET_H
#define TOFTSWEINOFFSET_H

#include <cmath>

//include this to use the params_for_optimisation struct
#include "lmcurve.h"

#define PI 3.14159265

double Tofts_model_with_weinmann_aif_offset(double t, const double *x, params_for_optimisation P1);

#endif