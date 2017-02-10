# PkView pre-release test checklist

This is an attempt to document steps to go through prior to each release.
It isn't exhaustive, but it is intended to cover the basics so no obvious
bugs go out to release.

Release procedure is to copy this file for all builds that are deemed to
require full test. At present it is not decided whether to test each
individual build (windows exe, windows zip, linux deb, etc..) or just one of
them. Then fill in the checkboxes like `[ ]` for each item checked.

Any comments should be recorded in the copy of the document. If bugs are
found, a comment should be added with the issue number. If the bug is a release
blocker, the relevant checkboxes should not be ticked until the bug is
fixed and the comment removed. If the bug is not a blocker the checkbox can be
ticked and the comment remains.

## Test build / system

 - Tested on OSX El Capitan 10.11.6, app bundle build

## General checks

Should do these last, tick to indicate that you have been doing the checks and
not found any problems.

- [x] All dialogs, check cancel really does Cancel

> Cancel when choosing overlay type does not work

- [x] Check console for errors - should be none

> 2017-02-10 12:33:47.306 python[1849:18307] modalSession has been exited prematurely
> - check for a reentrant call to endModalSession:
>
> Seems to be QT issue, no other effects noticed and unlikely to be fixed in QT4

- [x] Test widgets fail gracefully without a volume and/or overlay/roi as required
- [x] No visible GUI artifacts

## Basic volume viewing

- [x] Load volume, ROI and overlay
  - [x] From menu
  - [x] From drag/drop
  - [x] From command line

> Not possible using app bundle, tested on directory distribution

- [x] Verify view against previous release.
- [x] Check crosshair position on click in all windows
- [x] Check pan/zoom in normal and maximised mode
- [x] Check double click to maximise and then minimise, windows in consistent grid
- [x] Check space and time sliders consistent with previous version
- [x] Check ROI view options and alpha slider

> Issue #44 - ROI view options not quite working properly but all modes accessible

- [x] Check overlay view options and alpha slider
- [x] Load second overlay, check switching including update to Overview widget
- [x] Load second ROI, check switching including update to Overview widget

> Issue #34: 'Only in ROI' view not updated on ROI change

- [ ] Check voxel size scaling on appropriate dataset

> No appropriate dataset available, tested on other systems

- [x] Load replacement DCE, confirm all data cleared (check view, menus, lists)
- [x] Check histogram modifies view for overlay and volume

> Overlay histogram is ugly on OSX but still functional

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

## Overlay cluster widget

- [x] Check without overlay
- [x] Check run defaults with overlay
- [x] Check change number of clusters
- [x] Check voxel count
- [x] Check merge regions, voxel counts consistent

## T10 map Generation

- [ ] Check loading VFA as single 4d image
- [x] Check loading VFA as multiple 3d images
- [x] Check edit TR and run
- [x] Check B0 correction enable/disable
- [ ] Load AFI as single 4d or multiple 3d images
- [ ] Check edit FA and run
- [ ] Check smoothing, visible
- [ ] Check clamping, output overlay within clamp limits

> Issue #46: T10 modelling crash on OSX with unsuitable data
>
> No suitable data to hand to test this

## PK modelling

- [ ] Run defaults
- [ ] Change model and re-run
- [ ] Switch between generated overlays
- [ ] Change params and re-run (estimated injection time good to vary)

> No suitable data to hand to test this

## PK curve view

- [x] Without PK modelling run - just views image curves
- [ ] After PK modelling - model comparison.
- [ ] Current parameters update on click
- [ ] Normalise frames changes plot (hard to validate actual effect!)
- [ ] Temporal resolution changes x-scale on click

> No suitable data to hand to test this

## Mean values widget

- [x] Check with supervoxels and other clustering Widgets

> Does not switch to generated overlay

- [x] Confirm zero variance/range in voxel analysis

## Supervoxels

- [x] Run defaults
- [x] Change parameters and re-run

## Generate temporal animation

- [ ] Run defaults and view generated files

> Issue #47 - not working on OSX. Not blocking release


