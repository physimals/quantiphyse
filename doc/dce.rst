Dynamic Contrast Enhanced (DCE) MRI modelling
=============================================

*Widgets -> DCE-MRI*

.. image:: /screenshots/dce_widget_menu.png

The DCE modelling package allow pharmacokinetic modelling of DCE-MRI using a variety of models.
Two independent widgets are provided:

.. toctree::
  :maxdepth: 1
  
  dce/bayesian

The Bayesian DCE widget supports a number of models of varying complexity and a choice
of population AIFs or a measured AIF signal.

.. toctree::
  :maxdepth: 1

  dce/lsq

The Least-squares DCE widget supports the basic Tofts model and population AIFs for
clinical and preclinical applications.

The interface to the two widgets has been kept as similar as possible to facilitate comparison of
the methods, however generally the Bayesian approach is preferred for clinical applications as it
provides a greater range of model and AIF options.
