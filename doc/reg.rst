Registration and Motion Correction
==================================

*Widgets -> Processing -> Registration*

This widget enables registration and motion correction using various methods. Currently implemented 
methods are:

 - DEEDS - a nonlinear fully deformable registration method
 - FLIRT/MCFLIRT - a linear affine/rigid body registration method - requires an FSL installation
 - FNIRT a nonlinear registration method from FSL

Additional packages may be required to support these methods - you will need to install 
``quantiphyse_deeds`` for the first, while ``quantiphyse_fsl`` package plus a working FSL
installation are required for the second and third.

Registration mode
-----------------

The registration mode selects between registration and motion correction mode. The difference between
the two is that:

 - In motion correction mode the reference data is derived from the registration data
 - In motion correction mode only 4D data may be registered
 - In motion correction mode it is not possible to apply the transformation to other data sets
   (because there are multiple transformations, one for each 4D volume!)

Registration methods may choose to implement motion correction differently to registration, for 
example in the latter they might constrain the degree of change to physically plausible movements,
or they might skip early rough optimisation steps since motion correction data is usually at least
close to the reference data. In the case of ``FLIRT/MCFLIRT``, ``MCFLIRT`` is the motion
correction variant of the same basic registration method.

Registration data
-----------------

This is the data you wish to align with another data set or motion correct. It may be 3D or
4D - if it is 4D, each individual volume is registered with the reference data separately.

Reference data
--------------

This is the data set the output should align with. It must be 3D, hence if a 4D data set is 
chosen, a 3D ``Reference Volume`` must be selected from it. Options are:

 - Middle (median) volume
 - Mean of all volumes
 - Specified volume index

For motion correction, the reference data is the same as the 4D registration data however a 
specific reference volume must be chosen as above.

Output space
------------

The output of registration may be generated in one of three ways:

 - ``Reference``, i.e. at the resolution and field of view of the reference data This is 
   the default for most registration methods, e.g. if we register a low-resolution functional
   MRI image to a high-resolution structural image we normally expect output at the structural
   resolution.
 - ``Registration``, i.e. the same space of the original registration data. This may be 
   implemented by resampling the output in reference space onto the reference space.
 - ``Transformed`` - This is only available for linear registration methods on 3D data, and 
   causes the output voxel data to be completely unchanged, however the voxel->world transformation
   matrix is updated to align with the reference data. This can be useful as it avoids any 
   resampling or interpolation of the data, however bear in mind that any volumetric processing
   of the data alongside other data sets may require the resampling to be done anyway to ensure
   all data is defined on the same grid. In general use of this option followed by a resampling
   onto the reference or registration image data grid is equivalent to the first two methods. 
   
Not all registration methods may support all output space options.

Output name
-----------

A custom output name may be selected for the registered/motion corrected data set.

Apply transformation to other data sets
---------------------------------------

If selected, this is a list of other data sets which the same transformation should be applied to.
Note that these data sets are *not* used in the registration process itself. A common use case
for this is when an ROI has been drawn on a data set and it is necessary to align the data set
with another. In this case, the ROI can be selected as an additional data set and the transformed
ROI will align with the transformed data set.

Save Transformation
-------------------

If selected, the resulting transformation will be saved under the specified name. 
There are two possible types of transformation:

 - Image transformations where the output is an image data set. This is most common for non-linear
   registration methods (i.e. a warp field)

 - Transformations defined by a linear transformation matrix These are stored
   as Extra objects.

Saved transformations can be written to files and applied to other data sets using 
*Registration -> Apply Transform* widget. The method used to derive a transformation is stored 
as metadata within the transformation since in general the transformation can only be applied 
by the same method it was created by - e.g. you can't take the output warp field from ``FNIRT``
and use it with the ``DEEDS`` method.

Registration method options
---------------------------

Each registration method has its own set of options which are available when it is selected.
