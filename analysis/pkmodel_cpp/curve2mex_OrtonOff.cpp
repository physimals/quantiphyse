/*
Inputs:
t1 m dim time array
y1 mxn dim array of SE curves for the regions
pars [R1 R2 dce_flip_angle dce_TR dce_TE]
AIF1 5 dim array of AIF
T101 n dim array of T10 values
 
Storing return values
1: fitted parameters
2: fitted curve
3: Residual

*/

// Numerical recipes header file that makes it easier to create mex files
#include "nr3matlab.h" 
// Class used to optimise the stuff
#include "Optimizer_class.h"

void mexFunction(int nlhs, mxArray *plhs[], int nrhs, const mxArray *prhs[]) 
{
    // counters
    int ii, pp, qq, ss;

    // ~~~~~~~~~~~~~~~~~~~~~~~~~ Get matlab arrays~~~~~~~~~~~~~~~~~~~~~~~~~~
    // Use NR3 objects as wrappers
    const VecDoub t1(prhs[0]);
    const MatDoub y1(prhs[1]);
    const VecDoub pars(prhs[2]);
    const VecDoub AIF1(prhs[3]);
    const VecDoub T101(prhs[4]);

    // Get dimensions
    int m_t1 = t1.size(); // number of data pairs
    int mrows=y1.nrows();
    int ncols=y1.ncols();
    int n_t101= T101.size();

    //~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~ Number of parameters to fit ~~~~~~~~~~~~~~~

    // Sets the maximum number of parameters that we can use
    int n_par = 4; // number of parameters in model function f
    double pars3[4];
    double ub[4]={10, 1, 0.5, 0.5};
    double lb[4]={0, 0.05, -0.5, 0};

    /*
    Parameters used in the other versions.
    Note that the chosen model must also be changed
	Wein / WeinOff
	double ub[4]={10, 1, 10, 0.5};
    double lb[4]={0, 0.05, 0, 0};

	WeinOffVp
    double ub[4]={10, 1, 10, 0.4};
    double lb[4]={0, 0.05, 0, 0};
	*/

    //~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~Output arrays ~~~~~~~~~~~~~~~~~~~~~~~~~~~~

    MatDoub outdata(n_par, ncols, plhs[0]);
    MatDoub outdata2(m_t1, ncols, plhs[1]);
    VecDoub outdata3(ncols, plhs[2]);

    //~~~~~~~~~~~~~~~~~~~~~~~~~~~~~ Checking inputs ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

    if (ncols != n_t101) 
    {
        cout << " m_t1: " << m_t1 << " n_t101: " << n_t101 << endl;
        cout << " mrows: " << mrows << " ncols: " << ncols << endl;
        mexErrMsgTxt("Wrong dimensions for T101");
    }

    if (mrows != m_t1) 
    {
        cout << " m_t1: " << m_t1 << " n_t101: " << n_t101 << endl;
        cout << " mrows: " << mrows << " ncols: " << ncols << endl;
        mexErrMsgTxt("Wrong dimensions for y1");
    }

    if (pars.size() != 6 || AIF1.size() !=5) 
    {
        mexErrMsgTxt("Inputs have incorrect length");
    }


    //~~~~~~~~~~~~~~~~~~~~~~~~ Convert standard arrays ~~~~~~~~~~~~~~~~~~
    double AIF[5];
    for (ii=0; ii<5; ii++)
        AIF[ii]=AIF1[ii];

    double R1=pars[0];
    double R2 =pars[1];
    double dce_flip_angle = pars[2];
    double dce_TR = pars[3];
    double dce_TE= pars[4];
    double Dose = pars[5];


    // Assign memory to variable arrays and populate temporal array;
    double *t, *y;
    t = new double [m_t1];
    y = new double [m_t1];
    for (ii=0; ii<m_t1; ii++)
        {
            t[ii]=t1[ii];
        }

    double T10;
    double res_min, res_count;


    //~~~~~~~~~~~~~~~~~~~~~~~~~~~Initialise optimiser object~~~~~~~~~~~~~~~~~~~~~~~~~~

    OptimizeFunction OTofts(n_par, R1, R2, dce_TR, dce_TE, dce_flip_angle, AIF, m_t1, Dose);
    
    // Choosing model
    OTofts.SetModel(1);
	

	/*
	1) Orton with Offset
	2) Weinmann with offset
	3) Orton without Offset
    4) Weinmann with offset and vp
	*/

    //~~~~~~~~~~~~~~~~~~~~~~~~~~~~ Looping through voxels ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    for (pp=0; pp<ncols; pp++)
    {
        //Print number
        if (pp % 1000 == 0) 
            cout << "Pixel num " << pp << "/" << ncols << endl;

        // Using T10 of interest
        T10=T101[pp];

        // Using y values of interest
        for (ii=0; ii<m_t1; ii++)
        {
            y[ii]=y1[ii][pp];
        }


        // ~~~~~~~~~~ Run optimiser 3 times and choose optimal one ~~~~~~~~~~~~~~~~~~~~~~

        res_min=0;
        for (qq=0; qq<3; qq++)
        {
            OTofts.RandomInitialisation();
            OTofts.SetVoxelParameters(t, y, T10);
            //OTofts.Optimize();
            OTofts.OptimizeConstrain(ub, lb);

            OTofts.GenCurve();

            //Finding run with lowest error
            if ( (OTofts.residual < res_min) || (qq==0) )
            {
                res_min=OTofts.residual;

                //Storing current minimum
                for (ss=0; ss<n_par; ss++)
                {
                    pars3[ss]=OTofts.par[ss];
                }
                
            }

        }
        OTofts.SetPars(pars3);
        OTofts.GenCurve();

        // Storing return values
        // 1: fitted parameters

        for (ii=0; ii< n_par; ii++)
        {
            outdata[ii][pp]=floor(OTofts.par[ii]*10000 + 0.5)/10000;
            //cout << "Parameters: " << OTofts.par[ii] << endl;
        }
            
        // 2: Fitted curve
        for (ii=0; ii< m_t1; ii++)
            outdata2[ii][pp]=OTofts.SEfit[ii];
        // 3: Residual
        outdata3[pp]=OTofts.residual;
    }


    //~~~~~~~~  delete created variables ~~~~~~~~~~~~~~
    delete [] t;
    delete [] y;
}
