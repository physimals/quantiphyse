//
// Created by engs1170 on 07/01/16.
//

#ifndef INC_25_T10_CALCULATION_T10_CALCULATION_H
#define INC_25_T10_CALCULATION_T10_CALCULATION_H

#include <vector>

typedef unsigned long ulong;

//
//
// fa - flip angles (radians)
std::vector<double> T10mapping( std::vector< std::vector<double> > & favols, std::vector<double> & fa, double TR = 1);


#endif //INC_25_T10_CALCULATION_T10_CALCULATION_H
