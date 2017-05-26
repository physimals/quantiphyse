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
