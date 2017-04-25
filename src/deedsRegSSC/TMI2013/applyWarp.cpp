/* Helper-function for deeds if you need to upsample the deformation fields into high-res
 
 To compile simple run the following in your Terminal:
 
 g++ applyWarp.cpp -arch x86_64 -O3 -o applyWarp

 ./applyWarp output_vol second_vol.nii
 in order to upsample the fields and apply this deformation to second_vol.nii
 this will generate output_vol_second_deformed.nii
 (output_vol_deformed.nii must still be in same directory as output_vol_flow4D.dat)

*/
 

#include <iostream>
#include <fstream>
#include <math.h>
#include <stdio.h>
#include <stdlib.h>
#include <sys/time.h>
#include <vector>
#include <algorithm>
#include <functional>
#include <unistd.h>
#include <string.h>
#include <sstream>
#include <stdarg.h>
#include <unistd.h>
#include <pthread.h>

using namespace std;


   
int image_m=256; //will be set later
int image_n=256;
int image_o=106;
float SSD0; float SSD1;

#include "niftiIO.h"
#include "symmetricDiffeomorphic.h"

void warpImage(float* warped,float* im1,float* im1b,float* u1,float* v1,float* w1){
	int m=image_m;
	int n=image_n;
	int o=image_o;
	int sz=m*n*o;
	
	float ssd=0;
	float ssd0=0;
	float ssd2=0;
	
	interp3(warped,im1,u1,v1,w1,m,n,o,m,n,o,true);
	
	for(int i=0;i<m;i++){
		for(int j=0;j<n;j++){
			for(int k=0;k<o;k++){
				ssd+=pow(im1b[i+j*m+k*m*n]-warped[i+j*m+k*m*n],2);
				ssd0+=pow(im1b[i+j*m+k*m*n]-im1[i+j*m+k*m*n],2);
			}
		}
	}
	
	ssd/=m*n*o;
	ssd0/=m*n*o;
	SSD0=ssd0;
	SSD1=ssd;
	
}


int main (int argc, char * const argv[]) {
	
	char* flowend=new char[50];
	strcpy(flowend,"_flow4D.dat");
	char* outputflow=new char[200];
	strcpy(outputflow,argv[1]);
	strncat(outputflow,flowend,200);
	
	char* defend=new char[50];
	strcpy(defend,"_deformed.nii");
	char* outputdef=new char[200];
	strcpy(outputdef,argv[1]);
	strncat(outputdef,defend,200);

	char* secend=new char[50];
	strcpy(secend,"_second_deformed.nii");
	char* outputs=new char[200];
	strcpy(outputs,argv[1]);
	strncat(outputs,secend,200);
	
	

	float* im1;
    float* second;
	int M,N,O;
	char* header;
	
	FILE * pFile;
	long sizeflow;
	
	pFile = fopen(outputflow,"rb");
	if (pFile==NULL) perror ("Error opening file");
	else
	{
		fseek (pFile, 0, SEEK_END);
		sizeflow=ftell (pFile);
		fclose (pFile);
	}
	sizeflow/=4;
	float* flow=new float[sizeflow];
	readFloat(outputflow,flow,sizeflow);
	int sz1=sizeflow/3;
	float* u1=new float[sz1]; float* v1=new float[sz1]; float* w1=new float[sz1];
	for(int i=0;i<sz1;i++){
		u1[i]=flow[i]; v1[i]=flow[i+sz1]; w1[i]=flow[i+sz1*2];
	}
	
    readNifti(argv[2],second,M,N,O,header);

	readNifti(outputdef,im1,M,N,O,header);
	
    
	image_m=M; image_n=N; image_o=O;
	
	int m=image_m; int n=image_n; int o=image_o; int sz=m*n*o;
	int step1=round(pow((float)sz/(float)sz1,0.3333333));
	cout<<"grid-step: "<<step1<<"\n";
	int m1=m/step1; int n1=n/step1; int o1=o/step1; 
	
	//flow-fields
	//u is in x-direction (2nd dimension), v in y-direction (1st dim) and w in z-direction (3rd dim)
	float* ux=new float[sz]; float* vx=new float[sz]; float* wx=new float[sz];
	
	upsampleDeformations2(ux,vx,wx,u1,v1,w1,m,n,o,m1,n1,o1);
   
    float* warped=new float[sz];
    warpImage(warped,second,im1,ux,vx,wx);

	
	writeNifti(outputs,warped,header,m*n*o);

	
	return 0;
}
