/*


Author: Benjamin Irving (benjamin.irv@gmail.com)
Copyright (c) 2013-2015 University of Oxford, Benjamin Irving

*/

#include "ToftsOrton.h"

/*
Orton subfunction 
*/
double f(double time1, double alpha, double m1)
{

    double fta =(1/alpha) * (1-exp(-alpha*time1)) - (1/(alpha*alpha + m1*m1))*(alpha*cos(m1*time1) 
        + (m1 * sin(m1*time1)) - (alpha*exp(-alpha*time1)));
    return fta;
}

/*
Compute SE from Gd Concentration
*/
double compute_SE_from_Gd_concentration(double Ct, double R1, double R2, double flip_angle, double TR, double TE, double T10)
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
Computation of Ct with orton AIF
*/
double Ct_with_orton_aif(double a1, double a2, double m1, double m2, double offset, double Ktrans, double kep, double time1)
{
    double time0, tB, tmp1, tmp2;
    double Ct;

    time0=time1 -offset;

    if (time0 < 0) time1=0.0;
    else time1=time0;
    

    tB=(2*PI) /m1;

    tmp1=(a1*a2*Ktrans)/(kep-m2);
    tmp2=(((kep-m2)/a2)-1);

    if (time1 <=tB)
    {
        double ftm, ftkep;
        ftm = f(time1, m2, m1);
        ftkep=f(time1, kep, m1);
        Ct = tmp1 * (ftm + (tmp2 * ftkep));
    }
    else
    {
        double ftBm, ftBkep;
        ftBm =f(tB, m2, m1);
        ftBkep=f(tB, kep, m1);
        Ct = tmp1 * (ftBm * exp(-m2*(time1-tB)) + tmp2 * ftBkep * exp(-kep *(time1-tB)));
    }
    return Ct;

}

/*
This is the main input function 
*/

double Tofts_model_with_orton_aif(double t, const double *x, params_for_optimisation P1)
{

    //Optimisation parameters
    double Ktrans=x[0];
    double ve=x[1];
    double kep=Ktrans/ve;

    // Other parameters
    double T10=P1.T10;
    //AIF
    double A1=P1.AIF[0];
    double A2=P1.AIF[1];
    double m1=P1.AIF[2];
    double m2=P1.AIF[3];
    double offset=P1.AIF[4];

    //Output
    double Ct, SE;

    //Running subfunctions
    Ct = Ct_with_orton_aif(A1, A2, m1, m2, offset, Ktrans, kep, t);

    double R1=P1.R1;
    double R2=P1.R2;
    double flip_angle=P1.dce_flip_angle;
    double TR=P1.dce_TR;
    double TE=P1.dce_TE;

    SE = compute_SE_from_Gd_concentration(Ct, R1, R2, flip_angle, TR, TE, T10);

    return SE;
}


