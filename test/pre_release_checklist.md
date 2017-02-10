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
- [ ] Check ROI view options and alpha slider
- [ ] Check overlay view options and alpha slider
- [ ] Load second overlay, check switching including update to Overview widget
- [ ] Load second ROI, check switching including update to Overview widget
- [ ] Check voxel size scaling on appropriate dataset
- [ ] Load replacement DCE, confirm all data cleared (check view, menus, lists)
- [ ] Check histogram modifies view for overlay and volume
- [ ] Load large volume / overlay / roi to check large file handling on 64 bit system

## Voxel analysis widget

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

## Overlay statistics widget

- [ ] Check show/hide/recalculate without ROI, without overlay
- [ ] Check overlay with single region ROI
- [ ] Check histogram range and bins
- [ ] Change to multi-region ROI, check recalculate

## Curve cluster widget

- [ ] Check run defaults
- [ ] Check change number of clusters/modes and re-run
- [ ] Check voxel count
- [ ] Check merge regions, voxel counts consistent
- [ ] Check AutoMerge?

## Overlay cluster widget

- [ ] Check without overlay
- [ ] Check run defaults with overlay
- [ ] Check change number of clusters
- [ ] Check voxel count
- [ ] Check merge regions, voxel counts consistent

## T10 map Generation

- [ ] Check loading VFA as single 4d image
- [ ] Check loading VFA as multiple 3d images
- [ ] Check edit TR and run
- [ ] Check B0 correction enable/disable
- [ ] Load AFI as single 4d or multiple 3d images
- [ ] Check edit FA and run
- [ ] Check smoothing, visible
- [ ] Check clamping, output overlay within clamp limits

## PK modelling

- [ ] Run defaults
- [ ] Change model and re-run
- [ ] Switch between generated overlays
- [ ] Change params and re-run (estimated injection time good to vary)

## PK curve view

- [ ] Without PK modelling run - just views image curves
- [ ] After PK modelling - model comparison.
- [ ] Current parameters update on click
- [ ] Normalise frames changes plot (hard to validate actual effect!)
- [ ] Temporal resolution changes x-scale on click

## Mean values widget

- [ ] Check with supervoxels and other clustering Widgets
- [ ] Confirm zero variance/range in voxel analysis

## Supervoxels

- [ ] Run defaults
- [ ] Change parameters and re-run

## Generate temporal animation

- [ ] Run defaults and view generated files
