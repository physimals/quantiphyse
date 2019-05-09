DSC modelling widget user interface
===================================

.. image:: /screenshots/dsc_options.png

DSC options
~~~~~~~~~~~

 - ``DSC data`` is used to select the data set containing the 4D DSC time series

 - ``ROI`` is used to select the region of interest data set

 - ``Model choice`` selects the model to be used for the inference. See 
   :ref:`dsc_models` for a description of the models available.

 - ``TE`` is the echo time of the acquisition

 - ``Time interval between volumes`` should be given in seconds. In some cases this may
   not be fixed as part of the acquisition protocol, but instead a series of
   volumes acquired, each with the time at which it was acquired. In this case
   you must determine a sensible fixed time difference to use, for example by dividing
   the total acquisition time by the number of volumes acquired.

 - If ``Apply dispersion to AIF`` is selected, the model is modified to account for 
   dispersion of the tracer within the blood during transit.

 - If ``Infer delay parameter`` is selected, the arrival time of the tracer in each
   voxel is estimated (recommended).

 - If ``Infer arterial component`` is selected, contamination of the DSC signal by
   tracer in arteries is included in the model.

 - If ``Spatial regularization`` is selected, adaptive spatial smoothing on the 
   output parameter maps is performed using a Bayesian framework where the spatial
   variability of the parameter is inferred from the data (recommended).

Standard model options
~~~~~~~~~~~~~~~~~~~~~~

 - If ``Infer MTT`` is selected the mean transit time of the tracer is estimated

CPI model options
~~~~~~~~~~~~~~~~~

 - ``Number of control points`` selects the number of evenly spaced control points 
   that will be used to model the residue function.

 - ``Infer control point time position`` can be used to allow the control points to
   move their temporal position rather than being fixed in their original evenly
   spaced position. This may enable an accurate residue curve with fewer control
   points, but can also lead to numerical instability.

