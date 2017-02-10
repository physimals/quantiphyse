# PkView pre-release test checklist

This is an attempt to document steps to go through prior to each release.
It isn't exhaustive, but it is intended to cover the basics so no obvious
bugs go out to release.

Release procedure is to copy this file for all builds that are deemed to
require full test. At present it is not decided whether to test each
individual build (windows exe, windows zip, linux deb, etc..) or just one of
them. Then fill in the checkboxes like `[x]` for each item checked *if the
behaviour is acceptable!*.

Any comments should be recorded in the copy of the document (e.g. minor
issues or observations). If bugs are
found, a comment should be added with the issue number. *If the bug is a release
blocker, the checkboxe should not be ticked until the bug is
fixed and the comment removed*. If the bug is not a blocker the checkbox can be
ticked and the comment remains.

## Target release

 - Release 0.31

## Test build / system

Windows self-contained directory ZIP distribution - tested on Windows 7, 64 bit

## General checks

Should do these last, tick to indicate that you have been doing the checks and
not found any problems.

- [x] All dialogs, check cancel really does Cancel
- [x] Check console for errors - should be none
- [x] Test widgets fail gracefully without a volume and/or overlay/roi as required
- [x] No visible GUI artifacts

## Basic volume viewing

- [x] Load volume, ROI and overlay
  - [x] From menu
  - [x] From drag/drop
  - [x] From command line
- [x] Verify view against previous release.
- [x] Check crosshair position on click in all windows
- [x] Check pan/zoom in normal and maximised mode
- [x] Check double click to maximise and then minimise, windows in consistent grid
- [x] Check space and time sliders consistent with previous version
- [x] Check ROI view options and alpha slider
- [x] Check overlay view options and alpha slider
- [x] Load second overlay, check switching including update to Overview widget

> Overlays do not remember their colourmap or view mode - not really a bug
> expected behaviour at present, but worth considering whether correct

- [x] Load second ROI, check switching including update to Overview widget
- [x] Check voxel size scaling on appropriate dataset
- [x] Load replacement DCE, confirm all data cleared (check view, menus, lists)
- [x] Check histogram modifies view for overlay and volume
- [x] Load large volume / overlay / roi to check large file handling on 64 bit system

> Slow startup for single exeutable compared to filesystem distribution

## Voxel analysis widget

- [x] Check default to single click select giving signal enhancement curve
- [x] Check smoothing, signal enhancement checkboxes
- [x] Check colour changing
- [x] Enable multiple plots, check arrows, colour changing
- [x] Check scroll through volume with arrows
- [x] Check arrows in all 3 windows
- [x] Enable mean value, check consistent including colours
- [x] Check replot on temporal resolution change
- [x] Check clear graph clears arrows and removes arrows
- [x] Check switch back to single plotting

## Overlay statistics widget

- [x] Check show/hide/recalculate without ROI, without overlay
- [x] Check overlay with single region ROI
- [x] Check histogram range and bins
- [x] Change to multi-region ROI, check recalculate

## Curve cluster widget

- [x] Check run defaults
- [x] Check change number of clusters/modes and re-run
- [x] Check voxel count
- [x] Check merge regions, voxel counts consistent
- [x] Check AutoMerge?

> Issue #49: Hang running default curve clustering on very large volume.
> Only occurs in single-exe build, so will NOT distribute this until
> fixed.

## Overlay cluster widget

- [x] Check without overlay
- [x] Check run defaults with overlay
- [x] Check change number of clusters
- [x] Check voxel count
- [x] Check merge regions, voxel counts consistent

## T10 map Generation

- [x] Check loading VFA as single 4d image
- [x] Check loading VFA as multiple 3d images
- [x] Check edit TR and run
- [x] Check B0 correction enable/disable
- [x] Load AFI as single 4d or multiple 3d images
- [x] Check edit FA and run
- [x] Check smoothing, visible
- [x] Check clamping, output overlay within clamp limits

## PK modelling

- [x] Run defaults
- [x] Change model and re-run
- [x] Switch between generated overlays
- [x] Change params and re-run (estimated injection time good to vary)

## PK curve view

- [x] Without PK modelling run - just views image curves
- [x] After PK modelling - model comparison.
- [x] Current parameters update on click
- [x] Normalise frames changes plot (hard to validate actual effect!)
- [x] Temporal resolution changes x-scale on click

## Mean values widget

- [x] Check with supervoxels and other clustering Widgets
- [x] Confirm zero variance/range in voxel analysis

## Supervoxels

- [x] Run defaults
- [x] Change parameters and re-run

## Generate temporal animation

- [ ] Run defaults and view generated files

> Issue #47 - not working on Windows either, same reason as OSX
