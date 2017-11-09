
struct inverse_data{
    float* x1; float* y1; float* z1;
    float* x2; float* y2; float* z2;
    float* u1; float* v1; float* w1;
    int m2; int n2; int o2; int istart; int iend;
};
void *inverseIteration(void *threadarg){
    struct inverse_data *my_data;
    my_data = (struct inverse_data *) threadarg;
	float* x1=my_data->x1;
    float* y1=my_data->y1;
    float* z1=my_data->z1;
    float* x2=my_data->x2;
    float* y2=my_data->y2;
    float* z2=my_data->z2;
    
    float* u1=my_data->u1;
    float* v1=my_data->v1;
    float* w1=my_data->w1;
    
    int m2=my_data->m2;
    int n2=my_data->n2;
    int o2=my_data->o2;
    
    int istart=my_data->istart;
    int iend=my_data->iend;
    
    
    int M1=m2; int N1=n2; int O1=o2;
    
	
    //forward transform
    for(int k=0;k<o2;k++){
        for(int j=0;j<n2;j++){
            for(int i=istart;i<iend;i++){
                
                
                int x=floor(x1[i+j*m2+k*m2*n2]); int y=floor(y1[i+j*m2+k*m2*n2]);  int z=floor(z1[i+j*m2+k*m2*n2]);
                float dx=x1[i+j*m2+k*m2*n2]-x; float dy=y1[i+j*m2+k*m2*n2]-y; float dz=z1[i+j*m2+k*m2*n2]-z;
                
                x+=j; y+=i; z+=k;
                
                
                int ym=min(max(y,0),M1-1); int yp=min(max(y+1,0),M1-1);
                int xm=min(max(x,0),N1-1); int xp=min(max(x+1,0),N1-1);
                int zm=min(max(z,0),O1-1); int zp=min(max(z+1,0),O1-1);
                
                
                u1[i+j*m2+k*m2*n2]=0.5*x1[i+j*m2+k*m2*n2]-0.5*((1.0-dx)*(1.0-dy)*(1.0-dz)*x2[ym+xm*M1+zm*M1*N1]+(1.0-dx)*dy*(1.0-dz)*x2[yp+xm*M1+zm*M1*N1]+dx*(1.0-dy)*(1.0-dz)*x2[ym+xp*M1+zm*M1*N1]+(1.0-dx)*(1.0-dy)*dz*x2[ym+xm*M1+zp*M1*N1]+dx*dy*(1.0-dz)*x2[yp+xp*M1+zm*M1*N1]+(1.0-dx)*dy*dz*x2[yp+xm*M1+zp*M1*N1]+dx*(1.0-dy)*dz*x2[ym+xp*M1+zp*M1*N1]+dx*dy*dz*x2[yp+xp*M1+zp*M1*N1]);
                
                v1[i+j*m2+k*m2*n2]=0.5*y1[i+j*m2+k*m2*n2]-0.5*((1.0-dx)*(1.0-dy)*(1.0-dz)*y2[ym+xm*M1+zm*M1*N1]+(1.0-dx)*dy*(1.0-dz)*y2[yp+xm*M1+zm*M1*N1]+dx*(1.0-dy)*(1.0-dz)*y2[ym+xp*M1+zm*M1*N1]+(1.0-dx)*(1.0-dy)*dz*y2[ym+xm*M1+zp*M1*N1]+dx*dy*(1.0-dz)*y2[yp+xp*M1+zm*M1*N1]+(1.0-dx)*dy*dz*y2[yp+xm*M1+zp*M1*N1]+dx*(1.0-dy)*dz*y2[ym+xp*M1+zp*M1*N1]+dx*dy*dz*y2[yp+xp*M1+zp*M1*N1]);
                
                w1[i+j*m2+k*m2*n2]=0.5*z1[i+j*m2+k*m2*n2]-0.5*((1.0-dx)*(1.0-dy)*(1.0-dz)*z2[ym+xm*M1+zm*M1*N1]+(1.0-dx)*dy*(1.0-dz)*z2[yp+xm*M1+zm*M1*N1]+dx*(1.0-dy)*(1.0-dz)*z2[ym+xp*M1+zm*M1*N1]+(1.0-dx)*(1.0-dy)*dz*z2[ym+xm*M1+zp*M1*N1]+dx*dy*(1.0-dz)*z2[yp+xp*M1+zm*M1*N1]+(1.0-dx)*dy*dz*z2[yp+xm*M1+zp*M1*N1]+dx*(1.0-dy)*dz*z2[ym+xp*M1+zp*M1*N1]+dx*dy*dz*z2[yp+xp*M1+zp*M1*N1]);
                
            }
        }
    }
    return NULL;
}



void consistentMappingCL(float* u1,float* v1,float* w1,float* u1b,float* v1b,float* w1b,int m2,int n2,int o2,int factor){
    
    timeval time1,time2;
    int sz2=m2*n2*o2;
    float* x1=new float[sz2];
    float* y1=new float[sz2];
    float* z1=new float[sz2];
    float* x2=new float[sz2];
    float* y2=new float[sz2];
    float* z2=new float[sz2];
    
    float factor1=1.0/(float)factor;
    
    for(int i=0;i<sz2;i++){
        x1[i]=u1[i]*factor1;
        y1[i]=v1[i]*factor1;
        z1[i]=w1[i]*factor1;
        x2[i]=u1b[i]*factor1;
        y2[i]=v1b[i]*factor1;
        z2[i]=w1b[i]*factor1;
    }
    
    int lens[]={0,m2/4,m2/2,(3*m2)/4,m2};
    
    
    for(int iter=0;iter<10;iter++){
        
        struct inverse_data inverse1,inverse2,inverse3,inverse4;
        inverse1.m2=m2; inverse1.n2=n2; inverse1.o2=o2;
        inverse1.x1=x1; inverse1.y1=y1; inverse1.z1=z1;
        inverse1.x2=x2; inverse1.y2=y2; inverse1.z2=z2;
        inverse1.u1=u1; inverse1.v1=v1; inverse1.w1=w1;
        inverse2=inverse1; inverse3=inverse1; inverse4=inverse1;
        inverse1.istart=lens[0]; inverse1.iend=lens[1];
        inverse2.istart=lens[1]; inverse2.iend=lens[2];
        inverse3.istart=lens[2]; inverse3.iend=lens[3];
        inverse4.istart=lens[3]; inverse4.iend=lens[4];
        
        pthread_t thread1,thread2,thread3,thread4;
        
        pthread_create(&thread1,NULL,inverseIteration,(void *)&inverse1);
        pthread_create(&thread2,NULL,inverseIteration,(void *)&inverse2);
        pthread_create(&thread3,NULL,inverseIteration,(void *)&inverse3);
        pthread_create(&thread4,NULL,inverseIteration,(void *)&inverse4);
        pthread_join(thread1,NULL);
        pthread_join(thread2,NULL);
        pthread_join(thread3,NULL);
        pthread_join(thread4,NULL);
        
        //backward transform
        inverse1.x1=x2; inverse1.y1=y2; inverse1.z1=z2;
        inverse1.x2=x1; inverse1.y2=y1; inverse1.z2=z1;
        inverse1.u1=u1b; inverse1.v1=v1b; inverse1.w1=w1b;
        
        inverse2=inverse1; inverse3=inverse1; inverse4=inverse1;
        inverse1.istart=lens[0]; inverse1.iend=lens[1];
        inverse2.istart=lens[1]; inverse2.iend=lens[2];
        inverse3.istart=lens[2]; inverse3.iend=lens[3];
        inverse4.istart=lens[3]; inverse4.iend=lens[4];
        
        pthread_create(&thread1,NULL,inverseIteration,(void *)&inverse1);
        pthread_create(&thread2,NULL,inverseIteration,(void *)&inverse2);
        pthread_create(&thread3,NULL,inverseIteration,(void *)&inverse3);
        pthread_create(&thread4,NULL,inverseIteration,(void *)&inverse4);
        pthread_join(thread1,NULL);
        pthread_join(thread2,NULL);
        pthread_join(thread3,NULL);
        pthread_join(thread4,NULL);
        
        for(int i=0;i<sz2;i++){
            x1[i]=u1[i]; y1[i]=v1[i]; z1[i]=w1[i];
            x2[i]=u1b[i]; y2[i]=v1b[i]; z2[i]=w1b[i];
        }
    }
    
    
    for(int i=0;i<sz2;i++){
		u1[i]*=(float)factor;
		v1[i]*=(float)factor;
		w1[i]*=(float)factor;
		u1b[i]*=(float)factor;
		v1b[i]*=(float)factor;
		w1b[i]*=(float)factor;
	}
    
    delete x1; delete x2; delete y1; delete y2; delete z1; delete z2;
    
    
    
}