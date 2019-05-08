==========================================
DCE-MRI Data Analysis Tutorial
==========================================

Introduction
============

In this tutorial, we are going to explore how to quantify the haemodynamic parameters of DCE-MRI data using Quantiphyse. We will use the Tofts models to perform our analysis.

Data Preparation
================

First, we need to load the DCE-MRI data and ROI files to Quantiphyse. Be sure to specify the DCE-MRI data as ``Data`` and ROI file as ``ROI``. It is always helpful to check the timeseries of the DCE-MRI data using the ``Voxel analysis`` Widget:

.. image:: /screenshots/dce/DCE_tutorial_basic_timeseries.jpg

Acquisition Parameters
================================

If the timeseries of the data looks fine, the next step is to specify the sequence parameters for our analysis. Now load the ``Bayesian DCE`` widget.

.. image:: /screenshots/dce/DCE_tutorial_basic_load_fabber.jpg

We will see that the Bayesian DCE widget has been loaded onto the right hand side of the Quantiphyse interface.

.. image:: /screenshots/dce/DCE_tutorial_basic_interface.jpg

A full description of the interface can be found `DCE modelling widget user interface <interface.html>`.

Before we specify the acquisition parameters, we need to make sure that the correct data have been loaded. In the previous step, we have loaded the DCE-MRI data, ROI, and a T1 map. In the ``Input data`` section, we need to tell Quantiphyse the data that we loaded:

.. image:: /screenshots/dce/DCE_tutorial_basic_input_data.jpg

Now we are going to specify the sequence parameter values. These values can be found in the protocol files or the metadata from the scanning session. Note: It is very important to specify these values accurately to ensure the correct analysis. If the data is from an external source, please consult the person who acquired the data.

In our case, we are going to use the following values:

.. image:: /screenshots/dce/DCE_tutorial_basic_acquisition_parameters.jpg

In the AIF option, we are going to select ``Population (Parker)``. A detailed explanation on the different AIFs can be found `AIF options for Bayesian DCE modelling <aif.html>`.

Model Options
=============

After specifying the sequence parameters, the next step is to select the appropriate model to analyse the data. In this example, we are going to use ``Standard Tofts Model``. A full description of the different models provided by Quantiphye can be found `Models available for Bayesian DCE modelling <models.html>`. We are also going to specify the T1 value. Note: T1 values vary in different tissues. Although is it difficult to have a very precise estimation of the T1 value of our tissue of interest, it is important to specify a value that is close to the actual T1 value to improve the quantification of the haemodynamic parameters in our analysis. We will leave the other options unchecked.

.. image:: /screenshots/dce/DCE_tutorial_basic_model_options.jpg

Run Modelling
=============

At this point, we have finished the preparation for our analysis. Now click ``Run`` to start the analysis. Note: it may take a while to complete the analysis.
