 written by Mattias Heinrich.
 Copyright (c) 2014. All rights reserved.
 See the LICENSE.txt file in the root folder
 
 contact: heinrich(at)imi.uni-luebeck.de
          www.mpheinrich.de
 
 If you use this implementation or parts of it please cite:
 
 "MRF-Based Deformable Registration and Ventilation Estimation of Lung CT."
 by Mattias P. Heinrich, M. Jenkinson, M. Brady and J.A. Schnabel
 IEEE Transactions on Medical Imaging 2013, Volume 32, Issue 7, July 2013, Pages 1239-1248
 http://dx.doi.org/10.1109/TMI.2013.2246577
 
 or
 
 "Globally optimal deformable registration
 on minimum spanning tree using dense displacement sampling."
 by Mattias P. Heinrich, M. Jenkinson, M. Brady and J.A. Schnabel
 MICCAI (3) 2012: 115-122
 http://dx.doi.org/10.1007/978-3-642-33454-2_15
 
 AND
 
 "Towards Realtime Multimodal Fusion for Image- Guided Interventions using Self-Similarities"
 by Mattias P. Heinrich, Mark Jenkinson, Bartlomiej W. Papiez, Sir Michael Brady, and Julia A. Schnabel
 Medical Image Computing and Computer-Assisted Intervention - MICCAI 2013, LNCS 8149, Springer
 
 
 Tested with g++ on Mac OS X and Linux Ubuntu, use compileScript or directly:
 
 g++ TMI_MINDSSC.cpp -O3 -lpthread -msse4.2 -o tmiSSC
 
 replace msse4.2 by your current SSE version if needed
 for Windows you might need MinGW or CygWin

 This is intended for research purposes only and should not be used in clinical applications (no warranty)!

 
 You should give three filenames (only plain nifti format is supported) as input input_vol1.nii input_vol2.nii output_vol (no .nii for output), see help (-h) for details.

 Example usage: ./tmiSSC -F case1_fixed.nii -M case1_moving.nii -O output_case1_ssc
 Default parameter settings: -l 5 -G 7x6x5x4x3 -L 6x5x4x3x2 -Q 3x2x2x1x1 -s 1 -a 2.0 -r 50

To obtain deformation fields in mm use defTMI after running tmiSSC
(otherwise only a parametric displacement field in voxels is returned).

 If you find any bugs or have questions please don’t hesitate to contact me by email.
