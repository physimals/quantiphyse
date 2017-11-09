/*File-input-output and very basic nifti-reader writer functions */
void writeOutput(float* data,char* name,int length){
	
	ofstream ofs1(name,ofstream::binary);
	ofs1.write((char *) data,length*sizeof(float));
	ofs1.close();
	
	
	
}

void writeOutputI(int* data,char* name,int length){
	
	ofstream ofs1(name,ofstream::binary);
	ofs1.write((char *) data,length*sizeof(int));
	ofs1.close();
	
	
	
}

void writeOutputS(short* data,char* name,int length){
	
	ofstream ofs1(name,ofstream::binary);
	ofs1.write((char *) data,length*sizeof(short));
	ofs1.close();
	
	
	
}


void writeNifti(char filename1[],float* pixels,char* header,int sizep)
{
	int sizeh=352;
	header[70]=16;
	header[72]=32;
    
	ofstream file1 (filename1);
	if(file1.is_open()){
		file1.write(header,sizeh);
		file1.write(reinterpret_cast<char*>(pixels),sizep*sizeof(float) );
		file1.close();
		cout<<"File "<<filename1<<" written.\n";
	}
	
}

void writeNiftiShort(char filename1[],short* pixels,char* header,int sizep)
{
	int sizeh=352;
	short* data=new short[sizep];
	for(int i=0;i<sizep;i++)
		data[i]=pixels[i];
	
	header[70]=4;
	header[72]=16;	
	ofstream file1 (filename1);
	if(file1.is_open()){
		file1.write(header,sizeh);
		file1.write(reinterpret_cast<char*>(data),sizep*sizeof(short) );
		file1.close();
		cout<<"File "<<filename1<<" written.\n";

	}
	
}

void readFloat(char str2[], float*& pixels,int SZ){
	FILE * pFile;
	int i,j,offset;
	size_t result;
	
	pFile = fopen (str2, "rb" );
	if (pFile==NULL) {fputs ("File error",stderr); exit (1);}
	
	fseek(pFile,0,0);
	
	float* memory=new float[SZ];
	size_t lSize;
	float * buffer;
	lSize=SZ;
	buffer = (float*) malloc (sizeof(float)*lSize);
	if (buffer == NULL) {fputs ("Memory error",stderr); exit (2);}
	
	// copy the file into the buffer:
	result = fread (buffer,sizeof(float),lSize,pFile);
	if (result != lSize) {fputs ("Reading error",stderr); exit (3);}
	
	for(i=0;i<(SZ);i++)
		pixels[i]=buffer[i];
	free (buffer);
	fclose (pFile);
}

void readNifti(char str2[], float*& pixels,int& M,int& N,int &O,int &K,char*& header)
{
	
	FILE * pFile;
	int i,j,offset;
	size_t result;
	
	pFile = fopen (str2, "rb" );
	if (pFile==NULL) {fputs ("File error",stderr); exit (1);}
	
	unsigned int X=0;
	fseek(pFile,0,0);
	fread(&X,4,1,pFile);
	//cout<<"Magic number "<<X<<"\n";
	int dims[5];
	short dim;
	for (i=0;i<5;i++){
		fseek(pFile,40+i*2,0);
		fread(&dim,2,1,pFile);
		dims[i]=dim;
	}
	M=(int)dims[1];
	N=(int)dims[2];
	O=(int)dims[3];
    K=(int)dims[4];
	unsigned int datatype=0;
	fseek(pFile,70,0);
	fread(&datatype,2,1,pFile);
	
	float pixdims[8];
	fseek(pFile,76,0);
	fread(&pixdims,8*4,1,pFile);
	
	float voxoffset=0;
	fseek(pFile,108,0);
	fread(&voxoffset,4,1,pFile);
	offset=(int)voxoffset;
	cout<<"Dimensions are: "<<M<<"x"<<N<<"x"<<O<<"x"<<K<<" Datatype is "<<datatype<<"\n";

    float srow[16];
	fseek(pFile,280,0);
	fread(&srow,16*4,1,pFile);
    float srow_x=srow[0];
    float srow_y=srow[5];
    float srow_z=srow[10];
    
	//cout<<"Length of float "<<sizeof(float)<<"\n";
	pixels=new float [M*N*O*K];
	
	if(datatype==64){
		double* memory=new double[M*N*O*K];
		fseek(pFile,offset,0);
		long lSize;
		double * buffer;
		lSize=M*N*O*K;
		long result;
		buffer = (double*) malloc (sizeof(double)*lSize);
		if (buffer == NULL) {fputs ("Memory error",stderr); exit (2);}
		
		// copy the file into the buffer:
		result = fread (buffer,sizeof(double),lSize,pFile);
		if (result != lSize) {fputs ("Reading error",stderr); exit (3);}
		
		for(i=0;i<(M*N*O*K);i++)
			pixels[i]=buffer[i];
		free (buffer);

	}
	else{
		
		if(datatype==4){
			short* memory=new short[M*N*O*K];
			fseek(pFile,offset,0);
			long lSize;
			short * buffer;
			lSize=M*N*O*K;
			long result;
			buffer = (short*) malloc (sizeof(short)*lSize);
			if (buffer == NULL) {fputs ("Memory error",stderr); exit (2);}
			
			// copy the file into the buffer:
			result = fread (buffer,sizeof(short),lSize,pFile);
			if (result != lSize) {fputs ("Reading error",stderr); exit (3);}
			
			for(i=0;i<(M*N*O*K);i++)
				pixels[i]=buffer[i];
			free (buffer);

		}
		else{
			if(datatype==16){
				float* memory=new float[M*N*O*K];
				fseek(pFile,offset,0);
				long lSize;
				float * buffer;
				lSize=M*N*O*K;
				long result;
				buffer = (float*) malloc (sizeof(float)*lSize);
				if (buffer == NULL) {fputs ("Memory error",stderr); exit (2);}
				
				// copy the file into the buffer:
				result = fread (buffer,sizeof(float),lSize,pFile);
				if (result != lSize) {fputs ("Reading error",stderr); exit (3);}
				
				for(i=0;i<(M*N*O*K);i++)
					pixels[i]=buffer[i];
				free (buffer);
				
			}
			else{
			cout<<"ERROR: datatype is not supported.\n";
		}
		}
	}
	fclose (pFile);
	
	int size=offset;
	header=new char[size];
	ifstream file(str2,ios::in|ios::binary|ios::ate);
	if (file.is_open())
	{
		//read header as one block, separately
		header = new char [size];
		file.seekg (0, ios::beg);
		file.read (header, size);
		file.close();
	}
    

}



void readNiftiShort(char str2[], short*& pixels,int& M,int& N,int &O,char*& header)
{
	
	FILE * pFile;
	int i,j,offset;
	size_t result;
	
	pFile = fopen (str2, "rb" );
	if (pFile==NULL) {fputs ("File error",stderr); exit (1);}
	
	unsigned int X=0;
	fseek(pFile,0,0);
	fread(&X,4,1,pFile);
	//cout<<"Magic number "<<X<<"\n";
	int dims[4];
	short dim;
	for (i=0;i<4;i++){
		fseek(pFile,40+i*2,0);
		fread(&dim,2,1,pFile);
		dims[i]=dim;
	}
	M=(int)dims[1];
	N=(int)dims[2];
	O=(int)dims[3];
	unsigned int datatype=0;
	fseek(pFile,70,0);
	fread(&datatype,2,1,pFile);
	
	float pixdims[8];
	fseek(pFile,76,0);
	fread(&pixdims,8*4,1,pFile);
	
	float voxoffset=0;
	fseek(pFile,108,0);
	fread(&voxoffset,4,1,pFile);
	offset=(int)voxoffset;
	cout<<"Dimensions are: "<<M<<"x"<<N<<"x"<<O<<" Datatype is "<<datatype<<" (short)\n";
    
	//cout<<"Length of float "<<sizeof(float)<<"\n";
	pixels=new short [M*N*O];
	
    if(datatype==4||datatype==512){
        short* memory=new short[M*N*O];
        fseek(pFile,offset,0);
        long lSize;
        short * buffer;
        lSize=M*N*O;
        long result;
        buffer = (short*) malloc (sizeof(short)*lSize);
        if (buffer == NULL) {fputs ("Memory error",stderr); exit (2);}
        
        // copy the file into the buffer:
        result = fread (buffer,sizeof(short),lSize,pFile);
        if (result != lSize) {fputs ("Reading error",stderr); exit (3);}
        
        for(i=0;i<(M*N*O);i++)
            pixels[i]=buffer[i];
        free (buffer);
        
    }
    
    else{
        cout<<"ERROR: datatype is not supported.\n";
    }
    
	fclose (pFile);
	
	int size=offset;
	header=new char[size];
	ifstream file(str2,ios::in|ios::binary|ios::ate);
	if (file.is_open())
	{
		//read header as one block, separately
		header = new char [size];
		file.seekg (0, ios::beg);
		file.read (header, size);
		file.close();
	}
	
    
    
}
