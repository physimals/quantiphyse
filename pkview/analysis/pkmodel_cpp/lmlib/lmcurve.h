/*
 * Project:  LevenbergMarquardtLeastSquaresFitting
 *
 * File:     lmcurve.h
 *
 * Contents: Simplified interface for one-dimensional curve fitting
 *
 * Author:   Joachim Wuttke 2010
 * 
 * Licence:  see ../COPYING (FreeBSD)
 * 
 * Homepage: joachimwuttke.de/lmfit
 */
 
#ifndef LMCURVE_H
#define LMCURVE_H

 #include<lmmin.h>

#ifdef __cplusplus
extern "C" {
#endif

// struct for storing all variables needed by the static function

typedef struct {
  int n_par;
  double *AIF;
  double R1;
  double R2;
  double dce_TR;
  double dce_TE;
  // changing parameters
  double dce_flip_angle;
  double T10;
  double *ub;
  double *lb;
  double Dose;
} params_for_optimisation;

//~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~Defining structs ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

typedef struct {
    const double *t;
    const double *y;
    double (*f) (double t, const double *par);
} lmcurve_data_struct;

// variable input
typedef struct {
    const double *t;
    const double *y;
    double (*f) (double t, const double *par, params_for_optimisation P1);
    params_for_optimisation params;
} lmcurve_data_struct_var;


// ~~~~~~~~~~~~~~ Fixed function ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
void lmcurve_fit( int n_par, double *par, int m_dat,
                  const double *t, const double *y,
                  double (*f)( double t, const double *par ),
                  const lm_control_struct *control, lm_status_struct *status );

//~~~~~~~~~~~ Allowing variance in the function ~~~~~~~~~~~~~~~~~~~~~~~~~

void lmcurve_fit_var( int n_par, double *par, int m_dat,
                  const double *t, const double *y, params_for_optimisation P1,
                  double (*f)( double t, const double *par, params_for_optimisation P1),
                  const lm_control_struct *control, lm_status_struct *status );

//~~~~~~~~~~~ Allowing variance in the function ~~~~~~~~~~~~~~~~~~~~~~~~~

void lmcurve_fit_var_bound( int n_par, double *par, int m_dat,
                  const double *t, const double *y, params_for_optimisation P1,
                  double (*f)( double t, const double *par, params_for_optimisation P1),
                  const lm_control_struct *control, lm_status_struct *status );


#ifdef __cplusplus
}
#endif

#endif /* LMCURVE_H */
