#!/usr/bin/env python

"""

# Easiest option
# To build cython libraries in the current location
# Use: python setup.py build_ext --inplace
# run using ./quantiphyse.py

# Options 1: Create a wheel
python setup.py bdist_wheel

#remove existing installation
pip uninstall quantiphyse

# Option 2: installing directly on the system
python setup.py install
then run
quantiphyse from the terminal

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
import re
import glob

from setuptools import setup
from Cython.Build import cythonize
from Cython.Distutils import build_ext
from setuptools.extension import Extension

Description = """/
Quantiphyse
"""

# Update version info from git tags and return a standardized version
# of it for packaging
from update_version import get_std_version
version_str = get_std_version()

extensions = []
compile_args = []
link_args = []

if sys.platform.startswith('win'):
    compile_args.append('/EHsc')
elif sys.platform.startswith('darwin'):
    link_args.append("-stdlib=libc++")

# PK modelling extension

extensions.append(Extension("quantiphyse.packages.core.dce.pk_model",
                 sources=['quantiphyse/packages/core/dce/pk_model.pyx',
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
                 language="c++", extra_compile_args=compile_args, extra_link_args=link_args))

# T1 map generation extension

extensions.append(Extension("quantiphyse.packages.core.t1.t1_model",
                 sources=['quantiphyse/packages/core/t1/t1_model.pyx',
                          'src/T10/linear_regression.cpp',
                          'src/T10/T10_calculation.cpp'],
                 include_dirs=['src/T10',
                               numpy.get_include()],
                 language="c++", extra_compile_args=compile_args, extra_link_args=link_args))

# Supervoxel extensions

extensions.append(Extension("quantiphyse.packages.core.supervoxels.perfusionslic.additional.bspline_smoothing",
              sources=["quantiphyse/packages/core/supervoxels/perfusionslic/additional/bspline_smoothing.pyx"],
              include_dirs=[numpy.get_include()]))

extensions.append(Extension("quantiphyse.packages.core.supervoxels.perfusionslic.additional.create_im",
              sources=["quantiphyse/packages/core/supervoxels/perfusionslic/additional/create_im.pyx"],
              include_dirs=[numpy.get_include()]))

extensions.append(Extension("quantiphyse.packages.core.supervoxels.perfusionslic._slic_feat",
              sources=["quantiphyse/packages/core/supervoxels/perfusionslic/_slic_feat.pyx"],
              include_dirs=[numpy.get_include()]))

extensions.append(Extension("quantiphyse.packages.core.supervoxels.perfusionslic.additional.processing",
              sources=["quantiphyse/packages/core/supervoxels/perfusionslic/additional/processing.pyx",
                       "src/perfusionslic/processing.cpp"],
              include_dirs=["src/perfusionslic", numpy.get_include()],
              language="c++", extra_compile_args=compile_args, extra_link_args=link_args))

# MCFlirt extension - requires FSL to build

if sys.platform.startswith("win"):
  zlib = "zlib"
  extra_inc = "src/compat"
else:
  zlib = "z"
  extra_inc = "."

fsldir = os.environ.get("FSLDIR", "")
if fsldir:
    extensions.append(Extension("quantiphyse.packages.core.registration.mcflirt",
                 sources=['quantiphyse/packages/core/registration/mcflirt.pyx',
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
                 language="c++", extra_compile_args=compile_args, extra_link_args=link_args))
else:
    print("FSLDIR not set - not building MCFLIRT extension")

# deedsReg extension

extensions.append(Extension("quantiphyse.packages.core.registration.deeds",
                 sources=['quantiphyse/packages/core/registration/deeds.pyx',
                          'src/deedsRegSSC/TMI2013/deedsMSTssc.cpp'],
                 include_dirs=[numpy.get_include(), "src/deedsRegSSC/TMI2013/", extra_inc],
                 language="c++", extra_compile_args=compile_args, extra_link_args=link_args))

# setup parameters
setup(name='quantiphyse',
      cmdclass={'build_ext': build_ext},
      version=version_str,
      description='MRI viewer and analysis tool',
      long_description=Description,
      author='Benjamin Irving',
      author_email='benjamin.irving@eng.ox.ac.uk',
      url='www.birving.com',
      packages=['quantiphyse', 
                'quantiphyse.gui', 
                'quantiphyse.packages',
                'quantiphyse.analysis', 
                'quantiphyse.icons', 
                'quantiphyse.resources',
                'quantiphyse.utils', 
                'quantiphyse.volumes', 
                'quantiphyse.widgets'],
      include_package_data=True,
      data_files=[('quantiphyse/icons', glob.glob('quantiphyse/icons/*.svg') + glob.glob('quantiphyse/icons/*.png')),
                  ('quantiphyse/resources', ['quantiphyse/resources/darkorange.stylesheet'])
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
          'gui_scripts': ['quantiphyse = quantiphyse.qpmain:main'],
          'console_scripts': ['quantiphyse = quantiphyse.qpmain:main']
      })

