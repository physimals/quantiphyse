/* constant time box-filters (with and without SSE) and downsampling function */
void boxfilter4(__m128* output,__m128* input,__m128* temp1,__m128* temp2,int hw,int m,int n,int o){
    const int RANGE=hw;
    const int sz=m*n*o;
    
    for(int k=0;k<o;k++){
        for(int j=0;j<n;j++){
            __m128 sumA={0.0f,0.0f,0.0f,0.0f};
            const __m128* inRow=input+j*m+k*m*n;
            __m128* outRow=temp2+j*m+k*m*n;
                        int x = -RANGE;
            for (; x<=RANGE; x++) {
                sumA += inRow[x+RANGE]; ;
                if (x >= 0) outRow[x] = sumA;
            }
            for (; x+RANGE<m; x++) {
                sumA -= inRow[x-RANGE-1];
                sumA += inRow[x+RANGE];
                outRow[x] = sumA;
            }
            for (; x < m; x++) {
                sumA -= inRow[x-RANGE-1];
                outRow[x] = sumA;
            }
        }
    }
    for(int k=0;k<o;k++){
        for(int i=0;i<m;i++){
            __m128 sumA={0.0f,0.0f,0.0f,0.0f};
            int x = -RANGE;
            for (; x<=RANGE; x++) {
                sumA += temp2[i+(x+RANGE)*m+k*m*n];
                if (x >= 0)
                    temp1[i+x*m+k*m*n]=sumA;
            }
            for (; x+RANGE<n; x++) {
                sumA -= temp2[i+(x-RANGE-1)*m+k*m*n];
                sumA += temp2[i+(x+RANGE)*m+k*m*n];
                temp1[i+x*m+k*m*n]= sumA;;
            }
            for (; x < n; x++) {
                sumA -= temp2[i+(x-RANGE-1)*m+k*m*n];
                temp1[i+x*m+k*m*n] = sumA;
            }
            
        }
    }

    for(int j=0;j<n;j++){
        for(int i=0;i<m;i++){
            __m128 sumA={0.0f,0.0f,0.0f,0.0f};
            int x = -RANGE;
            for (; x<=RANGE; x++) {
                sumA += temp1[i+j*m+(x+RANGE)*m*n];
                if (x >= 0)
                    output[i+j*m+x*m*n]=sumA;
            }
            for (; x+RANGE<o; x++) {
                sumA -= temp1[i+j*m+(x-RANGE-1)*m*n];
                sumA += temp1[i+j*m+(x+RANGE)*m*n];
                output[i+j*m+x*m*n]= sumA;
            }
            for (; x < o; x++) {
                sumA -= temp1[i+j*m+(x-RANGE-1)*m*n];
                output[i+j*m+x*m*n] = sumA;
            }
        }
    }
}


void boxfilter1CC(float* output,float* input,float* temp1,float* temp2,int hw,int m,int n,int o){
    const int RANGE=hw;
    const int sz=m*n*o;
    
    for(int k=0;k<o;k++){
        for(int j=0;j<n;j++){
            float sumA=0;
            const float* inRow=input+j*m+k*m*n;
            float* outRow=temp2+j*m+k*m*n;
            int x = -RANGE;
            for (; x<=RANGE; x++) {
                sumA += inRow[x+RANGE]; ;
                if (x >= 0) outRow[x] = sumA;
            }
            for (; x+RANGE<m; x++) {
                sumA -= inRow[x-RANGE-1];
                sumA += inRow[x+RANGE];
                outRow[x] = sumA;
            }
            for (; x < m; x++) {
                sumA -= inRow[x-RANGE-1];
                outRow[x] = sumA;
            }
        }
    }
    
    for(int k=0;k<o;k++){
        for(int i=0;i<m;i++){
            float sumA=0;
            
            int x = -RANGE;
            for (; x<=RANGE; x++) {
                sumA += temp2[i+(x+RANGE)*m+k*m*n];
                if (x >= 0)
                    temp1[i+x*m+k*m*n]=sumA;
            }
            for (; x+RANGE<n; x++) {
                sumA -= temp2[i+(x-RANGE-1)*m+k*m*n];
                sumA += temp2[i+(x+RANGE)*m+k*m*n];
                temp1[i+x*m+k*m*n]= sumA;
            }
            for (; x < n; x++) {
                sumA -= temp2[i+(x-RANGE-1)*m+k*m*n];
                temp1[i+x*m+k*m*n] = sumA;
            }
        }
    }
    
    for(int j=0;j<n;j++){
        for(int i=0;i<m;i++){
            float sumA=0;
            
            int x = -RANGE;
            for (; x<=RANGE; x++) {
                sumA += temp1[i+j*m+(x+RANGE)*m*n];
                if (x >= 0)
                    output[i+j*m+x*m*n]=sumA;
            }
            for (; x+RANGE<o; x++) {
                sumA -= temp1[i+j*m+(x-RANGE-1)*m*n];
                sumA += temp1[i+j*m+(x+RANGE)*m*n];
                output[i+j*m+x*m*n]= sumA;
            }
            for (; x < o; x++) {
                sumA -= temp1[i+j*m+(x-RANGE-1)*m*n];
                output[i+j*m+x*m*n] = sumA;
            }
            
        }
    }
}



void boxfilter(float* input,float* temp1,float* temp2,int hw,int m,int n,int o){
    
	int sz=m*n*o;
	for(int i=0;i<sz;i++){
		temp1[i]=input[i];
	}
	
	for(int k=0;k<o;k++){
		for(int j=0;j<n;j++){
			for(int i=1;i<m;i++){
				temp1[i+j*m+k*m*n]+=temp1[(i-1)+j*m+k*m*n];
			}
		}
	}
	
	for(int k=0;k<o;k++){
		for(int j=0;j<n;j++){
			for(int i=0;i<(hw+1);i++){
				temp2[i+j*m+k*m*n]=temp1[(i+hw)+j*m+k*m*n];
			}
			for(int i=(hw+1);i<(m-hw);i++){
				temp2[i+j*m+k*m*n]=temp1[(i+hw)+j*m+k*m*n]-temp1[(i-hw-1)+j*m+k*m*n];
			}
			for(int i=(m-hw);i<m;i++){
				temp2[i+j*m+k*m*n]=temp1[(m-1)+j*m+k*m*n]-temp1[(i-hw-1)+j*m+k*m*n];
			}
		}
	}
	
	for(int k=0;k<o;k++){
		for(int j=1;j<n;j++){
			for(int i=0;i<m;i++){
				temp2[i+j*m+k*m*n]+=temp2[i+(j-1)*m+k*m*n];
			}
		}
	}
	
	for(int k=0;k<o;k++){
		for(int i=0;i<m;i++){
			for(int j=0;j<(hw+1);j++){
				temp1[i+j*m+k*m*n]=temp2[i+(j+hw)*m+k*m*n];
			}
			for(int j=(hw+1);j<(n-hw);j++){
				temp1[i+j*m+k*m*n]=temp2[i+(j+hw)*m+k*m*n]-temp2[i+(j-hw-1)*m+k*m*n];
			}
			for(int j=(n-hw);j<n;j++){
				temp1[i+j*m+k*m*n]=temp2[i+(n-1)*m+k*m*n]-temp2[i+(j-hw-1)*m+k*m*n];
			}
		}
	}
	
	for(int k=1;k<o;k++){
		for(int j=0;j<n;j++){
			for(int i=0;i<m;i++){
				temp1[i+j*m+k*m*n]+=temp1[i+j*m+(k-1)*m*n];
			}
		}
	}
	
	for(int j=0;j<n;j++){
		for(int i=0;i<m;i++){
			for(int k=0;k<(hw+1);k++){
				input[i+j*m+k*m*n]=temp1[i+j*m+(k+hw)*m*n];
			}
			for(int k=(hw+1);k<(o-hw);k++){
				input[i+j*m+k*m*n]=temp1[i+j*m+(k+hw)*m*n]-temp1[i+j*m+(k-hw-1)*m*n];
			}
			for(int k=(o-hw);k<o;k++){
				input[i+j*m+k*m*n]=temp1[i+j*m+(o-1)*m*n]-temp1[i+j*m+(k-hw-1)*m*n];
			}
		}
	}
	
	
}



void downsample(float* im1f,float* im,int step1,int d)
{
	int m=image_m;
	int n=image_n;
	int o=image_o;
	int sz=m*n*o;
	
	int step3=pow(step1,3);
	int m1=m/step1;
	int n1=n/step1;
	int o1=o/step1;
	int sz1=m1*n1*o1;
    
	float alpha2=1.0/(float)step3;
	int xx2,yy2,zz2;
    float* cost1=new float[d];
	for(int i=0;i<sz1;i++){
        
		int z1=i/(m1*n1);
		int x1=(i-z1*m1*n1)/m1;
		int y1=i-z1*m1*n1-x1*m1;
		
		z1*=step1;
		x1*=step1;
		y1*=step1;
		
        for(int d1=0;d1<d;d1++){
            cost1[d1]=0.0;
        }
		
		for(int j1=0;j1<step3;j1++){
			int i1=j1;
			int zz=i1/(step1*step1);
			int xx=(i1-zz*step1*step1)/step1;
			int yy=i1-zz*step1*step1-xx*step1;
			
			xx+=x1;
			yy+=y1;
			zz+=z1;
            for(int d1=0;d1<d;d1++){
                cost1[d1]+=im[yy+xx*m+zz*m*n+d1*sz];
            }
            
			
		}
        for(int d1=0;d1<d;d1++){
            cost1[d1]*=alpha2;
            im1f[i+d1*sz1]=cost1[d1];
        }
		
	}
    delete cost1;
	
}



