Fabber Bayesian modelling
=========================

*Widgets -> Fabber -> Fabber*

This widget allows use of the Fabber Bayesian model fitting tool within Quantiphyse. For more information 
on the Fabber method, see:

*Chappell, M.A., Groves, A.R., Woolrich, M.W., "Variational Bayesian inference for a non-linear forward model", 
IEEE Trans. Sig. Proc., 2009, 57(1), 223–236.*


A Simple example
----------------

In this example we will fit a simple polynomial model to a timeseries image.

First you need to load an image and ROI as described in the documentation. Here's what our data looks like.

.. image:: screenshots/fabber_img.png

Now select `Fabber` from the `Additional Widgets` menu.

.. image:: screenshots/fabber_widget.png

Setting Fabber options
~~~~~~~~~~~~~~~~~~~~~~

At the top, you must first select the model group you want to use. In this example we are using the ``GENERIC``
group which contains just two models, ``linear`` and ``poly``. The ``Forward Model`` menu lets you choose between 
these. In the next example we will use a more interesting model, but for now we will use ``poly`` which fits a 
simple polymonial to the data.

If we click on ``POLY Options`` next to the model, we get a list of model options:

.. image:: screenshots/poly_options.png

So this model just has the one option for the polynomial degree. We've changed it to degree 3, so we're fitting the 
timeseries for each voxel to a cubic equation.

There's also an ``Options`` button for the inference method. We're using ``vb`` for Variational Bayes - this is the main 
inference method in Fabber. ``nlls`` uses nonlinear least squares and is mostly used for comparison with Variational 
Bayes. There is also ``spatialvb`` which is similar to `vb` but incorporates spatial information to give a smoother 
output. These are out Variational Bayes options:

.. image:: screenshots/vb_options.png

The defaults are fine for this simple example.

Finally we have general Fabber options, viewed by clicking the ``Edit`` button.

.. image:: screenshots/fabber_options.png

These options mostly control what output is produced. We've just added the standard deviation as an additional output.

Running Fabber and viewing output
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

To run Fabber modelling, click ``Run Modelling``. The progress bar will give you an indication of time, but it 
shouldn't take long.

If we now look below the image at the ``Overlays`` box, we will see we have new overlays:

.. image:: screenshots/fabber_overlays.png

If you click on the menu box, you will find overlays containing the mean value of the four parameters in our 
polynomial equation, and also the standard deviation, since we asked for that as well. Finally there is the 
``modelfit`` overlay containing a timeseries of the model prediction for the calculated parameters. These overlays 
can be viewed, interacted with, and saved in the normal way.

Finally we might want to visualize the model fit, which we can do by selecting ``Model Curves`` from the 
``Widgets`` menu.  Click on a point in the image and you can see how closely the model matched the data.

.. image:: screenshots/fabber_modelfit.png

A More Realistic Example
------------------------

This example uses the CEST model, however the principles should be applicable to other models. I've loaded some 
CEST data and an ROI as before:

.. image:: screenshots/fabber_img_cest.png

Selecting a model from a group
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Now we want to run Fabber using the CEST model. First we need to select the group our model belongs to from the 
``Model Group`` menu:

.. image:: screenshots/fabber_modellib_cest.png

I've selected the CEST group, which gives us a single new model ```cest``. I can now select this model instead 
of ``poly``:

.. image:: screenshots/fabber_model_cest.png

Configuring the CEST model
~~~~~~~~~~~~~~~~~~~~~~~~~~

Lets set some options on this model. I need two matrix files, the data specification matrix and the pools matrix,
 so I click the ``Choose`` button and select the files which contain these matrices:

.. image:: screenshots/fabber_cest_mats.png

If I want to view or edit these files, the `Edit` button gives me a simple matrix editor:

.. image:: screenshots/fabber_cest_matrix_edit.png

I'll also add an optional ``ptrain`` matrix, and set the ``t12prior`` option:

.. image:: screenshots/fabber_cest_options.png

Finally I'll tweak the Variational Bayes options to set the maximum iterations to 20, in line with the 
``baycest`` script:

.. image:: screenshots/fabber_cest_vb_options.png

Running Fabber
~~~~~~~~~~~~~~

Now we can click ``Run Modelling`` again. This will take longer - about 10 minutes on my machine but this will 
vary considerably depending on how many cores you have available. At the end, we will again have overlays for 
the parameter means and standard deviations:

.. image:: screenshots/fabber_cest_overlays.png

As before, we can visualise the model fit using the ``Model Curves`` widget:

.. image:: screenshots/fabber_cest_modelfit.png

Adding an image prior
~~~~~~~~~~~~~~~~~~~~~

Image priors are a Fabber feature that allow us to provide an initial estimate for a parameter to the Variational 
Bayes method. To do this in Quantiphyse, first we load our image priors as overlays. In this example we have image 
priors for the ``T1a`` and ``T2a`` parameters in the files ``t1maprot`` and ``t2maprot``. Here's what the T2a 
prior looks like:

.. image:: screenshots/fabber_cest_t2a_prior.png

Now we tell Fabber to use them. If we click on the ``Parameter Priors`` button we see a list of model parameters.
Note that the set of parameters offered depends on the model selected, and on the model options. For example with
the Polynomial model, we have mode
This is in the Variational Bayes method options (*not* the CEST model options). The 
relevant options are `PSP_byname` which is the name of the parameter `PSP_byname_type` which is `I` for an image 
prior and `PSP_byname_image` where we select the overlay containing the image. These options are numbered so you 
can provide image priors for multiple parametes. When you enable one numbered option, the next becomes available 
automatically if you need it.

.. image:: screenshots/fabber_cest_set_priors.png

You should find that the ``PSP_byname_image`` options give you a menu of existing overlays to choose from.

We can now click `Run Modelling`` again to re-run with the image priors. Time taken should be similar to before.

To check that the image priors were indeed being used, we might want to view the Fabber log file. We can do this 
with the ``View Log`` button.

.. image:: screenshots/fabber_log.png

You can see the ``PSP_`` parameters are being picked up. Later on in the log we can see a report of the priors being 
used and verify that T1a and T2a are using ``I`` type (image) priors.

.. image:: screenshots/fabber_log_priors.png

Note that you will probably see multiple copies of the log in this file! This is because Quantiphyse runs multiple 
Fabber instances on your data for faster processing on multi-core processors. If you're just interested in viewing 
the options used you only need to look at one copy.

Running in batch mode
---------------------

Interactive is great for exploration, but once you've got a set of data files to run on it will become tedious. 
PkView can also run Fabber in batch mode using a YAML configuration file. Here's a YAML file for the CEST example 
presented above:

.. image:: screenshots/fabber_batch.png

We can run a batch file from the command line as follows:

    quantiphyse.exe --batch=fabber_cest.yaml

Instead of creating interactive overlays, this will simply save our requested output in the `out` folder that we 
specified. A subfolder is created for each subject, so you could easily add 'Subject2', etc and then run the whole 
set with the same options.

.. image:: screenshots/fabber_batch_output.png







