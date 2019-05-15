# Quantiphyse

Viewer and data processing for 3D/4D medical imaging data

## Overview

Quantiphyse provides tools for modelling and analysis of 3D/4D volumetric data, principally MRI data. 

Core features:
- Loading/Saving 3D/4D NIFTI files
- Analysis tools including single/multiple voxel analysis and data comparison
- Generic processing including smoothing, resampling, clustering

Features available via plugins
- Registration, motion correction
- Modelling tools for DCE, ASL, DSC and CEST MRI
- Integration of selected FSL tools

See: [http://quantiphyse.readthedocs.org/en/latest/](http://quantiphyse.readthedocs.org/en/latest/) for full documentation.

## License

Quantiphyse is available free under an academic (non-commercial) license. See the `LICENSE` file for
full details, and contact [OUI](https://process.innovation.ox.ac.uk/software) if interested in 
commercial licensing.

## Installation

See https://quantiphyse.readthedocs.io/en/latest/basics/install.html for current installation
instructions

### Running from source code (for developers)

Running from source is recommended only if your are interested in developing the software further.

1. Install the dependencies:

The list of Python dependencies is in `requirements.txt`

For example:

    pip install -r requirements.txt

2. Build extensions

`python setup.py build_ext --inplace`

3. Run from source directory

`python qp.py`

### Packaging

The scripts packaging/build.py is used to build a frozen distribution package in the form of a compressed archive (`tar.gz` or `.zip`) 
and a platform-dependent package (`deb`, `msi` or `dpg`). It should run autonomously, however you may need to input the sudo password 
on Linux in order to build a `deb` package. 

The `--snapshot` option removes the version number from package filenames so you can provided them for download without having to change the link URLs.

The `--maxi` option builds a package which includes selected plugins, assuming these are downloaded

## To Do list

### Issue tracker

Current issues can be viewed on the GitHub issue tracker (https://github.com/ibme-qubic/quantiphyse/issues)

### Roadmap

#### v0.6 (Released June 2018)

 - ASL tools first version (preprocess, model fit, calibration, multiphase)
 - Improved viewer (full resolution, aligned)

#### v0.8 (Target Mar 2019)

 - Integration of selected FSL tools (FLIRT, FAST, BET, FSL_ANAT?)      DONE
 - Improved registration support (apply transform)                      DONE
 - Improved ASL tools based on oxasl (inc. ENABLE, VEASL, DEBLUR)       DONE
 - Fabber T1                                                            DONE
 - Fabber DCE                                                           DONE
 - DSC widget                                                           DONE
 - Improvements to ROI builder - working 'paint' tool                   DONE
 - Motion simulation                                                    DONE
 - Add noise                                                            DONE

#### v1.0 (Target June 2019)

 - Stable interface for QpWidget, QpData, Process
 - Python 3                                                             DONE needs testing
 - Support PySide and PySide2 - ideally the latter by default           pyside2 branch needs testing
 - Improved manual data alignment tools                                 PART DONE
 - Otherwise no firm plans yet - selection from 'Vague plans' below

### Migration to PySide2

 - The current implementation uses PySide which is based on Qt4
 - Update to PySide2 when released which uses Qt5
 - Will provide support for HiDPI screens and proper scaling in OSx
 - PyQtgraph is currently the stumbling block as release version does not support Pyside2
 - Current git version has PySide2 modifications but not yet tested
 - Consider move to VisPy if this does not come to fruition

#### Vague Plans for Future

 - Refactoring of view classes
   - This is a mess at the moment. Need all view options to be stored as metadata
     and cleaner separation between the ImageView widget and the individual OrthoView
     widgets.

 - MoCo/Registration
   - Bartek's MC method

 - 3D view
   - Probably not that useful but fun and may be easy(?) with vispy. Reliant on good refactoring of ImageView
   - Application to surfaces (Tom K?)

 - Add Jola's texture analysis which sounds cool, whatever it is

 - PK modelling validation
   - QIBA in progress
   - QIN

 - Simplify/rewrite generic Fabber interface

 - Improve memory usage by swapping out data which are not being displayed?

 - All widgets which process within ROI should work with the subimage within the bounding box of the
   ROI, not the whole image. 
    - Supervoxels does this already with great performance improvement.

 - Support other file formats using NIBABEL.
   - DICOM conversion included where DCMSTACK is available

 - Add semiquantitative measures
   - Area under the curve
   - Enhancing fraction

 - Simulation tools
   - Fabber test data
   - 'Simulated brain'
