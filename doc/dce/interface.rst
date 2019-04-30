DCE modelling widget user interface
===================================

.. image:: /screenshots/bayesian_dce_interface.png

Input data
----------

 - ``DCE data`` is used to select the data set containing the 4D DCE time series
 - ``ROI`` is used to select an optional region of interest data set
 - ``T1`` is used to select an optional T1 map (e.g. derived from VFA images using
   the T1 widget). If a T1 map is not provided a single T1 value must be specified.
   This can be allowed to vary on a voxelwise basis as part of the fitting process.

Acquisition
-----------

 - ``Contrast agent relaxivity`` should be the T1 relaxivity from the manufaturer's documentation.
   A list of commonly used agents and their relaxivities is also given at
   `List of relaxivities`_.

 - ``Flip angle`` is defined by the acquisition parameters and should be given 
   in degrees.

 - Similarly ``TR`` is the repetition time for the acquisition and should be given
   in milliseconds.

 - ``Time between volumes`` should be given in seconds. In some cases this may
   not be fixed as part of the acquisition protocol, but instead a series of
   volumes acquired, each with the time at which it was acquired. In this case
   you must determine a sensible time difference to use, for example by dividing
   the total acquisition time by the number of volumes acquired.

 - ``Estimated injection time`` is the time delay between the first acquisition and the
   introduction of the DCE contrast agent in seconds. The latter is often not given immediately
   in order to establish a baseline signal. The delay time can be estimated as part of
   the modelling process - this is recommended to account for not just injection
   delay but also the variable transit time of the contrast agent to different voxels.

Model options
-------------

 - A selection of models are available - see :ref:`bayesian_dce_models` for a full description.

 - Similarly the choice of AIF is described in :ref:`bayesian_dce_aif`.

 - A T1 value in seconds must be given if a T1 map is not provided in the input data section.

 - If ``Allow T1 to vary`` is selected the T1 value (whether from a T1 map or the value given
   in this section) is allowed to vary slightly on a voxelwise basis. In general if you do
   not have a T1 map it is recommended to allow the T1 to vary to reflect variation within
   the region being modelled. If you do have a T1 map you may choose to treat this as 
   ground truth and not allow it to vary in the modelling.

 - If  ``Allow injection time to vary`` is selected, then the delay time from the start of 
   the acquisition to the arrival of the DCE tracer is inferred as part of the model fitting.
   Usually this should be enabled as described above, to account for variable transit times
   to different voxels.

 - For the Tofts model, there is a choice to infer :math:`K_{ep}` rather than :math:`V_e`.
   These are equivalent parameters related by the equation :math:`V_e = K_{trans} / K_{ep}`.
   Sometimes one choice may be more numerically stable than the other.


.. _`List of relaxivities`: http://mriquestions.com/what-is-relaxivity.html
