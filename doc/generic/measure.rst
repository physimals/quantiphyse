Measurement tool
================

*Widgets -> Visualisation -> Measurements*

The measurement tool is a simple utility for measuring distances and angles in 3D space.

.. image:: /screenshots/measure.png

Measuring distances
-------------------

Click the ``Measure Distance`` button and then select two points by consecutive clicks
in the viewer. The points do not need to be selected in the same viewing window. The
distance between the points will be displayed.

Distance is calculated using the voxel to world transformation of the main data.

Measuring angles
----------------

Click the ``Measure Distance`` button and then select three points by consecutive clicks
in the viewer. The points do not need to be selected in the same viewing window. The
angle formed at the second selected point by lines drawn to the first and last selected
points will be displayed.

Angles are calculated using the voxel to world transformation of the main data and are
always given as <= 180 degrees.
