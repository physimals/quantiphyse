/* Dense (stochastic) displacement sampling (deeds)
 for similarity term computation for each node and label.
 Uses a random subsampling (defined by global variable RAND_SAMPLES)
 (this step is not described in MICCAI paper)
 Quantisation of label space has to be integer or 0.5 (uses trilinear upsampling)
*/

void *dataCost(void *threadarg)
{
	struct cost_data *my_data;
	my_data = (struct cost_data *) threadarg;
	float* fixed=my_data->im1;
	float* moving=my_data->im1b;
	float* costall=my_data->costall;
	float alpha=my_data->alpha;
	int hw=my_data->hw;
	int step1=my_data->step1;
	float quant=my_data->quant;
	
	bool subpixel=false;
	if(quant==0.5)
		subpixel=true;
	
	
	float alpha1=(float)step1/(alpha*(float)quant);
	
	float randv=((float)rand()/float(RAND_MAX));
	timeval time1,time2;
	int m=image_m;
	int n=image_n;
	int o=image_o;
	int sz=m*n*o;
	
	int step3=pow(step1,3);
	int m1=m/step1;
	int n1=n/step1;
	int o1=o/step1;
	int sz1=m1*n1*o1;
	
	
	//dense displacement space
	int len=hw*2+1;
	int len4=pow(len,3);
	float* xs=new float[len4];
	float* ys=new float[len4];
	float* zs=new float[len4];
	
	for(int i=0;i<len;i++){
		for(int j=0;j<len;j++){
			for(int k=0;k<len;k++){
					xs[i+j*len+k*len*len]=(float)((j-hw)*quant);
					ys[i+j*len+k*len*len]=(float)((i-hw)*quant);
					zs[i+j*len+k*len*len]=(float)((k-hw)*quant);

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
	
	if(subpixel){
		//interpolation with subsampling factor of 2
		mi*=2; ni*=2; oi*=2;
		int szi=mi*ni*oi;
		float* x1=new float[szi];
		float* y1=new float[szi];
		float* z1=new float[szi];
		movingi=new float[szi];
		for(int k=0;k<oi;k++){
			for(int j=0;j<ni;j++){
				for(int i=0;i<mi;i++){
					x1[i+j*mi+k*mi*ni]=0.5*(float)j;
					y1[i+j*mi+k*mi*ni]=0.5*(float)i;
					z1[i+j*mi+k*mi*ni]=0.5*(float)k;
				}
			}
		}
		interp3(movingi,moving,x1,y1,z1,mi,ni,oi,m,n,o,false);
		delete []x1;
		delete []y1;
		delete []z1;
		for(int i=0;i<len4;i++){
			xs[i]*=2.0;
			ys[i]*=2.0;
			zs[i]*=2.0;
		}
	}
	else{
		movingi=new float[sz];
		for(int i=0;i<sz;i++){
			movingi[i]=moving[i];
		}
		
	}
		
	int samples=RAND_SAMPLES;
	bool randommode=samples<pow(step1,3);
	int maxsamp;
	if(randommode){
		maxsamp=samples;
	}
	else{
		maxsamp=pow(step1,3);
	}
	float* cost1=new float[len4];
	float* costcount=new float[len4];
	int frac=(int)(sz1/12);

	float alpha2=alpha1/(float)maxsamp;
	int xx2,yy2,zz2;
	for(int i=0;i<sz1;i++){
		//if((i%frac)==0){
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
			if(x1*2+(step1-1)*2+hw2>=ni|y1*2+(step1-1)*2+hw2>=mi|z1*2+(step1-1)*2+hw2>=oi)
				boundaries=false;
			if(x1*2-hw2<0|y1*2-hw2<0|z1*2-hw2<0)
				boundaries=false;
		}
		
		else{
			if(x1+(step1-1)+hw2>=ni|y1+(step1-1)+hw2>=mi|z1+(step1-1)+hw2>=oi)
				boundaries=false;
			if(x1-hw2<0|y1-hw2<0|z1-hw2<0)
				boundaries=false;
		}
		
		
		for(int l=0;l<len4;l++){
			cost1[l]=0.0;
		}
		
		for(int j1=0;j1<maxsamp;j1++){
			int i1;
			if(randommode)
				//stochastic sampling for speed-up (~8x faster)
				i1=(int)(rand()*pow(step1,3)/float(RAND_MAX));
			else
				i1=j1;
			int zz=i1/(step1*step1);
			int xx=(i1-zz*step1*step1)/step1;
			int yy=i1-zz*step1*step1-xx*step1;
			
			xx+=x1;
			yy+=y1;
			zz+=z1;

			for(int l=0;l<len4;l++){
				if(not(boundaries)){
					if(subpixel){
						xx2=max(min(xx*2+(int)xs[l],ni-1),0);
						yy2=max(min(yy*2+(int)ys[l],mi-1),0);
						zz2=max(min(zz*2+(int)zs[l],oi-1),0);
					}
					else{
						xx2=max(min(xx+(int)(xs[l]),ni-1),0);
						yy2=max(min(yy+(int)(ys[l]),mi-1),0);
						zz2=max(min(zz+(int)(zs[l]),oi-1),0);
					}
				}
				else{
					if(subpixel){
						xx2=xx*2+(int)xs[l];
						yy2=yy*2+(int)ys[l];
						zz2=zz*2+(int)zs[l];
					}
					else{
						xx2=xx+(int)xs[l];
						yy2=yy+(int)ys[l];
						zz2=zz+(int)zs[l];
					}
				}
				//point-wise similarity term (replace if needed, e.g. with pow( ,2.0)
				cost1[l]+=fabs(fixed[yy+xx*m+zz*m*n]-movingi[yy2+xx2*mi+zz2*mi*ni]);

			}
		}
		
		for(int l=0;l<len4;l++){
			costall[i+l*sz1]=alpha2*cost1[l];
		}
	}

	delete []movingi;

	delete []cost1;
	delete []costcount;
	delete []xs;
	delete []ys;
	delete []zs;
    
    return NULL;

}

template <typename TypeW>

void warpImage(TypeW* warped,TypeW* im1,float* u1,float* v1,float* w1){
    int m=image_m; int n=image_n; int o=image_o; int sz=m*n*o;
    interp3(warped,im1,u1,v1,w1,m,n,o,m,n,o,true);
}