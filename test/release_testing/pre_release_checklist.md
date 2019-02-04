# Quantiphyse pre-release test checklist

This is an attempt to document steps to go through prior to each release.
It isn't exhaustive, but it is intended to cover the basics so no obvious
bugs go out to release.

Release procedure is to copy this file into a directory for each release
e.g. 0.6. Each check should be done on each release build (Windows, OSX, 
Linux). Then fill in the checkboxes like `[ ]` for each item 
checked *if the behaviour is acceptable!*.

In general failure on one platform is not acceptable, however minor 
platform differences can be noted.

Any comments should be recorded in the copy of the document (e.g. minor
issues or observations). If bugs are
found, a comment should be added with the issue number. *If the bug is a release
blocker, the checkboxe should not be ticked until the bug is
fixed and the comment removed*. If the bug is not a blocker the checkbox can be
ticked and the comment remains.

## Target release

> Release version being tested

## Test build / system

> Fill in with the platform and distribution the test was done against

## General checks

Should do these last, tick to indicate that you have been doing the checks and
not found any problems.

- [ ] All dialogs, check cancel really does Cancel
- [ ] Check console for errors - should be none
- [ ] Test widgets fail gracefully without a volume and/or overlay/roi as required
- [ ] No visible GUI artifacts

## Basic volume viewing

- [ ] Load volume, ROI and overlay
  - [ ] From menu
  - [ ] From drag/drop
  - [ ] From command line
- [ ] Verify view against previous release.
- [ ] different resolution data (e.g. asl vs struc)
- [ ] Check crosshair position on click in all windows
- [ ] Check pan/zoom in normal and maximised mode
- [ ] Check double click to maximise and then minimise, windows in consistent grid
- [ ] Check space and time sliders consistent with previous version
- [ ] Load second overlay, check switching
- [ ] Load second ROI, check switching
- [ ] Clear all data, load replacement data set check range handled correctly
- [ ] Load large volume / overlay / roi to check large file handling on 64 bit system

### Notes

Issue #103: Load Data/ROI from menu are completely equivalent and show the same image selection box
Issue #69: Crosshairs sometimes ugly and some artifacts on OSX at high zoom levels

## Colour Histogram

- [ ] Check histogram modifies view for overlay and volume

## Value at voxel 

- [ ] Value of main data, ROI and overlay updates on click, respects voxel boundaries

## View options

- [ ] Relative position of overlay/ROI

## Overlay view options

- [ ] Change levels, updates view and histogram
- [ ] Automatic levels as percentile, check 100%, 90% within/without ROI
- [ ] Check handling of out of range values above/below 
- [ ] Colourmap selector updates histogram and view

Issue #104: Automatic levels within ROI does not seem to make difference

## ROI view options

- [ ] Shaded, contour, both and None working
- [ ] Alpha slider fast and working

## Data statistics widget

- [ ] Check show/hide/recalculate without ROI, without overlay
- [ ] Check overlay with single region ROI
- [ ] Check histogram range and bins
- [ ] Change to multi-region ROI, check recalculate

Issue #69: Histogram and radial profile not working on OSX - not blocker

## Voxel analysis widget

- [ ] Without 4D data - no curves
- [ ] With 4D data - check curves consistent colours
- [ ] Turn on/off curves 
- [ ] 3D Data values correct and update on click
- [ ] RMS comparison 
- [ ] Normalise frames changes plot (hard to validate actual effect!)
- [ ] Temporal resolution changes when volumes scale is changed
- [ ] Residuals display correct (base data not displayed)

Legend remains after remove all data
Issue #106 Data and Residuals not working, produces error

## Multi-voxel analysis

- [ ] Signal enhancement
- [ ] Check colour changing
- [ ] Check scroll through volume with arrows
- [ ] Check arrows in all 3 windows
- [ ] Enable mean value, check consistent including colours
- [ ] Remove individual curves
- [ ] Check replot on temporal resolution change
- [ ] Check clear graph clears arrows and removes arrows

Colour defaults to red but menu says grey

## Compare data

- [ ] Compare self-self
- [ ] Compare 3D
- [ ] Compare 3D-4D
- [ ] Compare 4D
- [ ] Check sample size and warning if disable
- [ ] Check within ROI, 3D and 4D

## Simple Maths

- [ ] Subtraction of data
- [ ] Multiplication of data by constant

Grid for simple math widget not well defined and can lead to errors

## Smoothing

- [ ] 3D and 4D data
- [ ] Effect of sigma
- [ ] Output name respected

## Registration

- [ ] Run on artificial moving data - DEEDS and MCFLIRT
- [ ] Modify parameters, check effect still sensible, no errors
- [ ] Register to different volume than median
- [ ] Register two 3D volumes

## PCA widget

- [ ] Test basic 4D data
- [ ] Number of components

Needs more functionality and better test but only really a preview so far

## Clustering widget

- [ ] Check without overlay
- [ ] Check run defaults
- [ ] Check change number of clusters/modes and re-run
- [ ] Check voxel count
- [ ] Check merge regions, voxel counts consistent
- [ ] Check 4D overlay, use of PCA modes

## Supervoxels

- [ ] Run 3D
- [ ] Run 4D
- [ ] Change parameters and re-run

## ROI analysis

- [ ] Run on single-region ROI
- [ ] Run on multi-region ROI

Issue #107

## ROI builder

- [ ] Pen tool, check on each slice
- [ ] random walker, check 3D and 4D
- [ ] Eraser, check on each slice
- [ ] Rectangle, check on each slice
- [ ] Ellipse, check on each slice
- [ ] Polygon, check on each slice
- [ ] Pick region, check with multi-region ROI (e.g. supervoxels)
- [ ] Check undo
- [ ] Check current label respected
- [ ] Check ROI name respected

Issues #108: Multiple errors

## Mean in ROI widget

- [ ] Check with supervoxels and other clustering Widgets
- [ ] Confirm zero variance/range in voxel analysis

## Data inspector

- [ ] View data orientation
- [ ] Move origin, check sensible outcome
- [ ] Tweak transform, check sensible outcome

## Batch builder

- [ ] Check empty data
- [ ] Load data, check updates until modified
- [ ] Check warning on TAB
- [ ] Check warning on invalid syntax
- [ ] Cut/paste Smoothing, run, check correct
- [ ] Check reset button
- [ ] Check save

## Resample

- [ ] Check to same grid
- [ ] Check lo-hi
- [ ] Check hi-lo
- [ ] Check 4d->3d and vice versa
- [ ] Check interpolation methods

## PK modelling

- [ ] Run defaults
- [ ] Change model and re-run
- [ ] Switch between generated overlays
- [ ] Change params and re-run (estimated injection time good to vary)

## T10 map Generation

- [ ] Check loading VFA as single 4d image
- [ ] Check loading VFA as multiple 3d images
- [ ] Check edit TR and run
- [ ] Check B0 correction enable/disable
- [ ] Load AFI as single 4d or multiple 3d images
- [ ] Check edit FA and run
- [ ] Check clamping, output overlay within clamp limits

Issue #109: Various issues including error on B0 correction
