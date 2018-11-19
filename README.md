# Quantiphyse

Viewer for 3D/4D data and Pk modelling

## Overview

This viewer provides tools for modelling and analysis of 3D/4D volumetric data, principally MRI data. 

Key features:
- Loading/Saving 3D/4D NIFTI files
- Analysis tools including single/multiple voxel analysis and data comparison
- Generic processing including smoothing, resampling, clustering
- Specialised processing including registration, motion correction
- Specialised modelling tools for DCE, ASL and CEST MRI
- Integration of selected FSL tools, if installed

See: [http://quantiphyse.readthedocs.org/en/latest/](http://quantiphyse.readthedocs.org/en/latest/) for full documentation.

## Installation

Installation packages are available on the [Wiki](https://ibme-gitcvs.eng.ox.ac.uk/quantiphyse/quantiphyse/wikis/home)

The packages are rather large because they include all dependencies (including Python). However this
does have the advantage of making them standalone.

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

#### Packaging

The scripts packaging/build.py is used to build a frozen distribution package in the form of a compressed archive (`tar.gz` or `.zip`) and a platform-dependent package (`deb`, `msi` or `dpg`). It should run autonomously, however you may need to input the sudo password on Linux in order to build a `deb` package. 

The `--snapshot` option removes the version number from package filenames so you can provided them for download without having to change the link URLs.

The `--maxi` option builds a package which includes selected plugins, assuming these are downloaded

#### OSx 10.11

Installing from source on OSX is not fun. The major issue is QT since the required version (4.8) is 
deprecated and hard to install properly. 

I have had most success using Anaconda and installing PySide using the conda tool. This should bring in the appropriate version of QT.

Alternatively, homebrew+pip can be used, as described below. Note that these instructions have not been
recently tested and you will probably need to use your own initiative a bit.

For OSx it is recommended that you don't use the system version of python so that libraries can be updated without
affecting the underlying system. 

1) Homebrew is ideal for running a separate version of python. Install homebrew from http://brew.sh/ if it's not 
already installed. 

2) Install python

    brew update
    brew install python

2) git clone this repository

3) cd into the directory

    pip install -U pip
    pip install -U setuptools
    pip install numpy 
    pip install scipy
    pip install -r requirements.txt
    pip install PySide

4) Run the script
    
    python qp.py

#### Using a python virtualenv

If you're running from source it can be a good idea to create a Python virtual environment so the
dependencies you install do not affect anything else on your system. See (https://virtualenv.readthedocs.org/en/latest/) for details.

On Windows, Anaconda is recommended and comes with virtual environment support as standard.

#### Resource file

The resource file is compiled by

For python 2:

    pyside-rcc resource -o resource.py

For python 3:

    pyside-rcc resource -o resource.py -py3

This is then imported at the beginning of the app so that the program can find the resources. 

## To Do list

### Issue tracker

Current issues can be viewed on the GitLab issue tracker(https://ibme-gitcvs.eng.ox.ac.uk/quantiphyse/quantiphyse/issues)

### Roadmap

#### v0.6 (Released June 2018)

 - ASL tools first version (preprocess, model fit, calibration, multiphase)
 - Improved viewer (full resolution, aligned)

#### v0.8 (Target Jan 2019)

 - Integration of selected FSL tools (FLIRT, FAST, BET, FSL_ANAT?)      DONE?
 - Improved registration support (apply transform)                      PART DONE
 - Improved manual data alignment tools                                 PART DONE
 - Improved ASL tools based on oxasl (inc. ENABLE, VEASL, DEBLUR)       PART DONE
 - Fabber T1 (integrate with existing T1 widget?)                       NOT DONE
 - Fabber DCE (integrate with existing DCE widget?)                     NOT DONE
 - DSC widget                                                           PART DONE

#### v1.0 (Target Feb/March 2019)

No firm plans yet - selection from 'Vague plans' below

#### Vague Plans for Future

 - Python 3 (untested currently but should be mostly OK)
 
 - MoCo/Registration
   - Bartek's MC method
   - Revise interface to allow for MC and registration to be treated separately (MCFLIRT/FLIRT) (or not)
   - Standard way to save the transformation (matrix or warp map)
   - Could add FNIRT based option

 - 3D view
   - Probably not that useful but fun and may be easy(?) with vispy

 - Add Jola's texture analysis which sounds cool, whatever it is

 - PK modelling validation
   - QIBA in progress
   - QIN

 - Simplify/rewrite generic Fabber interface

 - Improve memory usage by swapping out data which are not being displayed?

 - All widgets which process within ROI should work with the subimage within the bounding box of the
   ROI, not the whole image. 
    - Supervoxels does this already with great performance improvement.

 - Improve batch processing unification
   - Most GUI tools now use the new Process system so they are available in batch

 - Support other file formats using NIBABEL.
   - DICOM conversion included where DCMSTACK is available

 - Improve /rethink generic maths/processing widget / console
   - Need to link data grids with data 

 - Add semiquantitative DCE-MRI measures
   - Area under the curve
   - Enhancing fraction

 - Simulation tools
   - Motion simulation  DONE
   - Add noise          DONE
   - Fabber test data
   - 'Simulated brain'

### Migration to PySide2

 - The current implementation uses PySide which is based on Qt4
 - Update to PySide2 when released which uses Qt5
 - Will provide support for HiDPI screens and proper scaling in OSx
 - PyQtgraph is currently the stumbling block as release version does not support Pyside2
 - Current git version has PySide2 modifications but not yet tested
 - Consider move to VisPy if this does not come to fruition
