

# Feature Summary

A list of PKView features and their current status. Detailed explanation can be found 
in the [Pkview documents](http://pkview.readthedocs.io/en/latest/).

## Visualisation

 - Axial, coronal and sagittal views
 - ROI overlay
 - Overlay maps for the entire image or constrained to the ROI
 - Switching between multiple overlays
 - Dynamic signal enhancment visualisation
 - individual voxel curve analysis
 - Multivoxel curve analysis
 
## IO

- Load DCE-MRI, ROI and overlays
- Save overlays as 3D images

## Modelling
- PK modelling of clinical and preclinical DCE-MRI 
(*this implementation still requires testing*)
- Command line batch T10 and PK modelling 
(*T1 modelling should be implemented as a widget as well*)
- Visualisation of model fit

## Analysis
=======
## Analysis
- Region map statistics
- PCA based curve clustering
- Overlay clustering

# Wishlist
Wishlist of things to implement

### Multiple ROIs
- Switch between mutiple ROIs in the same way that you can switch between multiple
overlays (see fig)
- (enhancement) Make certain outputs such as clustering an ROI instead of an overlay
so that it can be used for regional analysis

<img src="images/feat/mult_roi.jpg">

### Supervoxel extraction
### Histogram analysis of ROI
### T1 widget
### Test PK modelling and T10 modelling   
- Dataset for testing purposes

### Migration of PySide2 when released.

# Publications

Publications linked to this work
