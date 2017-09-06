/*


Author: Benjamin Irving (benjamin.irv@gmail.com)
Copyright (c) 2013-2015 University of Oxford, Benjamin Irving

*/

#include "ToftsWeinOffsetVp.h"

/*
Compute SE from Gd Concentration
*/

double compute_SE_from_Gd_concentration4(double Ct, double R1, double R2, double flip_angle, double TR, double TE, double T10)
{

    double alpha, P, Q, a, b, c, SE;

    alpha=flip_angle*PI/180;
    P=TR /T10;
    Q=R1 * Ct *TR;

    a = exp(-R2 * Ct * TE);
    b = 1 - exp(-P - Q) - (cos(alpha) * (exp(-P) - exp(-2*P - Q)));
    c = 1 - exp(-P) - (cos(alpha) * (exp(-P - Q) - exp(-2*P - Q)));

    SE = a * (b/c) - 1;

    return SE;
}

/*
Computation of Ct with weinmann AIF (extended Tofts model with vp*Cp)
*/
double Ct_with_weinmann_vp_aif(double a1, double a2, double m1, double m2, double offset, 
	double Ktrans, double kep, double time1, double offset_pk, double vp, double Dose)
{
    double time0;
    double Ct, Cp;

    time0=time1 -offset - offset_pk;

    if (time0 < 0) 
    {
        time1=0.0;
        Ct = 0;
    }
    else 
    {
        time1=time0;
        Cp = Dose * (a1 *exp(-m1*time1) + a2 * exp (-m2*time1));

        Ct =  Dose*Ktrans * ( (a1/(m1-kep))*(exp(-time1*kep) - exp(-time1*m1))
        + (a2/(m2-kep))*(exp(-time1*kep) - exp(-time1*m2)) ) + vp*Cp; 
    }
            
    return Ct;
}



/*
This is the main input function 
*/
double Tofts_model_with_weinmann_aif_offset_vp(double t, const double *x, 
	params_for_optimisation P1)
{

    //Optimisation parameters
    double Ktrans=x[0];
    double ve=x[1];
    double kep=Ktrans/ve;

    double offset_pk=x[2];
    double vp=x[3];

    // Other parameters
    double T10=P1.T10;
    //AIF
    double A1=P1.AIF[0];
    double A2=P1.AIF[1];
    double m1=P1.AIF[2];
    double m2=P1.AIF[3];
    double offset=P1.AIF[4];

    //Dose
    double Dose=P1.Dose;

    //Output
    double Ct, SE;

    //Running subfunctions
    Ct = Ct_with_weinmann_vp_aif(A1, A2, m1, m2, offset, Ktrans, kep, t, offset_pk, vp, Dose);

    double R1=P1.R1;
    double R2=P1.R2;
    double flip_angle=P1.dce_flip_angle;
    double TR=P1.dce_TR;
    double TE=P1.dce_TE;

    SE = compute_SE_from_Gd_concentration4(Ct, R1, R2, flip_angle, TR, TE, T10);

    return SE;
}


