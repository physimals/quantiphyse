
void ind2sub(float* subdisp,int len,int ind){

    int search=(len-1)/2;
    int z=ind/(len*len);
    int x=(ind-z*len*len)/len;
    int y=ind-z*len*len-x*len;

    subdisp[0]=(float)(y-search);
    subdisp[1]=(float)(x-search);
    subdisp[2]=(float)(z-search);

}


void prepNCC(float* meanvar1,float* vol1,int r,int m,int n,int o){
    
    
    int sz=m*n*o;
    
    float* temp1=new float[sz];
    float* temp2=new float[sz];
    float* mean1=new float[sz];
    
    float* var1=new float[sz];
    
    float* vxsum=new float[sz];
    
    float* val1=new float[sz];
    
    int r2=max(r,1);
    for(int i=0;i<sz;i++){
        val1[i]=1;
    }
    boxfilter1CC(vxsum,val1,temp1,temp2,r2,m,n,o);
    
    
    boxfilter1CC(mean1,vol1,temp1,temp2,r2,m,n,o);
    for(int i=0;i<sz;i++){
        meanvar1[i]=1.0f/vxsum[i];
        mean1[i]*=meanvar1[i];
        meanvar1[i+sz]=mean1[i];
        val1[i]=vol1[i]*vol1[i];
    }
    boxfilter1CC(var1,val1,temp1,temp2,r2,m,n,o);
    for(int i=0;i<sz;i++){
        var1[i]*=meanvar1[i];
        var1[i]-=mean1[i]*mean1[i];
        meanvar1[i+sz*2]=sqrt(var1[i]);
    }
    
    
    delete val1; delete temp1; delete temp2; delete mean1;
    delete var1;
    
}


void *costVolFilter(void *threadarg)
{
    struct cost_data *my_data;
    my_data = (struct cost_data *) threadarg;
	float* targetS = my_data->targetS;
	float* warped1S = my_data->warped1S;
    float* meanvar1=my_data->meanvar1;
    float* meanvar2=my_data->meanvar2;
    float* tempmem=my_data->tempmem;


    float* costvol=my_data->costvol;
    int hw=my_data->hw;
    int sparse=my_data->sparse;
    int r=my_data->r;
    int istart=my_data->istart; int iend=my_data->iend;
    
    int m=image_m; int n=image_n; int o=image_o;
    int sz=m*n*o;

    int m1=m/sparse; int n1=n/sparse; int o1=o/sparse;
    int sz1=m1*n1*o1;

    //uses SSE filtering so should be four-aligned
    int len=hw*2+1; int len3=len*len*len;
    int len4=len3-len3%4+(((len3%4)==0)?0:4);

    int pad1=hw; int pad2=pad1*2;

    int mp=m1+pad2; int np=n1+pad2; int op=o1+pad2;
    int szp=mp*np*op;


    float* temp1=tempmem;
    float* temp2=tempmem+sz1*4;
    float* distance2=tempmem+2*sz1*4;
    float* datacost2=tempmem+3*sz1*4;

    for(int l4=istart;l4<iend;l4++){ //for all displacement labels

        for(int l=0;l<4;l++){
            for(int k=0;k<o1;k++){
                for(int j=0;j<n1;j++){
                    for(int i=0;i<m1;i++){
                        int l2=l4*4+l;
                        if(l2<len3){ //ensure no empty labels (for four-alignment) are used
                            int zs=l2/(len*len); int xs=(l2-zs*len*len)/len; int ys=l2-zs*len*len-xs*len;
                            int y2=ys+i; int x2=xs+j; int z2=zs+k;
                            int movind=y2+x2*mp+z2*mp*np;
                            
                            distance2[(i+j*m1+k*m1*n1)*4+l]=targetS[i+j*m1+k*m1*n1]*warped1S[movind]; //voxelwise inner-product
                            
                        }//end of if
                    }
                }
            }
        }
        
        boxfilter4((__m128*)datacost2,(__m128*)distance2,(__m128*)temp1,(__m128*)temp2,r,m1,n1,o1);
        
        for(int l=0;l<4;l++){
            for(int k=0;k<o1;k++){
                for(int j=0;j<n1;j++){
                    for(int i=0;i<m1;i++){
                        int l2=l4*4+l;
                        if(l2<len3){ //ensure no empty labels (for four-alignment) are used
                            int zs=l2/(len*len); int xs=(l2-zs*len*len)/len; int ys=l2-zs*len*len-xs*len;
                            int y2=ys+i; int x2=xs+j; int z2=zs+k;
                            int tarind=i+j*m1+k*m1*n1;
                            int movind=y2+x2*mp+z2*mp*np;
                            float covar=datacost2[tarind*4+l];
                            covar*=meanvar1[tarind]; //normalise by number of voxels
                            covar-=meanvar1[tarind+sz1]*meanvar2[movind+szp]; //minus product of means
                            float ncc=1.0f;
                            if(fabs(meanvar1[tarind+sz1*2])>0.0f&fabs(meanvar2[movind+szp*2])>0.0f)
                             ncc=1.0f-min(max((float)(covar)/(meanvar1[tarind+sz1*2]*meanvar2[movind+szp*2]),-1.0f),1.0f); //divide by product of variances
                            if(ncc!=ncc)
                                ncc=1.0f;
                            costvol[tarind+l2*sz1]=ncc;

                            //negate squared-ncc to form dissimilarity
                        }//end of if
                    }
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
    printf("original image size: %dx%dx%d, lowres: %dx%dx%d\n",m,n,o,m1,n1,o1);
    pthread_t thread1, thread2, thread3, thread4;
    gettimeofday(&time1, NULL);

    
    //downsample warped images to current resolution
    float* targetS=new float[sz1];
    float* warped1S=new float[sz1];
    downsample(targetS,target,sparse,1);
    downsample(warped1S,warped1,sparse,1);

    gettimeofday(&time2, NULL);
    
    
    //padding of moving image (symmetrically mirrored boundaries)
    int pad1=hw; int pad2=pad1*2;
    int mp=m1+pad2; int np=n1+pad2; int op=o1+pad2;
    int szp=mp*np*op;
    float* warped1p=new float[szp];
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
            }
        }
    }

    //prepare NCC calculations (pre-calculate means and variances)
    float* meanvar1=new float[sz1*3];
    float* meanvar2=new float[szp*3];
    prepNCC(meanvar1,targetS,r,m1,n1,o1);
    prepNCC(meanvar2,warped1p,r,mp,np,op);
    timeD=(time2.tv_sec+time2.tv_usec/1e6-(time1.tv_sec+time1.tv_usec/1e6));
    
    
    printf("Time for prepCC (lr) : %2.2f sec. \n",timeD);
    int len=hw*2+1; int len3=len*len*len;
    int len4=len3-len3%4+(((len3%4)==0)?0:4);
    printf("m1=%d n1=%d o1=%d. len3: %d, len4: %d, r: %d, sparse: %d\n",m,n,o,len3,len4,r,sparse);


    float* tempmem=new float[sz1*64];

    cout<<"starting multi-threading of costVolume filtering now!\n";

    int len44=len4/4;
    int lens[]={0,len44/4,len44/2,(3*len44)/4,len44};
    gettimeofday(&time1, NULL);
    struct cost_data cost1,cost2,cost3,cost4;
    cost1.targetS=targetS; cost1.warped1S=warped1p; cost1.meanvar1=meanvar1; cost1.meanvar2=meanvar2;
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


    delete targetS; delete warped1p;
    delete meanvar1; delete meanvar2;
    delete tempmem;

    float numd=(float)len4*(float)sz1;

    printf("TimeP : %2.2f sec. TimeD: %2.2f sec. \nSpeedP: %2.2f MPix/s. SpeedD: %2.2f MPix/s\n",timeP,timeD,numd/timeP/1e6,numd/timeD/1e6);


    

}
