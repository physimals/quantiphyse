/*


Author: Benjamin Irving (benjamin.irv@gmail.com)
Copyright (c) 2013-2015 University of Oxford, Benjamin Irving

*/

// Optimizer_class.cpp
#include "Optimizer_class.h"

OptimizeFunction::OptimizeFunction()
{
}

OptimizeFunction::~OptimizeFunction()
{
    // delete SEfit when object goes out of scope
    delete [] par_int;
    delete [] SEfit;
    delete [] SEfit_init;
    delete [] par;
}

/* Constructor */
void OptimizeFunction::set_data(int n_par1, double R1, double R2,
    double dce_TR, double dce_TE, double dce_flip_angle, double AIF [5], 
    int m_dat1, double Dose)
{
    //Initialisation of parameters (total number of parameters)
    n_par=n_par1;

    //number of points to be input
    m_dat=m_dat1;

    //Fixed scan parameters
    P1.R1=R1;
    P1.R2=R2;
    P1.dce_TR=dce_TR;
    P1.dce_TE=dce_TE;
    P1.dce_flip_angle=dce_flip_angle;
    P1.AIF=AIF;
    P1.Dose=Dose;

    //output and initial curves
    // Allocating memory in the class
    par_int = new double [n_par];
    par = new double [n_par];
    SEfit = new double [m_dat];
    SEfit_init = new double [m_dat];

    // Initialise random number generation based on time
    srand ((unsigned int)time(NULL));

}


void OptimizeFunction::SetModel(int model11)
{
    model1=model11;
    // Assign pointer to function of interest 
    // [To do]. Can change this to point to different functions to optimise
    //cout << "Using Tofts model with orton AIF" << endl;
    //PKfunc=Tofts_model_with_orton_aif;

    if (model1==1)
    {
        //cout << "Using Tofts model with orton AIF (with offset)" << endl;
        PKfunc=Tofts_model_with_orton_aif_offset;
        // Set number of variables to fit that this function has
        n_par_specific=3;
        P1.n_par=n_par_specific;


    }
    else if (model1==2)
    {
        //cout << "Using Tofts model with orton AIF (without offset)" << endl;
        PKfunc=Tofts_model_with_orton_aif;
        // Set number of variables to fit that this function has
        n_par_specific=2;
        P1.n_par=n_par_specific;

    }
    else if (model1==3)
    {
        //cout << "Using Tofts model with weinmann AIF (with offset)" << endl;
        PKfunc=Tofts_model_with_weinmann_aif_offset;
        // Set number of variables to fit that this function has
        n_par_specific=3;
        P1.n_par=n_par_specific;

    }
    else if (model1==4)
    {
        //cout << "Using Tofts model with weinmann AIF (with offset and vp)" << endl;
        PKfunc=Tofts_model_with_weinmann_aif_offset_vp;
        n_par_specific=4;
        P1.n_par=n_par_specific;
    }

}

void OptimizeFunction::SetVoxelParameters(double t1[], double y1[], double T10)
{
    // parameters to fit
    t=t1;
    y=y1;

    // Fixed voxel parameters
    P1.T10=T10;
}

/*
The function randomly initialises the PK parameter fit
*/
void OptimizeFunction::RandomInitialisation()
{
    
    // Ktrans initialisation
//    randnum=((double)rand()/(RAND_MAX));
    randnum = 0.5;
    par[0]=randnum*2;

    // ve initialisation
    //randnum=((double)rand()/(RAND_MAX));
    randnum = 0.5;
    par[1]=randnum*0.6 +0.4;

    if (model1==3)
    {
        par[2]=0;
    }
    else
    {
        //Including offset parameter if used
        //randnum=((double)rand()/(RAND_MAX));
        randnum = 0.5;
        par[2]=randnum*1.0;
    }

    //vp initialisation
    if (model1==4){
        par[3]=0;
    }

    // store initialised parameters separately (for comparison)
    int ii;
    for (ii=0; ii<n_par; ii++)
    {
        par_int[ii]=par[ii];
    }

}

void OptimizeFunction::Optimize()
{
    // setup controls
    control = lm_control_double;
    //control.printflags = 3; // monitor status (+1) and parameters (+2)

    lmcurve_fit_var( n_par_specific, par, m_dat, t, y, P1, PKfunc, &control, &status );
}


void OptimizeFunction::OptimizeConstrain(double *ub, double *lb)
{
    // setup controls
    control = lm_control_double;
    //control.printflags = 3; // monitor status (+1) and parameters (+2)

    P1.ub=ub;
    P1.lb=lb;

    lmcurve_fit_var_bound( n_par_specific, par, m_dat, t, y, P1, PKfunc, &control, &status);
}


/* 
Reset the parameters to a chosen value
*/
void OptimizeFunction::SetPars(double *pars)
{
    int ii;
    for (ii=0; ii<n_par; ii++)
    {
        par[ii]=pars[ii];
    }
    
}

void OptimizeFunction::GenCurve()
{
    int ii;
    residual=0;

    for ( ii = 0; ii < m_dat; ii++)
    {
        //Model fit
        SEfit[ii]=PKfunc(t[ii], par, P1);
        //Initial find using random parameters
        SEfit_init[ii]=PKfunc(t[ii], par_int, P1);
        //Calculating the residual;
        residual=residual + (y[ii]-SEfit[ii])*(y[ii]-SEfit[ii]);
    }
}


