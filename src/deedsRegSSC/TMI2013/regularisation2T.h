/* Incremental diffusion regularisation of parametrised transformation
 using (globally optimal) belief-propagation on minimum spanning tree.
 Fast distance transform (see fastDT2.h) uses squared differences.
 Similarity cost for each node and label has to be given as input.
*/

void *regularisation(void *threadarg)
{
	struct regulariser_data *my_data;
	my_data = (struct regulariser_data *) threadarg;
	float* u1 = my_data->u1;
	float* v1 = my_data->v1;
	float* w1 = my_data->w1;
	float* u0 = my_data->u0;
	float* v0 = my_data->v0;
	float* w0 = my_data->w0;
	float* costall=my_data->costall;
	float alpha=my_data->alpha;
	int hw=my_data->hw;
	int step1=my_data->step1;
	float quant=my_data->quant;
	int* ordered=my_data->ordered;
	int* parents=my_data->parents;
		
	int m2=image_m;
	int n2=image_n;
	int o2=image_o;
		
	int m=m2/step1;
	int n=n2/step1;
	int o=o2/step1;
	
	timeval time1,time2;
	
	int sz=m*n*o;
	
	//dense displacement space
	int len=hw*2+1;
	float* xs=new float[len*len*len];
	float* ys=new float[len*len*len];
	float* zs=new float[len*len*len];
	
	for(int i=0;i<len;i++){
		for(int j=0;j<len;j++){
			for(int k=0;k<len;k++){
				xs[i+j*len+k*len*len]=(j-hw)*quant;
				ys[i+j*len+k*len*len]=(i-hw)*quant;
				zs[i+j*len+k*len*len]=(k-hw)*quant;
			}
		}
	}
	int len2=len*len*len;
	
	int *selected=new int[sz];
	short *allinds=new short[sz*len2];
	float *cost1=new float[len2];
	float *vals=new float[len2];
	int *inds=new int[len2];
	gettimeofday(&time1, NULL);
	
	float alpha1=(float)step1/(alpha*quant);
	//inverse of regularisation weighting alpha
	//includes (division by) distance of control points (step1) and quantisation

	int xs1,ys1,zs1,xx,yy,zz,xx2,yy2,zz2;

	for(int i=0;i<len2;i++){
		cost1[i]=0;
	}
	
	int frac=(int)(sz/25);
	//calculate mst-cost
	for(int i=(sz-1);i>0;i--){ //do for each control point
		if((i%frac)==0){
			cout<<"x"<<flush;
		}
		int ochild=ordered[i];
		int oparent=parents[ordered[i]];
		int z1=ochild/(m*n);
		int x1=(ochild-z1*m*n)/m;
		int y1=ochild-z1*m*n-x1*m;
		int z2=oparent/(m*n);
		int x2=(oparent-z2*m*n)/m;
		int y2=oparent-z2*m*n-x2*m;
		
		for(int l=0;l<len2;l++){
			cost1[l]=costall[ochild+l*sz];
		}
		//important for INCREMENTAL regularisation (offset delta)
		float dx1=(u0[y2+x2*m+z2*m*n]-u0[y1+x1*m+z1*m*n])/(float)quant;
		float dy1=(v0[y2+x2*m+z2*m*n]-v0[y1+x1*m+z1*m*n])/(float)quant;
		float dz1=(w0[y2+x2*m+z2*m*n]-w0[y1+x1*m+z1*m*n])/(float)quant;
		
		//fast distance transform see fastDT2.h
		dt3x(cost1,inds,len,dx1,dy1,dz1);
		
		//argmin for each label
		for(int l=0;l<len2;l++){
			allinds[y1+x1*m+z1*m*n+l*sz]=inds[l];
		}
		
		//add mincost to parent node
		for(int l=0;l<len2;l++){
			costall[oparent+l*sz]+=cost1[l];
		}
		
	}
	
	//mst-cost & select displacement for root note
	int i=0;
	int oroot=ordered[i];
	int z1=oroot/(m*n);
	int x1=(oroot-z1*m*n)/m;
	int y1=oroot-z1*m*n-x1*m;
	for(int l=0;l<len2;l++){
		cost1[l]=costall[oroot+l*sz];
	}
	float value; int index;
	minimumIndA(cost1,value,index,len2);
	for(int l=0;l<len2;l++){
		allinds[y1+x1*m+z1*m*n+l*sz]=l;
	}
	selected[y1+x1*m+z1*m*n]=index;
	u1[y1+x1*m+z1*m*n]=xs[index]+u0[y1+x1*m+z1*m*n];
	v1[y1+x1*m+z1*m*n]=ys[index]+v0[y1+x1*m+z1*m*n];	
	w1[y1+x1*m+z1*m*n]=zs[index]+w0[y1+x1*m+z1*m*n];
	
	
	//select displacements and add to previous deformation field
	for(int i=1;i<sz;i++){
		int ochild=ordered[i];
		int oparent=parents[ordered[i]];
		int z1=ochild/(m*n);
		int x1=(ochild-z1*m*n)/m;
		int y1=ochild-z1*m*n-x1*m;
		int z2=oparent/(m*n);
		int x2=(oparent-z2*m*n)/m;
		int y2=oparent-z2*m*n-x2*m;
		//select from argmin of based on parent selection
		index=allinds[y1+x1*m+z1*m*n+selected[y2+x2*m+z2*m*n]*m*n*o];
		selected[y1+x1*m+z1*m*n]=index;
		u1[y1+x1*m+z1*m*n]=xs[index]+u0[y1+x1*m+z1*m*n];
		v1[y1+x1*m+z1*m*n]=ys[index]+v0[y1+x1*m+z1*m*n];	
		w1[y1+x1*m+z1*m*n]=zs[index]+w0[y1+x1*m+z1*m*n];
		
	}
	
	//cout<<"Deformation field calculated!\n";

	delete cost1;
	delete vals;
	delete inds;
	delete allinds;
	delete selected;
    
    return NULL;
	
}

