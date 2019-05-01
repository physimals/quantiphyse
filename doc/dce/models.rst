.. _bayesian_dce_models:

Models available for Bayesian DCE modelling
===========================================

Currently five models DCE models are available in the Bayesian
DCE widget. These models are implemented using the
`Fabber <https://fabber-core.readthedocs.io/>`_. model fitting
framework [1]_. More details about the implementation of these models is
given in the `Fabber DCE <https://fabber-dce.readthedocs.io/>`_
documentation.

The standard and extended one-compartment Tofts model [2]_
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

The Extended Tofts model differes from the standard model
in the inclusion of the :math:`V_p` parameter.
                
The two-compartment exchange model (2CXM) [3]_
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

The Compartmental Tissue Uptake model (CTU) [4]_
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

The Adiabatic Approximation to the Tissue Homogeniety model (AATH) [5]_
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

References
~~~~~~~~~~

.. [1] *Chappell, M.A., Groves, A.R., Woolrich, M.W., "Variational Bayesian
   inference for a non-linear forward model", IEEE Trans. Sig. Proc., 2009,
   57(1), 223–236.*

.. [2] http://www.paul-tofts-phd.org.uk/DCE-MRI_siemens.pdf

.. [3] https://onlinelibrary.wiley.com/doi/full/10.1002/mrm.25991

.. [4] https://onlinelibrary.wiley.com/doi/full/10.1002/mrm.26324

.. [5] https://journals.sagepub.com/doi/10.1097/00004647-199812000-00011
