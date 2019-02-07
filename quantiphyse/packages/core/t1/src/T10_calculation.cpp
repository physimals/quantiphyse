//
// Created by engs1170 on 07/01/16.
//

#include "T10_calculation.h"
#include "linear_regression.h"


// Required for M_PI etc on Windows
#define _USE_MATH_DEFINES
#include <cmath>
#include <iostream>
#include <complex>

// Even with above, sometimes M_PI is not there...
#ifndef M_PI
    #define M_PI 3.14159265358979323846
#endif

using namespace std;

// Complex inverse cosine is part of C++11 so for Python 2.7 we need
// to define it. See Wolfram for details. This uses the same branch cut
// as the C++11 standard library function and has been tested for 
// agreement
const complex<double> I(0, 1);
const complex<double> ONE(1, 0);
const complex<double> PI2(M_PI / 2, 0);

static complex<double> acos_impl(complex<double> z)
{
	return PI2 + I*log(I * z + sqrt(ONE - z*z));
}


// TODO write a nonlinear version
// TODO Smoothing

// Perform VFA T1 mapping on a single voxel
// Linear mapping may underestimate the T1 values
double T10_single_linear(vector<double> &favox, vector<double> &fa_rad, ulong num_fa, double TR){

    vector<double> x(num_fa, 0);
    vector<double> y(num_fa, 0);
    double b, v1;
    double t1;

    for (ulong ii=0; ii<num_fa; ii++){
        x[ii] = favox[ii] / tan(fa_rad[ii]);
        y[ii] = favox[ii] / sin(fa_rad[ii]);
    }

    // Return intercept and gradient from linear regression.
    pair<double, double> ab = linreg(y, x);
    b = ab.second;

    // requiring gradient to be greater than 0
    if (b > 0) {
        v1 = log(b);
        t1 = -TR/v1;
    }
    else {
        t1 = 0;
    }

    // TODO for testing purposes
    if (t1 > 5.0){
        t1 = 5.0;
    }

    if (t1 < 0) {
        t1 = 0;
    }
    // Optional: calculate M0 as well
    return t1;
}

// Return the afi map for the region
//
//  Arguments:
//          afivols: nx2 Two vectors describing the two volumes
//          fa_afi: Flip angle of AFI map in degrees
// Ref 1: DOI 10.1002/mrm.21120
vector <double> afimapping(vector<vector<double> > afivols, double fa_afi, vector<double> TR_afi){

    ulong num_voxels = afivols[0].size();
    double TR1 = TR_afi.at(0);
    double TR2 = TR_afi.at(1);
    double n, r, alpha;
    complex<double> alphac;
    vector<double> K(num_voxels, 0);

    // Flip angle in radiation
    double flip_angle = fa_afi * (M_PI/180);

    for (unsigned int ii=0; ii < num_voxels; ii++){

//        cout << ii << endl;

        // n = TR2/ TR1
        n = TR2 / TR1;

        // r = Signal2/Signal1
        r = afivols[1][ii] / afivols[0][ii];

        // Eq 6 of Ref 1
        complex<double> cmpl ((r*n - 1) / (n-r), 0);
        alphac = acos_impl(cmpl);
        alpha = alphac.real();

        // Ration of actual flip angle and angle
        // This correction is applied to the flip angles of the T10 calculation
        K[ii] = alpha/flip_angle;

//        cout << "k: " << K[ii] << endl;
    }

    return K;

}

// Run through an entire array to perform T10 mapping
vector<double> T10mapping( vector< std::vector<double> > & favols, vector<double> & fa, double TR) {

    ulong num_fa = fa.size();
    ulong num_voxels = favols[0].size();

    vector<double> fa_rad (num_fa, 0);
    vector<double> favox(num_fa, 0);
    vector<double> t10vec(num_voxels, 0);

    // Convert flip angles to radians
    int cc = 0;
    for (vector<double>::iterator iter = fa.begin(); iter != fa.end(); iter++) {
        fa_rad[cc] = (*iter * (M_PI/180));
        cc++;
    }

    //cout << "t10 calculation for " << num_voxels << " voxels \n";
    // Loop through all voxels
    for (unsigned int jj=0; jj < num_voxels; jj++){

        // Store value at each fa
        for (unsigned int kk=0; kk < num_fa; kk++){
            favox[kk] = favols.at(kk).at(jj);
        }

        // Calculating T10
        t10vec[jj] = T10_single_linear(favox, fa_rad, num_fa, TR);
    }

    return t10vec;
}



// Run through an entire array to perform T10 mapping with AFI calculation
vector<double> T10mapping( dd favols, d fa, double TR, dd afivols, double fa_afi, d TR_afi) {

    ulong num_fa = fa.size();
    ulong num_voxels = favols[0].size();

    vector<double> fa_rad (num_fa, 0);
    vector<double> favox(num_fa, 0);
    vector<double> t10vec(num_voxels, 0);

    // AFI calculation
    vector<double> k = afimapping(afivols, fa_afi, TR_afi);

    //cout << "t10 calculation for " << num_voxels << " voxels \n";
    // Loop through all voxels
    for (unsigned int jj=0; jj < num_voxels; jj++){

        for (unsigned int ii =0; ii < num_fa; ii++) {
            fa_rad[ii] = (fa[ii] * k.at(jj) * (M_PI/180));
        }

        // Store value at each fa
        for (unsigned int kk=0; kk < num_fa; kk++){
            favox[kk] = favols.at(kk).at(jj);
        }

        // Calculating T10
        t10vec[jj] = T10_single_linear(favox, fa_rad, num_fa, TR);
    }

    return t10vec;
}
