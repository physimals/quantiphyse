# PkView pre-release test checklist

## Basic volume viewing

* Load volume, ROI and overlay
  * From menu
  * From drag/drop
  * From command line

* Verify view against previous release. 
* Check crosshair position on click in all windows
* Check double click to maximise and then minimise
* Check space and time sliders consistent with previous version
* Check ROI view options and alpha slider
* Check overlay view options and alpha slider
* Load second overlay, check switching including update to Overview widget
* Load second ROI, check switching including update to Overview widget
* Check voxel size scaling on appropriate dataset

## Voxel analysis widget

* Check default to single click select giving signal enhancement curve
* Check smoothing, signal enhancement checkboxes
* Check colour changing
* Enable multiple plots, check arrows, colour changing
* Check scroll through volume with arrows
* Check arrows in all 3 windows
* Enable mean value, check consistent including colours
* Check replot on temporal resolution change
* Check clear graph clears arrows and removes arrows
* Check switch back to single plotting
* Change temporal resolution

## Overlay statistics widget

* Check show/hide/recalculate without ROI, without overlay
* Check overlay with single region ROI
* Check histogram range and bins
* Change to multi-region ROI, check recalculate

## Curve cluster widget

* Check run defaults
* Check change number of clusters/modes and re-run
* Check voxel count
* Check merge regions, voxel counts consistent
* Check AutoMerge?

## Overlay cluster widget

* Check without overlay
* Check run defaults with overlay
* Check change number of clusters
* Check voxel count
* Check merge regions, voxel counts consistent

