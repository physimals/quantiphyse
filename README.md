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

Current issues can be viewed on the GitHub issue tracker (https://github.com/physimals/quantiphyse/issues)

### Roadmap

#### v0.6 (Released June 2018)

 - ASL tools first version (preprocess, model fit, calibration, multiphase)
 - Improved viewer (full resolution, aligned)

#### v0.8 (Target Mar 2019)

 - Integration of selected FSL tools (FLIRT, FAST, BET, FSL_ANAT?)      [x]
 - Improved registration support (apply transform)                      [x]
 - Improved ASL tools based on oxasl (inc. ENABLE, VEASL, DEBLUR)       [x]
 - Fabber T1                                                            [x]
 - Fabber DCE                                                           [x]
 - DSC widget                                                           [x]
 - Improvements to ROI builder - working 'paint' tool                   [x]
 - Motion simulation                                                    [x]
 - Add noise                                                            [x]

#### v0.10 (Target 2020)

 - Stable interface for QpWidget, QpData, Process                       [ ]
 - Python 3                                                             [x]
 - Support PySide and PySide2 - ideally the latter by default           [x]
 - Improved manual data alignment tools                                 [ ]
 - Multi-overlay view                                                   [x]
 - Perfusion simulator                                                  [x]

### Migration to PySide2

 - Current version of Quantipihyse is targeted at Pyside2
 - *Should* still run under Pyside1 but not guaranteed
 - Currently using our own fork of `pyqtgraph` awaiting official release with Pyside2 support

#### Vague Plans for Future

 - MoCo/Registration
   - Bartek's MC method

 - 3D view
   - Probably not that useful but fun and may be easy(?) with vispy. Reliant on good refactoring of ImageView
   - Application to surfaces (Tom K?)
   - Use VisPy?

 - Add Jola's texture analysis which sounds cool, whatever it is

 - PK modelling validation
   - QIBA [x]
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
