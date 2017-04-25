
//global image dimensions
int image_m=1; //will be set later
int image_n=1;
int image_o=1; int image_d=12;
float timeP,timeD; //global variables for comp. time



#include "niftiIO.h"
#include "transformations.h"




int deeds2def(char* fixedin,char* outputstem) {
    
    timeval time1,time2,time1a,time2a;
    
    //READ IN IMAGES AND EVALUATION LABELS
    
    float* target;
    int M,N,O,K;
    char* header=new char[352];
    
    readNifti(fixedin,target,M,N,O,K,header);
        
    //global image dimensions
    image_m=M; image_n=N; image_o=O;
    
    int m=image_m; int n=image_n; int o=image_o; int sz=m*n*o;
    
    char* output1=new char[200];
    sprintf(output1,"%s_deformation.nii",outputstem);
    char* input1=new char[200];
    sprintf(input1,"%s_flow.dat",outputstem);

    cout<<"Input filenames: "<<fixedin<<", \nand "<<input1<<"\n";

    float* flow=new float[sz*3];

    //read float array
    ifstream file(input1,ios::in|ios::binary);
    if(file.is_open()){
        file.read((char*)flow,sz*3*sizeof(float));
        //binary are read character by character reinterpret_cast converts them to float
        flow=reinterpret_cast<float*>(flow);
    }
    else{
        printf("File error. Did not find file. Exiting.\n");
        exit(1);
    }
    
    file.close();
    float* pixdim=reinterpret_cast<float*>(header+76);
    float vox_x=(float)pixdim[1];
    float vox_y=(float)pixdim[2];
    float vox_z=(float)pixdim[3];
    
    
    float* srow=reinterpret_cast<float*>(header+280);
    float srow_x=(float)srow[0];
    float srow_y=(float)srow[5];
    float srow_z=(float)srow[10];
    
    printf("srow: %f, %f, %f\n",srow_x,srow_y,srow_z);
    
    //set-up new header for 5D deformation field (in mm)
    char* header2=new char[352];
    copy(header,header+352,header2);
    
    short* dimensions=new short[6];
    dimensions[0]=5; dimensions[1]=m; dimensions[2]=n; dimensions[3]=o; dimensions[4]=1; dimensions[5]=3;
    char* dimchar=reinterpret_cast<char*>(dimensions);
    copy(dimchar,dimchar+12,header2+40);

    float* pixnew=new float[6];
    pixnew[0]=1; pixnew[1]=vox_x; pixnew[2]=vox_y; pixnew[3]=vox_z; pixnew[4]=1; pixnew[5]=1;
    char* pixchar=reinterpret_cast<char*>(pixnew);
    copy(pixchar,pixchar+24,header2+76);

    
    float* deformation=new float[sz*3];

        for(int k=0;k<o;k++){
            for(int j=0;j<n;j++){
                for(int i=0;i<m;i++){
                    deformation[i+j*m+k*m*n]=srow_x*((float)i+flow[i+j*m+k*m*n+sz]);
                    deformation[i+j*m+k*m*n+sz]=srow_y*((float)j+flow[i+j*m+k*m*n]);
                    deformation[i+j*m+k*m*n+2*sz]=srow_z*((float)k+flow[i+j*m+k*m*n+2*sz]);
                }
            }
        }
    
    
    //write Nifti-deformation field
    //set datatype to float
	header2[70]=16;
	header2[72]=32;
    
	ofstream file1(output1);
	if(file1.is_open()){
		file1.write(header2,352);
		file1.write(reinterpret_cast<char*>(deformation),sz*3*sizeof(float) );
		file1.close();
		cout<<"File "<<output1<<" written.\n";
	}
    
    return 0;
}
