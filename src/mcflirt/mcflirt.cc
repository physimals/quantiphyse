/*  mcflirt.cc - Motion Correction FLIRT
    
    Peter Bannister, FMRIB Image Analysis Group
    
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

#include <math.h>
#include <iostream>
#include <iomanip>
#include <fstream>
#include <stdlib.h>
#include <stdio.h>
#include <string>
#include <sstream>
#include <stdexcept>

#include "newimage/newimageall.h"
#include "miscmaths/optimise.h"
#include "newimage/costfns.h"
#include "newmatap.h"

#include "Globaloptions.h"
#include "Log.h"

using namespace MISCMATHS;
using namespace NEWMAT;
using namespace NEWIMAGE;
using namespace UTILS;


//------------------------------------------------------------------------//

// OPTIMISATION SUPPORT


int vector2affine(const ColumnVector& inparams, int n, const ColumnVector& centre,
 		  Matrix& aff)
{
  ColumnVector tmp_params(3);
  ColumnVector params(12);

  if (n<=0) return 0;
  // order of parameters is 3 rotation + 3 translation + 3 scales + 3 skews
  // angles are in radians

  if ((bool)(Globaloptions::getInstance().twodcorrect)) {
    tmp_params = inparams;
    params = 0.0;
    // remember to keep scales at unity
    params(7) = 1.0; params(8) = 1.0; params(9) = 1.0;
    params(3) = tmp_params(1); params(4) = tmp_params(2); params(5) = tmp_params(3);
  } else
    params = inparams;
  
  switch (Globaloptions::getInstance().anglerep) 
    {
    case Euler:
      compose_aff(params,n,centre,aff,construct_rotmat_euler);
      break;
    case Quaternion:
      compose_aff(params,n,centre,aff,construct_rotmat_quat);
      break;
    default:
      cerr << "Invalid Rotation Representation" << endl;
      return -1;
    }
  return 0;
}  


int vector2affine(const ColumnVector& params, int n, Matrix& aff)
{
  return vector2affine(params,n,Globaloptions::getInstance().impair->testvol.cog("scaled_mm"),aff);
}


int affmat2vector(const Matrix& aff, int n, const ColumnVector& centre,
 		  ColumnVector& params)
{
  switch (Globaloptions::getInstance().anglerep) 
    {
    case Euler:
      decompose_aff(params,aff,centre,rotmat2euler);
      break;
    case Quaternion:
      decompose_aff(params,aff,centre,rotmat2quat);
      break;
    default:
      cerr << "Invalid Rotation Representation" << endl;
    }
  return 0;
}


int affmat2vector(const Matrix& aff, int n, ColumnVector& params)
 {
   return affmat2vector(aff,n,Globaloptions::getInstance().impair->testvol.cog("scaled_mm"),params);
 }


 void set_param_basis(Matrix &parambasis, int no_params)
 {
   parambasis = 0.0;
   for (int i=1; i<=no_params; i++) {
     parambasis(i,i)=1.0;
   }
 }

 void set_param_tols(ColumnVector &param_tol, int no_params)
 {
   Globaloptions& globalopts = Globaloptions::getInstance();
       // Tolerances are: 0.57 degrees (0.005 radians), 0.2mm translation
       //    0.02 scale and 0.001 skew
   float diagonal[12]={0.005, 0.005, 0.005, 0.2, 0.2, 0.2, 0.002, 0.002, 0.002,
   		      0.001, 0.001, 0.001};
   if (param_tol.Nrows()<no_params) {
     param_tol.ReSize(no_params);
   }
   for (int i=1; i<=no_params; i++) {
     param_tol(i)=diagonal[i-1];
   }
   for (int i=1; i<4; i++)
     param_tol(i) /= globalopts. rot_param;
 }


 void initialise_params(ColumnVector& params)
 {
   Real paramsf[12] = {0, 0, 0, 0, 0, 0, 1, 1, 1, 0, 0, 0};
   params << paramsf;
 }



 void powell_opt(ColumnVector& params, int no_params, ColumnVector& param_tol, 
 		int &no_its, float &fans, float (*costfunc)(const ColumnVector&), 
 		int itmax)
 {
   // sets up the initial parameters and calls the powell optimisation routine
   if (params.MaximumAbsoluteValue() < 0.001)  initialise_params(params);
   { 
     Matrix affmattst(4,4);
     vector2affine(params,no_params,affmattst);
   }
   Matrix parambasis(no_params,no_params);
   set_param_basis(parambasis,no_params);
   float ptol[13];
   for (int i=1; i<=no_params; i++) { ptol[i] = param_tol(i); }
  
   // the optimisation call
   //powell(params,parambasis,no_params,ptol,no_its, fans, costfunc, itmax);
   fans = MISCMATHS::optimise(params,no_params,param_tol,costfunc,no_its,itmax,
			      Globaloptions::getInstance().boundguess);
 }


void optimise(ColumnVector& params, int no_params, ColumnVector& param_tol, 
 	      int &no_its, float &fans, float (*costfunc)(const ColumnVector &), 
 	      int itmax=4)
{
  ColumnVector sub_params(3);
  ColumnVector sub_tols(3);
  
  if ((bool)(Globaloptions::getInstance().twodcorrect)){
    no_params = 3;
    sub_params(1) = params(3); sub_params(2) = params(4); sub_params(3) = params(5);
    sub_tols(1) = param_tol(3); sub_tols(2) = param_tol(4); sub_tols(3) = param_tol(5);
    powell_opt(sub_params,no_params,sub_tols,no_its,fans,costfunc,itmax);
  } else {
    powell_opt(params,no_params,param_tol,no_its,fans,costfunc,itmax);
  }
  

  if ((bool)(Globaloptions::getInstance().twodcorrect)){
    no_params = 12;
    cerr << "Params: " << sub_params(1) << " : " << sub_params(2) << " : " << sub_params(3) << endl;
    cerr << "Tolerances: " << sub_tols(1) << " : " << sub_tols(2) << " : " << sub_tols(3) << endl;
    params = sub_params;
    //params(3) = sub_params(1); params(4) = sub_params(2); params(5) = sub_params(3);
  }
  
}

 ////////////////////////////////////////////////////////////////////////////

 // OPTIMISATION SUPPORT (cost function interfaces)


 float costfn(const Matrix& uninitaffmat)
 {
   Tracer tr("costfn");

   Matrix affmat = uninitaffmat * Globaloptions::getInstance().initmat;  // apply initial matrix

   float retval = 0.0;
   Globaloptions& globalopts = Globaloptions::getInstance();
   if (globalopts.verbose>=20) {
     cerr << "Cost::affmat = " << endl << affmat << endl;
   }
 
   globalopts.impair->set_costfn(globalopts.maincostfn);

   retval = globalopts.impair->cost(affmat);  // breaking here
   return retval;
 }


 float costfn(const ColumnVector& params)
 {
   Tracer tr("costfn");

   Matrix affmat(4,4);
   vector2affine(params,Globaloptions::getInstance().no_params,affmat);
   float retval = costfn(affmat);

   return retval;
 }
  

 //------------------------------------------------------------------------//

 float estimate_scaling(const volume<float>& vol) {
   Tracer tr("estimate_scaling");
   return Min(Min(vol.xdim(),vol.ydim()),vol.zdim());
 }

 float estimate_scaling() {
   Tracer tr("estimate_scaling");
   return estimate_scaling(Globaloptions::getInstance().impair->refvol);
 }

 ////////////////////////////////////////////////////////////////////////////

 int optimise_strategy1(Matrix& matresult, float& fans, int input_dof, 
 		       int max_iterations, float new_tolerance)
 {
   Tracer tr("optimise_strategy1");
   // the most basic strategy - just do a single optimisation run at the
   //  specified dof
   int dof=input_dof;
   if (dof<6) { 
     cerr << "Erroneous dof " << dof << " : using 6 instead\n"; 
     dof=6; 
   }
   if (dof>12) {
     cerr << "Erroneous dof " << dof << " : using 12 instead\n"; 
     dof=12;
   }

   ColumnVector params(12), param_tol(12);
   int no_its=0;
   Globaloptions::getInstance().no_params = Max(dof, 6);
   set_param_tols(param_tol,12);
   param_tol = param_tol * new_tolerance;
   
   affmat2vector(matresult,dof,params);
   optimise(params,dof,param_tol,no_its,fans,costfn,max_iterations);
   vector2affine(params,dof,matresult);

   return no_its;
 
}  

 ////////////////////////////////////////////////////////////////////////////


 void usroptimise(Matrix &matresult, int usrdof, int usrmaxitn, float new_tolerance)
 {
   Tracer tr("usroptimise");
   // OPTIMISE
   int dof = Min(Globaloptions::getInstance().dof,usrdof);
  
   float costval=0.0;
   optimise_strategy1(matresult,costval,dof,usrmaxitn, new_tolerance);
 
   // matresult is the desired solution (cost is costval)
 }


void usrsetscale(volume<float>& newrefvol, volume<float>& newtestvol, int usrscale) {
   Tracer tr("usrsetscale");
   Costfn *globalpair=0;
   if (Globaloptions::getInstance().impair != 0) 
     delete Globaloptions::getInstance().impair;
   globalpair = new Costfn(newrefvol,newtestvol);
   globalpair->set_no_bins(Globaloptions::getInstance().no_bins/usrscale);
   globalpair->smoothsize = Globaloptions::getInstance().smoothsize;
   Globaloptions::getInstance().impair = globalpair;
 }


 void g_smooth(volume<float>& testvol) {
   Tracer tr("g_smooth");
   volume<float> result;
   
   result = testvol;
   volume<float> g_kern = gaussian_kernel3D(1.933, 8);
   testvol.setextrapolationmethod(mirror);
   result = convolve(testvol, g_kern);
   testvol = result;
 }

 ////////////////////////////////////////////////////////////////////////////
void double_end_slices(volume<float>& testvol)
{
  // this is necessary for single slice volumes so that interpolation can
  //  be done (in general it is good to do for small number of slices so
  //  that the end ones get counted and not de-weighted by the cost fns)
  volume<float> newtestvol(testvol.xsize(),testvol.ysize(),testvol.zsize()+2);
  newtestvol.setdims(testvol.xdim(),testvol.ydim(),8.0f);
  for (int z=0; z<= testvol.zsize()+1; z++) {
    for (int y=0; y<testvol.ysize(); y++) {
      for (int x=0; x<testvol.xsize(); x++) {
	int ez = z-1;
	if (ez<0) ez=0;
	if (ez>=testvol.zsize())  ez=testvol.zsize()-1;
	newtestvol(x,y,z) = testvol(x,y,ez);
      }
    }
  }
  testvol = newtestvol;
}

void fix2D(volume<float>& vol) 
{
  float fov = Globaloptions::getInstance().fov; // make a globaloption
  
  if ( (vol.zsize()<3) || (vol.zsize()*vol.zdim()<fov) || (bool)(Globaloptions::getInstance().twodcorrect)) {     
    Globaloptions::getInstance().twodcorrect = 1;
    Globaloptions::getInstance().smoothsize = 0.1;

    double_end_slices(vol);
  }
}


 void correct(const int direction, volume<float>& reference_volume, volume4D<float>& timeseries, const float scaling, const float new_tolerance, vector<Matrix>& mat_array_in, vector<Matrix>& mat_array_out, int mean_cond) {
   Tracer tr("correct");
   Globaloptions& globalopts = Globaloptions::getInstance();
   volume<float> testvol, newtestvol, refvol;
   Matrix offsettrans, finalmat(4,4);

   offsettrans=IdentityMatrix(4);
   int i=globalopts. refnum + direction;
   int stop = -1 - mean_cond;

   refvol = reference_volume;
   fix2D(refvol);
   
   if ((!Globaloptions::getInstance(). no_reporting) && (Globaloptions::getInstance().twodcorrect == 1))
     cerr << "restricting optimization to R_z, T_x and T_y" << endl;
    
   /*
     not the most elegant logic but if we come into this loop with i = -2, and with stop = -2
     (i.e. stage 4 + mean_reg), it crashes as it passes stopping cond. and tries to correct timeseries[-2]
   */

   if ((i == -2) && (stop == -1))
     stop = -2;
   
   while ( i != (direction == 1 ? globalopts. no_volumes : stop)) {
     if (!globalopts. no_reporting) 
       cerr << "[" << i << "]";
     testvol = timeseries[i];
     
     if (globalopts. edgeflag){
       if (!globalopts. no_reporting) 
	 cerr <<"Calculating contour image for volume [" << i << "]" << endl;
       fixed_edge_detect(testvol, 15000);  
     } else if (globalopts. gdtflag){
       if (!globalopts. no_reporting) 
	 cerr <<"Calculating gradient image for volume [" << i << "]" << endl;
       volume<float> gtempvol = testvol;
       gtempvol = gradient(testvol);
       testvol = gtempvol;
     }

     fix2D(testvol);

     offsettrans = mat_array_in[i];
     usrsetscale(refvol,testvol,(int) scaling);
     usroptimise(offsettrans,globalopts.dof,1,new_tolerance);

     finalmat = offsettrans * globalopts.initmat;
    
     mat_array_out[i] = finalmat;
     i += direction;
     
     if ((scaling == 8.0) && (i < globalopts. no_volumes - 1) && (i > -1) && (globalopts. fudgeflag == 0))
       // if first scaling level, use previous result to initialise next transformation search
       mat_array_in[i] = finalmat;
    
   }
 }

 void decompose_mats(int* mat_index, vector<Matrix>& mat_array, const volume<float>& refvol){
   Tracer tr("decompose_mats");
   Globaloptions& globalopts = Globaloptions::getInstance();
   Log& logger = Log::getInstance();
   Matrix level0(4,4), level1(4,4), level2(4,4), product(4,4);
   ColumnVector param_vec(12);
   ColumnVector center(3);
   float rmax = 80.0;
   float rms_rel_mean = 0.0;
   float rms_abs_mean = 0.0;
   float tmp_rms;

   string filename = globalopts. outputfname + ".par";
   string rms_rel_filename = globalopts. outputfname + "_rel.rms";
   string rms_abs_filename = globalopts. outputfname + "_abs.rms";
   string rms_rel_mean_filename = globalopts. outputfname + "_rel_mean.rms";
   string rms_abs_mean_filename = globalopts. outputfname + "_abs_mean.rms";

   ofstream outfile, rmsrelfile, rmsabsfile, rmsrelmeanfile, rmsabsmeanfile;

   param_vec = 0;   
   center(1) = 0.5*(refvol.xsize() - 1.0)*refvol.xdim();
   center(2) = 0.5*(refvol.ysize() - 1.0)*refvol.ydim();
   center(3) = 0.5*(refvol.zsize() - 1.0)*refvol.zdim();
   if (globalopts. plotflag)
     outfile. open(filename.c_str());
     
   string pathname = globalopts. inputfname;
   find_pathname(pathname);
   if (globalopts. matflag || globalopts. rmsrelflag || globalopts. rmsabsflag) {
     if (logger.establishDir(globalopts. outputfname + ".mat") != 0){
       cerr << "Error! Could not create directory: " << pathname << logger. getDir() << ". No write permission" << endl;
       globalopts. tmpmatflag = 0;
     }
   }

   if (globalopts. rmsrelflag){
     rmsrelfile. open(rms_rel_filename.c_str());
     for (int i = 1; i < globalopts. no_volumes; i++){
       tmp_rms = rms_deviation(mat_array[i-1], mat_array[i],center,rmax);
       rmsrelfile << tmp_rms << endl;
       rms_rel_mean += tmp_rms;
     }
     rmsrelmeanfile. open(rms_rel_mean_filename.c_str());
     rmsrelmeanfile << (rms_rel_mean/ (globalopts. no_volumes - 1)) << endl;
   }  
   
   
   if (globalopts. rmsabsflag){
     rmsabsfile. open(rms_abs_filename.c_str());
     for (int i = 0; i < globalopts. no_volumes; i++){
       tmp_rms = rms_deviation(IdentityMatrix(4), mat_array[i],center,rmax);
       rmsabsfile << tmp_rms << endl;
       rms_abs_mean += tmp_rms;
     }
     rmsabsmeanfile. open(rms_abs_mean_filename.c_str());
     rmsabsmeanfile << (rms_abs_mean/ globalopts. no_volumes) << endl;
   }
 
   for (int i = 0; i < globalopts. no_volumes; i++){
     if (i == globalopts. refnum){
       ostringstream osc;
       product = IdentityMatrix(4);
       osc << "MAT_" << setw(4) << setfill('0') << i;
       if (globalopts. tmpmatflag)
	 logger.out(osc.str().c_str(), product, false);
       if (globalopts. plotflag) {
	 decompose_aff(param_vec, product, refvol.cog("scaled_mm"), rotmat2euler);
	 if (!outfile) {
	   cerr << "error: unable to open output file!\n";
	   exit(0);
	 }
	 outfile << param_vec(1) << "  " << param_vec(2) << "  " 
		 << param_vec(3) << "  " << param_vec(4) << "  " 
		 << param_vec(5) << "  " << param_vec(6) << "  " << endl;
       }
       
     } else {
       ostringstream oscP;
       oscP << "MAT_" << setw(4) << setfill('0') << i;
       if (globalopts. matflag)
	 logger.out(oscP.str().c_str(), mat_array[i], false);
       if (globalopts. plotflag){
	 decompose_aff(param_vec, mat_array[i], refvol.cog("scaled_mm"), rotmat2euler);
	 if (!outfile) {
	   cerr << "error: unable to open output file!\n";
	   exit(0);
	 }
	 outfile << param_vec(1) << "  " << param_vec(2) << "  " 
		 << param_vec(3) << "  " << param_vec(4) << "  " 
		 << param_vec(5) << "  " << param_vec(6) << "  " << endl;
       }
     }
   }
 }

 void eval_costs(volume<float>& refvol, volume4D<float>& timeseries, vector<Matrix>& mat_array, float current_scale) {
   Globaloptions& globalopts = Globaloptions::getInstance();
   ofstream outfile;
   
   outfile. open("/usr/people/prb/medx/motion/releasetest/costs.txt");
   for (int i=0; i < globalopts. no_volumes; i++){
     usrsetscale(refvol, timeseries[i], (int)current_scale);
     outfile << costfn(mat_array[i]) << endl;
   }
 }

 
 void run_and_save_stats(const volume4D<float>& timeseries) {
   Tracer tr("run_and_save_stats");
   Globaloptions& globalopts = Globaloptions::getInstance();
   volume<float> variancevol, meanvol, sigmavol;
  
   int vmax = timeseries.tsize();

   meanvol = timeseries[0];
   variancevol = timeseries[0];
   sigmavol = timeseries[0];

   meanvol = 0.0;
   variancevol = 0.0;
   sigmavol = 0.0;

   // calculate the mean value and variance at each voxel
   for (int x=0; x< timeseries[0].xsize(); x++) {
     for (int y=0; y< timeseries[0].ysize(); y++) {
       for (int z=1; z< (timeseries[0].zsize()-1); z++) {
	 for (int i=0; i< vmax; i++) 
	   meanvol(x,y,z) += timeseries[i](x,y,z);
	 meanvol(x,y,z) = meanvol(x,y,z)/(float)vmax;
       }
     }
   }
   
   // change limits on z index for end slice exclusion
   for (int x=0; x< timeseries[0].xsize(); x++) {
     for (int y=0; y< timeseries[0].ysize(); y++) {
       for (int z=1; z< (timeseries[0].zsize()-1); z++) {
	 for (int i=0; i< vmax; i++) 
	   variancevol(x,y,z) += (timeseries[i](x,y,z) - meanvol(x,y,z))*(timeseries[i](x,y,z) - meanvol(x,y,z));
	 variancevol(x,y,z) = variancevol(x,y,z)/((float)(vmax - 1));
	 sigmavol(x,y,z) = sqrt(variancevol(x,y,z));
       }
     }
   }
   
   if (!globalopts. no_reporting) 
     cerr <<"Saving mean volume... " << endl;
   save_volume(meanvol, globalopts.outputfname+"_meanvol");
  
   if (!globalopts. no_reporting) 
     cerr <<"Saving variance volume... " << endl;
   save_volume(variancevol, globalopts.outputfname+"_variance");

   if (!globalopts. no_reporting) 
     cerr <<"Saving standard deviation volume... " << endl;
   save_volume(sigmavol, globalopts.outputfname+"_sigma");
 }

int exec_main (int argc,char** argv)
{
  Tracer tr("main");
  volume4D<float> timeseries, meanseries;
  volume<float> refvol, anisorefvol, testvol, meanvol, extrefvol;
  Globaloptions& globalopts = Globaloptions::getInstance();
  float current_scale=8.0, new_tolerance=0.8;
  int mat_index[3];
  ColumnVector centre(3);
  vector<Matrix> mat_array0, mat_array1, mat_array2;
  int mean_cond = 0;

  globalopts.parse_command_line(argc, argv);
  if (!globalopts. no_reporting) cerr << endl << "McFLIRT v 2.0 - FMRI motion correction" << endl << endl;
  int original_refvol=globalopts.refnum;
  if (!globalopts. no_reporting) cerr <<"Reading time series... " << endl;
  read_volume4D(timeseries, globalopts.inputfname);
  globalopts.datatype = dtype(globalopts.inputfname);
  globalopts. no_volumes = timeseries.tsize();
  
  for (int vol_count = 0; vol_count < globalopts. no_volumes; vol_count++) {
    mat_array0.push_back(IdentityMatrix(4));
    mat_array1.push_back(IdentityMatrix(4));
    mat_array2.push_back(IdentityMatrix(4));
  }

  if (globalopts. refnum == -1) globalopts. refnum = globalopts. no_volumes/2;

  for (int mean_its = 0; mean_its < 1 + globalopts. meanvol; mean_its++) {
    if (globalopts. no_stages>=1) {
      if (!globalopts. no_reporting) cerr <<"first iteration - 8mm scaling, set tolerance" << endl;
      new_tolerance=8*0.2*0.5; current_scale=8.0; mat_index[0] = (int) (new_tolerance*current_scale);
      
      if (mean_its == 0) {
        if (globalopts. reffileflag) {
          read_volume(extrefvol, globalopts. reffilename);
          anisorefvol = extrefvol;
          globalopts. refnum = -1;
        } else {
	  anisorefvol = timeseries[globalopts. refnum];
        }
      } else { //2nd pass - generate mean volume, clear mat_array0
	meanvol = timeseries[0];
	meanvol = 0.0;
	for (int i = 0; i < globalopts. no_volumes; i++){	  
	  testvol = timeseries[i];
	  timeseries[i].setextrapolationmethod(extraslice);
	  timeseries[i].setinterpolationmethod(trilinear);
	  affine_transform(timeseries[i],testvol,mat_array1[i],1.0);
	  meanvol = meanvol + testvol;
	}
	
	for (int x = 0; x < meanvol. xsize(); x++)
	  for (int y = 0; y < meanvol. ysize(); y++)
	    for (int z = 0; z < meanvol. zsize(); z++)
	      meanvol(x,y,z) = meanvol(x,y,z)/(float)globalopts. no_volumes;    
	
	save_volume(meanvol, globalopts.outputfname + "_mean_reg");
	
	anisorefvol = meanvol;
	globalopts. refnum = -1; // to ensure stopping condition in ::correct subroutine
	for (int i=0; i < globalopts. no_volumes; i++)
	  mat_array0[i] = IdentityMatrix(4);
	mean_cond = 1;
      }
      
      if (!globalopts. no_reporting)  cerr <<"Rescaling reference volume [" << globalopts. refnum << "] to " 
					   << current_scale << " mm pixels" << endl;
	
      refvol = isotropic_resample(anisorefvol,current_scale);
      
      fix2D(refvol);

      if (globalopts. edgeflag){
	if (!globalopts. no_reporting) cerr <<"Calculating contour image for reference volume" << endl;
	fixed_edge_detect(refvol, 15000);
	if (!globalopts. no_reporting) cerr <<"Saving contour reference volume... " << endl;
	save_volume(refvol, "crefvol_"+globalopts.outputfname);
      } else if (globalopts. gdtflag){
	if (!globalopts. no_reporting) cerr <<"Calculating gradient image for reference volume" << endl;
	volume<float> gtempvol = refvol;  gtempvol = gradient(refvol);
	if (!globalopts. no_reporting) cerr <<"Saving gradient reference volume... " << endl;
	save_volume(refvol, "grefvol_"+globalopts.outputfname);
      }
      
      globalopts.initmat=IdentityMatrix(globalopts.initmat.Nrows());
      if (!globalopts. no_reporting) cerr <<"Registering volumes ... ";
      correct(1, refvol, timeseries, current_scale, new_tolerance, mat_array0, mat_array1, mean_cond);
      correct(-1, refvol, timeseries, current_scale, new_tolerance, mat_array0, mat_array1, mean_cond);
    } else {
      for (int i=0; i<globalopts.no_volumes; i++)  mat_array1[i] = mat_array0[i];
    }
    
    if (globalopts. no_stages>=2) {
      if (!globalopts. no_reporting) cerr <<endl << "second iteration - drop to 4mm scaling" << endl;
      new_tolerance=4*0.2; current_scale=4.0; mat_index[1] = (int) (new_tolerance*current_scale);
      
      if (!globalopts. no_reporting) cerr <<"Rescaling reference volume [" << globalopts. refnum << "] to " 
					  << current_scale << " mm pixels" << endl;
      refvol = isotropic_resample(anisorefvol,current_scale);
      
      if (globalopts. edgeflag){
	if (!globalopts. no_reporting) cerr <<"Calculating contour image for reference volume" << endl;
	fixed_edge_detect(refvol, 15000);  
	if (!globalopts. no_reporting) cerr <<"Saving contour reference volume... " << endl;
	save_volume(refvol, "crefvol_"+globalopts.outputfname);
      } else if (globalopts. gdtflag){
	if (!globalopts. no_reporting) cerr <<"Calculating gradient image for reference volume" << endl;
	volume<float> gtempvol = refvol;
	gtempvol = gradient(refvol);
	if (!globalopts. no_reporting) cerr <<"Saving gradient reference volume... " << endl;
	save_volume(refvol, "grefvol_"+globalopts.outputfname);
      }
      
      if (!globalopts. no_reporting) cerr <<"Registering volumes ... ";
      correct(1, refvol, timeseries, current_scale, new_tolerance, mat_array1, mat_array2, mean_cond);
      correct(-1, refvol, timeseries, current_scale, new_tolerance, mat_array1, mat_array2, mean_cond);
    } else {
      for (int i=0; i<globalopts.no_volumes; i++)  mat_array2[i] = mat_array1[i];
    }
    
    
    if (globalopts. no_stages>=3) {
      if (!globalopts. no_reporting) cerr << endl << "third iteration - 4mm scaling, eighth tolerance" << endl;
      new_tolerance = 0.1; mat_index[2] = (int) (new_tolerance*current_scale);
      
      if (!globalopts. no_reporting) cerr <<"Registering volumes ... ";
      correct(1, refvol, timeseries, current_scale, new_tolerance, mat_array2, mat_array1, mean_cond);
      correct(-1, refvol, timeseries, current_scale, new_tolerance, mat_array2, mat_array1, mean_cond);
    } else {
      for (int i=0; i<globalopts.no_volumes; i++)  mat_array1[i] = mat_array2[i];
    }
  }
      
  mean_cond = 0;

  if (globalopts. no_stages>=4) {
    if (!globalopts. no_reporting) cerr << endl << "fourth iteration - 4mm scaling, eighth tolerance, sinc interpolation" << endl;
    
    if (!globalopts. no_reporting) cerr <<"Registering volumes ... ";
    if (globalopts.maincostfn == NormCorr)  globalopts.maincostfn = NormCorrSinc;
    correct(1, refvol, timeseries, current_scale, new_tolerance, mat_array1, mat_array0, mean_cond);
    correct(-1, refvol, timeseries, current_scale, new_tolerance, mat_array1, mat_array0, mean_cond);
  } else {
    for (int i=0; i<globalopts.no_volumes; i++)  mat_array0[i] = mat_array1[i];
  }

  Matrix init_trans(4,4);
  if (globalopts.init_transform.size()<1) {
    init_trans = IdentityMatrix(4);
  } else {
    init_trans = read_ascii_matrix(globalopts.init_transform);
  }

  // interpolate with final transform values
  for (int i=0; i < globalopts. no_volumes; i++){
    // initial testvol is used as the reference (for properties like sform)
    if (globalopts. reffileflag) {
      testvol = extrefvol; 
    } else {
      testvol = timeseries[i];  
    }
    if (globalopts. sinc_final) {
      timeseries[i].setextrapolationmethod(extraslice);
      timeseries[i].setinterpolationmethod(sinc);
      affine_transform(timeseries[i],testvol,mat_array0[i]*init_trans,1.0);
    } else  if (globalopts. nn_final) {
      timeseries[i].setextrapolationmethod(extraslice);
      timeseries[i].setinterpolationmethod(nearestneighbour);
      affine_transform(timeseries[i],testvol,mat_array0[i]*init_trans,1.0);
    } else  if (globalopts. spline_final) {
      timeseries[i].setextrapolationmethod(extraslice);
      timeseries[i].setinterpolationmethod(spline);
      affine_transform(timeseries[i],testvol,mat_array0[i]*init_trans,1.0);
    } else {
      timeseries[i].setextrapolationmethod(extraslice);
      timeseries[i].setinterpolationmethod(trilinear);
      affine_transform(timeseries[i],testvol,mat_array0[i]*init_trans,1.0);
    }
    timeseries[i] = testvol;
  }

  if (globalopts. statflag) run_and_save_stats(timeseries);
  if (globalopts. tmpmatflag) {
    if ( globalopts.reffileflag ) 
      decompose_mats(mat_index, mat_array0, extrefvol);
    else if ( globalopts.meanvol ) 
      decompose_mats(mat_index, mat_array0, meanvol);
    else {
       if (!globalopts. no_reporting) 
	 cout << "refnum = " << globalopts.refnum << endl << "Original_refvol = " << original_refvol << endl;
      if (globalopts.refnum<0) 
	throw(runtime_error("Negative refnum encountered when not in refile/meanvol mode."));
      decompose_mats(mat_index, mat_array0, timeseries[globalopts. refnum]);
    }
  }
  if (globalopts. costmeas) eval_costs(refvol, timeseries, mat_array0, current_scale);
  if (!globalopts. no_reporting) cerr << endl << "Saving motion corrected time series... " << endl;
  timeseries.setDisplayMaximumMinimum(timeseries.max(),timeseries.min());
  save_volume4D_dtype(timeseries, globalopts.outputfname, globalopts.datatype);
}

std::vector<float> mcflirt_run (std::vector<float> &vol, std::vector<int> &extent, std::vector<float> &voxeldims, std::vector<std::string> &opts)
{
  volume4D<float> meanseries;
  volume<float> refvol, anisorefvol, testvol, meanvol, extrefvol;

  // Default constructor sets default values
  Globaloptions& globalopts = Globaloptions::getInstance();
  float current_scale=8.0, new_tolerance=0.8;
  int mat_index[3];
  ColumnVector centre(3);
  vector<Matrix> mat_array0, mat_array1, mat_array2;
  int mean_cond = 0;

  // Turn vector of options into argc and then use CL parsing function
  // Use meaningless placeholders for filenames to stop program helpfully telling us its usage info and then stopping
  char *argv[opts.size()+5];
  argv[0] = strdup("mcflirt_run");
  argv[1] = strdup("-in");
  argv[2] = strdup("<numpy array>");
  argv[3] = strdup("-out");
  argv[4] = strdup("<numpy array>");
  for (int i=0; i<opts.size(); i++) {
    argv[i+5] = strdup(opts[i].c_str()); // FIXME leak
  }
  globalopts.parse_command_line(opts.size()+5, argv);

  if (!globalopts. no_reporting) cerr << endl << "McFLIRT v 2.0 - FMRI motion correction" << endl << endl;
  int original_refvol=globalopts.refnum;
  if (!globalopts. no_reporting) cerr <<"Reading time series... " << endl;

  if (extent.size() != 4) {
    throw std::runtime_error("Must be 4 dimension in extent");
  }
  if (voxeldims.size() != 4) {
    throw std::runtime_error("Must be 4 voxel dimensions");
  }
  // The volume object will not own the data using this constructor so no need to copy
  volume4D<float> timeseries(extent[0], extent[1], extent[2], extent[3], &vol[0]);
  timeseries.setxdim(voxeldims[0]);
  timeseries.setydim(voxeldims[1]);
  timeseries.setzdim(voxeldims[2]);
  timeseries.setTR(voxeldims[3]);
  globalopts. no_volumes = timeseries.tsize();

  for (int vol_count = 0; vol_count < globalopts. no_volumes; vol_count++) {
    mat_array0.push_back(IdentityMatrix(4));
    mat_array1.push_back(IdentityMatrix(4));
    mat_array2.push_back(IdentityMatrix(4));
  }

  if (globalopts. refnum == -1) globalopts. refnum = globalopts. no_volumes/2;

  for (int mean_its = 0; mean_its < 1 + globalopts. meanvol; mean_its++) {
    if (globalopts. no_stages>=1) {
      if (!globalopts. no_reporting) cerr <<"first iteration - 8mm scaling, set tolerance" << endl;
      new_tolerance=8*0.2*0.5; current_scale=8.0; mat_index[0] = (int) (new_tolerance*current_scale);

      if (mean_its == 0) {
        if (globalopts. reffileflag) {
          read_volume(extrefvol, globalopts. reffilename);
          anisorefvol = extrefvol;
          globalopts. refnum = -1;
        } else {
	  anisorefvol = timeseries[globalopts. refnum];
        }
      } else { //2nd pass - generate mean volume, clear mat_array0
	meanvol = timeseries[0];
	meanvol = 0.0;
	for (int i = 0; i < globalopts. no_volumes; i++){
	  testvol = timeseries[i];
	  timeseries[i].setextrapolationmethod(extraslice);
	  timeseries[i].setinterpolationmethod(trilinear);
	  affine_transform(timeseries[i],testvol,mat_array1[i],1.0);
	  meanvol = meanvol + testvol;
	}

	for (int x = 0; x < meanvol. xsize(); x++)
	  for (int y = 0; y < meanvol. ysize(); y++)
	    for (int z = 0; z < meanvol. zsize(); z++)
	      meanvol(x,y,z) = meanvol(x,y,z)/(float)globalopts. no_volumes;

	//save_volume(meanvol, globalopts.outputfname + "_mean_reg");

	anisorefvol = meanvol;
	globalopts. refnum = -1; // to ensure stopping condition in ::correct subroutine
	for (int i=0; i < globalopts. no_volumes; i++)
	  mat_array0[i] = IdentityMatrix(4);
	mean_cond = 1;
      }

      if (!globalopts. no_reporting)  cerr <<"Rescaling reference volume [" << globalopts. refnum << "] to "
					   << current_scale << " mm pixels" << endl;

      refvol = isotropic_resample(anisorefvol,current_scale);

      fix2D(refvol);

      if (globalopts. edgeflag){
	if (!globalopts. no_reporting) cerr <<"Calculating contour image for reference volume" << endl;
	fixed_edge_detect(refvol, 15000);
	//if (!globalopts. no_reporting) cerr <<"Saving contour reference volume... " << endl;
	//save_volume(refvol, "crefvol_"+globalopts.outputfname);
      } else if (globalopts. gdtflag){
	if (!globalopts. no_reporting) cerr <<"Calculating gradient image for reference volume" << endl;
	volume<float> gtempvol = refvol;  gtempvol = gradient(refvol);
	//if (!globalopts. no_reporting) cerr <<"Saving gradient reference volume... " << endl;
	//save_volume(refvol, "grefvol_"+globalopts.outputfname);
      }

      globalopts.initmat=IdentityMatrix(globalopts.initmat.Nrows());
      if (!globalopts. no_reporting) cerr <<"Registering volumes ... ";
      correct(1, refvol, timeseries, current_scale, new_tolerance, mat_array0, mat_array1, mean_cond);
      correct(-1, refvol, timeseries, current_scale, new_tolerance, mat_array0, mat_array1, mean_cond);
    } else {
      for (int i=0; i<globalopts.no_volumes; i++)  mat_array1[i] = mat_array0[i];
    }

    if (globalopts. no_stages>=2) {
      if (!globalopts. no_reporting) cerr <<endl << "second iteration - drop to 4mm scaling" << endl;
      new_tolerance=4*0.2; current_scale=4.0; mat_index[1] = (int) (new_tolerance*current_scale);

      if (!globalopts. no_reporting) cerr <<"Rescaling reference volume [" << globalopts. refnum << "] to "
					  << current_scale << " mm pixels" << endl;
      refvol = isotropic_resample(anisorefvol,current_scale);

      if (globalopts. edgeflag){
	if (!globalopts. no_reporting) cerr <<"Calculating contour image for reference volume" << endl;
	fixed_edge_detect(refvol, 15000);
	//if (!globalopts. no_reporting) cerr <<"Saving contour reference volume... " << endl;
	//save_volume(refvol, "crefvol_"+globalopts.outputfname);
      } else if (globalopts. gdtflag){
	if (!globalopts. no_reporting) cerr <<"Calculating gradient image for reference volume" << endl;
	volume<float> gtempvol = refvol;
	gtempvol = gradient(refvol);
	//if (!globalopts. no_reporting) cerr <<"Saving gradient reference volume... " << endl;
	//save_volume(refvol, "grefvol_"+globalopts.outputfname);
      }

      if (!globalopts. no_reporting) cerr <<"Registering volumes ... ";
      correct(1, refvol, timeseries, current_scale, new_tolerance, mat_array1, mat_array2, mean_cond);
      correct(-1, refvol, timeseries, current_scale, new_tolerance, mat_array1, mat_array2, mean_cond);
    } else {
      for (int i=0; i<globalopts.no_volumes; i++)  mat_array2[i] = mat_array1[i];
    }


    if (globalopts. no_stages>=3) {
      if (!globalopts. no_reporting) cerr << endl << "third iteration - 4mm scaling, eighth tolerance" << endl;
      new_tolerance = 0.1; mat_index[2] = (int) (new_tolerance*current_scale);

      if (!globalopts. no_reporting) cerr <<"Registering volumes ... ";
      correct(1, refvol, timeseries, current_scale, new_tolerance, mat_array2, mat_array1, mean_cond);
      correct(-1, refvol, timeseries, current_scale, new_tolerance, mat_array2, mat_array1, mean_cond);
    } else {
      for (int i=0; i<globalopts.no_volumes; i++)  mat_array1[i] = mat_array2[i];
    }
  }

  mean_cond = 0;

  if (globalopts. no_stages>=4) {
    if (!globalopts. no_reporting) cerr << endl << "fourth iteration - 4mm scaling, eighth tolerance, sinc interpolation" << endl;

    if (!globalopts. no_reporting) cerr <<"Registering volumes ... ";
    if (globalopts.maincostfn == NormCorr)  globalopts.maincostfn = NormCorrSinc;
    correct(1, refvol, timeseries, current_scale, new_tolerance, mat_array1, mat_array0, mean_cond);
    correct(-1, refvol, timeseries, current_scale, new_tolerance, mat_array1, mat_array0, mean_cond);
  } else {
    for (int i=0; i<globalopts.no_volumes; i++)  mat_array0[i] = mat_array1[i];
  }

  Matrix init_trans(4,4);
  if (globalopts.init_transform.size()<1) {
    init_trans = IdentityMatrix(4);
  } else {
    init_trans = read_ascii_matrix(globalopts.init_transform);
  }

  // interpolate with final transform values
  for (int i=0; i < globalopts. no_volumes; i++){
    // initial testvol is used as the reference (for properties like sform)
    if (globalopts. reffileflag) {
      testvol = extrefvol;
    } else {
      testvol = timeseries[i];
    }
    if (globalopts. sinc_final) {
      timeseries[i].setextrapolationmethod(extraslice);
      timeseries[i].setinterpolationmethod(sinc);
      affine_transform(timeseries[i],testvol,mat_array0[i]*init_trans,1.0);
    } else  if (globalopts. nn_final) {
      timeseries[i].setextrapolationmethod(extraslice);
      timeseries[i].setinterpolationmethod(nearestneighbour);
      affine_transform(timeseries[i],testvol,mat_array0[i]*init_trans,1.0);
    } else  if (globalopts. spline_final) {
      timeseries[i].setextrapolationmethod(extraslice);
      timeseries[i].setinterpolationmethod(spline);
      affine_transform(timeseries[i],testvol,mat_array0[i]*init_trans,1.0);
    } else {
      timeseries[i].setextrapolationmethod(extraslice);
      timeseries[i].setinterpolationmethod(trilinear);
      affine_transform(timeseries[i],testvol,mat_array0[i]*init_trans,1.0);
    }
    timeseries[i] = testvol;
  }

  if (globalopts. statflag) run_and_save_stats(timeseries);
  if (globalopts. tmpmatflag) {
    if ( globalopts.reffileflag )
      decompose_mats(mat_index, mat_array0, extrefvol);
    else if ( globalopts.meanvol )
      decompose_mats(mat_index, mat_array0, meanvol);
    else {
       if (!globalopts. no_reporting)
	 cout << "refnum = " << globalopts.refnum << endl << "Original_refvol = " << original_refvol << endl;
      if (globalopts.refnum<0)
	throw(runtime_error("Negative refnum encountered when not in refile/meanvol mode."));
      decompose_mats(mat_index, mat_array0, timeseries[globalopts. refnum]);
    }
  }
  if (globalopts. costmeas) eval_costs(refvol, timeseries, mat_array0, current_scale);
  if (!globalopts. no_reporting) cerr << endl << "Saving motion corrected time series... " << endl;
  timeseries.setDisplayMaximumMinimum(timeseries.max(),timeseries.min());

  // Copy each time slice into a vector for returning
  // FIXME not clear why we can't just return vol since changes are inplace. But it doesn't work...
  vector<float> retvol;
  for (int t=0; t<extent[3]; t++) {
    retvol.insert(retvol.end(), timeseries[t].fbegin(), timeseries[t].fend());
  }

  return retvol;
}
