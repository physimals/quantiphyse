.. _plugins:

Quantiphyse plugins
===================

Some Quantiphyse functionality requires the installation of plugins. The following plugins are currently available:

 - ``quantiphyse-dce`` - DCE modelling
 - ``quantiphyse-fabber`` - Bayesian model fitting - required for various specialised tools
 - ``quantiphyse-fsl`` - Interface to selected FSL tools (requires FSL installation)
 - ``quantiphyse-cest`` - CEST-MRI modelling
 - ``quantiphyse-asl`` - ASL-MRI modelling (requires FSL installation)
 - ``quantiphyse-dsc`` - DSC-MRI modellingg
 - ``quantiphyse-qbold`` - Quantitative BOLD MRI model fitting
 - ``quantiphyse-t1`` - T1 mapping
 - ``quantiphyse-sv`` - Supervoxel generation
 - ``quantiphyse-deeds`` - Fully deformable registration using the DEEDS method
 - ``quantiphyse-datasim`` - Data simulation (Experimental)

Plugins are installed from PyPi, e.g.::

    pip install quantiphyse-dce

They will be automatically detected and added to Quantiphyse next time you run it. The packages
available on the OUI software store have all plugins included which were available at the 
time of release.
