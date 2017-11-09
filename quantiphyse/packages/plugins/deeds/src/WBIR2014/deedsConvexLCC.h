
//global image dimensions
int image_m=1; //will be set later
int image_n=1;
int image_o=1;
float timeP,timeD; //global variables for comp. time



//struct for multi-threading
struct cost_data{
    float* targetS; float* warped1S;
    float* meanvar1; float* meanvar2;
    float* costvol; float* tempmem;
    int hw;
    int sparse;
    int r;
    int istart; int iend;
};


#include "niftiIO.h"
#include "transformations.h"
#include "inverseMapping.h"
#include "boxfilter4.h"
#include "dataCostLCC.h"
#include "smoothCost.h"


int deeds(char* fixedin,char* movingin,char* movingsegin,char* outputstem,int kernel,float sigma,int maxlevel,int* label_hw,bool segment,bool symmetric) {
    
    timeval time1,time2,time1a,time2a;
    
    //REGISTRATION SETTINGS
    float thetas[]={0.003,0.01,0.03,0.1,0.3,1};//thetas for 5 coupling iterations

  //  int kernel=2; //radius of cost-aggregation in voxels
  //  float sigma=0.6f; //sigma for Gaussian smoothing of displacement fields
    
  //  int maxlevel=3; //number of resolution levels
    
   // int label_hw[]={6,4,2};
    //half-width of displacement search space L={±0,±1,..,label_hw}^3 voxels
    
    float* scale_factor=new float[maxlevel];//[]={3,2,1};
    for(int i=0;i<maxlevel;i++){
        scale_factor[i]=maxlevel-i;
    }
    //scaling of multi-resolution levels (in voxels)

    printf("SETTINGS: sigma: %f, kernel: %d\n",sigma,kernel);
    
    
    //READ IN IMAGES AND EVALUATION LABELS
    cout<<"Input filename: "<<fixedin<<"\n";
    
    float* moving; float* target;
    int M,N,O,K;
    char* header;
    
    readNifti(fixedin,target,M,N,O,K,header);
    readNifti(movingin,moving,M,N,O,K,header);
    
    //global image dimensions
    image_m=M; image_n=N; image_o=O;
    
    int m=image_m; int n=image_n; int o=image_o; int sz=m*n*o;
    
    
    
    //set initial flow-fields to 0; i indicates backward (inverse) transform
    //u is in x-direction (2nd dimension), v in y-direction (1st dim) and w in z-direction (3rd dim)
    float* ux=new float[sz]; float* vx=new float[sz]; float* wx=new float[sz];
    float* uxi=new float[sz]; float* vxi=new float[sz]; float* wxi=new float[sz];
    for(int i=0;i<sz;i++){
        ux[i]=0.0; vx[i]=0.0; wx[i]=0.0;
        uxi[i]=0.0; vxi[i]=0.0; wxi[i]=0.0;
    }
    float* flowx=new float[sz*3];

    for(int i=0;i<sz;i++){
        flowx[i]=ux[i]; flowx[i]=vx[i+sz]; flowx[i+sz*2]=wx[i];
    }

        gettimeofday(&time1a, NULL);
    

    for(int level=0;level<maxlevel;level++){
        
        float subdisp[3]={0,0,0};
        
        int hw=label_hw[level];
        int sparse=scale_factor[level];
        int r=kernel;
        int len=hw*2+1; int len3=pow(hw*2+1,3);
        float h1=0.05;
        int m1=m/sparse; int n1=n/sparse; int o1=o/sparse;
        int sz1=m1*n1*o1;
        
        float* costvol=new float[sz1*len3];
        float *warped1=new float[m*n*o];
        
        float* costvoli=new float[sz1*len3];
        float *warped1i=new float[m*n*o];
        
        //warp images and calculate similarity map (quite memory intensive)
        warpImage(warped1,moving,ux,vx,wx);
        dataReg(costvol,target,warped1,hw,sparse,r,h1);
        if(symmetric){
            warpImage(warped1i,target,uxi,vxi,wxi);
            dataReg(costvoli,moving,warped1i,hw,sparse,r,h1);
        }
        //initialise flow-fields from previous level
        float* u1=new float[sz1]; float* v1=new float[sz1]; float* w1=new float[sz1];
        float* u0=new float[sz1]; float* v0=new float[sz1]; float* w0=new float[sz1];
        float* u1i=new float[sz1]; float* v1i=new float[sz1]; float* w1i=new float[sz1];
        float* u0i=new float[sz1]; float* v0i=new float[sz1]; float* w0i=new float[sz1];
        upsampleDeformations2scale(u1,v1,w1,ux,vx,wx,m1,n1,o1,m,n,o);
        upsampleDeformations2scale(u0,v0,w0,ux,vx,wx,m1,n1,o1,m,n,o);
        if(symmetric){
            upsampleDeformations2scale(u1i,v1i,w1i,uxi,vxi,wxi,m1,n1,o1,m,n,o);
            upsampleDeformations2scale(u0i,v0i,w0i,uxi,vxi,wxi,m1,n1,o1,m,n,o);
        }
        
        int* minind=new int[sz1]; float* flow0=new float[sz1*3];
        int* minindi=new int[sz1]; float* flow0i=new float[sz1*3];
        
        gettimeofday(&time1, NULL);
        
        //Iterations of alternating smoothing and update of similarity maps
        for(int stb=0;stb<5;stb++){
            cout<<stb<<" "<<flush;
            //remove previous field (will be added again later)
            for(int i=0;i<sz1;i++){
                flow0[i]=u1[i]-u0[i];
                flow0[i+sz1]=v1[i]-v0[i];
                flow0[i+2*sz1]=w1[i]-w0[i];
                if(symmetric){
                    flow0i[i]=u1i[i]-u0i[i];
                    flow0i[i+sz1]=v1i[i]-v0i[i];
                    flow0i[i+2*sz1]=w1i[i]-w0i[i];
                }
            }
            
            //update of similarity maps
            steinbruecker(minind,costvol,flow0,hw,thetas[stb],m1,n1,o1);
            if(symmetric){
                steinbruecker(minindi,costvoli,flow0i,hw,thetas[stb],m1,n1,o1);
            }
            //pick new argmin and add previous field
            for(int i=0;i<sz1;i++){
                int ind=minind[i];
                ind2sub(subdisp,len,ind);
                
                u1[i]=subdisp[1]+u0[i];
                v1[i]=subdisp[0]+v0[i];
                w1[i]=subdisp[2]+w0[i];
                if(symmetric){
                    ind=minindi[i];
                
                    ind2sub(subdisp,len,ind);
                    u1i[i]=subdisp[1]+u0i[i];
                    v1i[i]=subdisp[0]+v0i[i];
                    w1i[i]=subdisp[2]+w0i[i];
                }
            }

            //Gaussian smoothing of (incremented) flow field
            volfilter(u1,m1,n1,o1,11,sigma);
            volfilter(v1,m1,n1,o1,11,sigma);
            volfilter(w1,m1,n1,o1,11,sigma);
            
            if(symmetric){
            volfilter(u1i,m1,n1,o1,11,sigma);
            volfilter(v1i,m1,n1,o1,11,sigma);
            volfilter(w1i,m1,n1,o1,11,sigma);

            //enforce inverse-consitstency
            consistentMappingCL(u1,v1,w1,u1i,v1i,w1i,m1,n1,o1,1);
            }
            
        }
        gettimeofday(&time2, NULL);
        
        float timeS=(time2.tv_sec+time2.tv_usec/1e6-(time1.tv_sec+time1.tv_usec/1e6));
        printf("\nTime for steinbruecker-coupling: %f secs, Speed: %f MPix/s\n",timeS,5.0f*(float)sz1*len3/timeS*1e-6);
        
        delete u0; delete v0; delete w0;
        delete costvol; delete flow0; delete minind;
        delete u0i; delete v0i; delete w0i;
        delete costvoli; delete flow0i; delete minindi;
        
        //upscale displacement field to original image resolution
        upsampleDeformations2scale(ux,vx,wx,u1,v1,w1,m,n,o,m1,n1,o1);
        delete u1; delete v1; delete w1;
        if(symmetric){
            upsampleDeformations2scale(uxi,vxi,wxi,u1i,v1i,w1i,m,n,o,m1,n1,o1);
        }
        delete u1i; delete v1i; delete w1i;
        
        delete warped1; delete warped1i;

        for(int i=0;i<sz;i++){
            flowx[i]=ux[i]; flowx[i+sz]=vx[i]; flowx[i+sz*2]=wx[i];
        }
    
        //evaluate std(J) of transformation
        float jac=jacobian(ux,vx,wx,m,n,o,1);
        
        
    }//end of scale levels
    

    
    for(int i=0;i<sz;i++){
        flowx[i]=ux[i]; flowx[i+sz]=vx[i]; flowx[i+sz*2]=wx[i];
    }
    
    char* output1=new char[200];
    sprintf(output1,"%s_deformed.nii",outputstem);
    char* output2=new char[200];
    sprintf(output2,"%s_flow.dat",outputstem);
    char* output3=new char[200];
    sprintf(output3,"%s_segment.nii",outputstem);
  
    float* warpout=new float[sz];
    warpImage(warpout,moving,ux,vx,wx);
    writeNifti(output1,warpout,header,sz);

    //optionally write-out warped Labels
    if(segment){
        for(int i=0;i<sz;i++){
            ux[i]=round(ux[i]);
            vx[i]=round(vx[i]);
            wx[i]=round(wx[i]);
        }
        short *seg;
        readNiftiShort(movingsegin,seg,M,N,O,header);
        short* warpedseg=new short[sz];
        warpImage(warpedseg,seg,ux,vx,wx);
    
        writeNiftiShort(output3,warpedseg,header,sz);
    }
    writeOutput(flowx,output2,sz*3);
    
    gettimeofday(&time2a, NULL);
    
    timeP=(time2a.tv_sec+time2a.tv_usec/1e6-(time1a.tv_sec+time1a.tv_usec/1e6));
    printf("Total registration time: %f secs.\n",timeP);

    
    return 0;
}
