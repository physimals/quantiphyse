# To Do list

## Issue tracker

Current issues can be viewed on the GitLab issue tracker(https://ibme-gitcvs.eng.ox.ac.uk/biomedia-perfusion/PkView/issues)

## Future plans

This is a rough indication of future plans which are not yet specific enough to be added as issues

 - MoCo/Registration
   - Definitely want Bartek's MC method
   - More registration/motion correction options, could add FNIRT based option, MIND

 - Add Jola's texture analysis which sounds cool, whatever it is

 - PK modelling validation
   - QIBA in progress
   - QIN

 - ROI builder widget for putting together simple ROIs
   - In progress

 - Simplify Fabber interface
   - possible model-specific widgets?

 - Improve memory usage by swapping out overlays which are not being displayed?

 - All widgets which process within ROI should work with the subimage within the bounding box of the
   ROI, not the whole image. 
    - Supervoxels does this already with great performance improvement.

 - Unified batch processing language to allow all analysis to be run in batch on multiple cases 
   - In progress
   - Most GUI tools now use the new Process system so they are available in batch

 - Support other file formats using NIBABEL.
   - DICOM conversion in progress

 - Generic maths/processing widget to do things like add/subtract overlays. Very easy with numpy. 
   - In progress

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
multiple overlays in a single computation, etc. An example would be using an overlay as an image prior
for Fabber. Some of this works on the basis that multiple data sets are defined on the same grid.

This is not a straightforward problem to solve so a likely pathway towards supporting this would be:

 - Display files which do not match the main data grid, but do not allow them to be used in analysis / computation
 - Provide interpolation methods for files not on the main data grid so that slices, etc. can be 
   extracted with the same shape as the main data
 - Migrate analysis tools to use interpolation methods. Issues might arise with data which is oriented
   similarly to the main data but at a different resolution. Slice averages in this case might be
   well-defined without interpolation, and the results with interpolation might be different. Possibly
   need a method for extraction a slice which optionally allows the resolution to diverge from the
   main data (but not the orientation).

