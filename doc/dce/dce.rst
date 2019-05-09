Dynamic Contrast Enhanced (DCE) MRI
===================================

*Widgets -> DCE-MRI*

.. image:: /screenshots/dce_widget_menu.png

Dynamic Contrast Enhanced MRI (DCE-MRI) is an advanced MRI technique that captures the tissue T1 changes over time after the administration of a contrast agent. The most common application of DCE-MRI is in monitoring tumours and multiple sclerosis. Thus, DCE-MRI data are typically acquired from patients with cancer or multiple sclerosis. The objective of analysing DCE-MRI data is to quantify a number of haemodynamic parameters (such as Ktrans, perfusion, and permeability), which are important biomarkers to understand the physiology of tumours.

Here, we will explain the steps to analyse DCE-MRI data to quantify the haemodynamic parameters using Quantiphyse. The DCE modelling package allow pharmacokinetic modelling of DCE-MRI using a variety of models.
Two independent widgets are provided:

.. toctree::
  :maxdepth: 1
  
  bayesian

The Bayesian DCE widget supports a number of models of varying complexity and a choice
of population AIFs or a measured AIF signal.

.. toctree::
  :maxdepth: 1

  lsq

The Least-squares DCE widget supports the basic Tofts model and population AIFs for
clinical and preclinical applications.

The interface to the two widgets has been kept as similar as possible to facilitate comparison of
the methods, however generally the Bayesian approach is preferred for clinical applications as it
provides a greater range of model and AIF options.

Publications
------------

The following publications are useful citations for the DCE processing widget:

 - **Bayesian inference method**: *Chappell MA, Groves AR, Whitcher B, Woolrich MW. Variational 
   Bayesian inference for a non-linear forward model. IEEE Transactions on Signal Processing 
   57(1):223-236, 2009.*

