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
- scipy

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

##Advanced
### 1) Setting up a virtualenv system

```bash
sudo apt-get install python-virtualenv     # Installing virtualenv library
mkdir python-vm # make a directory to store the virtualenv
cd ~/python-vm
virtualenv pyvm # Create a vm named pyvm
source ~/python-vm/pyvm/bin/activate #start the vim
```

Deactivating the vm

```bash
deactivate
```

Installing python libraries in the vm (make sure system libraries in 2) are installed)
```bash
pip install --upgrade pip
pip install --upgrade setuptools
pip install distribute
pip install numpy
pip install scipy
pip install -r requirements.txt
pip install PySide
```

### 2) System libraries required for pip install of dependencies in a virtualenv

libffi-dev

libssl-dev

pip install requests[security]

**numpy / scitkit-learn / scipy**

gfortran

libatlas-base-dev

libblas-dev

liblapack-dev

python-all-dev

**matplotlib**

libfreetype6-dev

libfreetype6

libpng12-dev

libpng12


**PySide**

qt4-qmake

shiboken

libshiboken-dev

libqt4-dev


### 3) Resource file

The resource file is compiled by

pyside-rcc resource -o resource.py

This is then imported at the beginning of the app so that the program can find the resources. 

