#include "deeds_thread.h"
#include "stdint.h"

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
	int m; int n; int o;
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
	int m; int n; int o;
	int rand_samples;
};
struct mind_data{
	float* im1;
    uint64_t* mindq;
    int qs;
	int m; int n; int o;
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

#include "fastdt2.h"
#include "symmetricDiffeomorphic.h"
#include "primsMST.h"
#include "regularisation2T.h"
#include "MIND-SSC.h"
#include "dataCostD_mind.h"

#include <string>
#include <sstream>

std::string deeds_warp(float *im, float *ux, float *vx, float *wx, int m, int n, int o, float *retbuf)
{
	warpImage(retbuf,im,ux,vx,wx,m,n,o);
	return "";
}

std::string deeds(float* im1, float* im1b, int m, int n, int o, float *ux, float *vx, float *wx, 
                  float alpha=2.0, int randsamp2=50, int maxlevel=5)
{
    // Options - just default for now
	int* grid_step=NULL;
	int* label_hw=NULL;
	int* label_quant=NULL;
	//bool symmetric=True;
	//bool segment=false;
	std::stringstream log;

	log << "Starting DEEDS registration" << endl;
	log << "alpha=" << alpha << endl;
	log << "randsamp=" << randsamp2 << endl;
	log << "levels=" << maxlevel << endl;
	//log << "symmetric=" << symmetric << endl;
	
	int s_grid[10]={7,6,5,4,3,2,2,2,2,2};
    int s_search[10]={6,5,4,3,2,1,1,1,1,1};
    int s_quant[10]={3,2,2,1,1,1,1,1,1,1};
    //char levelstr[]="%dx%dx%dx%dx%dx%dx%dx%dx%dx%d";

	if (!grid_step) grid_step = s_grid;
	if (!label_hw) label_hw = s_search;
	if (!label_quant) label_quant = s_quant;

	//Initialise random variable
	//	srand (time(0));	
	//RAND_SAMPLES=randsamp2;
    
	int sz=m*n*o;
	float *warped1=new float[sz];
	float *warped2=new float[sz];
    
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
    //for(int i=0;i<maxlevel;i++){
    //    mind_step[i]=ceil(label_quant[i]*0.49999);
    //}
    
	int step1; int hw1; float quant1;
    
	//set initial flow-fields to 0; i indicates backward (inverse) transform
	//u is in x-direction (2nd dimension), v in y-direction (1st dim) and w in z-direction (3rd dim)
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
    struct mind_data mind1,mind2;
    
	// Allocate space for MIND descriptors 
	uint64_t* im1_mind=new uint64_t[sz];
	uint64_t* im1b_mind=new uint64_t[sz];
        
	for(int level=0;level<maxlevel;level++){
        quant1=(float)label_quant[level];
        
		mind1.m=m; mind1.n=n; mind1.o=o;
        mind1.im1=im1; mind1.mindq=im1_mind; mind1.qs=(int)max(min(quant1,2.0f),1.0f); //qs determines size of patches for MIND
		mind2.m=m; mind2.n=n; mind2.o=o;
        mind2.im1=im1b; mind2.mindq=im1b_mind; mind2.qs=(int)max(min(quant1,2.0f),1.0f);
        
        create_thread(&thread1,quantisedMIND,(void *)&mind1);
        create_thread(&thread2,quantisedMIND,(void *)&mind2);
        join_thread(thread1);
        join_thread(thread2);
		
		
		struct regulariser_data reg1,reg2;
		struct cost_data cosd1,cosd2,cosd1b,cosd2b;
		
		//warp both high-resolution images according
		warpImage(warped1,im1,ux,vx,wx,m,n,o);
		warpImage(warped2,im1b,uxi,vxi,wxi,m,n,o);
        
		step1=grid_step[level];
		hw1=label_hw[level];
		
		int len3=(int)pow((float)hw1*2+1,3);
		m1=m/step1; n1=n/step1; o1=o/step1; sz1=m1*n1*o1;
		
		//resize flow from u1 to current scale (grid spacing)
		float* u0=new float[sz1]; float* v0=new float[sz1]; float* w0=new float[sz1];
		float* u0i=new float[sz1]; float* v0i=new float[sz1]; float* w0i=new float[sz1];
		upsampleDeformations2(u0,v0,w0,u1,v1,w1,m1,n1,o1,m2,n2,o2);
		upsampleDeformations2(u0i,v0i,w0i,u1i,v1i,w1i,m1,n1,o1,m2,n2,o2);
        
		log<<"==========================================================\n";
		log<<"Level "<<level<<" grid="<<step1<<" with sizes: "<<m1<<"x"<<n1<<"x"<<o1<<" hw="<<hw1<<" quant="<<quant1<<"\n";
		log<<"==========================================================\n";
		
		delete []u1; delete []v1; delete []w1;
		delete []u1i; delete []v1i; delete []w1i;
		u1=new float[sz1]; v1=new float[sz1]; w1=new float[sz1];
		u1i=new float[sz1]; v1i=new float[sz1]; w1i=new float[sz1];
        
		//Minimum-spanning-tree
		int* ordered1=new int[sz1];
		int* parents1=new int[sz1];
		primsGraph(im1b,ordered1,parents1,step1, m, n, o);
		int* ordered2=new int[sz1];
		int* parents2=new int[sz1];
		primsGraph(im1,ordered2,parents2,step1, m, n, o);
        
        //gettimeofday(&time1, NULL);
        
        uint64_t* warped1_mind=new uint64_t[sz];
        uint64_t* warped2_mind=new uint64_t[sz];
        
        mind1.im1=warped1; mind1.mindq=warped1_mind; mind1.qs=(int)max(min(quant1,2.0f),1.0f);
        mind2.im1=warped2; mind2.mindq=warped2_mind; mind2.qs=(int)max(min(quant1,2.0f),1.0f);
        
        create_thread(&thread1,quantisedMIND,(void *)&mind1);
        create_thread(&thread2,quantisedMIND,(void *)&mind2);
        join_thread(thread1);
        join_thread(thread2);

		log<<"Start similarity computation\n";
    
		//data-cost/similarity computation 4-threaded (uses plenty of memory)
		float* costall1=new float[sz1*len3];
		float* costall2=new float[sz1*len3];
        
		cosd1.m=m;cosd1.n=n;cosd1.o=o;
		cosd1.rand_samples = randsamp2;
		cosd1.im1=im1b; cosd1.im1b=warped1; cosd1.alpha=alpha; cosd1.costall=costall1;
        cosd1.fixed_mind=im1b_mind; cosd1.moving_mind=warped1_mind;
		cosd1.hw=hw1; cosd1.step1=(float)step1; cosd1.quant=quant1; cosd1.istart=0; cosd1.iend=sz1/2;
		cosd2.m=m;cosd2.n=n;cosd2.o=o;
		cosd2.rand_samples = randsamp2;
		cosd2.im1=im1; cosd2.im1b=warped2; cosd2.alpha=alpha; cosd2.costall=costall2;
        cosd2.fixed_mind=im1_mind; cosd2.moving_mind=warped2_mind;
		cosd2.hw=hw1; cosd2.step1=(float)step1; cosd2.quant=quant1; cosd2.istart=0; cosd2.iend=sz1/2;
        
		cosd1b.m=m;cosd1b.n=n;cosd1b.o=o;
		cosd1b.rand_samples = randsamp2;
		cosd1b.im1=im1b; cosd1b.im1b=warped1; cosd1b.alpha=alpha; cosd1b.costall=costall1;
        cosd1b.fixed_mind=im1b_mind; cosd1b.moving_mind=warped1_mind;
		cosd1b.hw=hw1; cosd1b.step1=(float)step1; cosd1b.quant=quant1; cosd1b.istart=sz1/2; cosd1b.iend=sz1;
		cosd2b.m=m;cosd2b.n=n;cosd2b.o=o;
		cosd2b.rand_samples = randsamp2;
		cosd2b.im1=im1; cosd2b.im1b=warped2; cosd2b.alpha=alpha; cosd2b.costall=costall2;
        cosd2b.fixed_mind=im1_mind; cosd2b.moving_mind=warped2_mind;
		cosd2b.hw=hw1; cosd2b.step1=(float)step1; cosd2b.quant=quant1; cosd2b.istart=sz1/2; cosd2b.iend=sz1;
        
		create_thread( &thread1, dataCost, (void *) &cosd1);
		create_thread( &thread2, dataCost, (void *) &cosd2);
        create_thread( &thread1b, dataCost, (void *) &cosd1b);
		create_thread( &thread2b, dataCost, (void *) &cosd2b);
		join_thread( thread1);
		join_thread( thread2);
		join_thread( thread1b);
		join_thread( thread2b);
		
		//incremental diffusion regularisation
		log<<"\nStart regularisation on MST!\n";
		log<<"==================================================\n";
        
		reg1.m=m; reg1.n=n; reg1.o=o;
		reg1.u1=u1; reg1.v1=v1; reg1.w1=w1; reg1.costall=costall1;
		reg1.u0=u0; reg1.v0=v0; reg1.w0=w0; reg1.alpha=alpha;
		reg1.hw=hw1; reg1.step1=step1; reg1.quant=quant1;
		reg1.ordered=ordered1; reg1.parents=parents1;
		
		reg2.m=m; reg2.n=n; reg2.o=o;
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
        
		//upsample deformations from grid-resolution to high-resolution (trilinear=1st-order spline)
		upsampleDeformations2(ux,vx,wx,u1,v1,w1,m,n,o,m1,n1,o1);
		upsampleDeformations2(uxi,vxi,wxi,u1i,v1i,w1i,m,n,o,m1,n1,o1);
		//float jac=jacobian(u1,v1,w1,m1,n1,o1,step1, log);
        float energy=harmonicEnergy(ux,vx,wx,m,n,o);
		log<<"harmonic energy of deformation field: "<<energy<<"\n";
        
		m2=m1; n2=n1; o2=o1;
        
        delete[] warped1_mind;
        delete[] warped2_mind;
		
		delete []u0; delete []v0; delete []w0;
		delete []u0i; delete []v0i; delete []w0i;
		delete []costall1; delete []costall2;
		delete []parents1; delete []ordered1;
		delete []parents2; delete []ordered2;
	}
	
	delete[] im1_mind;
	delete[] im1b_mind;

    //optionally write-out warped Labels
    /*
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
    }*/

	delete []u1; delete []v1; delete []w1;
	delete []u1i; delete []v1i; delete []w1i;
	delete []uxi; delete []vxi; delete []wxi;
	delete[] warped1;
    delete[] warped2;

	return log.str();
}

