/*

Main class and interface for running the Pk modelling


Author: Benjamin Irving (benjamin.irv@gmail.com)
Copyright (c) 2013-2015 University of Oxford, Benjamin Irving

*/

#include "pkrun2.h"

#include <sstream>

using namespace pkmodellingspace;
using namespace std;

// Initialising an empty OTofts object in the constructor
Pkrun2::Pkrun2(std::vector<double> & tt1, std::vector< std::vector<double> > & yy1, std::vector<double> & T101in)
    : t1(tt1) , y1(yy1), T101(T101in), OTofts()
{
    // counting the current point
    pcur = 0;

    // Get dimensions
    n_par = 4; // number of parameters in model function f
    m_t1 = (int)t1.size(); // number of data pairs
    mrows = (int)y1.size();
    ncols = (int)y1[0].size();
    n_t101 = (int)T101.size();
    
    // Assign memory to variable arrays and populate temporal array for a single instance
    t = new double [m_t1];
    y = new double [m_t1];

    for (ii=0; ii<m_t1; ii++)

        {
            t[ii]=t1.at(ii);
        }

    //~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~Output arrays ~~~~~~~~~~~~~~~~~~~~~~~~~~~~

    // Initilising output vectors by setting all values to -1
    outdata.resize(mrows, vector<double>(n_par, -1));
    outdata2.resize(mrows, vector<double>(m_t1, -1));
    outdata3.resize(mrows, -1);

    //~~~~~~~~~~~~~~~~~~~~~~~~~~~~~ Checking inputs ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

    if (mrows != n_t101)
    {
        cout << " m_t1: " << m_t1 << " n_t101: " << n_t101 << endl;
        cout << " mrows: " << mrows << " ncols: " << ncols << endl;
        cout << "Wrong dimensions for T101  \n";
    }

    if (ncols != m_t1)
    {
        cout << " m_t1: " << m_t1 << " n_t101: " << n_t101 << endl;
        cout << " mrows: " << mrows << " ncols: " << ncols << endl;
        cout << "Wrong dimensions for y1 \n";
    }

}

Pkrun2::~Pkrun2()
{

    //~~~~~~~~  delete created variables ~~~~~~~~~~~~~~
    delete [] t;
    delete [] y;

}

void Pkrun2::set_bounds(vector<double> & ub1, vector<double> & lb1)
{
    // Sets the maximum number of parameters that we can use
    ub[0]= ub1.at(0); ub[1]=ub1.at(1); ub[2]=ub1.at(2); ub[3]=ub1.at(3);
    lb[0]= lb1.at(0); lb[1]=lb1.at(1); lb[2]=lb1.at(2); lb[3]=lb1.at(3);
}


void Pkrun2::set_parameters(double R1in, double R2in, double dce_flip_anglein, double dce_TRin, double dce_TEin, double Dosein)
{

    R1=R1in;
    R2 =R2in;
    dce_flip_angle = dce_flip_anglein;
    dce_TR = dce_TRin;
    dce_TE= dce_TEin;
    Dose = Dosein;

}

// Calculate the contrast to noise ratio of the data
void Pkrun2::calculate_CNR()
{
// TODO : calculate the CNR and return it as a volume
}

string Pkrun2::rinit(int model1, double injtmins)
{
    //~~~~~~~~~~~~~~~~~~~~~~~~~~~Pass all the data to the optimizer object ~~~~~~~~~~~~~~~~~~~~~~~~~~
    // Set the AIF and model type
    string log;

    if (model1 ==1)
    {
        // AIF[0] = aB (2.84 mM) in Orton 2008?
        // AIF[1] = aG (1.36 /min) in Orton 2008?
        // AIF[2] = muB in Orton 2008 (22.8 / min)
        // AIF[3] = muG in Orton 2008 (0.171 / min)
        log = "Orton with offset (Clinical) \n";
        AIF[0]=2.65; AIF[1]=1.51; AIF[2]=22.40; AIF[3]=0.23; AIF[4]=injtmins;
    }
    else if (model1 ==2)
    {
        log = "Orton without offset (Clinical) \n";
        AIF[0]=2.65; AIF[1]=1.51; AIF[2]=22.40; AIF[3]=0.23; AIF[4]=injtmins;
    }
    else if (model1 ==3)
    {
        log = "Weinmann with offset (Pre-clinical) \n";
        AIF[0]=9.2; AIF[1]=4.2; AIF[2]=2.3; AIF[3]=0.05; AIF[4]=injtmins;
    }
    else if (model1 ==4)
    {
        log = "Weinmann with offset and vp (Pre-clinical) \n";
        AIF[0]=9.2; AIF[1]=4.2; AIF[2]=2.3; AIF[3]=0.05; AIF[4]=injtmins;
    }

    OTofts.set_data(n_par, R1, R2, dce_TR, dce_TE, dce_flip_angle, AIF, m_t1, Dose);

    // Choosing model
    OTofts.SetModel(model1);

    return log;
}

string Pkrun2::run(int pause1)
{
    stringstream log;

    //~~~~~~~~~~~~~~~~~~~~~~~~~~~~ Looping through voxels ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    for (pp=pcur; pp<mrows; pp++)
    {
        // Using T10 of interest
        T10=T101.at(pp);

        // Using y values of interest
        for (ii=0; ii<m_t1; ii++)
        {
            y[ii]=y1.at(pp).at(ii);
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
            outdata.at(pp).at(ii)=floor(OTofts.par[ii]*10000 + 0.5)/10000;
            //cout << "Parameters: " << OTofts.par[ii] << endl;
        }

        // 2: Fitted curve
        for (ii=0; ii< m_t1; ii++)
            outdata2.at(pp).at(ii)=OTofts.SEfit[ii];
        // 3: Residual
        outdata3.at(pp)=OTofts.residual;

        //Print number and position
        if ((pp % pause1 == 0) && (pp>0))
        {
            log << "Pixel num " << pp << "/" << mrows << endl;
            pcur = pp+1;
            return log.str();
        }
    }

    return log.str();
}

// Returns the Pk parameters for each voxel (Ktrans, ve, offset, vp)
const vector<vector<double> > Pkrun2::get_parameters()
{
    return outdata;
}

// Returns the fitted curve for each voxel
vector<vector<double> > Pkrun2::get_fitted_curve()
{
    return outdata2;
}

// Returns the residual for each voxel
const vector<double> Pkrun2::get_residual()
{
    return outdata3;
}
