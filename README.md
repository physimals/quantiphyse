PkView
======
Viewer for 3D/4D data and Pk modelling

Contributers:
Benjamin Irving

![alt text](images/Screenshot1.png "Screenshot")

### Dependencies:
Python 2.7

#### Python libraries:

- PySide
- matplotlib
- numpy 
- nibabel
- pyqtgraph
- Cython
- scikit-image
- scikit-learn


### Overview

### Recommendation
I recommend using a virtualenv with pip so that the latest libraries are used. 

### Installation

1) Install dependencies
```bash
sudo apt-get install numpy scipy build-essentials pip
```

2) Install required python libraries using pip

3) Build c++/Cython code
```bash
python setup.py build_ext --inplace
```

### Usage

``` bash
python pkviewer2
```
or

``` bash
./pkviewer2
```

See:
https://github.com/benjaminirving/PkView_help_files
for usage

### Notes
- This software is currently tested and built in a virtualenv to use the latest dependencies and may not work with older python libraries


