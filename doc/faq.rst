.. _faq:

Frequently Asked Questions
==========================

Installation
^^^^^^^^^^^^

Errors when installing from pip because modules not available
-------------------------------------------------------------

Usually these problems are not related directly to Quantiphyse but
involve dependencies which require specific versions of a module.

If you encounter these types of problems, you might want to try
using ``conda`` instead of pip which we generally find is more reliable
for packages which include native (i.e. non-Python) code. Instead of ``pip install``
try ``conda install`` for the packages which are causing trouble, then
try ``pip install quantiphyse`` afterwards.

Error on startup after installing plugins
-----------------------------------------

One known issue can be identified by starting quantiphyse from the command line. If it fails
with an error message that ends as follows::

    pkg_resources.ContextualVersionConflict: (deprecation 2.0.6 (/usr/local/lib/python2.7/dist-packages), Requirement.parse('deprecation<=2.*,>=1.*'), set(['fslpy']))                          

This can be fixed with::

    pip install deprecation==1.2 --user

The cause is an apparently invalid requirements specification in a dependency package.

Error installing dependencies using conda
-----------------------------------------

The error usually includes the following::

    UnsatisfiableError: The following specifications were found to be incompatible with each other:

The cause seems to be a bug in Conda version 4.7.x when using the conda-forge channel. To fix, use the following
to downgrade to an older version of conda::

    conda config --set allow_conda_downgrades true
    conda install conda=4.6.14

Running
^^^^^^^

On Windows the data viewer and graphs do not work properly
----------------------------------------------------------

The symptoms of this problem include:

 - The image viewer windows only update when you drag on them with the mouse
 - Graph plots (e.g. in voxel analysis) do not appear

This seems to be an issue with PySide which affects the pyqtgraph library on Windows. 
We have found that installing PySide and pyqtgraph using ``conda`` rather than ``pip``
can help.

Fabber modelling widgets do not work (e.g. CEST/ASL/DCE/DSC)
------------------------------------------------------------

These functions require an up to date version of Fabber. We expect **FSL 6.0.1**
to include sufficiently up to date versions of this code - this should be
available very soon. If you can't wait for this, please contact the maintainers
and we will explain how to install an interim version which will work.

This does not affect the packages downloaded from the OUI Software Store
which include prebuilt versions of Fabber and the required models.
