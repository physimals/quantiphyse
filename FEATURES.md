

# Feature Summary

A list of PKView features and their current status. Detailed explanations of the current features can be found 
in the [Pkview documents](http://pkview.readthedocs.io/en/latest/).

Most importantly a wishlist of features to implement before release can be found in the [Wishlist](# Wishlist) section below.

!["pkview"](images/feat/pkview.jpg)


## Visualisation

 - Axial, coronal and sagittal linked views
 - ROI overlay
 - Overlay maps for the entire image or constrained to the ROI
 - Switching between multiple overlays
 - Dynamic signal enhancment visualisation
 - individual voxel curve analysis
 - Multivoxel curve analysis
 - Contrast and brightness adjustment
 - Zooming using right mouse button
 - Scrolling through volume using mouse wheel
 - Exporting a window as a jpg or a number of other image formats
 
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

### 1) Multiple ROIs

- Switch between mutiple ROIs in the same way that you can switch between multiple
overlays (see fig)
  - Make certain outputs such as clustering an ROI instead of an overlay
so that it can be used for regional analysis without having to save the output and reload as an ROI

!["mult roi"](images/feat/mult_roi.jpg)

### 2) Supervoxel extraction
- Add a widget for the Perfusion supervoxel method
- My source code and demo is available at: https://github.com/benjaminirving/perfusion-slic
- This is a preprocessing step but useful to implement as a demo of the method

### 3) Histogram analysis of ROI
- Add a regional histogram option in the **overlay options** widget
- Provide options to set number of bins and range so that comparisons can be made between cases
- This would be really useful for Tessa and Helen's work on the Rhythm and Perform trials.
- Under the current overlay statistics

!["overlay statistics"](images/feat/overlay_statistics.jpg)


### 4) T1 widget
- Create a T1 widget that generates a T1 map from a series of variable flip angle images
- The code is implemented in PKView for command line use and should also be integrated as a widget
- The current command line version passes a yaml configuration file as an argument
- There are two versions:
*1) T1 with actual flip angle caclulation (preclinical)*
```
PKView --T10afibatch eg3_t10config_preclinical.yaml
```

*2) T1 without actual flip angle (clinical)*
```
PKView --T10afibatch eg2_t10config_clinical.yaml
```
- These yaml arguments provide a template to implement a widget
- Code:  
		- Python wrapper code is found in `pkview/analysis`  
		- c++ analysis code is found in `src/`  

### 5) Testing of PK modelling and T10 modelling   
- The PK and T10 modelling in the widget require further testing (Ben TODO)
- Steps
		- Include example publicly available test dataset
		- Include automated c++ (googletest) tests for the code to validation

### 6) Migration to PySide2 when released.
- The current implementation uses PySide which is based on Qt4
- Update to PySide2 when released which uses Qt5
- Will provide support for HiDPI screens and proper scaling in OSx

### 7) Add semiquantitative DCE-MRI measures
- Area under the curve
- Enhancing fraction

### 8) Support Jola with addition of a texture analysis widget

# Release roadmap
...

# Publications

Publications linked to this work:
To add
