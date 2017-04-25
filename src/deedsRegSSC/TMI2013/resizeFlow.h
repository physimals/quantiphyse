//global image dimensions
int image_m=1; //will be set later
int image_n=1;
int image_o=1; int image_d=12;
float timeP,timeD; //global variables for comp. time



#include "niftiIO.h"
//#include "transformations.h"
#include "symmetricDiffeomorphic.h"




int resizeFlow2def(char* fixedin,char* outputstem,bool def){
    
    timeval time1,time2,time1a,time2a;
    
    //READ IN IMAGES AND EVALUATION LABELS
    
    float* target;
    int M,N,O,K;
    char* header=new char[352];
    
    readNifti(fixedin,target,M,N,O,K,header);
    
    //global image dimensions
    image_m=M; image_n=N; image_o=O;
    
    int m=image_m; int n=image_n; int o=image_o; int sz=m*n*o;

    char* output2=new char[200];
    sprintf(output2,"%s_displacements.nii",outputstem);

    char* output1=new char[200];
    sprintf(output1,"%s_deformation.nii",outputstem);
    char* input1=new char[200];
    sprintf(input1,"%s_flowLR.dat",outputstem);
    
    cout<<"Input filenames: "<<fixedin<<", \nand "<<input1<<"\n";
    
	FILE * pFile;
	long sizeflow;
	pFile = fopen(input1,"rb");
	if (pFile==NULL) perror ("Error opening file");
	else
	{
		fseek (pFile, 0, SEEK_END);
		sizeflow=ftell (pFile);
		fclose (pFile);
	}
	sizeflow/=4;
	float* flowLR=new float[sizeflow];
	
    //read float array
    ifstream file(input1,ios::in|ios::binary);
    if(file.is_open()){
        file.read((char*)flowLR,sizeflow*sizeof(float));
        //binary are read character by character reinterpret_cast converts them to float
        flowLR=reinterpret_cast<float*>(flowLR);
    }
    else{
        printf("File error. Did not find file. Exiting.\n");
        exit(1);
    }
    
    int sz1=sizeflow/3;
    
    int step1=round(pow((float)sz/(float)sz1,0.3333333));
	cout<<"grid-step: "<<step1<<"\n";
	int m1=m/step1; int n1=n/step1; int o1=o/step1;

    float* flow=new float[sz*3];
    upsampleDeformations2(flow,flow+sz,flow+sz*2,flowLR,flowLR+sz1,flowLR+sz1*2,m,n,o,m1,n1,o1);

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
    
    //write Nifti-displacement/deformation field
    //set datatype to float
	header2[70]=16;
	header2[72]=32;
    
    
	ofstream file1(output2);
	if(file1.is_open()){
		file1.write(header2,352);
		file1.write(reinterpret_cast<char*>(flow),sz*3*sizeof(float) );
		file1.close();
		cout<<"File "<<output2<<" written.\n";
	}
    
    float* pixnew=new float[6];
    pixnew[0]=1; pixnew[1]=vox_x; pixnew[2]=vox_y; pixnew[3]=vox_z; pixnew[4]=1; pixnew[5]=1;
    char* pixchar=reinterpret_cast<char*>(pixnew);
    copy(pixchar,pixchar+24,header2+76);
    
    if(def){ //deformation field required
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

	ofstream file1(output1);
	if(file1.is_open()){
		file1.write(header2,352);
		file1.write(reinterpret_cast<char*>(deformation),sz*3*sizeof(float) );
		file1.close();
		cout<<"File "<<output1<<" written.\n";
	}
    
    }
    return 0;
}

/*
void resizeFlow(){
	
	char* flowend=new char[50];
	strcpy(flowend,"_flowLR.dat");
	char* outputflow=new char[200];
	strcpy(outputflow,argv[1]);
	strncat(outputflow,flowend,200);
	
	char* defend=new char[50];
	strcpy(defend,"_deformed.nii");
	char* outputdef=new char[200];
	strcpy(outputdef,argv[1]);
	strncat(outputdef,defend,200);
    
	char* uend=new char[50];
	strcpy(uend,"_flow.dat");
	char* outputHR=new char[200];
	strcpy(outputHR,argv[1]);
	strncat(outputHR,uend,200);
	
	float* im1;
	int M,N,O,K;
	char* header;
	
	FILE * pFile;
	long sizeflow;
	cout<<outputflow<<"\n";
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
	
	readNifti(outputdef,im1,M,N,O,K,header);
	
	image_m=M; image_n=N; image_o=O;
	
	int m=image_m; int n=image_n; int o=image_o; int sz=m*n*o;
	int step1=round(pow((float)sz/(float)sz1,0.3333333));
	cout<<"grid-step: "<<step1<<"\n";
	int m1=m/step1; int n1=n/step1; int o1=o/step1;
	
	//flow-fields
	//u is in x-direction (2nd dimension), v in y-direction (1st dim) and w in z-direction (3rd dim)
	float* flowx=new float[sz*3];
	upsampleDeformations2(flowx,flowx+sz,flowx+sz*2,u1,v1,w1,m,n,o,m1,n1,o1);
    
	
	writeOutput(flowx,outputHR,m*n*o*3);
    
	
	return 0;
}*/
