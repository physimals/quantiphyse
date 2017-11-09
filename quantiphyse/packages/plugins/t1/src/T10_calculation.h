//
// Created by engs1170 on 07/01/16.
//

#ifndef INC_25_T10_CALCULATION_T10_CALCULATION_H
#define INC_25_T10_CALCULATION_T10_CALCULATION_H

#include <sys/types.h>
#include <vector>

typedef size_t ulong;

typedef std::vector< std::vector<double> > & dd;
typedef std::vector<double> & d;

//
//
// fa - flip angles (radians)
// Without AFI calculation
std::vector<double> T10mapping( dd favols, d fa, double TR = 1.0);

// With AFI calculation
std::vector<double> T10mapping( dd favols, d fa, double TR, dd afivols, double fa_afi,  d TR_afi);


#endif //INC_25_T10_CALCULATION_T10_CALCULATION_H
