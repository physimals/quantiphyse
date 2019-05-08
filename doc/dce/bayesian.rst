.. _bayesian_dce:

Bayesian DCE modelling
======================

This widget provides DCE model fitting to output image maps of physiological parameters
if interest such as :math:`K_{trans}`, :math:`F_p`, :math:`PS`, :math:`V_p` and :math:`V_e`. A Bayesian
inference approach is used, this has the advantage that prior knowledge about likely
parameter values can be incorporated. This allows more complex models to be implemented
and, for example, allows a measured T1 value to vary slightly to better fit the data.

Tutorials
---------

  .. toctree::
   :maxdepth: 1

   tutorial_basic

  .. toctree::
   :maxdepth: 1

   tutorial_simulation

Reference
---------

.. toctree::
  :maxdepth: 1

  interface
  models
  aif
