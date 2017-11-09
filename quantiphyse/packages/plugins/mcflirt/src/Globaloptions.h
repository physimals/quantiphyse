/*  Globaloptions.h
    
    Copyright (C) 1999-2001 University of Oxford  */

/*  Part of FSL - FMRIB's Software Library
    http://www.fmrib.ox.ac.uk/fsl
    fsl@fmrib.ox.ac.uk
    
    Developed at FMRIB (Oxford Centre for Functional Magnetic Resonance
    Imaging of the Brain), Department of Clinical Neurology, Oxford
    University, Oxford, UK
    
    
    LICENCE
    
    FMRIB Software Library, Release 5.0 (c) 2012, The University of
    Oxford (the "Software")
    
    The Software remains the property of the University of Oxford ("the
    University").
    
    The Software is distributed "AS IS" under this Licence solely for
    non-commercial use in the hope that it will be useful, but in order
    that the University as a charitable foundation protects its assets for
    the benefit of its educational and research purposes, the University
    makes clear that no condition is made or to be implied, nor is any
    warranty given or to be implied, as to the accuracy of the Software,
    or that it will be suitable for any particular purpose or for use
    under any specific conditions. Furthermore, the University disclaims
    all responsibility for the use which is made of the Software. It
    further disclaims any liability for the outcomes arising from using
    the Software.
    
    The Licensee agrees to indemnify the University and hold the
    University harmless from and against any and all claims, damages and
    liabilities asserted by third parties (including claims for
    negligence) which arise directly or indirectly from the use of the
    Software or the sale of any products based on the Software.
    
    No part of the Software may be reproduced, modified, transmitted or
    transferred in any form or by any means, electronic or mechanical,
    without the express permission of the University. The permission of
    the University is not required if the said reproduction, modification,
    transmission or transference is done without financial return, the
    conditions of this Licence are imposed upon the receiver of the
    product, and all original and amended source code is included in any
    transmitted product. You may be held legally responsible for any
    copyright infringement that is caused or encouraged by your failure to
    abide by these terms and conditions.
    
    You are not permitted under this Licence to use this Software
    commercially. Use for which any financial return is received shall be
    defined as commercial use, and includes (1) integration of all or part
    of the source code or the Software into a product for sale or license
    by or on behalf of Licensee to third parties or (2) use of the
    Software or any derivative of it for research with the final aim of
    developing software products for sale or license to a third party or
    (3) use of the Software or any derivative of it for research with the
    final aim of developing non-software products for sale or license to a
    third party, or (4) use of the Software to provide any service to an
    external organisation for which payment is received. If you are
    interested in using the Software commercially, please contact Isis
    Innovation Limited ("Isis"), the technology transfer company of the
    University, to negotiate a licence. Contact details are:
    innovation@isis.ox.ac.uk quoting reference DE/9564. */

#ifndef __GLOBALOPTIONS_
#define __GLOBALOPTIONS_

#include <math.h>
#include <iostream>
#include <fstream>
#include <stdlib.h>
#include <stdio.h>
#include <string>
#include "newimage/newimageall.h"
#include "newimage/costfns.h"

enum anglereps { Euler, Quaternion };

using namespace NEWIMAGE;

class Globaloptions {
 public:
  static Globaloptions& getInstance();
  ~Globaloptions() { delete gopt; }
  
  string inputfname;
  string outputfname;
  int verbose;
  int no_params;
  int dof;
  int no_bins;
  int refnum;
  int no_volumes;
  int gdtflag;
  int edgeflag;
  int histflag;
  int matflag;
  int statflag;
  int plotflag;
  int tmpmatflag;
  int no_reporting;
  int costmeas;
  int meanvol;
  int sinc_final;
  int spline_final;
  int nn_final;
  int rmsrelflag;
  int rmsabsflag;
  float scaling;
  short datatype;
  float smoothsize;
  float rot_param;
  int no_stages;
  int fudgeflag;
  float fov;
  int twodcorrect;

  int reffileflag;
  string reffilename;

  string init_transform;

  costfns maincostfn;
  Costfn *impair;  
  Matrix initmat;
  anglereps anglerep;
  ColumnVector boundguess;

  void parse_command_line(int argc, char** argv);

 private:
  Globaloptions();
  
  const Globaloptions& operator=(Globaloptions&);
  Globaloptions(Globaloptions&);
      
  static Globaloptions* gopt;

  void print_usage(int argc, char *argv[]);
  
};

inline Globaloptions& Globaloptions::getInstance(){
  if(gopt == NULL)
    gopt = new Globaloptions();
  
  return *gopt;
}

inline Globaloptions::Globaloptions()
{
  outputfname = "";
  inputfname = "";
  no_params = 6;
  dof = 6;
  no_bins = 256;
  anglerep = Euler;
  verbose = 0;
  maincostfn = NormCorr;
  initmat = IdentityMatrix(4);
  impair = 0;
  refnum = -1;
  no_volumes = 0;
  gdtflag = 0;
  edgeflag = 0;
  histflag = 0;
  matflag = 0;
  statflag = 0;
  plotflag = 0;
  tmpmatflag = 0;
  meanvol = 0;
  costmeas = 0;
  no_reporting = 1;
  scaling = 6.0;
  smoothsize = 1.0;
  rot_param = 1;
  no_stages = 3;
  sinc_final = 0;
  spline_final = 0;
  nn_final = 0;
  rmsrelflag = 0;
  rmsabsflag = 0;
  fudgeflag = 0;
  fov = 20.0;
  twodcorrect = 0;
  reffileflag = 0;

  init_transform = "";

  boundguess.ReSize(2);
  boundguess << 10.0 << 1.0;

}

#endif










