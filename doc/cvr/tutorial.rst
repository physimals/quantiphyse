.. _dce_tutorial_basic:

==========================================
BOLD-PETCO2 CVR Data Analysis Tutorial
==========================================

Introduction
============

In this tutorial, we are going to explore how to quantify cerebrovascular reactivity using PETCO2-BOLD MRI.

The input data files should be found in the folder ``cvr_input_data``

Load the data
=============

First, we need to load the BOLD data and the brain mask file to Quantiphyse. These are named ``filtered_func_data.nii.gz`` and ``mask.nii.gz``. 
You can load these either using the menu item ``File->Load data`` or by dragging and dropping the data files into the viewer window from
the file manager. Be sure to specify the BOLD data as ``Data`` and mask file as ``ROI``. 

.. image:: /screenshots/cvr/cvr_data.png

It is always helpful to check the timeseries of the DCE-MRI data using the ``Voxel analysis`` Widget:

.. image:: /screenshots/cvr/cvr_data_timeseries.png

This clearly shows the increase in the BOLD signal during the hypercapnia blocks.

In this case the raw BOLD data has been pre-processed using the FSL FEAT tool to perform temporal filtering and smoothing. This will result
in a smoother CVR map. The raw BOLD data is also available in the input folder. It may be interesting to try using this instead - you 
will find that the resulting CVR map is a lot noiser!

The CVR analysis Widget
=======================

This can be found under ``Widgets->BOLD->CVR PETCO2``

.. image:: /screenshots/cvr/widget.png

The BOLD data you loaded will probably already be selected as 'BOLD timeseries data' - if not select it using the list box.
For the ROI, make sure you have selected the analysis mask loaded previously.

Acquisition Parameters
======================

In order to fit the data we need the measurement of the pCO2 timeseries and to match it to the BOLD-MRI timeseries. This will 
involve loading the 'Physiological data' file. This is a text file in which each line is an observation. The first column contains
the time point in seconds, the second the CO2 measurement, the third the O2 measurement, and the fourth the scan trigger which 
controls when images are acquired. This information is contained within the file 'phys_data.txt'.

To load this file, either drag/drop it from a file manager window into the 'Physiological Data' entry, or click 'Choose', navigate
to the input data folder and select the file.

The following acquisition parameters may also be specified:

 - Baseline period: Time in seconds before any manipulation of pCO2
 - ON block duration: Length in seconds of increased pCO2 lock
 - OFF block duration: Time in seconds between ON blocks
 - pCO2 sampling frequency: Number of readings of pCO2 per second
 - pCO2 mechanical delay: Approximate time in seconds taken for exhaled CO2 to reach the sensor

In our case the defaults are all fine.

Bayesian Modelling
==================

.. image:: /screenshots/cvr/bayesian.png

The Bayesian modelling tool performs inference using a fast variational Bayes technique to return maps of CVR, estimated delay time
and constant signal offset.

To avoid the output getting confused with subsequent runs you can specify a data set name suffix - e.g. ``vb``.

Click 'Run' to perform the analysis. The following output files will be generated:

 - ``cvr_vb`` - The CVR map
 - ``delay_vb`` - The delay time map in seconds
 - ``sig0_vb`` - The constant signal offset
 - ``modelfit_vb`` - The model fit

To check the model fit, use the Voxel Analysis widget and click on voxels in the image to see the data overlaid with
the model prediction.

GLM modelling
=============

.. image:: /screenshots/cvr/glm.png

The GLM modelling tool performs a similar analysis by inverting a linear model. In order to estimate the delay time, the GLM must
be fitted for a range of delay times with the best fit (least squares) selected as the output. The minimum and maximum delay times
to be tested can be specified, as well as the step length. Of course the more delay times you test the longer the analysis will take.
Unlike the Bayesian approach, only the specific delay times tested will be returned in the delay time map, so this will effectively
be a discrete rather than a continuous map.

Again, you can specify an output dataset name suffix, e.g. ``glm``.
