#!/usr/bin/env python

"""


# Easiest option
# To build cython libraries in the current location
# Use: python setup.py build_ext --inplace
# run using ./pkviewer2

# Options 1: Create a wheel
python setup.py bdist_wheel

#remove existing installation
pip uninstall PKView

# Option 2: installing directly on the system
python setup.py install
then run
pkviewer2 from the terminal

# Option 3: Build a directory of wheels for pyramid and all its dependencies
pip wheel --wheel-dir=/tmp/wheelhouse pyramid
# Install from cached wheels
pip install --use-wheel --no-index --find-links=/tmp/wheelhouse pyramid
# Install from cached wheels remotely
pip install --use-wheel --no-index --find-links=https://wheelhouse.example.com/ pyramid

# Option 4: Build a .deb

# Option 5: py2app on OSx
Still not working completely. Try using a custom virtualenv

# Experimental
pex nii2dcm -c nii2dcm -o cnii2dcm -v

Setup.py for cx_freeze

Run:
python setup_cxfreeze.py build

issues:
currently saves the icons in the wrong folder and needs to be manually moved

"""
import numpy

from cx_Freeze import setup, Executable

# from setuptools import setup
from Cython.Build import cythonize
from Cython.Distutils import build_ext
from setuptools.extension import Extension

Description = """/
PkView
"""

# Compiling the Cython extensions
ext1 = Extension("pkview/analysis/pk_model",
                 sources=['pkview/analysis/pk_model.pyx',
                          'src/pkmodelling/Optimizer_class.cpp',
                          'src/pkmodelling/pkrun2.cpp',
                          'src/pkmodelling/ToftsOrton.cpp',
                          'src/pkmodelling/ToftsOrtonOffset.cpp',
                          'src/pkmodelling/ToftsWeinOffset.cpp',
                          'src/pkmodelling/ToftsWeinOffsetVp.cpp',
                          'src/pkmodelling/lmlib/lmcurve.cpp',
                          'src/pkmodelling/lmlib/lmmin.cpp'],
                 include_dirs=['src/pkmodelling/lmlib/',
                               'src/pkmodelling/',
                               numpy.get_include()],
                 language="c++")

ext2 = Extension("pkview/analysis/t1_model",
                 sources=['pkview/analysis/t1_model.pyx',
                          'src/T10/linear_regression.cpp',
                          'src/T10/T10_calculation.cpp'],
                 include_dirs=['src/T10',
                               numpy.get_include()],
                 language="c++",
                 extra_compile_args=['-std=c++11'])

extensions = [ext1, ext2]

# Dependencies are automatically detected, but it might need
# fine tuning.

buildOptions = dict(packages=['scipy', 'sklearn', 'skimage', 'pyqtgraph'], excludes=['PyQt4', 'Tkinter'],
                    include_files=['pkview/icons'])
# removed sklearn and numpy from includes... should still work

import sys
base = 'Win32GUI' if sys.platform == 'win32' else None

executables = [
    Executable('pkviewer2', base=base)
]

setup(name='PKView',
      cmdclass={'build_ext': build_ext},
      version='0.17',
      description='pCT and DCE-MRI viewer and analysis tool',
      long_description=Description,
      author='Benjamin Irving',
      author_email='benjamin.irving@eng.ox.ac.uk',
      url='www.birving.com',
      ext_modules=cythonize(extensions),
      options=dict(build_exe=buildOptions),
      executables=executables)
