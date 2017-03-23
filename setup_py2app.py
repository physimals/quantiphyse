#!/usr/bin/env python

"""


# Easiest option
# To build cython libraries in the current location
# Use: python setup.py build_ext --inplace
# run using ./quantiphyse

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
- use virtualenv python27_quantiphysepackage...
python setup_py2app.py py2app 

# Experimental
pex nii2dcm -c nii2dcm -o cnii2dcm -v

"""
import numpy

from setuptools import setup
from Cython.Build import cythonize
from Cython.Distutils import build_ext
from setuptools.extension import Extension

Description = """/
Quantiphyse
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

# setup parameters
setup(name='Quantiphyse',
      cmdclass={'build_ext': build_ext},
      app=['quantiphyse.py'],
      version='0.17',
      options = {"py2app": {
                          'includes': ['sklearn.utils.lgamma',
                                       'sklearn.neighbors.typedefs',
                                       'sklearn.utils.sparsetools._graph_validation',
                                       'sklearn.utils.weight_vector'],
                         # 'iconfile':'pkview/icons/main_icon.icns',
                         'qt_plugins': 'imageformats',
                         }
      },
      description='pCT and DCE-MRI viewer and analysis tool',
      long_description=Description,
      author='Benjamin Irving',
      author_email='benjamin.irving@eng.ox.ac.uk',
      url='www.birving.com',
      packages=['pkview', 'pkview.QtInherit', 'pkview.analysis', 'pkview.icons', 'pkview.resources', 'pkview.tests',
                'pkview.utils', 'pkview.volumes', 'pkview.widgets'],
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
                                     'pkview/icons/voxel.png']),
                  ('pkview/resources/', ['pkview/resources/darkorange.stylesheet'])
                  ],
      #install_requires=['skimage', 'scikit-learn', 'numpy', 'scipy'],
      setup_requires=['py2app', 'Cython'],
      install_requires=['six', 'nibabel', 'scikit-image', 'scikit-learn', 'pyqtgraph',
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
      )

