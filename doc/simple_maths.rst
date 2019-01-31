Simple maths
============

*Widgets -> Processing -> Simple Maths*

This widget is a simplified version of the console and allows new data to be created from
simple operations on existing data.

The text entered must be a valid Python expression and can include the names of existing ROIs 
and overlays which will be Numpy arrays. Numpy functions can be accessed using the ``np`` 
namespace.

Examples
--------

Add Gaussian noise to some data

newdata = ``mydata + np.random.normal(0, 100)``

Calculate the difference between two data sets

newdata = ``mydata1 - mydata2``

Scale data to range 0-1

newdata = ``(mydata - mydata.min()) / (mydata.max() - mydata.min())``

