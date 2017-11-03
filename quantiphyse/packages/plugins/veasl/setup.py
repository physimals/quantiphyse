#!/usr/bin/env python

"""
Build Quantiphyse package for veaslc
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

desc = "Quantiphyse package for vessel-encoded ASL"
longdesc = desc
version = "0.0.1"

# veasl extension
extensions.append(Extension("qpveasl.veasl",
                 sources=['qpveasl/veasl.pyx',
                          'model.cc'],
                 include_dirs=[numpy.get_include()],
                 language="c++", 
                 extra_compile_args=compile_args, 
                 extra_link_args=link_args))

# setup parameters
setup(name='qpveasl',
      cmdclass={'build_ext': build_ext},
      version=version,
      description=desc,
      long_description=longdesc,
      author='Michael Chappell, Martin Craig'',
      author_email='martin.craig@eng.ox.ac.uk',
      packages=['qpveasl'],
      include_package_data=True,
      data_files=[],
      setup_requires=['Cython'],
      install_requires=[],
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
      ext_modules=cythonize(extensions))

