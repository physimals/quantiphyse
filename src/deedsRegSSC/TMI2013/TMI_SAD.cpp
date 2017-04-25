/*
 Copyright (c) 2014, Mattias P. Heinrich
 Contact: heinrich(at)imi.uni-luebeck.de
 www.mpheinrich.de
 All rights reserved.
 
 Redistribution and use in source and binary forms, with or without
 modification, are permitted provided that the following conditions are met:
 
 1. Redistributions of source code must retain the above copyright notice, this
 list of conditions and the following disclaimer.
 2. Redistributions in binary form must reproduce the above copyright notice,
 this list of conditions and the following disclaimer in the documentation
 and/or other materials provided with the distribution.
 
 THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS" AND
 ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
 WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE
 DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT OWNER OR CONTRIBUTORS BE LIABLE FOR
 ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES
 (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES;
 LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND
 ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT
 (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF THIS
 SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.
 
 The views and conclusions contained in the software and documentation are those
 of the authors and should not be interpreted as representing official policies,
 either expressed or implied, of the FreeBSD Project.
*/
 
/*
 If you use this implementation or parts of it please cite:
 
 "MRF-Based Deformable Registration and Ventilation Estimation of Lung CT."
 by Mattias P. Heinrich, M. Jenkinson, M. Brady and J.A. Schnabel
 IEEE Transactions on Medical Imaging 2013, Volume 32, Issue 7, July 2013, Pages 1239-1248
 http://dx.doi.org/10.1109/TMI.2013.2246577
 
 or
 
 "Globally optimal deformable registration
 on minimum spanning tree using dense displacement sampling."
 by Mattias P. Heinrich, M. Jenkinson, M. Brady and J.A. Schnabel
 MICCAI (3) 2012: 115-122
 http://dx.doi.org/10.1007/978-3-642-33454-2_15
 
 
 Tested with g++ on Mac OS X and Linux Ubuntu, compile with:
 
 g++ TMI_SAD.cpp -O3 -lpthread -msse4.2 -o tmiSAD
 
 replace msse4.2 by your current SSE version if needed
 for Windows you might need MinGW or CygWin
 
Input volumes should have same dimensions and be in nifti-format.

 */

#include <sstream>
#include <fstream>
#include <iostream>
#include <map>
#include <vector>
#include <algorithm>
#include <numeric>
#include <sys/time.h>
#include <math.h>
#include <inttypes.h>
#include <pthread.h>
#include <xmmintrin.h>
#include <pmmintrin.h>

using namespace std;


#include "deedsMSTsad.h"

int main(int argc, const char * argv[])
{
    
    if(argc<4||argv[1][1]=='h'){
        cout<<"=============================================================\n";
        cout<<"Usage (required input arguments):\n";
        cout<<"./tmiSAD -F fixed.nii -M moving.nii -O output\n";
        cout<<"optional parameters:\n";
        cout<<" -a <regularisation parameter alpha> (default 2.0)\n";
        cout<<" -r <number of random samples per node> (default 64)\n";
        cout<<" -l <number of levels> (default 5)\n";
        cout<<" -G <grid spacing for each level> (default 7x6x5x4x3)\n";
        cout<<" -L <maximum search radius - each level> (default 6x5x4x3x2)\n";
        cout<<" -Q <quantisation of search step size> (default 5x4x3x2x1)\n";
        cout<<" -s <use symmetric approach> (default 1)\n";
        cout<<" -S <moving_segmentation.nii> (short int)\n";
        cout<<"=============================================================\n";
        return 1;
    }
    
    
    typedef pair<char,int> val;
    map<char,int> argin;
    argin.insert(val('F',0));
    argin.insert(val('M',1));
    argin.insert(val('O',2));
    argin.insert(val('a',3));
    argin.insert(val('r',4));
    argin.insert(val('l',5));
    argin.insert(val('G',6));
    argin.insert(val('L',7));
    argin.insert(val('Q',8));
    argin.insert(val('s',9));
    argin.insert(val('S',10));
    
    // parsing the input
    int requiredArgs=0;
    char* fixedfile=new char[200];
    char* movingfile=new char[200];
    char* outputstem=new char[200];
    char* movsegfile=new char[200];
    
    float alpha=2.0;
    int randsamp=64;
    int maxlevel=5;
    int num=maxlevel; int num2=maxlevel; int num3=maxlevel;
    int s_grid[10]={7,6,5,4,3,2,2,2,2,2};
    int s_search[10]={6,5,4,3,2,1,1,1,1,1};
    int s_quant[10]={5,4,3,2,1,1,1,1,1,1};
    char levelstr[]="%dx%dx%dx%dx%dx%dx%dx%dx%dx%d";
    
    bool symmetric=true;
    bool segment=false;
    
    for(int k=1;k<argc;k++){
        if(argv[k][0]=='-'){
            if(argin.find(argv[k][1])==argin.end()){
                cout<<"Invalid option: "<<argv[k]<<" use -h for help\n";
            }
            switch(argin[argv[k][1]]){
                case 0:
                    sprintf(fixedfile,"%s",argv[k+1]);
                    requiredArgs++;
                    break;
                case 1:
                    sprintf(movingfile,"%s",argv[k+1]);
                    requiredArgs++;
                    break;
                case 2:
                    sprintf(outputstem,"%s",argv[k+1]);
                    requiredArgs++;
                    break;
                case 3:
                    alpha=atof(argv[k+1]);
                    break;
                case 4:
                    randsamp=atoi(argv[k+1]);
                    break;
                case 5:
                    maxlevel=atoi(argv[k+1]);
                    break;
                case 6:
                    num=sscanf(argv[k+1],levelstr,&s_grid[0],&s_grid[1],&s_grid[2],&s_grid[3],&s_grid[4],&s_grid[5],&s_grid[6],&s_grid[7],&s_grid[8],&s_grid[9]);
                    break;
                case 7:
                    num2=sscanf(argv[k+1],levelstr,&s_search[0],&s_search[1],&s_search[2],&s_search[3],&s_search[4],&s_search[5],&s_search[6],&s_search[7],&s_search[8],&s_search[9]);
                    break;
                case 8:
                    num3=sscanf(argv[k+1],levelstr,&s_quant[0],&s_quant[1],&s_quant[2],&s_quant[3],&s_quant[4],&s_quant[5],&s_quant[6],&s_quant[7],&s_quant[8],&s_quant[9]);
                    break;
                case 9:
                    symmetric=atoi(argv[k+1]);
                    break;
                case 10:
                    sprintf(movsegfile,"%s",argv[k+1]);
                    segment=true;
                    break;
                default:
                    cout<<"Invalid option: "<<argv[k]<<" use -h for help\n";
                    break;
            }
        }
    }
    if(requiredArgs!=3){
        cout<<"Missing argmuents, use -h for help.\n";
    }
    
    if((num!=maxlevel)|(num2!=maxlevel)|(num3!=maxlevel)){
        cout<<"Max level and number of grid-spacing, search range\n or quantisation steps are not equal.\n";
    }
    
    cout<<"calling deeds | symmetry: "<<symmetric<<" | alpha: "<<alpha<<" | metric: SAD\n";
    deeds(fixedfile,movingfile,movsegfile,outputstem,randsamp,alpha,maxlevel,s_grid,s_search,s_quant,segment,symmetric);
    
    
    return 0;
}


