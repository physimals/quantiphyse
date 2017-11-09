//
// Created by engs1170 on 07/01/16.
//

#include "linear_regression.h"

using namespace std;

// Simple linear regression for 1D feature vectors
// y = a + bx
//
// b = Cov(x, y)/var(x) = Sxy/Sx
// a = y_mean - b * x_mean
//

double vec_mean(vector<double> x)
{
    double x_mean = 0;

    for (vector<double>::iterator iter = x.begin(); iter != x.end(); iter++) {
        x_mean += *iter;
    }
    x_mean = x_mean / x.size();
    return x_mean;

}

pair<double, double> linreg (vector<double> y, vector<double> x)
{
    // y_mean, x_mean
    double y_mean, x_mean;
    // Sx, Sxy
    double Sx, Sxy;
    // a, b
    double a, b;

    // Calculate the means
    y_mean = vec_mean(y);
    x_mean = vec_mean(x);

    // Calculate the covariance and variance
    Sx = 0;
    Sxy = 0;
    for (unsigned int ii=0; ii<y.size(); ii++) {
        Sx += (x.at(ii) - x_mean) * (x.at(ii) - x_mean);
        Sxy += (x.at(ii) - x_mean) * (y.at(ii) - y_mean);
    }

    // Calculating gradient and intercept
    b = Sxy/Sx;
    a = y_mean - b * x_mean;

    return pair<double, double>(a, b);
};

//void linreg2 (vector<double> y, vector<double> x, double & a, double & b)
//{
//    a = 1.2;
//    b = 2.3;
//};