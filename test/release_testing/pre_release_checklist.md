# Quantiphyse pre-release test checklist

This document records testing of a Quantiphyse release.

Each widget needs to be individually tested and either passed or
failed. In addition there are a set of generic non-widget specific tests.

Observations or minor non-blocking issues can be recorded in the 'Notes'
section. This may include references to bugs which do not need to be 
fixed prior to release.

Release blocking issues should be raised as bugs and listed in the
'Blockers' section. The widget cannot pass while blocking issues exist.

In general failure on one platform is not acceptable, however minor 
platform differences and limitations can be noted.

## Example of a widget test

### Coffee making widget - FAIL

#### Notes

 - A bit too much sugar for my taste
 - Issue #1234: Does not remember users preferred blend

#### Blocking issues

 - Issue #1452: Error when coffee jar is empty
 - Issue #9876: Water is cold

## Release procedure

Release procedure is to copy this file into a directory for each release
e.g. 0.6. Each check should be done on each release build (Windows, OSX, 
Linux). 

## Target release

v0.8

## Test build / system

Simultaneous test on Windows 7, Ubuntu 18.04, OSX Mojave 10.14.1

## General checks

Should do these last, tick to indicate that you have been doing the checks and
not found any problems.

- [ ] Check for errors or output on console
- [ ] Check for visible GUI artifacts
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
- [ ] Value of main data, ROI and overlay updates on click, respects voxel boundaries
- [ ] Relative position of overlay/ROI
- [ ] Change levels, updates view and histogram
- [ ] Automatic levels as percentile, check 100%, 90% within/without ROI
- [ ] Check handling of out of range values above/below 
- [ ] Colourmap selector updates histogram and view
- [ ] Shaded, contour, both and None working
- [ ] Alpha slider fast and working

## Widget checks

### Data statistics

### Histogram

### Radial profile

### Voxel analysis

### Multi-voxel analysis

### Compare data

### Measurement

### Simple Maths

### Smoothing

### PCA

### Clustering

### Supervoxels

### ROI analysis

### Mean in ROI

### ROI builder

### Orient data

### Resample

### Mean in ROI

### Registration / Apply Transform

### Batch builder

### Add Noise

### Simulate Motion

### ASL Preprocess

### Multiphase ASL

### ASL pipeline

### CEST

### DCE

### Bayesian DCE

### DSC

### T1

### Fabber T1

### Fabber

### Simulated Fabber Data

## Batch examples

- [ ] Calculate volumes
- [ ] CEST
- [ ] Clustering
- [ ] DSC
- [ ] ENABLE
- [ ] Fabber
- [ ] Mean values
- [ ] Moco DEEDS
- [ ] Moco MCFLIRT
- [ ] Multiphase ASL
- [ ] Multiple cases
- [ ] OXASL
- [ ] Pipeline
- [ ] PK preclinical
- [ ] PK clinical
- [ ] Reg DEEDS
- [ ] Reg FLIRT NOT YET IMPLEMENTED
- [ ] Reg FNIRT NOT YET IMPLEMENTED
- [ ] Resampling
- [ ] Save
- [ ] Simple maths
- [ ] Summary stats
- [ ] Supervoxels
- [ ] T10 clinical
- [ ] T10 preclinical
- [ ] Fabber T1 NOT YET IMPLEMENTED

