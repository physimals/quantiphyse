struct min_data{
    float* costvol; float* flow0;
    int* minind; float* minval;
    float theta;
    int hw; int m; int n; int o; int lstart; int lend;
};


void *costSmoothTh(void *threadarg)
{
    struct min_data *my_data;
    my_data = (struct min_data *) threadarg;
    float* costvol = my_data->costvol;
    float* flow0=my_data->flow0;
    int* minind = my_data->minind;
    float* minval = my_data->minval;

    int m=my_data->m;
    int n=my_data->n;
    int o=my_data->o;
    int hw = my_data->hw;
    float theta = my_data->theta;
    int lstart=my_data->lstart; int lend=my_data->lend;

    int sz=m*n*o;
    int len=hw*2+1; int len3=len*len*len;


    for(int l=0;l<len3;l++){
        int zs=l/(len*len);
        int xs=(l-zs*len*len)/len;
        int ys=l-zs*len*len-xs*len;
        zs-=hw; ys-=hw; xs-=hw;
        for(int i=lstart;i<lend;i++){
            //add coupling term to similarity map and find new argmin
            float cost=costvol[i+l*sz]+theta*((flow0[i]-(float)xs)*(flow0[i]-(float)xs)+(flow0[i+sz]-(float)ys)*(flow0[i+sz]-(float)ys)+(flow0[i+2*sz]-(float)zs)*(flow0[i+2*sz]-(float)zs));
            if(cost<minval[i]){
                minind[i]=l;
                minval[i]=cost;
            }
        }


    }
    return NULL;
}

//multi-threading of costSmoothTh
void steinbruecker(int* result,float* costvol,float* flow0,int hw,float theta,int m,int n,int o){

    int len=hw*2+1; int len3=len*len*len;

    int sz=m*n*o;
    float* minval=new float[sz];
    for(int i=0;i<sz;i++){
        minval[i]=1e20;
    }

    struct min_data min1,min2,min3,min4;

    int lens[]={0,sz/4,sz/2,(3*sz)/4,sz};
    min1.costvol=costvol; min1.minind=result; min1.flow0=flow0; min1.hw=hw;
    min1.theta=theta; min1.minval=minval;
    min1.m=m; min1.n=n; min1.o=o;
    min1.lstart=lens[0]; min1.lend=lens[1];
    min2=min1;
    min2.lstart=lens[1]; min2.lend=lens[2];
    min3=min1;
    min3.lstart=lens[2]; min3.lend=lens[3];
    min4=min1;
    min4.lstart=lens[3]; min4.lend=lens[4];


    pthread_t thread1, thread2, thread3, thread4;

   pthread_create(&thread1,NULL,costSmoothTh,(void *)&min1);
    pthread_create(&thread2,NULL,costSmoothTh,(void *)&min2);
    pthread_create(&thread3,NULL,costSmoothTh,(void *)&min3);
   pthread_create(&thread4,NULL,costSmoothTh,(void *)&min4);
    pthread_join(thread1,NULL);
    pthread_join(thread2,NULL);
   pthread_join(thread3,NULL);
    pthread_join(thread4,NULL);



}
