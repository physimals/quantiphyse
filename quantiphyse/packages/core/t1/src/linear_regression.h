//
// Created by engs1170 on 07/01/16.
//
// References:
// 1) http://seismo.berkeley.edu/~kirchner/eps_120/Toolkits/Toolkit_10.pdf
//

#ifndef INC_25_T10_CALCULATION_LINEAR_REGRESSION_H
#define INC_25_T10_CALCULATION_LINEAR_REGRESSION_H

#include <vector>

// Arguments:
// y -
// x -
//
// Returns:
//      tuple (a, b) where a is the intercept and b is the gradient
std::pair<double, double> linreg (std::vector<double>, std::vector<double>);

//void linreg2 (std::vector<double>, std::vector<double>, double&, double&);


#endif //INC_25_T10_CALCULATION_LINEAR_REGRESSION_H
