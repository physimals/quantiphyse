Data Resampling
===============

*Widgets -> Utilities -> Resample Data*

The resampling widget enables data defined on one grid to be resampled onto the
grid of another data set. For example you might want to resample low-resolution
functional data onto a higher resolution structural image.

The tool can also be used to perform generic up/down sampling of data (e.g.
from 1mm x1mm x1mm to 2mm x 2mm x 2mm or 0.5mm x 0.5mm x 0.5mm).

Resampling data onto the grid of another data set
-------------------------------------------------

Select the data set from the first menu, then select ``On to grid from another data set``
as the resampling method. This will display a drop down list menu of other data sets.
Select the data set whose grid you want to use from this list. The interpolation order
can also be selected (nearest neighbour may be useful when resamplinig an ROI). Choose
a name for the new data set (or just use the suggested name), then click ``Resample``

.. warning::
    Resampling onto another data set's grid is done using interpolation at the voxel
    co-ordinates of the target grid. If the target grid is of lower resolution than
    the source data this is probably not appropriate as you would want to do some kind
    of averaging over the source voxels which make up a given target voxel. It may
    be better in this case to downsample the data first.

This screenshot shows some high resolution structural data being resampled onto low
resolution functional data.

.. image:: /screenshots/resample_t1.png

And here is the result:

.. image:: /screenshots/resample_t1_asl.png

Note that the field of view of the target data set is smaller and hence the resampled
data has a smaller field of view than the input.

Up/Down sampling data
---------------------

In this case select ``Upsample`` to increase the resolution, ``Downsample`` to decrease
it. The ``Factor`` is the increase or decrease factor in each dimension, e.g. choosing ``3``
for an upsampling operation would mean each 3D voxel would be replaced with 3x3x3 = 27
smaller voxels.

Selecting ``2D only`` will only performing the up/downsampling in the first two data
dimensions (normally left/right anterior/posterior). This can be useful for data where the
third dimension consists of slices at lower resolution to the first two.

Upsampling is accomplished by interpolation using the order specified. Downsampling is performed
by averaging over voxels (e.g. for 3D downsampling with a factor of 2, 2x2x2=8 voxels are averaged
to generate each output voxel.

Here is an example of the same structural image up and down sampled by a factor of 3:

.. image:: /screenshots/resample_t1_up.png

.. image:: /screenshots/resample_t1_down.png
