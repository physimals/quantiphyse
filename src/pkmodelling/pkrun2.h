/*


Author: Benjamin Irving (benjamin.irv@gmail.com)
Copyright (c) 2013-2015 University of Oxford, Benjamin Irving

*/


#ifndef PKRUN2_H
#define PKRUN2_H

#include <cmath>
#include <vector>
#include <iostream>

#include "Optimizer_class.h"

/*
    //~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~ bounds ~~~~~~~~~~~~~~~

    // Sets the maximum number of parameters that we can use
    n_par = 4; // number of parameters in model function f
    ub[0]= 10; ub[1]=1; ub[2]=0.5; ub[3]=0.5;
    lb[0]=0; lb[1]=0.05; lb[2]=-0.5; lb[3]=0;

    Parameters used in the other versions.
    Note that the chosen model must also be changed
    Wein / WeinOff
    double ub[4]={10, 1, 10, 0.5};
    double lb[4]={0, 0.05, 0, 0};

    WeinOffVp
    double ub[4]={10, 1, 10, 0.4};
    double lb[4]={0, 0.05, 0, 0};

*/

namespace pkmodellingspace {

class Pkrun2 {
/*
This is the wrapper class to control the Pkrun from a GUI or some other controller.
The actuall work on a per voxel basis is done by OptimizerClass
*/

private:
    // counters
    int pcur, ii, pp, qq, ss;

    int m_t1, mrows, ncols, n_t101;

    int n_par; // number of parameters in model function f
    double pars3[4], ub[4], lb[4];

    std::vector<double> t1;
    std::vector< std::vector <double> > y1;
    std::vector<double> T101;

    // Output
    std::vector<std::vector<double> > outdata;
    std::vector<std::vector<double> > outdata2;
    std::vector <double> outdata3;

    double R1, R2, dce_flip_angle, dce_TR, dce_TE, Dose;

    // Values working on individual voxel level
    double AIF[5];
    double *t, *y;
    double T10;
    double res_min;

    OptimizeFunction OTofts;

public:

    // Constructor
    // Missing a std:: in declaration
    Pkrun2(std::vector<double> & t1, std::vector< std::vector<double> > & y1, std::vector<double> & T101in);

    // Destructor
    ~Pkrun2();

    void set_bounds(std::vector<double> & ub1, std::vector<double> & lb1);

    void set_parameters(double R1in, double R2in, double dce_flip_anglein, double dce_TRin, double dce_TEin, double Dosein);

    // calculate the Contrast to noise ratio for each voxel
    void calculate_CNR();

    // run the pk model
    std::string rinit(int model1, double injtmins);
    std::string run(int pause1);

    const std::vector<std::vector<double> > get_parameters();
    std::vector<std::vector<double> > get_fitted_curve();
    const std::vector<double> get_residual();


};
}

#endif // PKRUN2_H
