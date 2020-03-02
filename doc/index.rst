

================
|qp| Quantiphyse 
================

.. |qp| image:: screenshots/qp_logo.png 
    :height: 48px

.. image:: screenshots/sample_image.png
    :scale: 30%
    :align: right

Quantiphyse is a visualisation and analysis tool for 3D and 4D biomedical data. It is particularly suited 
for physiological or functional imaging timeseries data. 

Quantiphyse is built around the concept of making spatially 
resolved measurements of physical or physiological processes from imaging data using 
model-based or model-free methods, often exploiting Bayesian inference techniques.

Quantiphyse can analyse data by voxels or within regions of interest that may be manually or 
automatically created, e.g. using supervoxel or clustering methods. 

.. image:: screenshots/collage.png
    :scale: 50%
    :align: left

Features
--------

 - 2D orthographic visualisation and navigation of data, regions of interest (ROIs) and overlays
 - Generic analysis tools including clustering, supervoxel generation and curve comparison
 - Tools for CEST, ASL, DCE, DSC and qBOLD MRI analysis and modelling
 - Integration with selected FSL tools
 - ROI generation
 - Registration and motion correction
 - Extensible via plugins - see :ref:`plugins`.

License
-------

© 2017-2020 University of Oxford

Quantiphyse is Open Source software, licensed under the Apache Public License version 2.0

    http://www.apache.org/licenses/LICENSE-2.0

License details are displayed on first use and in the ``LICENSE`` file included in the distribution. 
Note that this does not apply to all available plugins - you should check the licensing
terms for a plugin before using it.

Tutorials
---------

 - `CEST-MRI tutorial <cest/cest_tutorial.html>`_
 - `IMAGO ASL-MRI tutorial <asl/imago_tutorial.html>`_
 - `FSL ASL-MRI tutorial <asl/asl_tutorial.html>`_

Getting Quantiphyse
-------------------

Quantiphyse is available on PyPi - see :ref:`install`.

Major releases of Quantiphyse are also available via the `Oxford University Innovation Software 
Store <https://process.innovation.ox.ac.uk/software>`_. The packages held by OUI have no 
external dependencies and can be installed on Windows, Mac and Linux. They may lag behind
the current PyPi release in terms of functionality.

User Guide
----------

.. toctree::
   :maxdepth: 1

   basics/getting_started
   asl/asl
   cest/cest
   dce/dce
   dsc/dsc
   qbold/qbold
   generic/generic_tools
   advanced/advanced_tools
   faq
    
Bugs/Issues
-----------

Bugs may be submitted using the Github `issue tracker for Quantiphyse <https://github.com/ibme-qubic/quantiphyse/issues>`_.

For any other comments or feature requests please contact the  `current maintainer: <mailto:martin.craig@eng.ox.ac.uk>`_

Contributors
------------

 - `Martin Craig <mailto:martin.craig@eng.ox.ac.uk>`_ (Current maintainer)
 - `Ben Irving <mailto:mail@birving.com>`_ (Original author)
 - `Michael Chappell <mailto:michael.chappell@eng.ox.ac.uk>`_
 - Paula Croal
 - Moss Zhao

Acknowledgements
----------------

 - Julia Schnabel
 - Sir Mike Brady

Images © 2017-2019 University of Oxford

