Simulated Fabber data
=====================

*Widgets -> Simulation -> Simulated Fabber Data*

This widget uses the Fabber Bayesian model fitting framework in reverse to generate simulated 
data for any model known to the Fabber framework. This is particularly useful when used in
conjunction with model fitting tools that use the Fabber framework as it enables the 
construction of 'round trip' self-consistency tests that ensure the model can fit to data
it has itself generated.

The simulation tool can also be used for other applications, for example evaulating the
effect of noise on fitting accuracy and model comparison in cases where a variety of 
models exist with different levels of complexity.

.. note::
    The simulation tool should be regarded as an advanced tool and exposes the full 
    complexity of the Fabber framework. As a result it is not as user friendly as 
    the modelling packages based on Fabber which simplify things in a way which is
    specific to their particular application.

.. toctree::
  :maxdepth: 1

  sim_interface
  sim_tutorial

