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
 If you use this implementation (without self-similarites) please cite:
 
 “Non-parametric Discrete Registration with Convex Optimisation.”
 by Mattias P. Heinrich, Bartlomiej W. Papież, Julia A. Schnabel, Heinz Handels
 Biomedical Image Registration - WBIR 2014, LNCS 8454, Springer, pp 51-61
 
 Tested with g++ on Mac OS X and Linux Ubuntu, compile with:
 
 g++ WBIR_LCC.cpp -O3 -lpthread -msse4.2 -o wbirLCC
 
 replace msse4.2 by your current SSE version if needed
 for Windows you might need MinGW or CygWin
 
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


#include "deedsConvexLCC.h"

int main(int argc, const char * argv[])
{
    
    if(argc<4||argv[1][1]=='h'){
        cout<<"==========================================================\n";
        cout<<"Usage (required input arguments):\n";
        cout<<"./deedsConvex -F fixed.nii -M moving.nii -O output\n";
        cout<<"optional parameters:\n";
        cout<<" -g <regularisation Gaussian sigma> (default 0.6)\n";
        cout<<" -r <radius of cost aggregation> (default 2)\n";
        cout<<" -l <number of levels> (default 3)\n";
        cout<<" -L <maximum search radius for each level> (default 6x4x2)\n";
        cout<<" -s <use symmetric approach> (default 1)\n";
        cout<<" -S <moving_segmentation.nii> (short int)\n";
        cout<<"==========================================================\n";
        return 1;
    }
    
    
    typedef pair<char,int> val;
    map<char,int> argin;
    argin.insert(val('F',0));
    argin.insert(val('M',1));
    argin.insert(val('O',2));
    argin.insert(val('g',3));
    argin.insert(val('r',4));
    argin.insert(val('l',5));
    argin.insert(val('L',6));
    argin.insert(val('s',7));
    argin.insert(val('S',8));

    // parsing the input
    int requiredArgs=0;
     char* fixedfile=new char[200];
     char* movingfile=new char[200];
     char* outputstem=new char[200];
     char* movsegfile=new char[200];
    
    float sigma=0.6;
    int radius=2;
    int maxlevel=3;
    int num=maxlevel;
    int s_radii[10]={6,4,2,2,2,2,2,2,2,2};
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
                    sigma=atof(argv[k+1]);
                    break;
                case 4:
                    radius=atoi(argv[k+1]);
                    break;
                case 5:
                    maxlevel=atoi(argv[k+1]);
                    break;
                case 6:
                    num=sscanf(argv[k+1],levelstr,&s_radii[0],&s_radii[1],&s_radii[2],&s_radii[3],&s_radii[4],&s_radii[5],&s_radii[6],&s_radii[7],&s_radii[8],&s_radii[9]);
                    break;
                case 7:
                    symmetric=atoi(argv[k+1]);
                    break;
                case 8:
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
    
    if(num!=maxlevel){
        cout<<"Max level and number of radii are not equal.\n";
    }
    
    cout<<"calling deeds | symmetry: "<<symmetric<<"\n";
    deeds(fixedfile,movingfile,movsegfile,outputstem,radius,sigma,maxlevel,s_radii,segment,symmetric);

    
    return 0;
}

