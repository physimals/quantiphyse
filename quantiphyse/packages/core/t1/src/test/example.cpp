#include <iostream>
#include <tuple>

#include "T10/linear_regression.h"
#include "io_nifti.h"
#include "T10/T10_calculation.h"
#include "T10/plotting.h"
#include <opencv2/opencv.hpp>

using namespace std;

int main() {

    vector<double> fa3, fa9, fa12, fa15, fa6, fa24, fa35;
    int ndim;
    vector<int> dims;
    vector<double> t10vol;

//    string data_folder = "/home/ENG/engs1170/Code/25_T10_calculation/test_data/QIBA_v12_Tofts_beta1/QIBA_v12_Tofts_GE/6s_jit_3s_T1_200_S0_500_sigma_5/DICOM_T1/";
    string data_folder = "/home/ENG/engs1170/Code/25_T10_calculation/test_data/QIBA_v12_Tofts_beta1/QIBA_v12_Tofts_GE/6s_jit_3s_T1_500_S0_500_sigma_5/DICOM_T1/";
//    string data_folder = "/home/ENG/engs1170/Code/25_T10_calculation/test_data/QIBA_v12_Tofts_beta1/QIBA_v12_Tofts_GE/6s_jit_3s_T1_2000_S0_500_sigma_5/DICOM_T1/";

    string v1 = "fa3.nii";
    string v2 = "fa6.nii";
    string v3 = "fa9.nii";
    string v4 = "fa15.nii";
    string v5 = "fa24.nii";
    string v6 = "fa35.nii";
    vector<double> fa = {3, 6, 9, 15, 24, 35};
    double TR = 0.005;

    tie(fa3, ndim, dims) = load_nifti_1D_vector(data_folder + v1, 0);
    tie(fa6, ndim, dims) = load_nifti_1D_vector(data_folder + v2, 0);
    tie(fa9, ndim, dims) = load_nifti_1D_vector(data_folder + v3, 0);
    tie(fa15, ndim, dims) = load_nifti_1D_vector(data_folder + v4);
    tie(fa24, ndim, dims) = load_nifti_1D_vector(data_folder + v5);
    tie(fa35, ndim, dims) = load_nifti_1D_vector(data_folder + v6);

    // Create a vector of flip angle vectors
    vector< vector<double> > fa_vols =  {fa3, fa6, fa9, fa15, fa24, fa35};

    // Perform T10 mapping
    // vector<double> T10mapping( vector< vector<double> > & favols, vector<double> & fa);
    t10vol = T10mapping(fa_vols, fa, TR);

    string out_path = data_folder + "T10.nii";
    save_nifti_1D_vector(out_path, t10vol, data_folder+v1);

    int slice1 = 0;
    plotting::plot_slice(fa3.data(), dims[0], dims[1], dims[2], slice1, "FA3");
    plotting::plot_slice(t10vol.data(), dims[0], dims[1], dims[2], slice1, "T10");

    // mean value:
    double sum1 = accumulate(t10vol.begin(), t10vol.end(), 0.0);
    double mean1 = sum1 / t10vol.size();
    cout << "mean " << mean1 << endl;


    // mean value vessel:
    double sum3 = 0.0;
    int count3 = 0;
    for (int ii=0; ii < (50*10); ii++){
        if (t10vol.at(ii) > 0) {
            sum3 += t10vol.at(ii);
            count3 += 1;
        }
    }
    double mean3 = sum3/count3;
    cout << "mean3 " << mean3 << endl;

    // mean value tissue:
    double sum4 = 0.0;
    int count4 = 0;
    for (int ii=(50*10); ii < (50*80); ii++){
        if ((t10vol.at(ii) > 0) & (t10vol.at(ii) < 10)) {
//            cout << t10vol.at(ii) << " ";
            sum4 += t10vol.at(ii);
            count4 += 1;
        }
    }
    double mean4 = sum4/count4;
    cout << "mean4 " << mean4 << endl;

    cv::waitKey(0);
    return 0;
}

