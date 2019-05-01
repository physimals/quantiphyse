Arterial Spin Labelling (ASL) MRI
=================================

- *Widgets -> ASL -> ASL data processing*

This widget provides a complete pipeline for Arterial Spin Labelling MRI analysis using the Fabber 
Bayesian model fitting framework. The pipeline is designed for brain ASL MRI scans and some
of the options assume this, however with care it could be used for other types of ASL scan.

Tutorials
---------

.. toctree::
   :maxdepth: 1

   asl_tutorial

A walkthrough tutorial based on the 
`FSL course practical session on ASL <https://fsl.fmrib.ox.ac.uk/fslcourse/lectures/practicals/ASLpractical/index.html>`_

.. toctree::
   :maxdepth: 1

   IMAGO ASL tutorial <imago_tutorial>

Reference
---------

This set of pages goes through each page of the widget in turn an explains the options systematically
with some examples.

.. toctree::
   :maxdepth: 1

   ASL data <asl_data>
   Corrections <asl_corr>
   Structural data <asl_struc>
   Calibration <asl_calib>
   Analysis <asl_analysis>
   Output <asl_output>
   Multiphase ASL <asl_multiphase>
   General preprocessing <asl_preproc>
   
Publications
------------

The following publications are useful citations for various features of the ASL 
processing pipeline: 

 - **Bayesian inference method**: *Chappell MA, Groves AR, Whitcher B, Woolrich MW. Variational 
   Bayesian inference for a non-linear forward model. IEEE Transactions on Signal Processing 
   57(1):223-236, 2009.*

 - **Spatial regularization**: *A.R. Groves, M.A. Chappell, M.W. Woolrich, Combined Spatial and 
   Non-Spatial Prior for Inference on MRI Time-Series , NeuroImage 45(3) 795-809, 2009.*

 - **Arterial contribution to signal**: *Chappell MA, MacIntosh BJ, Donahue MJ, Gunther M, Jezzard P, 
   Woolrich MW. Separation of Intravascular Signal in Multi-Inversion Time Arterial Spin 
   Labelling MRI. Magn Reson Med 63(5):1357-1365, 2010.*

 - **Partial volume correction**: *Chappell MA, MacIntosh BJ, Donahue MJ,Jezzard P, Woolrich MW. 
   Partial volume correction of multiple inversion time arterial spin labeling MRI data, 
   Magn Reson Med, 65(4):1173-1183, 2011.*
