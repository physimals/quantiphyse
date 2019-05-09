.. _plugins:

Quantiphyse plugins
===================

Some Quantiphyse functionality requires the installation of plugins. The following plugins are currently available:

 - ``quantiphyse-dce`` - DCE modelling
 - ``quantiphyse-fabber`` - Bayesian model fitting - required for various specialised tools
 - ``quantiphyse-fsl`` - Interface to selected FSL tools (requires FSL installation)
 - ``quantiphyse-cest`` - CEST-MRI modelling (requires ``quantiphyse-fabber``)
 - ``quantiphyse-asl`` - ASL-MRI modelling (requires FSL installation and ``quantiphyse-fabber``)
 - ``quantiphyse-dsc`` - DSC-MRI modellingg (requires ``quantiphyse-fabber``)
 - ``quantiphyse-t1`` - T1 mapping (requires ``quantiphyse-fabber``)

Plugins are installed from PyPi, e.g.::

    pip install quantiphyse-dce

They will be automatically detected and added to Quantiphyse next time you run it. The packages
available on the OUI software store have all plugins included which were available at the 
time of release.
