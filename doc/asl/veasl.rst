VEASL
=====

*Widgets -> ASL -> VEASL*

VEASL is a tool for analysing Vessel Encoded ASL MRI

Options
-------

- ``Data`` - an ASL data set
- ``ROI`` - ROI selecting voxels to use for inference. This is a subset of the image voxels used for the internal inference of 
  global parameters. The ``Auto generate`` button creates a suitable ROI from the voxels showing strongest Tag-Control difference. Note
  that output will be generated for all image voxels regardless of the ROI used for inference.
- ``Sources per class`` - Number of vessels to include in each class. The classes can be viewed using the ``Class List`` expander below
- ``Inference method`` - ``MAP`` (maximum a posteriori) is the only method currently supported
- ``Modulation matrix`` - ``Default`` is the only option currently supported
- ``Infer vessel locations`` - Whether to infer the co-ordinates of the vessel locations using the provided values as a starting point. 
  If subject motion is believed to be the main cause of uncertainty in the positions, a rigid transformation of the initial positions can
  be inferred.
- ``Infer flow velocity`` - Whether to infer the flow velocity in each vessel

Image list
----------

This may be used to re-order the interpretation of volumes in your data set. Normally the first two volumes are tag/control followed
by the encoded volumes.

Priors
------
Prior values for the inference. Prior means of co-ordinates are the initial values provided, however the prior standard deviation may be specified.
The mean and standard deviation for the velocity may be specified if this is being inferred. The prior standard deviation for the rotation
angle may also be specified if a rigid transformation is being inferred.

Class list
----------

This displays the list of classes, the vessels in each, and after a successful run, the proportions of each class that were inferred.

Vessels
-------

Initial vessel locations should be specified here. A matrix file can be dragged in to the values grid, or the values can be edited manually. 
A visual plot of the locations is shown, this will be updated after the run to show the inferred positions as well.

Encoding setup
--------------

The parameters used for the encoded images must be specified here. The default is the ``TWO`` format, however the alternative ``MAC`` format
is also supported. Refer to *Chappell et al 2012* for information about the encoding parameters.

Run
---

Note that VEASL does not currently provide progress feedback so do not expect the progress bar to move!

After a successful run, the log may be viewed. Two data files are generated: ``flow`` and ``prob``. In addition, the inferred vessel 
locations are displayed under ``Vessels`` and the inferred class proportions under ``Class list``.

