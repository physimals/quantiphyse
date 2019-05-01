.. _bayesian_dce_aif:

AIF options for Bayesian DCE modelling
======================================

The arterial input function (AIF) is a critical piece of information used in performing 
blood-borne tracer modelling, such as DCE-MRI. It describes the arterial supply of contrast
agent to the tissue. Quantiphyse supposrts a number of AIF options in the analysis.

.. image:: /screenshots/dce/dce_aifs.jpg

The AIF can be described as a series of values giving either the concentration
or the DCE signal at the same time intervals used in the DCE acquisition. In this case, the type of AIF is 'Measured DCE signal' or 'Measured concentration curve'. Note that applying an offset time to the AIF to account for injection and transit time is not
required as the model can be given and/or infer a delay time to account for this. 
This type of AIF is usually measured for the particular subject by averaging the
signal in voxels believed to be close to pure arterial voxels, i.e. in a major
artery. 

Alternatively 'population' AIFs can be used. These are derived from the measurement of
AIFs in a large number of subjects and fitting the outcome to a simple mathematical
function. This avoids the need to measure the AIF individually for each subject, and
avoids additional subject variation associated with this additional measurement. However
a population AIF may not reflect the individual subject's physiology particularly when
studying a group in which arterial transit may be slower or subject to greater 
dispersion than the general population.

Two population AIFs are provided as derived by Orton (2008) [1]_ and Parker (2006) [2]_. They can be specified using the 'Population (Orton 2008)' or 'Population (Parker)' respectively. These are parameterised functions and in our implementation we used the parameter values defined in the respective papers.

References
~~~~~~~~~~

.. [1] `Matthew R Orton et al 2008 Phys. Med. Biol. 53 1225 <https://iopscience.iop.org/article/10.1088/0031-9155/53/5/005/meta>`_

.. [2] https://onlinelibrary.wiley.com/doi/full/10.1002/mrm.21066