//
// Created by engs1170 on 07/01/16.
//

#include "T10_calculation.h"
#include "linear_regression.h"

#include <cmath>
#include <iostream>

using namespace std;

// TODO write a nonlinear version
// TODO Smoothing

// Perform VFA T1 mapping on a single voxel
// Linear mapping may underestimate the T1 values
double T10_single_linear(vector<double> &favox, vector<double> &fa_rad, ulong num_fa, double TR){

    vector<double> x(num_fa, 0);
    vector<double> y(num_fa, 0);
    double a, b, v1, v2;
    double t1;

    for (int ii=0; ii<num_fa; ii++){
        x[ii] = favox[ii] / tan(fa_rad[ii]);
        y[ii] = favox[ii] / sin(fa_rad[ii]);
    }

    // Return intercept and gradient from linear regression.
    tie(a, b) = linreg(y, x);

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
    vector<double> K(num_voxels, 0);

    // Flip angle in radiation
    double flip_angle = fa_afi * (M_PI/180);


    for (int ii=0; ii < num_voxels; ii++){

        cout << ii << endl;

        // n = TR2/ TR1
        n = TR2 / TR1;

        // r = Signal2/Signal1
        r = afivols[0][ii] / afivols[1][ii];

        // Eq 6 of Ref 1
        alpha = acos((r*n - 1) / (n-r));

        // Ration of actual flip angle and angle
        // This correction is applied to the flip angles of the T10 calculation
        K[ii] = alpha/flip_angle;
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
    cout << "Converting flip angles to radians \n";
    int cc = 0;
    for (double ii : fa) {
        fa_rad[cc] = (ii * (M_PI/180));
        cc++;
    }

    cout << "t10 calculation for " << num_voxels << " voxels \n";
    // Loop through all voxels
    for (int jj=0; jj < num_voxels; jj++){

        // Store value at each fa
        for (int kk=0; kk < num_fa; kk++){
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


    // Convert flip angles to radians
    cout << "Converting flip angles to radians \n";
    int cc = 0;
    for (double ii : fa) {
        fa_rad[cc] = (ii * k.at(cc) * (M_PI/180));
        cc++;
    }

    cout << "t10 calculation for " << num_voxels << " voxels \n";
    // Loop through all voxels
    for (int jj=0; jj < num_voxels; jj++){

        // Store value at each fa
        for (int kk=0; kk < num_fa; kk++){
            favox[kk] = favols.at(kk).at(jj);
        }

        // Calculating T10
        t10vec[jj] = T10_single_linear(favox, fa_rad, num_fa, TR);
    }

    return t10vec;
}
