# Quantiphyse pre-release test checklist

## Target release

v0.6

## Test build / systems

Tested on Windows 7 x64, Linux (Ubuntu 16.04) and OSX (10.11.6)

## General checks

Should do these last, tick to indicate that you have been doing the checks and
not found any problems.

- [x] All dialogs, check cancel really does Cancel
- [x] Check console for errors - should be none
- [x] Test widgets fail gracefully without a volume and/or overlay/roi as required
- [x] No visible GUI artifacts

Issue #69: pyqtgraph artifacts on OSX

## Basic volume viewing

- [x] Load volume, ROI and overlay
  - [x] From menu
  - [x] From drag/drop
  - [x] From command line
- [x] Verify view against previous release.
- [x] different resolution data (e.g. asl vs struc)
- [x] Check crosshair position on click in all windows
- [x] Check pan/zoom in normal and maximised mode
- [x] Check double click to maximise and then minimise, windows in consistent grid
- [x] Check space and time sliders consistent with previous version
- [x] Load second overlay, check switching
- [x] Load second ROI, check switching
- [x] Clear all data, load replacement data set check range handled correctly
- [x] Load large volume / overlay / roi to check large file handling on 64 bit system

Issue #103: Load Data/ROI from menu are completely equivalent and show the same image selection box
Issue #69: Crosshairs sometimes ugly and some artifacts on OSX at high zoom levels

## Colour Histogram

- [x] Check histogram modifies view for overlay and volume

## Value at voxel 

- [x] Value of main data, ROI and overlay updates on click, respects voxel boundaries

## View options

- [x] Relative position of overlay/ROI

## Overlay view options

- [x] Change levels, updates view and histogram
- [x] Automatic levels as percentile, check 100%, 90% within/without ROI
- [x] Check handling of out of range values above/below 
- [x] Colourmap selector updates histogram and view

Issue #104: Automatic levels within ROI does not seem to make difference

## ROI view options

- [x] Shaded, contour, both and None working
- [x] Alpha slider fast and working

## Data statistics widget

- [x] Check show/hide/recalculate without ROI, without overlay
- [x] Check overlay with single region ROI
- [x] Check histogram range and bins
- [x] Change to multi-region ROI, check recalculate

Issue #69: Histogram and radial profile not working on OSX

## Voxel analysis widget

- [x] Without 4D data - no curves
- [x] With 4D data - check curves consistent colours
- [x] Turn on/off curves 
- [x] 3D Data values correct and update on click
- [x] RMS comparison 
- [x] Normalise frames changes plot (hard to validate actual effect!)
- [x] Temporal resolution changes when volumes scale is changed
- [x] Residuals display correct (base data not displayed)

Legend remains after remove all data

## Multi-voxel analysis

- [x] Signal enhancement
- [x] Check colour changing
- [x] Check scroll through volume with arrows
- [x] Check arrows in all 3 windows
- [x] Enable mean value, check consistent including colours
- [x] Remove individual curves
- [x] Check replot on temporal resolution change
- [x] Check clear graph clears arrows and removes arrows

Colour defaults to red but menu says grey

## Compare data

- [x] Compare self-self
- [x] Compare 3D
- [x] Compare 3D-4D
- [x] Compare 4D
- [x] Check sample size and warning if disable
- [x] Check within ROI, 3D and 4D

## Simple Maths

- [x] Subtraction of data
- [x] Multiplication of data by constant

Grid for simple math widget not well defined and can lead to errors

## Smoothing

- [x] 3D and 4D data
- [x] Effect of sigma
- [x] Output name respected

## Registration

- [x] Run on artificial moving data - DEEDS and MCFLIRT
- [x] Modify parameters, check effect still sensible, no errors
- [x] Register to different volume than median
- [x] Register two 3D volumes
- [x] Run MCFLIRT on ASL example

MCFLIRT performed poorly on artifical data maybe due to unrealistic distances.
When run on realistic data it looked fine.

## PCA widget

- [x] Test basic 4D data
- [x] Number of components

Needs more functionality and better test but only really a preview so far

## Clustering widget

- [x] Check without overlay
- [x] Check run defaults
- [x] Check change number of clusters/modes and re-run
- [x] Check voxel count
- [x] Check merge regions, voxel counts consistent
- [x] Check 4D overlay, use of PCA modes

## Supervoxels

- [x] Run 3D
- [x] Run 4D
- [x] Change parameters and re-run

## ROI analysis

- [x] Run on single-region ROI
- [x] Run on multi-region ROI

## ROI builder

- [x] Pen tool, check on each slice
- [x] random walker, check 3D and 4D
- [x] Eraser, check on each slice
- [x] Rectangle, check on each slice
- [x] Ellipse, check on each slice
- [x] Polygon, check on each slice
- [x] Pick region, check with multi-region ROI (e.g. supervoxels)
- [x] Check undo
- [x] Check current label respected
- [x] Check ROI name respected

Issues #108: Multiple issues. Blockers fixed

## Mean in ROI widget

- [x] Check with supervoxels and other clustering Widgets
- [x] Confirm zero variance/range in voxel analysis

## Data inspector

- [x] View data orientation
- [x] Move origin, check sensible outcome
- [x] Tweak transform, check sensible outcome

## Batch builder

- [x] Check empty data
- [x] Load data, check updates until modified
- [x] Check warning on TAB
- [x] Check warning on invalid syntax
- [x] Cut/paste Smoothing, run, check correct
- [x] Check reset button
- [x] Check save

## Resample

- [x] Check to same grid
- [x] Check lo-hi
- [x] Check hi-lo
- [x] Check 4d->3d and vice versa
- [x] Check interpolation methods

## PK modelling

- [x] Run defaults
- [x] Change model and re-run
- [x] Switch between generated overlays
- [x] Change params and re-run (estimated injection time good to vary)

## T10 map Generation

- [x] Check loading VFA as single 4d image
- [x] Check loading VFA as multiple 3d images
- [x] Check edit TR and run
- [x] Check B0 correction enable/disable
- [x] Load AFI as single 4d or multiple 3d images
- [x] Check edit FA and run
- [x] Check clamping, output overlay within clamp limits

Issue #109: Various issues - blockers fixed

## ASL tools

 - [x] Single TI preprocessing (difference, average)
 - [x] Single TI modelling
 - [x] Multi-TI preprocessing (diff, average)
 - [x] Multi-TI modelling
 - [x] Spatial option
 - [x] Voxelwise calibration (FSL course example)
 - [x] Refregion calibration (FSL course example)
 - [x] Multiphase with/without correction (JL example)

One error on OSX - can't set 'perfusion' as current data. Looked like delay in adding data
in multiple threads. Not blocker.