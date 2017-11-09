
//global image dimensions
int image_m=1; //will be set later
int image_n=1;
int image_o=1; int image_d=12;
float SSD0=0.0; float SSD1=0.0; float SSD2=0.0;
float beta=1; int RAND_SAMPLES=64;

float timeP,timeD; //global variables for comp. time



//structs for multi-threading
struct regulariser_data{
	float* u1; float* v1; float* w1;
	float* u0; float* v0; float* w0;
	float* costall;
	float alpha;
	int hw;
	int step1;
	float quant;
	int* ordered;
	int* parents;
};

struct cost_data{
	float* im1;
	float* im1b;
	float* costall;
	float alpha;
	int hw;
	float step1;
	float quant;
    uint64_t* fixed_mind;
    uint64_t* moving_mind;
    int istart; int iend;
};
struct mind_data{
	float* im1;
    uint64_t* mindq;
    int qs;
};

void minimumIndA(float *numbers,float &value,int &index,int length)
{
	value=numbers[0];
	int i;
	index=0;
    for(i=1;i<length;i++){
        if(numbers[i]<value){
			index=i;
			value=numbers[i];
		}
    }
}
/*
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
	
}*/

#include "fastdt2.h"
#include "symmetricDiffeomorphic.h"
#include "primsMST.h"
#include "regularisation2T.h"
#include "MIND-SSC.h"
#include "dataCostD.h"

int deeds(char* fixedin,char* movingin,char* movingsegin,char* outputstem,int randsamp2,
          float alpha,int maxlevel,int* grid_step,int* label_hw,int* label_quant,bool segment,bool symmetric) {

	//Initialise random variable
//	srand (time(0) );
	timeval time1,time2,time1a,time2a;
	/*
	
	char* flowend=new char[50];
	strcpy(flowend,"_flow4D.dat");
	char* defend=new char[50];
	strcpy(defend,"_deformed.nii");
	char* outputflow=new char[200];
	strcpy(outputflow,argv[3]);
	strncat(outputflow,flowend,200);
	cout<<"Fileoutput (flow): "<<outputflow<<"\n";
	char* outputdef=new char[200];
	strcpy(outputdef,argv[3]);
	strncat(outputdef,defend,200);
	cout<<"Fileoutput (deformed): "<<outputdef<<"\n";
	
	float alpha=atof(argv[4]);
	int randsamp2=atoi(argv[5]);*/
	
	RAND_SAMPLES=randsamp2;
    
    
	float* im1; float* im1b;
	int M,N,O,K;
	char* header;
	
	readNifti(fixedin,im1b,M,N,O,K,header);
	readNifti(movingin,im1,M,N,O,K,header);
	
	image_m=M; image_n=N; image_o=O;
	
	int m=image_m; int n=image_n; int o=image_o; int sz=m*n*o;
    
	float *warped1=new float[m*n*o];
	float *warped2=new float[m*n*o];
    
	
	//==========================================================================================
	//==========================================================================================
	//IMPORTANT SETTINGS FOR CONTROL POINT SPACING AND LABEL SPACE
    //int maxlevel=4;
    
	//int label_hw[]={6,5,4,2};//
	//half-width of search space L={±0,±1,..,label_hw}^3 * label_quant
	
	//int grid_step[]={8,6,4,2};//
	//spacing between control points in grid
	//d.o.f.: 2.8, 3.4, 4.3, 6.1(3.4)
    
	//float label_quant[]={3,2,1,1};//
	//quantisation of search space L, important: can only by integer or 0.5 so far!
    //float* mind_step=new float[maxlevel];
    //[]={3,2,2,1,1};//{1,1,1,1,1};//
    for(int i=0;i<maxlevel;i++){
     //   mind_step[i]=ceil(label_quant[i]*0.49999);
    }
    
	int step1; int hw1; float quant1;
    
	//set initial flow-fields to 0; i indicates backward (inverse) transform
	//u is in x-direction (2nd dimension), v in y-direction (1st dim) and w in z-direction (3rd dim)
	float* ux=new float[sz]; float* vx=new float[sz]; float* wx=new float[sz];
	float* uxi=new float[sz]; float* vxi=new float[sz]; float* wxi=new float[sz];
	for(int i=0;i<sz;i++){
		ux[i]=0.0; vx[i]=0.0; wx[i]=0.0;
		uxi[i]=0.0; vxi[i]=0.0; wxi[i]=0.0;
	}
	int m2,n2,o2,sz2;
	int m1,n1,o1,sz1;
	m2=m/grid_step[0]; n2=n/grid_step[0]; o2=o/grid_step[0]; sz2=m2*n2*o2;
	float* u1=new float[sz2]; float* v1=new float[sz2]; float* w1=new float[sz2];
	float* u1i=new float[sz2]; float* v1i=new float[sz2]; float* w1i=new float[sz2];
	for(int i=0;i<sz2;i++){
		u1[i]=0.0; v1[i]=0.0; w1[i]=0.0;
		u1i[i]=0.0; v1i[i]=0.0; w1i[i]=0.0;
	}
    
    
    //uses two-threads, so that forward and backward transform are estimated simultaneously
    //if this uses too much memory it could be changed to a single-thread
    THREAD_ID thread1, thread2, thread1b, thread2b;
    int  iret1, iret2;
    struct mind_data mind1,mind2;
    
    
	gettimeofday(&time1a, NULL);
    
	//==========================================================================================
	//==========================================================================================
	float* bench=new float[6*maxlevel];
	for(int level=0;level<maxlevel;level++){
        quant1=label_quant[level];
        
        //calculate MIND descriptors (could be reused for further levels to save computation time)
       // uint64_t* im1_mind=new uint64_t[m*n*o];
        //uint64_t* im1b_mind=new uint64_t[m*n*o];
        
       // mind1.im1=im1; mind1.mindq=im1_mind; mind1.qs=max(min(quant1,2.0f),1.0f); //qs determines size of patches for MIND
        //mind2.im1=im1b; mind2.mindq=im1b_mind; mind2.qs=max(min(quant1,2.0f),1.0f);
        
        //create_thread(&thread1,quantisedMIND,(void *)&mind1);
        //create_thread(&thread2,quantisedMIND,(void *)&mind2);
        //join_thread(thread1);
        //join_thread(thread2);
		
		
		struct regulariser_data reg1,reg2;
		struct cost_data cosd1,cosd2,cosd1b,cosd2b;
		
		//warp both high-resolution images according
		warpImage(warped1,im1,ux,vx,wx);
		warpImage(warped2,im1b,uxi,vxi,wxi);
        
		step1=grid_step[level];
		hw1=label_hw[level];
		
		int len3=pow(hw1*2+1,3);
		m1=m/step1; n1=n/step1; o1=o/step1; sz1=m1*n1*o1;
		
		//resize flow from u1 to current scale (grid spacing)
		float* u0=new float[sz1]; float* v0=new float[sz1]; float* w0=new float[sz1];
		float* u0i=new float[sz1]; float* v0i=new float[sz1]; float* w0i=new float[sz1];
		upsampleDeformations2(u0,v0,w0,u1,v1,w1,m1,n1,o1,m2,n2,o2);
		upsampleDeformations2(u0i,v0i,w0i,u1i,v1i,w1i,m1,n1,o1,m2,n2,o2);
        
		cout<<"==========================================================\n";
		cout<<"Level "<<level<<" grid="<<step1<<" with sizes: "<<m1<<"x"<<n1<<"x"<<o1<<" hw="<<hw1<<" quant="<<quant1<<"\n";
		cout<<"==========================================================\n";
		
		u1=new float[sz1]; v1=new float[sz1]; w1=new float[sz1];
		u1i=new float[sz1]; v1i=new float[sz1]; w1i=new float[sz1];
        
		//Minimum-spanning-tree
		int* ordered1=new int[sz1];
		int* parents1=new int[sz1];
		primsGraph(im1b,ordered1,parents1,step1);
		int* ordered2=new int[sz1];
		int* parents2=new int[sz1];
		primsGraph(im1,ordered2,parents2,step1);
        
        gettimeofday(&time1, NULL);
        
        //uint64_t* warped1_mind=new uint64_t[m*n*o];
        //uint64_t* warped2_mind=new uint64_t[m*n*o];
        
        //mind1.im1=warped1; mind1.mindq=warped1_mind; mind1.qs=max(min(quant1,2.0f),1.0f);
        //mind2.im1=warped2; mind2.mindq=warped2_mind; mind2.qs=max(min(quant1,2.0f),1.0f);
        
        //create_thread(&thread1,quantisedMIND,(void *)&mind1);
        //create_thread(&thread2,quantisedMIND,(void *)&mind2);
        //join_thread(thread1);
        //join_thread(thread2);
		gettimeofday(&time2, NULL);
		float timeMIND=time2.tv_sec+time2.tv_usec/1e6-(time1.tv_sec+time1.tv_usec/1e6);
		cout<<"Start similarity computation! \n";
		cout<<"==================================================\n";
		gettimeofday(&time1, NULL);
        
		//data-cost/similarity computation 4-threaded (uses plenty of memory)
		float* costall1=new float[sz1*len3];
		float* costall2=new float[sz1*len3];
        
		cosd1.im1=im1b; cosd1.im1b=warped1; cosd1.alpha=alpha; cosd1.costall=costall1;
		cosd1.hw=hw1; cosd1.step1=step1; cosd1.quant=quant1; cosd1.istart=0; cosd1.iend=sz1/2;
		cosd2.im1=im1; cosd2.im1b=warped2; cosd2.alpha=alpha; cosd2.costall=costall2;
		cosd2.hw=hw1; cosd2.step1=step1; cosd2.quant=quant1; cosd2.istart=0; cosd2.iend=sz1/2;
        
		cosd1b.im1=im1b; cosd1b.im1b=warped1; cosd1b.alpha=alpha; cosd1b.costall=costall1;
		cosd1b.hw=hw1; cosd1b.step1=step1; cosd1b.quant=quant1; cosd1b.istart=sz1/2; cosd1b.iend=sz1;
		cosd2b.im1=im1; cosd2b.im1b=warped2; cosd2b.alpha=alpha; cosd2b.costall=costall2;
		cosd2b.hw=hw1; cosd2b.step1=step1; cosd2b.quant=quant1; cosd2b.istart=sz1/2; cosd2b.iend=sz1;
        
		create_thread( &thread1, dataCost, (void *) &cosd1);
		create_thread( &thread2, dataCost, (void *) &cosd2);
        create_thread( &thread1b, dataCost, (void *) &cosd1b);
		create_thread( &thread2b, dataCost, (void *) &cosd2b);
		join_thread( thread1);
		join_thread( thread2);
		join_thread( thread1b);
		join_thread( thread2b);
		
		gettimeofday(&time2, NULL);
		float timeData=time2.tv_sec+time2.tv_usec/1e6-(time1.tv_sec+time1.tv_usec/1e6);
		cout<<"\nTime for data cost: "<<timeData<<"\nSpeed: "<<(float)sz1*(float)len3*(float)RAND_SAMPLES/timeData<<" dof/s\n";
		
		//incremental diffusion regularisation
		cout<<"Start regularisation on MST!\n";
		cout<<"==================================================\n";
		gettimeofday(&time1, NULL);
        
		reg1.u1=u1; reg1.v1=v1; reg1.w1=w1; reg1.costall=costall1;
		reg1.u0=u0; reg1.v0=v0; reg1.w0=w0; reg1.alpha=alpha;
		reg1.hw=hw1; reg1.step1=step1; reg1.quant=quant1;
		reg1.ordered=ordered1; reg1.parents=parents1;
		
		reg2.u1=u1i; reg2.v1=v1i; reg2.w1=w1i; reg2.costall=costall2;
		reg2.u0=u0i; reg2.v0=v0i; reg2.w0=w0i; reg2.alpha=alpha;
		reg2.hw=hw1; reg2.step1=step1; reg2.quant=quant1;
		reg2.ordered=ordered2; reg2.parents=parents2;
        
		create_thread( &thread1, regularisation, (void *) &reg1);
		create_thread( &thread2, regularisation, (void *) &reg2);
		join_thread( thread1);
		join_thread( thread2);
        
        /*
         //according to TMI 2013 paper
         //make transformations diffeomorphic (important) using scaling-and-squaring
         diffeomorphic(u1,v1,w1,m1,n1,o1,4,step1);
         diffeomorphic(u1i,v1i,w1i,m1,n1,o1,4,step1);
         //calculate inverses and compose new symmetric mapping (forward and backward)
         symmetricMapping(u1,v1,w1,u1i,v1i,w1i,m1,n1,o1,step1);
         */
        
        //consistent mapping according to the MICCAI 2013 paper
        consistentMapping(u1,v1,w1,u1i,v1i,w1i,m1,n1,o1,step1);
        
        
        gettimeofday(&time2, NULL);
		float timeSmooth=time2.tv_sec+time2.tv_usec/1e6-(time1.tv_sec+time1.tv_usec/1e6);
		cout<<"\nComputation time for smoothness terms : "<<timeSmooth<<" secs.\nSpeed: "<<(float)sz1*(float)len3/timeSmooth<<" dof/s\n";
        
		
		//upsample deformations from grid-resolution to high-resolution (trilinear=1st-order spline)
		upsampleDeformations2(ux,vx,wx,u1,v1,w1,m,n,o,m1,n1,o1);
		upsampleDeformations2(uxi,vxi,wxi,u1i,v1i,w1i,m,n,o,m1,n1,o1);
		float jac=jacobian(u1,v1,w1,m1,n1,o1,step1);
        float energy=harmonicEnergy(ux,vx,wx,m,n,o);
		cout<<"harmonic energy of deformation field: "<<energy<<"\n";
        
        
		//warpImage(warped1,im1,im1b,ux,vx,wx);
		//cout<<"SSD before registration: "<<SSD0<<" and after "<<SSD1<<"\n";
		m2=m1; n2=n1; o2=o1;
		cout<<"\n";
        
        bench[0+level*6]=SSD1;
        bench[1+level*6]=jac;
        bench[2+level*6]=energy;
        bench[3+level*6]=timeMIND;
        bench[4+level*6]=timeSmooth;
        bench[5+level*6]=timeData;
        //delete warped1_mind;
        //delete warped2_mind;
		
		delete []u0; delete []v0; delete []w0;
		delete []u0i; delete []v0i; delete []w0i;
		delete []costall1; delete []costall2;
		delete []parents1; delete []ordered1;
		delete []parents2; delete []ordered2;
        //delete im1_mind;
        //delete im1b_mind;
        
	}
	//===============================================================
	//===============================================================

    
    float* flow1=new float[sz1*3];
	for(int i=0;i<sz1;i++){
        flow1[i]=u1[i]; flow1[i+sz1]=v1[i]; flow1[i+sz1*2]=w1[i];
    }
    char* output1=new char[200];
    sprintf(output1,"%s_deformed.nii",outputstem);
    char* output2=new char[200];
    sprintf(output2,"%s_flowLR.dat",outputstem);
    char* output3=new char[200];
    sprintf(output3,"%s_segment.nii",outputstem);

    float* warpout=new float[sz];
    warpImage(warpout,im1,ux,vx,wx);
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
   
    writeOutput(flow1,output2,sz1*3);
   
    gettimeofday(&time2a, NULL);
    
    timeP=(time2a.tv_sec+time2a.tv_usec/1e6-(time1a.tv_sec+time1a.tv_usec/1e6));
    printf("Total registration time: %f secs.\n",timeP);

	
	
	return 0;
}

