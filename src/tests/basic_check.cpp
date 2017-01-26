//
// Created by engs1170 on 07/01/16.
//

#include <algorithm>
#include <vector>
#include <tuple>
#include <opencv2/opencv.hpp>

#include "gtest/gtest.h"

#include "linear_regression.h"
#include "io_nifti.h"
#include "T10_calculation.h"

using namespace std;

tuple<double, double> T10calc(string data_folder){

    vector<double> fa3, fa9, fa12, fa15, fa6, fa24, fa35;
    int ndim;
    vector<int> dims;
    vector<double> t10vol;

    string v1 = "fa3.nii";
    string v2 = "fa6.nii";
    string v3 = "fa9.nii";
    string v4 = "fa15.nii";
    string v5 = "fa24.nii";
    string v6 = "fa35.nii";
    vector<double> fa = {3, 6, 9, 15, 24, 35};
    double TR = 0.005;
    tie(fa3, ndim, dims) = load_nifti_1D_vector(data_folder + v1);
    tie(fa6, ndim, dims) = load_nifti_1D_vector(data_folder + v2);
    tie(fa9, ndim, dims) = load_nifti_1D_vector(data_folder + v3);
    tie(fa15, ndim, dims) = load_nifti_1D_vector(data_folder + v4);
    tie(fa24, ndim, dims) = load_nifti_1D_vector(data_folder + v5);
    tie(fa35, ndim, dims) = load_nifti_1D_vector(data_folder + v6);
    vector< vector<double> > fa_vols =  {fa3, fa6, fa9, fa15, fa24, fa35};
    t10vol = T10mapping(fa_vols, fa, TR);

    // mean vessel:
    double sum3 = 0.0;
    int count3 = 0;
    for (int ii=0; ii < (50*10); ii++){
        if (t10vol.at(ii) > 0) {
            sum3 += t10vol.at(ii);
            count3 += 1;
        }
    }
    double mean_vessel = sum3/count3;
//    cout << "mean3 " << mean_vessel << endl;

    // mean tissue:
    double sum4 = 0.0;
    int count4 = 0;
    for (int ii=(50*10); ii < (50*80); ii++){
        if ((t10vol.at(ii) > 0) & (t10vol.at(ii) < 10)) {
            sum4 += t10vol.at(ii);
            count4 += 1;
        }
    }

    double mean_tissue = sum4/count4;
//    cout << "mean4 " << mean_tissue << endl;

    return make_tuple(mean_vessel, mean_tissue);
}

// Test regression on integer solutions
TEST(regression_test, regression_gradient_intercep_int) {

    double a, b;
    vector<double> x = {1.5, 2.5, 3.5, 4.5, 5.5};
    vector<double> y = {2, 4, 6, 8, 10};

    tie(a, b) = linreg(y, x);
    EXPECT_EQ(2, b);
    EXPECT_EQ(-1, a);

}

// Test regression on floating number solutions
TEST(regression_test, regression_gradient_intercept_double) {

    double a, b;
    vector<double> x = {1, 2, 4, 8};
    vector<double> y = {12, 56, 34, 89};

    tie(a, b) = linreg(y, x);
    EXPECT_EQ(8.8956521739130441, b);
    EXPECT_EQ(14.391304347826086, a);
}

// Test T10 on QIBA data (allows a 20% error rate)
TEST(T10_test, QIBA_T1_500){

    string data_folder = "/home/ENG/engs1170/Code/25_T10_calculation/test_data/QIBA_v12_Tofts_beta1/QIBA_v12_Tofts_GE/6s_jit_3s_T1_500_S0_500_sigma_5/DICOM_T1/";

    double variance = 0.2; // proportion of allowed variance
    double tissue_t10 = 0.5;
    double vessel_t10 = 1.4;
    double mean_vessel, mean_tissue;

    tie(mean_vessel, mean_tissue) = T10calc(data_folder);

    ASSERT_TRUE(mean_tissue > (tissue_t10 - variance*tissue_t10));
    ASSERT_TRUE(mean_tissue < (tissue_t10 + variance*tissue_t10));
    ASSERT_TRUE(mean_vessel > (vessel_t10 - variance*vessel_t10));
    ASSERT_TRUE(mean_vessel < (vessel_t10 + variance*vessel_t10));
}

// Test T10 on QIBA data (allows a 20% error rate)
TEST(T10_test, QIBA_T1_200){

    string data_folder = "/home/ENG/engs1170/Code/25_T10_calculation/test_data/QIBA_v12_Tofts_beta1/QIBA_v12_Tofts_GE/6s_jit_3s_T1_200_S0_500_sigma_5/DICOM_T1/";

    double variance = 0.2; // proportion of allowed variance
    double tissue_t10 = 0.2;
    double vessel_t10 = 1.4;
    double mean_vessel, mean_tissue;

    tie(mean_vessel, mean_tissue) = T10calc(data_folder);

    ASSERT_TRUE(mean_tissue > (tissue_t10 - variance*tissue_t10));
    ASSERT_TRUE(mean_tissue < (tissue_t10 + variance*tissue_t10));
    ASSERT_TRUE(mean_vessel > (vessel_t10 - variance*vessel_t10));
    ASSERT_TRUE(mean_vessel < (vessel_t10 + variance*vessel_t10));
}

// Main file
int main(int argc, char **argv) {
    ::testing::InitGoogleTest(&argc, argv);
    return RUN_ALL_TESTS();
}