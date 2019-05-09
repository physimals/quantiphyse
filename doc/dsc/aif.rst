.. _dsc_aif:

AIF options for DSC modelling
=============================

The arterial input function (AIF) is a critical piece of information used in performing 
blood-borne tracer modelling, such as DCE-MRI. It describes the arterial supply of contrast
agent to the tissue. 

The AIF can be described as a series of values giving either the concentration
or the DSC signal at the same time intervals used in the DSC acquisition. Note that
applying an offset time to the AIF to account for injection and transit time is not
required as the model can be given and/or infer a delay time to account for this. 
This type of AIF is usually measured for the particular subject by averaging the
signal in voxels believed to be close to pure arterial voxels, i.e. in a major
artery.

.. image:: /screenshots/dsc_aif_options.png

The DSC AIF can be supplied in two different ways, selected by the ``AIF source`` option.
In each case the supplied AIF may either be a set of DSC signal values, or a 
set of tracer concentration values. The ``AIF type`` option selects between these
two possibilities

Global sequence of values
~~~~~~~~~~~~~~~~~~~~~~~~~

In this case each voxel has the same AIF which is supplied as a series of values 
giving either the concentration or the DSC signal at the same time intervals used 
in the DSC acquisition.

The series of values must be pasted into the ``AIF`` entry widget. A text file
containing the values can be drag/dropped onto this entry as a convenient way
of entering the values.

Voxelwise image
~~~~~~~~~~~~~~~

In this case a 4D image must be supplied which, at each voxel, contains the AIF 
for that voxel. This allows for the possibility of the AIF varying at each voxel.
