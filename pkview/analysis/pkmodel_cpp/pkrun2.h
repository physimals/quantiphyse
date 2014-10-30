#ifndef PKRUN2_H
#define PKRUN2_H

#include <cmath>
#include <vector>
#include <iostream>

#include "Optimizer_class.h"

using std::vector;

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

    vector<double> t1;
    vector< vector <double> > y1;
    vector<double> T101;

    // Output
    vector<vector<double> > outdata;
    vector<vector<double> > outdata2;
    vector <double> outdata3;

    double R1, R2, dce_flip_angle, dce_TR, dce_TE, Dose;

    // Values working on individual voxel level
    double AIF[5];
    double *t, *y;
    double T10;
    double res_min, res_count;

    OptimizeFunction OTofts;

public:

    // Constructor
    Pkrun2(std::vector<double> & t1, vector< std::vector<double> > & y1, std::vector<double> & T101in);

    // Destructor
    ~Pkrun2();

    void set_bounds(vector<double> & ub1, vector<double> & lb1);

    void set_parameters(double R1in, double R2in, double dce_flip_anglein, double dce_TRin, double dce_TEin, double Dosein);

    // run the pk model
    void rinit(int model1, double injtmins);

    double run(int pause1);

    const vector<vector<double> > get_parameters();
    vector<vector<double> > get_fitted_curve();
    const vector<double> get_residual();


};
}

#endif // PKRUN2_H
