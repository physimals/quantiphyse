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



"""
import numpy

from setuptools import setup
from Cython.Build import cythonize
from Cython.Distutils import build_ext
from distutils.extension import Extension

Description = """/
PkView
"""

# Compiling the Cython extensions
extensions = Extension("pkview/analysis/pkmodel_cpp/pk",
                       sources=['pkview/analysis/pkmodel_cpp/pk.pyx',
                                'pkview/analysis/pkmodel_cpp/Optimizer_class.cpp',
                                'pkview/analysis/pkmodel_cpp/pkrun2.cpp',
                                'pkview/analysis/pkmodel_cpp/ToftsOrton.cpp',
                                'pkview/analysis/pkmodel_cpp/ToftsOrtonOffset.cpp',
                                'pkview/analysis/pkmodel_cpp/ToftsWeinOffset.cpp',
                                'pkview/analysis/pkmodel_cpp/ToftsWeinOffsetVp.cpp',
                                'pkview/analysis/pkmodel_cpp/lmlib/lmcurve.cpp',
                                'pkview/analysis/pkmodel_cpp/lmlib/lmmin.cpp'],
                       include_dirs=['pkview/analysis/pkmodel_cpp/lmlib/',
                                     'pkview/analysis/pkmodel_cpp/',
                                     numpy.get_include()],
                       language="c++")
# setup parameters
setup(name='PKView',
      cmdclass={'build_ext': build_ext},
      version='0.15.3',
      description='pCT and DCE-MRI viewer and analysis tool',
      long_description=Description,
      author='Benjamin Irving',
      author_email='benjamin.irving@eng.ox.ac.uk',
      url='www.birving.com',
      packages=['pkview', 'pkview.QtInherit', 'pkview.analysis', 'pkview.annotation', 'pkview.libs',
                'pkview.analysis.pkmodel_cpp', 'pkview.icons'],
      include_package_data=True,
      data_files=[('pkview/icons/', ['pkview/icons/picture.svg',
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
                                     'pkview/icons/voxel.png'])],
      #install_requires=['skimage', 'scikit-learn', 'numpy', 'scipy'],
      install_requires=['six', 'nibabel', 'scikit-image', 'scikit-learn', 'pyqtgraph',
                        'pynrrd', 'Cython', 'matplotlib', 'mock', 'nose', 'python-dateutil', 'pytz'],
      #install_requires=['six', 'numpy', 'scipy', 'nibabel', 'scikit-image', 'scikit-learn', 'pyqtgraph',
      #                  'pynrrd', 'Cython', 'matplotlib', 'PySide'],
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
      ext_modules=cythonize([extensions], language="c++"),
      scripts=["pkviewer2"])

