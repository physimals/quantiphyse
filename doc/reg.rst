Registration and Motion Correction
==================================

*Widgets -> Processing -> Registration*

This widget enables registration and motion correction using various methods. Currently implemented methods 
are:

 - DEEDS - a nonlinear fully deformable registration method
 - FLIRT/MCFLIRT - a linear affine/rigid body registration method - requires an FSL installation

Not all methods may be included in all builds.

Registration mode
-----------------

The registration mode selects between registration and motion correction mode. The difference between
the two is that:

 - In motion correction mode the reference data is derived from the registration data
 - In motion correction mode only 4D data may be registered
 - In motion correction mode it is not possible to apply the transformation to other data sets

Registration methods may choose to implement motion correction differently to registration, for 
example they might constrain the degree of change to physically plausible movements.

Registration data
-----------------

This is the data you wish to align with another data set (the *reference* data). It may be 3D or
4D - if it is 4D, each individual volume is registered with the reference data separately.

Reference data
--------------

This is the data set the output should align with. It must be 3D, hence if a 4D data set is 
chosen, some method is required to reduce it to 3D. Options are:

 - Middle (median) volume
 - Mean of all volumes
 - Specified volume index

Output data space
-----------------

The output of registration may be generated in one of three ways:

 - In reference space, i.e. at the resolution and field of view of the reference data
 - In registration space, i.e. the same space of the original registration data
 - In a transformed space derived from the registration data and the transformation. This 
   is normally available only for rigid body registration methods where it enables the output
   transformation to be applied directly to the voxel->world data set transformation. This
   means no interpolation is necessary on the output data.

Not all registration methods may support all output space options.

Apply transform to other data sets
----------------------------------

This applies the registration transformation to another data set, which normally should be in
the same data space as the registration data. A common use of this is to align a region
of interest defined on some data set with another data set.

New data name
-------------

The registered data can be saved under a specified name, or can be set to replace the original data.

Registration method options
---------------------------

Each registration method has its own set of options which are available when it is selected.

Save transformation
-------------------

If selected, the resulting transformation will be saved. There are two possible types of transformation:

 - Image transformations where the output is an image data set. This is most common for non-linear
   registration methods (i.e. a warp field)

 - Transformations defined by some other data structure, e.g. an affine matrix. These are stored
   as Extra objects.

Saved transformations can be written to files and applied to other data sets using 'Apply Transform'
mode. The method used to derive a transformation is stored as metadata within the transformation since 
in general the transformation can only be applied by the same method it was created by.
