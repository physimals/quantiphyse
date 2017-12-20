# To Do list

## Issue tracker

Current issues can be viewed on the GitLab issue tracker(https://ibme-gitcvs.eng.ox.ac.uk/quantiphyse/quantiphyse/issues)

## Future plans

This is a rough indication of future plans which are not yet specific enough to be added as issues

 - MoCo/Registration
   - Definitely want Bartek's MC method
   - More registration/motion correction options, could add FNIRT based option

 - Add Jola's texture analysis which sounds cool, whatever it is

 - PK modelling validation
   - QIBA in progress
   - QIN

 - Simplify Fabber interface
   - possible model-specific widgets?
   - ASL/CEST in progress

 - Improve memory usage by swapping out data which are not being displayed?

 - All widgets which process within ROI should work with the subimage within the bounding box of the
   ROI, not the whole image. 
    - Supervoxels does this already with great performance improvement.

 - Unified batch processing language to allow all analysis to be run in batch on multiple cases 
   - Most GUI tools now use the new Process system so they are available in batch

 - Package/plugin system
   - Has been sketched out, Fabber tools are implemented as a package as a test case

 - Support other file formats using NIBABEL.
   - DICOM conversion included where DCMSTACK is available

 - Generic maths/processing widget to do things like add/subtract data. Very easy with numpy. 
   - Basic version exists, could be improved

 - Add semiquantitative DCE-MRI measures
   - Area under the curve
   - Enhancing fraction

### Migration to PySide2 when released.

 - The current implementation uses PySide which is based on Qt4
 - Update to PySide2 when released which uses Qt5
 - Will provide support for HiDPI screens and proper scaling in OSx

### Supporting data which is not defined on the same voxel grid

This is fairly standard in *viewing* software, e.g. FSLVIEW, and would typically use the affine transform
in the Nifti file to reorient to standard RAS space, or leave one file in its own space and re-orient 
everything else to that space. This can be done by the viewer although slice views might need interpolation.

This is a bit more problematic for Quantiphyse as we want to be able to compare data by slices, use
multiple data in a single computation, etc. An example would be using data as an image prior
for Fabber. Some of this works on the basis that multiple data sets are defined on the same grid.

This is not a straightforward problem to solve so a likely pathway towards supporting this would be:

 - Provide interpolation methods for files not on the main data grid so that slices, etc. can be 
   extracted with the same shape as the main data
   
   - This has been implemented although 2d slices on a 3d volume will not work well

 - Migrate analysis tools to use interpolation methods. Issues might arise with data which is oriented
   similarly to the main data but at a different resolution. Slice averages in this case might be
   well-defined without interpolation, and the results with interpolation might be different. Possibly
   need a method for extraction a slice which optionally allows the resolution to diverge from the
   main data (but not the orientation).

   - Analysis tools currently use interpolated data only on the same grid as the main data

 - Modify image viewer to use original raw data at full resolution and in appropriate orientation

   - Probably use QT built in affine transformation classes


