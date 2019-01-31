
.. image:: screenshots/qp_logo.png 
    :height: 48px
    :align: right

===========
Quantiphyse 
===========

Quantiphyse is a viewing and analysis tool for 3D and 4D biomedical data. It is particularly suited 
for physiological or functional imaging data comprised of multi volumes in a 4D (time-) series 
and/or multimodal imaging data. Quantiphyse is built around the concept of making spatially 
resolved measurements of physical or physiological processes from imaging data using either 
model-based or model-free methods, in a large part exploiting Bayesian inference techniques.
Quantiphyse can analyse data both voxelwise or within regions of interest that may be manually or 
automatically created, e.g. supervoxel or clustering methods. 

.. image:: screenshots/sample_image.png

Features include:

 - 2D orthographic viewing and navigation of data, regions of interest (ROIs) and overlays
 - Universal analysis tools including clustering, supervoxel generation and curve comparison
 - Tools for CEST, ASL, DCE and DSC-MRI analysis and modelling
 - Integration with selected FSL tools
 - ROI generation
 - Registration and motion correction
 - Extensible via plugins

This documentation is based on the latest development version

Download
--------
Quantiphyse is available via the `Oxford University Innovation Software 
Store <https://process.innovation.ox.ac.uk/software>`_ 

License
-------
Quantiphyse is available free under an academic (non-commercial) license. See the `OUI Software 
Store <https://process.innovation.ox.ac.uk/software>`_ for more details

User Guide
----------

Basic functions
===============

.. toctree::
   :maxdepth: 2

   overview
   getting_started
   overlay_stats
   modelfit
   
Generic analysis and processing tools
=====================================

.. toctree::
   :maxdepth: 1

   compare
   curve_compare
   simple_maths
   reg
   smoothing
   cluster
   sv
   roi_analysis
   roibuilder
   mean_values
   hist
   rp
   
Current included plugins
===============

.. toctree::
   :maxdepth: 1

   t1
   pk
   cest
   asl_overview

Advanced Tools
==============

.. toctree::
   :maxdepth: 1

   batch
   console
   nifti_extension
   
Bugs/Issues
-----------

Please report bug, issues, feature requests or other comments to the  `current maintainer: <mailto:martin.craig@eng.ox.ac.uk>`_

Contributors
------------

 - `Martin Craig <mailto:martin.craig@eng.ox.ac.uk>`_ (Current maintainer)
 - `Ben Irving <mailto:mail@birving.com>`_ (Original author)
 - `Michael Chappell <mailto:michael.chappell@eng.ox.ac.uk>`_
 - Paula Croal

Acknowledgements
----------------

 - Julia Schnabel
 - Sir Mike Brady

Images copyright 2018 University of Oxford

