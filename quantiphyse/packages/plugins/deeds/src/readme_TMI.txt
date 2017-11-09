 written by Mattias Heinrich.
 Copyright (c) 2014. All rights reserved.
 See the LICENSE.txt file in the root folder
 
 contact: heinrich(at)imi.uni-luebeck.de
          www.mpheinrich.de
 
 If you use this implementation or parts of it please cite:
 
 “Non-parametric Discrete Registration with Convex Optimisation.”
 by Mattias P. Heinrich, Bartlomiej W. Papież, Julia A. Schnabel, Heinz Handels
 Biomedical Image Registration - WBIR 2014, LNCS 8454, Springer, pp 51-61
 
 and
 
 "Towards Realtime Multimodal Fusion for Image- Guided Interventions using Self-Similarities"
 by Mattias P. Heinrich, Mark Jenkinson, Bartlomiej W. Papiez, Sir Michael Brady, and Julia A. Schnabel
 Medical Image Computing and Computer-Assisted Intervention - MICCAI 2013, LNCS 8149, Springer
 
 
 Tested with g++ on Mac OS X and Linux Ubuntu, compile with:
 
 g++ WBIR_SSC.cpp -O3 -lpthread -msse4.2 -o wbirSSC
 g++ WBIR_LCC.cpp -O3 -lpthread -msse4.2 -o wbirLCC
 
 replace msse4.2 by your current SSE version if needed
 for Windows you might need MinGW or CygWin

 This is intended for research purposes only and should not be used in clinical applications (no warranty)!

 
 You should give three filenames (only plain nifti format is supported) as input input_vol1.nii input_vol2.nii output_vol (no .nii for output), see help (-h) for details.

 Example usage: ./wbirSSC -F case1_fixed.nii -M case1_moving.nii -O output_case1_ssc
 Default parameter settings: -l 3 -L 6x4x2 -s 1 -g 0.6

 If you find any bugs or have questions please don’t hesitate to contact me by email.
