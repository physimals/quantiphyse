# Quantiphyse pre-release test checklist

This is an attempt to document steps to go through prior to each release.
It isn't exhaustive, but it is intended to cover the basics so no obvious
bugs go out to release.

Release procedure is to copy this file for all builds that are deemed to
require full test. At present this is the 'maxi' package for each platform
(Windows, Linux, OSX). Then fill in the checkboxes like `[x]` for each item 
checked *if the behaviour is acceptable!*.

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
- [ ] Check crosshair position on click in all windows
- [ ] Check pan/zoom in normal and maximised mode
- [ ] Check double click to maximise and then minimise, windows in consistent grid
- [ ] Check space and time sliders consistent with previous version
- [ ] Load second overlay, check switching including update to Overview widget
- [ ] Load second ROI, check switching including update to Overview widget
- [ ] Clear all data, load replacement data set check range handled correctly
- [ ] Load large volume / overlay / roi to check large file handling on 64 bit system

## Colour Histogram

- [ ] Check histogram modifies view for overlay and volume

## View options

- [ ] Relative position of overlay/ROI
- [ ] Check voxel size scaling on appropriate dataset

## Overlay view options

- [ ] Change levels, updates view and histogram
- [ ] Automatic levels as percentile, check 100%, 90% within/without ROI
- [ ] Check handling of out of range values above/below 
- [ ] Colourmap selector updates histogram and view

## ROI view options

- [ ] Shaded, contour, both and None working
- [ ] Alpha slider fast and working

## Data statistics widget

- [ ] Check show/hide/recalculate without ROI, without overlay
- [ ] Check overlay with single region ROI
- [ ] Check histogram range and bins
- [ ] Change to multi-region ROI, check recalculate

## Clustering widget

- [ ] Check without overlay
- [ ] Check run defaults
- [ ] Check change number of clusters/modes and re-run
- [ ] Check voxel count
- [ ] Check merge regions, voxel counts consistent
- [ ] Check AutoMerge?
- [ ] Check 4D overlay, use of PCA modes

## 4D data analysis widget

- [ ] Check default to single click select giving signal enhancement curve
- [ ] Check smoothing, signal enhancement checkboxes
- [ ] Check colour changing
- [ ] Enable multiple plots, check arrows, colour changing
- [ ] Check scroll through volume with arrows
- [ ] Check arrows in all 3 windows
- [ ] Enable mean value, check consistent including colours
- [ ] Check replot on temporal resolution change
- [ ] Check clear graph clears arrows and removes arrows
- [ ] Check switch back to single plotting

## Model curves view

- [ ] Without 4D data - no curves
- [ ] With 4D data - check curves consistent colours
- [ ] Turn on/off curves 
- [ ] 3D Data values correct and update on click
- [ ] RMS comparison 
- [ ] Normalise frames changes plot (hard to validate actual effect!)
- [ ] Temporal resolution changes when volumes scale is changed
- [ ] Residuals display correct (base data not displayed)

## Compare data

- [ ] Compare 3D
- [ ] Compare 3D-4D
- [ ] Compare 4D
- [ ] Check sample size and warning if disable
- [ ] Check within ROI, 3D and 4D

## Mean values widget

- [ ] Check with supervoxels and other clustering Widgets
- [ ] Confirm zero variance/range in voxel analysis

## Supervoxels

- [ ] Run defaults
- [ ] Change parameters and re-run

## PK modelling

- [ ] Run defaults
- [ ] Change model and re-run
- [ ] Switch between generated overlays
- [ ] Change params and re-run (estimated injection time good to vary)

## Simple Maths

- [ ] Subtraction of data
- [ ] Multiplication of data by constant

## Smoothing

- [ ] 3D and 4D data
- [ ] Effect of sigma
- [ ] Output name respected

## T10 map Generation

- [ ] Check loading VFA as single 4d image
- [ ] Check loading VFA as multiple 3d images
- [ ] Check edit TR and run
- [ ] Check B0 correction enable/disable
- [ ] Load AFI as single 4d or multiple 3d images
- [ ] Check edit FA and run
- [ ] Check smoothing, visible
- [ ] Check clamping, output overlay within clamp limits

## Registration

- [ ] Run on artificial moving data - DEEDS and MCFLIRT
- [ ] Modify parameters, check effect still sensible, no errors
- [ ] Register to different volume than median
- [ ] Register two 3D volumes

## ROI analysis

- [ ] Run on single-region ROI
- [ ] Run on multi-region ROI

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

## Data inspector

- [ ] View data orientation
- [ ] Move origin, check sensible outcome
- [ ] Tweak transform, check sensible outcome

## Batch builder

- [ ] Check empty data
- [ ] Load data, check updates until modified
- [ ] Check warning on TAB
- [ ] Check warning on invalid syntax
- [ ] Cut/paste Fabber, run, check correct
- [ ] Check reset button

