/*


Author: Benjamin Irving (benjamin.irv@gmail.com)
Copyright (c) 2013-2015 University of Oxford, Benjamin Irving

*/

#ifndef OPTIMIZER_CLASS_H
#define OPTIMIZER_CLASS_H

// std libraries
#include <stdio.h>
#include <iostream>
#include <cmath>
#include <stdlib.h> 
#include <time.h>

// My libraries
#include "lmcurve.h"

// Functions to optimise:
// Tofts-Orton method
#include "ToftsOrton.h"
#include "ToftsOrtonOffset.h"
#include "ToftsWeinOffset.h"
#include "ToftsWeinOffsetVp.h"
// Defined values

using namespace std;

// function to optimise the fit

class OptimizeFunction
{

public: 

//Input
int n_par, m_dat, model1;
// True number of parameters
int n_par_specific;
double *par, *par_fix, *t, *y;

// Structure to pass variables to C optimiser library
params_for_optimisation P1;

// Output:

double *SEfit, *SEfit_init, *par_int;

// Residual of the curve fit
double residual;

private:

// Controllers for C levenberg library
lm_status_struct status;
lm_control_struct control;

// Random number
double randnum;

// Pointer to function
double (*PKfunc)(double t, const double *x, params_for_optimisation P1);

public:

    OptimizeFunction();

    // Destructor
    ~OptimizeFunction();

  	// Get variables for optimisation
    void set_data(int n_par1, double R1, double R2, double dce_TR, double dce_TE,
        double dce_flip_angle, double AIF [5], int m_dat1, double Dose);

    //Set PK model
    void SetModel(int model1);

    //Set parameters for an individual optimisation
  	void SetVoxelParameters(double t1[], double y1[], double T10);

    //Random initialisation of parameters
    void RandomInitialisation();

  	// Run optimisation
    void Optimize();

    // Run optimisation
    void OptimizeConstrain(double *ub, double *lb);
  
    void SetPars(double * pars);

    // Generate output curve and residual
    void GenCurve();
  
  
};

#endif
