Simulate Motion
---------------

*Widgets -> Simulation -> Simulate Motion*

This widget simulates random motion in a 4D data set. It may be useful for testing algorithms for 
motion correction, however the motion simulated may not be particularly realistic as it is uncorrelated
and occurs randomly in all dimensions. In practice, real motion is often more prevalent in certain 
directions than others, and may well be correlated from one time point to another (e.g. a patient
may manage to stay still for most of a long scan but then find it difficult to avoid motion the
longer it goes on.

.. image:: /screenshots/motion.png

``Motion standard deviation`` is the std.dev of the Gaussian which is used to generate random movement
in each dimension. ``Padding`` adds extra voxels to the edge of the data so that motion can occur beyond
the edges of the data without losing voxels. Both are specified in mm and are converted to voxels using
the data voxel->world transformation matrix.

