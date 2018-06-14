# To Do list

## Issue tracker

Current issues can be viewed on the GitLab issue tracker(https://ibme-gitcvs.eng.ox.ac.uk/quantiphyse/quantiphyse/issues)

## Roadmap

### v0.6 (June 2018)

 - ASL tools first version (preprocess, model fit, calibration, multiphase)
 - Improved viewer (full resolution, aligned)

### v0.8 (July/August 2018)

 - Integration of selected FSL tools
 - Improved manual data alignment tools
 - Improved registration support (apply transform)
 - ENABLE
 - Fabber T1 (integrate with/replace existing T1 widget?)
 - Fabber DCE (integrate with/replace existing DCE widget)

### Vague Plans for Future

 - MoCo/Registration
   - Definitely want Bartek's MC method
   - Revise interface to allow for MC and registration to be treated separately (MCFLIRT/FLIRT) (or not)
   - Standard way to save the transformation (matrix or warp map)
   - Could add FNIRT based option

 - 3D view
   - Probably not that useful but fun and easy(?) with vispy

 - Add Jola's texture analysis which sounds cool, whatever it is

 - PK modelling validation
   - QIBA in progress
   - QIN

 - Simplify/rewrite generic Fabber interface

 - Improve memory usage by swapping out data which are not being displayed?

 - All widgets which process within ROI should work with the subimage within the bounding box of the
   ROI, not the whole image. 
    - Supervoxels does this already with great performance improvement.

 - Improve batch processing unification
   - Most GUI tools now use the new Process system so they are available in batch

 - Support other file formats using NIBABEL.
   - DICOM conversion included where DCMSTACK is available

 - Improve /rethink generic maths/processing widget / console
   - Need to link data grids with data 

 - Add semiquantitative DCE-MRI measures
   - Area under the curve
   - Enhancing fraction

## Migration to PySide2

 - The current implementation uses PySide which is based on Qt4
 - Update to PySide2 when released which uses Qt5
 - Will provide support for HiDPI screens and proper scaling in OSx
 - PyQtgraph is currently the stumbling block as release version does not support Pyside2
 - Current git version has PySide2 modifications but not yet tested
 - Consider move to VisPy if this does not come to fruition


