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
import platform
import os
import sys

from setuptools import setup
from Cython.Build import cythonize
from Cython.Distutils import build_ext
from setuptools.extension import Extension

Description = """/
PkView
"""

extensions = []

# PK modelling extension

extensions.append(Extension("pkview.analysis.pk_model",
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
                 language="c++"))

# T1 map generation extension

extensions.append(Extension("pkview.analysis.t1_model",
                 sources=['pkview/analysis/t1_model.pyx',
                          'src/T10/linear_regression.cpp',
                          'src/T10/T10_calculation.cpp'],
                 include_dirs=['src/T10',
                               numpy.get_include()],
                 language="c++",
                 extra_compile_args=['-std=c++11']))

# Supervoxel extensions

extensions.append(Extension("pkview.analysis.perfusionslic.additional.bspline_smoothing",
              sources=["pkview/analysis/perfusionslic/additional/bspline_smoothing.pyx"],
              include_dirs=[numpy.get_include()]))

extensions.append(Extension("pkview.analysis.perfusionslic.additional.create_im",
              sources=["pkview/analysis/perfusionslic/additional/create_im.pyx"],
              include_dirs=[numpy.get_include()]))

extensions.append(Extension("pkview.analysis.perfusionslic._slic_feat",
              sources=["pkview/analysis/perfusionslic/_slic_feat.pyx"],
              include_dirs=[numpy.get_include()]))

extensions.append(Extension("pkview.analysis.perfusionslic.additional.processing",
              sources=["pkview/analysis/perfusionslic/additional/processing.pyx",
                       "src/perfusionslic/processing.cpp"],
              include_dirs=["src/perfusionslic", numpy.get_include()],
              language="c++",
              extra_compile_args=["-std=c++11"]))

# MCFlirt extension - requires FSL to build

fsldir = os.environ.get("FSLDIR", "")
if fsldir:
  if sys.platform.startswith("win"):
    zlib = "zlib"
    extra_inc = "compat"
  else:
    zlib = "z"
    extra_inc = "."

  extensions.append(Extension("pkview.analysis.mcflirt",
                 sources=['pkview/analysis/mcflirt.pyx',
                          'src/mcflirt/mcflirt.cc',
                          'src/mcflirt/Globaloptions.cc',
                          'src/mcflirt/Log.cc'],
                 include_dirs=['src/mcflirt/',
                               os.path.join(fsldir, "include"),
                               os.path.join(fsldir, "extras/include/newmat"),
                               os.path.join(fsldir, "extras/include/boost"),
                               numpy.get_include(), extra_inc],
                 libraries=['newimage', 'miscmaths', 'fslio', 'niftiio', 'newmat', 'znz', zlib],
                 library_dirs=[os.path.join(fsldir, "lib"),os.path.join(fsldir, "extras/lib")],
                 language="c++"))
else:
    print("FSLDIR not set - not building MCFLIRT extension")

# setup parameters
setup(name='PKView',
      cmdclass={'build_ext': build_ext},
      version='0.32',
      description='pCT and DCE-MRI viewer and analysis tool',
      long_description=Description,
      author='Benjamin Irving',
      author_email='benjamin.irving@eng.ox.ac.uk',
      url='www.birving.com',
      packages=['pkview', 'pkview.QtInherit', 'pkview.analysis', 'pkview.icons', 'pkview.resources', 'pkview.tests',
                'pkview.utils', 'pkview.volumes', 'pkview.widgets'],
      include_package_data=True,
      data_files=[('pkview/icons', ['pkview/icons/picture.svg',
                                     'pkview/icons/pencil.svg',
                                     'pkview/icons/clear.svg',
                                     'pkview/icons/edit.svg',
                                     'pkview/icons/clustering.svg',
                                     'pkview/icons/main_icon.png',
                                     'pkview/icons/voxel.svg',
                                     'pkview/icons/picture.png',
                                     'pkview/icons/pencil.png',
                                     'pkview/icons/clear.png',
                                     'pkview/icons/edit.png',
                                     'pkview/icons/clustering.png',
                                     'pkview/icons/voxel.png']),
                  ('pkview/resources', ['pkview/resources/darkorange.stylesheet'])
                  ],
      #install_requires=['skimage', 'scikit-learn', 'numpy', 'scipy'],
      setup_requires=['Cython'],
      install_requires=['six', 'nibabel', 'scikit-image', 'scikit-learn', 'pyqtgraph', 'pyaml', 'PyYAML',
                        'pynrrd', 'matplotlib', 'mock', 'nose', 'python-dateutil', 'pytz', 'numpy', 'scipy'],
      classifiers=["Programming Language :: Python :: 2.7",
                   "Development Status:: 3 - Alpha",
                   'Programming Language :: Python',
                   'Operating System :: MacOS :: MacOS X',
                   'Operating System :: Microsoft :: Windows',
                   'Operating System :: POSIX',
                   "Intended Audience :: Education",
                   "Intended Audience :: Science/Research",
                   "Intended Audience :: End Users/Desktop",
                   "Topic :: Scientific/Engineering :: Bio-Informatics",
                   ],
      ext_modules=cythonize(extensions),
      entry_points={
          'gui_scripts': ['pkview2 = pkview.pkviewer:main'],
          'console_scripts': ['pkview2 = pkview.pkviewer:main']
      })

