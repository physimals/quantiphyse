# To Do list

## Issue tracker

Current issues can be viewed on the GitLab issue tracker(https://ibme-gitcvs.eng.ox.ac.uk/biomedia-perfusion/PkView/issues)

## Future plans

This is a rough indication of future plans which are not yet specific enough to be added as issues

 - More registration/motion correction options. MCFLIRT is linear only, could add FNIRT based option
   for nonlinear registration or integrate MIND/DEEDS
 - PK modelling validation is in progress against QIN and QIBA test data sets
 - ROI builder widget for putting together simple ROIs
 - Improve memory usage by swapping out overlays which are not being displayed
 - All widgets which process within ROI should work with the subimage within the bounding box of the
   ROI, not the whole image. Supervoxels does this already with great performance improvement.
 - Unified batch processing language to allow all analysis to be run in batch on multiple cases
 - Support other file formats using NIBABEL.
 - Include DICOM conversion
 - Generic maths/processing widget to do things like add/subtract overlays. Very easy with numpy.

### 6) Migration to PySide2 when released.
- The current implementation uses PySide which is based on Qt4
- Update to PySide2 when released which uses Qt5
- Will provide support for HiDPI screens and proper scaling in OSx

### 7) Add semiquantitative DCE-MRI measures
- Area under the curve
- Enhancing fraction

### 8) Support Jola with addition of a texture analysis widget
