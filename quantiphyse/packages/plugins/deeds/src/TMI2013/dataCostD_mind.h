/* Dense (stochastic) displacement sampling (deeds)
 for similarity term computation for each node and label.
 Uses a random subsampling (defined by global variable RAND_SAMPLES)
 Quantisation of label space has to be integer when using MIND descriptors
 */

// Get a random number between 0 and 1 (not including 1!)
#ifdef _WIN32
  float getrand(unsigned int *state) {
	  // Apparently rand() is threadsafe under win32
      return ((float)rand())/(RAND_MAX+1);
  }
#else
  float getrand(unsigned int *state) {
      // But not in POSIX, so use rand_r instead with the local state
      return float(rand_r(state))/(float(RAND_MAX)+1);
  }
#endif

const uint64_t m1=0x5555555555555555;
const uint64_t m2=0x3333333333333333;
const uint64_t m4=0x0f0f0f0f0f0f0f0f;
const uint64_t h01=0x0101010101010101;

int popcount_3(uint64_t x)
{
    x-=(x>>1)&m1;
    x=(x&m2)+((x>>2)&m2);
    x=(x+(x>>4))&m4;
    return (x*h01)>>56;
}

/*
unsigned char wordbits[65536];
static int popcount32(uint32_t i)
{
    return (wordbits[i&0xFFFF] + wordbits[i>>16]);
}

static int popcount64(uint64_t i){
    return( wordbits[i&0xFFFF] + wordbits[(i>>16)&0xFFFF] + wordbits[(i>>32)&0xFFFF] + wordbits[i>>48]);
}
*/

void *dataCost(void *threadarg)
{
	struct cost_data *my_data;
	my_data = (struct cost_data *) threadarg;
	//float* fixed=my_data->im1;
	float* moving=my_data->im1b;
	float* costall=my_data->costall;
	float alpha=my_data->alpha;
	int hw=my_data->hw;
	int step1=(int)my_data->step1;
	float quant=my_data->quant;
    uint64_t* fixed_mind=my_data->fixed_mind;
    uint64_t* moving_mind=my_data->moving_mind;
    int istart=my_data->istart;
    int iend=my_data->iend;
	//int beta=1; // MSC: This was a global but is used nowhere else. No idea what it is for.

	// We need local state for the rand_r() function, because
	// rand() is not threadsafe on POSIX
	// 
	// The initial value below will make results reproducible by generating 
	// the same set of random numbers for the same run. Could also use time(0)
	// to generate different random numbers each time e.g. to check
	// robustness of results
    // 
	// unsigned int state = time(0)
	unsigned int state = istart;

    //no subpixel support when using MIND descriptors yet
	bool subpixel=false;
	//if(quant==0.5)
	//	subpixel=true;
	
    for(int i1=0;i1<65536;i1++){
        //    wordbits[i1]=__builtin_popcount(i1);
    }
	float alpha1=(float)step1/(alpha*(float)quant);
	//float randv=getrand(&state);

	int m=my_data->m;
	int n=my_data->n;
	int o=my_data->o;
	int sz=m*n*o;
	
	//int step3=(int)pow((float)step1,3);
	int m1=m/step1;
	int n1=n/step1;
	int o1=o/step1;
	int sz1=m1*n1*o1;
	
	
	//dense displacement space
	int len=hw*2+1;
	int len4=(int)pow((float)len,3);
	float* xs=new float[len4];
	float* ys=new float[len4];
	float* zs=new float[len4];
    int* inds=new int[len4];
	
	for(int i=0;i<len;i++){
		for(int j=0;j<len;j++){
			for(int k=0;k<len;k++){
                int ind1=i+j*len+k*len*len;
                xs[i+j*len+k*len*len]=(float)((j-hw)*quant);
                ys[i+j*len+k*len*len]=(float)((i-hw)*quant);
                zs[i+j*len+k*len*len]=(float)((k-hw)*quant);
                inds[ind1]=(int)(ys[ind1]+xs[ind1]*m+zs[ind1]*m*n);
			}
		}
	}
	
	int hw2;
	if(subpixel)
		hw2=hw;
	else
		hw2=hw*(int)quant;
	
	float* movingi;
    
	int mi=m;
	int ni=n;
	int oi=o;
    
    
    movingi=new float[sz];
    for(int i=0;i<sz;i++){
        movingi[i]=moving[i];
    }
    
    
	int samples=my_data->rand_samples;
	bool randommode=samples<pow((float)step1,3);
	int maxsamp;
	if(randommode){
		maxsamp=samples;
	}
	else{
		maxsamp=(int)pow((float)step1,3);
	}
	float* cost1=new float[len4];
	float* costcount=new float[len4];
	//int frac=(int)(sz1/25);
    //float beta1=(1.0f-beta);
	float alpha2=alpha1/(float)maxsamp;
	int xx2,yy2,zz2;

	for(int i=istart;i<iend;i++){
		//if(((i-istart)%frac)==0){
		//	cout<<"x"<<flush;
		//}
		int z1=i/(m1*n1);
		int x1=(i-z1*m1*n1)/m1;
		int y1=i-z1*m1*n1-x1*m1;
		
		z1*=step1;
		x1*=step1;
		y1*=step1;
		
		bool boundaries=true; //check image boundaries to save min/max computations
		if(subpixel){
			if(x1*2+(step1-1)*2+hw2>=ni || y1*2+(step1-1)*2+hw2>=mi || z1*2+(step1-1)*2+hw2>=oi)
				boundaries=false;
			if(x1*2-hw2<0 || y1*2-hw2<0 || z1*2-hw2<0)
				boundaries=false;
		}
		
		else{
			if(x1+(step1-1)+hw2>=ni || y1+(step1-1)+hw2>=mi || z1+(step1-1)+hw2>=oi)
				boundaries=false;
			if(x1-hw2<0 || y1-hw2<0 || z1-hw2<0)
				boundaries=false;
		}
		
		
		for(int l=0;l<len4;l++){
			cost1[l]=0.0;
		}

		for(int j1=0;j1<maxsamp;j1++){
			int i1;
			if(randommode) {
				//stochastic sampling for speed-up (~8x faster)
				i1=(int)(getrand(&state)*pow((float)step1,3));
			}
			else {
				i1=j1;
			}
			int zz=i1/(step1*step1);
			int xx=(i1-zz*step1*step1)/step1;
			int yy=i1-zz*step1*step1-xx*step1;

			xx+=x1;
			yy+=y1;
			zz+=z1;
			int ind1=yy+xx*m+zz*m*n;
			
			for(int l=0;l<len4;l++){
                int ind2;
				if(!boundaries){
                    
                    xx2=max(min(xx+(int)(xs[l]),ni-1),0);
                    yy2=max(min(yy+(int)(ys[l]),mi-1),0);
                    zz2=max(min(zz+(int)(zs[l]),oi-1),0);
                    ind2=yy2+xx2*m+zz2*m*n;
				}
				else{
                    ind2=ind1+inds[l];
				}
				//point-wise similarity term (hamming distance of MIND descriptors)
                cost1[l]+=popcount_3(fixed_mind[ind1]^moving_mind[ind2]);
			}
		}

		for(int l=0;l<len4;l++){
			costall[i+l*sz1]=0.5f*alpha2*cost1[l];
		}
	}
    
    
    
	delete []movingi;
    
	delete []cost1;
	delete []costcount;
	delete []xs;
	delete []ys;
	delete []zs;
	delete []inds;
    
    return NULL;
    
}

template <typename TypeW>

void warpImage(TypeW* warped,TypeW* im1,float* u1,float* v1,float* w1, int m, int n, int o){
    //int sz=m*n*o;
    interp3(warped,im1,u1,v1,w1,m,n,o,m,n,o,true);
}