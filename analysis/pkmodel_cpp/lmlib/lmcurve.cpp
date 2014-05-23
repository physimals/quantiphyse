/* 

 Based on the following file:
 Project:  LevenbergMarquardtLeastSquaresFitting
 File:     lmcurve.c
 Author:   Joachim Wuttke 2010
 
 */
 
#ifdef __cplusplus
extern "C" {
#endif

#include "lmcurve.h"
#include "lmmin.h"

#include "stdio.h"

// ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~ Only fixed parameters ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

void lmcurve_evaluate( const double *par, int m_dat, const void *data,
                       double *fvec, int *info )
{
    int i;
    for ( i = 0; i < m_dat; i++ )
        fvec[i] =
            ((lmcurve_data_struct*)data)->y[i] -
            ((lmcurve_data_struct*)data)->f(
                ((lmcurve_data_struct*)data)->t[i], par);   

}


void lmcurve_fit( int n_par, double *par, int m_dat, 
                  const double *t, const double *y,
                  double (*f)( double t, const double *par),
                  const lm_control_struct *control, lm_status_struct *status )
{
    lmcurve_data_struct data;
    data.t=t;
    data.y=y;
    data.f=f;

    lmmin( n_par, par, m_dat, (const void*) &data,
           lmcurve_evaluate, control, status, lm_printout_std );
}


// ~~~~~~~~~~~~~~~~~~~ Allowing other parameters to vary in the function ~~~~~~~~~~~~~~~~~~~~~~~~~~~

void lmcurve_evaluate_var( const double *par, int m_dat, const void *data,
                       double *fvec, int *info )
{

    int i;
    for ( i = 0; i < m_dat; i++ )
    {
        fvec[i] =
            ((lmcurve_data_struct_var*)data)->y[i] -
            ((lmcurve_data_struct_var*)data)->f(
                ((lmcurve_data_struct_var*)data)->t[i], par,  ((lmcurve_data_struct_var*)data)->params);
    }

}


void lmcurve_fit_var( int n_par, double *par, int m_dat, 
                  const double *t, const double *y, params_for_optimisation P1,
                  double (*f)( double t, const double *par, params_for_optimisation P1),
                  const lm_control_struct *control, lm_status_struct *status )
{

    lmcurve_data_struct_var data;
    data.t=t;
    data.y=y;
    data.f=f;
    data.params=P1;

    lmmin( n_par, par, m_dat, (const void*) &data,
           lmcurve_evaluate_var, control, status, lm_printout_std );
}

// ~~~~~~~~~~~~~~~~~~~ Adding upper and lower bounds to the function ~~~~~~~~~~~~~~~~~~~~

void lmcurve_evaluate_var_bound( const double *par, int m_dat, const void *data,
                       double *fvec, int *info )
{

    int i, j;
    int n_par=((lmcurve_data_struct_var*)data)->params.n_par;

    // Upper and lower bounds
    double *ub, *lb;
    ub = ((lmcurve_data_struct_var*)data)->params.ub;
    lb = ((lmcurve_data_struct_var*)data)->params.lb;
    
    for ( i = 0; i < m_dat; i++)
    {
        fvec[i] =
            ((lmcurve_data_struct_var*)data)->y[i] -
            ((lmcurve_data_struct_var*)data)->f(
                ((lmcurve_data_struct_var*)data)->t[i], par,  ((lmcurve_data_struct_var*)data)->params);

        // Bounds add an additional penalty for going over bounds

        for (j=0; j<n_par; j++)
        {

          // Upper bound for each variable
          if (par[j]>ub[j])
          {
            fvec[i]=fvec[i] * (par[j]-ub[j]+1)*(par[j]-ub[j]+1);
          }

          // Lower bound for each variable
          if (par[j]<lb[j])
          {
            fvec[i]=fvec[i] * (-par[j]+lb[j]+1)*(-par[j]+lb[j]+1);
          }

        }
        
    }

}


void lmcurve_fit_var_bound( int n_par, double *par, int m_dat, 
                  const double *t, const double *y, params_for_optimisation P1,
                  double (*f)( double t, const double *par, params_for_optimisation P1),
                  const lm_control_struct *control, lm_status_struct *status )
{

    lmcurve_data_struct_var data;
    data.t=t;
    data.y=y;
    data.f=f;
    data.params=P1;

    lmmin( n_par, par, m_dat, (const void*) &data,
           lmcurve_evaluate_var_bound, control, status, lm_printout_std );
}

#ifdef __cplusplus
}
#endif