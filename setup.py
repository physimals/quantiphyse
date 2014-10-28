#!/usr/bin/env python

"""

# To build cython libraries
# Use: python setup.py build_ext --inplace


"""

try:
    from setuptools import setup
except ImportError:
    from distutils.core import setup
from Cython.Build import cythonize
from Cython.Distutils import build_ext
from distutils.extension import Extension

#TODO cython doesn't seem to work from outside the folder?

Description = """/
PkView
"""

#TODO pyqtgraph provides a good example

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
                       include_dirs=['pkview/analysis/pkmodel_cpp/lmlib/', 'pkview/analysis/pkmodel_cpp/'],
                       language="c++")
# setup parameters
setup(name='PKView',
      cmdclass={'build_ext': build_ext},
      version='0.13',
      description='pCT and DCE-MRI viewer and analysis tool',
      long_description=Description,
      author='Benjamin Irving',
      author_email='benjamin.irving@eng.ox.ac.uk',
      url='www.birving.com',
      packages=['pkview'],
      classifiers=["Programming Language :: Python :: 2.7"],
      ext_modules=cythonize([extensions], language="c++")
)


