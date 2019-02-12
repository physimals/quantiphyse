Frequently Asked Questions
==========================

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

Errors when installing from pip because modules not available
-------------------------------------------------------------

Usually these problems are not related directly to Quantiphyse but
involve dependencies which require specific versions of a module.

If you encounter these types of problems, you might want to try
using ``conda`` instead of pip which we generally find is more reliable
for packages which include native (i.e. non-Python) code. Instead of ``pip install``
try ``conda install`` for the packages which are causing trouble, then
try ``pip install quantiphyse`` afterwards.
