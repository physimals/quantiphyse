
const uint64_t m1=0x5555555555555555;
const uint64_t m2=0x3333333333333333;
const uint64_t m4=0x0f0f0f0f0f0f0f0f;
const uint64_t h01=0x0101010101010101;

unsigned int popcount64(unsigned long long x)
{
    x = (x & 0x5555555555555555ULL) + ((x >> 1) & 0x5555555555555555ULL);
    x = (x & 0x3333333333333333ULL) + ((x >> 2) & 0x3333333333333333ULL);
    x = (x & 0x0F0F0F0F0F0F0F0FULL) + ((x >> 4) & 0x0F0F0F0F0F0F0F0FULL);
    return (x * 0x0101010101010101ULL) >> 56;
}

int popcount_3(uint64_t x)
{
    x-=(x>>1)&m1;
    x=(x&m2)+((x>>2)&m2);
    x=(x+(x>>4))&m4;
    return (x*h01)>>56;
}

void ind2sub(float* subdisp,int len,int ind){

    int search=(len-1)/2;
    int z=ind/(len*len);
    int x=(ind-z*len*len)/len;
    int y=ind-z*len*len-x*len;

    subdisp[0]=(float)(y-search);
    subdisp[1]=(float)(x-search);
    subdisp[2]=(float)(z-search);

}


void *costVolFilter(void *threadarg)
{
    struct cost_data *my_data;
    my_data = (struct cost_data *) threadarg;
    uint64_t* targetS=my_data->targetS;
    uint64_t* warped1S=my_data->warped1S;
    float* tempmem=my_data->tempmem;
    float* costvol=my_data->costvol;
    int hw=my_data->hw;
    int sparse=my_data->sparse;
    int r=my_data->r;
    int istart=my_data->istart; int iend=my_data->iend;
    
    //timeval time1,time2;
    int m=image_m; int n=image_n; int o=image_o;
    int sz=m*n*o;

    int m1=m/sparse; int n1=n/sparse; int o1=o/sparse;
    int sz1=m1*n1*o1;

    int len=hw*2+1; int len3=len*len*len;
    int len4=len3-len3%4+(((len3%4)==0)?0:4);

    int pad1=hw; int pad2=pad1*2;

    int mp=m1+pad2; int np=n1+pad2; int op=o1+pad2;
    int szp=mp*np*op;


   // float* temp1=new float[sz1*4];
   // float* temp2=new float[sz1*4];

   // float* distance2=new float[sz1*4];
   // float* datacost2=new float[sz1*4];

    float* temp1=tempmem;
    float* temp2=tempmem+sz1*4;
    float* distance2=tempmem+2*sz1*4;
    float* datacost2=tempmem+3*sz1*4;

    float alpha=4.0f*0.0156f/(float)pow(r*2.0f+1.0f,3);
    for(int l4=istart;l4<iend;l4++){

        //gettimeofday(&time1, NULL);
        for(int l=0;l<4;l++){
            for(int k=0;k<o1;k++){
                for(int j=0;j<n1;j++){
                    for(int i=0;i<m1;i++){
                        int l2=l4*4+l;
                        if(l2<len3){ //ensure no empty labels (for four-alignment) are used

                            int zs=l2/(len*len); int xs=(l2-zs*len*len)/len; int ys=l2-zs*len*len-xs*len;
                            int y2=ys+i; int x2=xs+j; int z2=zs+k;
                            int movind=y2+x2*mp+z2*mp*np;
                            distance2[(i+j*m1+k*m1*n1)*4+l]=alpha*popcount_3(targetS[i+j*m1+k*m1*n1]^warped1S[movind]);//+popcount_3(movingS[movind]^warped2S[i+j*m1+k*m1*n1]);
                        }
                    }
                }
            }
        }

        boxfilter4((__m128*)datacost2,(__m128*)distance2,(__m128*)temp1,(__m128*)temp2,r,m1,n1,o1);
        //recursive b-spline smoothing
       // boxfilter4((__m128*)distance2,(__m128*)datacost2,(__m128*)distance2,(__m128*)temp1,(__m128*)temp2,r,m1,n1,o1);
       // boxfilter4((__m128*)datacost2,(__m128*)temp1,(__m128*)temp2,r,m1,n1,o1);

        for(int l=0;l<4;l++){
            int l2=l4*4+l;
            if(l2<len3){ //ensure no empty labels (for four-alignment) are used
                for(int i=0;i<sz1;i++){
                    costvol[i+l2*sz1]=datacost2[i*4+l];
                    //if(datacost2[i*4+l]<minval[i]){
                    //    minval[i]=datacost2[i*4+l]; minind[i]=l2;
                    //}
                }
            }
        }



    }//end of l4 loop
    return NULL;


}

void dataReg(float* costvol,float* target,float* warped1,int hw,int sparse,int r,float h1){
    timeval time1,time2;
    int m=image_m; int n=image_n; int o=image_o;
    int sz=m*n*o;
    int m1=m/sparse; int n1=n/sparse; int o1=o/sparse;
    int sz1=m1*n1*o1;
    printf("start mind image size: %dx%dx%d, lowres: %dx%dx%d\n",m,n,o,m1,n1,o1);
    pthread_t thread1, thread2, thread3, thread4;
    gettimeofday(&time1, NULL);

    uint64_t* targetS=new uint64_t[sz1];
    struct mind_data mind1,mind2;
    mind1.im1=target; mind1.mindq=targetS; mind1.qs=min(sparse,2); mind1.lr=sparse;//qs determines size of patches for MIND


    uint64_t* warped1S=new uint64_t[sz1];
    mind2.im1=warped1; mind2.mindq=warped1S; mind2.qs=min(sparse,2); mind2.lr=sparse;//qs determines size of patches for MIND

    pthread_create(&thread1,NULL,quantisedMIND,(void *)&mind1);
    pthread_create(&thread2,NULL,quantisedMIND,(void *)&mind2);
    pthread_join(thread1,NULL);
    pthread_join(thread2,NULL);


    gettimeofday(&time2, NULL);
    
    timeD=(time2.tv_sec+time2.tv_usec/1e6-(time1.tv_sec+time1.tv_usec/1e6));


    printf("Time for MIND (lr) : %2.2f sec. \n",timeD);
    //padding of moving images (symmetrically mirrored boundaries)
    int pad1=hw; int pad2=pad1*2;
    int mp=m1+pad2; int np=n1+pad2; int op=o1+pad2;
    int szp=mp*np*op;
    uint64_t* warped1p=new uint64_t[szp];

    for(int k=0;k<op;k++){
        int k2=k-pad1;
        if(k<pad1)
            k2=pad1-1-k;
        if(k>=o1+pad1)
            k2=o1*2-k+pad1-1;
        for(int j=0;j<np;j++){
            int j2=j-pad1;
            if(j<pad1)
                j2=pad1-1-j;
            if(j>=n1+pad1)
                j2=n1*2-j+pad1-1;
            for(int i=0;i<mp;i++){
                int i2=i-pad1;
                if(i<pad1)
                    i2=pad1-1-i;
                if(i>=m1+pad1)
                    i2=m1*2-i+pad1-1;
                warped1p[i+j*mp+k*mp*np]=warped1S[i2+j2*m1+k2*m1*n1];
                //moving1p[i+j*mp+k*mp*np]=movingS[i2+j2*m1+k2*m1*n1];
            }
        }
    }



    int len=hw*2+1; int len3=len*len*len;
    int len4=len3-len3%4+(((len3%4)==0)?0:4);
    printf("m1=%d n1=%d o1=%d. len3: %d, len4: %d, r: %d, sparse: %d\n",m,n,o,len3,len4,r,sparse);




    float* tempmem=new float[sz1*64];

    cout<<"starting multi-threading of costVolume filtering now!\n";

    int len44=len4/4;
    int lens[]={0,len44/4,len44/2,(3*len44)/4,len44};
    gettimeofday(&time1, NULL);
    struct cost_data cost1,cost2,cost3,cost4;
    cost1.targetS=targetS; cost1.warped1S=warped1p;
    cost1.costvol=costvol; cost1.tempmem=tempmem;
    cost1.hw=hw; cost1.sparse=sparse; cost1.r=r; cost1.istart=lens[0]; cost1.iend=lens[1];
    cost2=cost1; cost2.istart=lens[1]; cost2.iend=lens[2];
    cost2.tempmem=tempmem+sz1*16;
    cost3=cost1; cost3.istart=lens[2]; cost3.iend=lens[3];
    cost3.tempmem=tempmem+2*sz1*16;
    cost4=cost1; cost4.istart=lens[3]; cost4.iend=lens[4];
    cost4.tempmem=tempmem+3*sz1*16;


    pthread_create(&thread1,NULL,costVolFilter,(void *)&cost1);
    pthread_create(&thread2,NULL,costVolFilter,(void *)&cost2);
    pthread_create(&thread3,NULL,costVolFilter,(void *)&cost3);
    pthread_create(&thread4,NULL,costVolFilter,(void *)&cost4);
    pthread_join(thread1,NULL);
    pthread_join(thread2,NULL);
    pthread_join(thread3,NULL);
    pthread_join(thread4,NULL);

    gettimeofday(&time2, NULL);
    
    timeP=(time2.tv_sec+time2.tv_usec/1e6-(time1.tv_sec+time1.tv_usec/1e6));


    delete targetS; delete warped1p;  delete tempmem;

    float numd=(float)len4*(float)sz1;

    printf("TimeP : %2.2f sec. TimeD: %2.2f sec. \nSpeedP: %2.2f MPix/s. SpeedD: %2.2f MPix/s\n",timeP,timeD,numd/timeP/1e6,numd/timeD/1e6);



}
