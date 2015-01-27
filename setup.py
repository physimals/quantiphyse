#!/usr/bin/env python

"""

# To build cython libraries
# Use: python setup.py build_ext --inplace

#remove existing installation
pip uninstall PKView

#Gemfury repository
sudo pip install PKView --extra-index-url https://pypi.fury.io/CgC8MN8cE6hedVSt5EmK/benjaminirving/

#installing on the system
python setup.py install
then run
pkviewer2 from the terminal

# creating a deb file. Doesn't work yet with images
python setup.py --command-packages=stdeb.command bdist_deb


"""

try:
    from setuptools import setup
except ImportError:
    from distutils.core import setup
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
                       include_dirs=['pkview/analysis/pkmodel_cpp/lmlib/', 'pkview/analysis/pkmodel_cpp/'],
                       language="c++")
# setup parameters
setup(name='PKView',
      cmdclass={'build_ext': build_ext},
      version='0.141',
      description='pCT and DCE-MRI viewer and analysis tool',
      long_description=Description,
      author='Benjamin Irving',
      author_email='benjamin.irving@eng.ox.ac.uk',
      url='www.birving.com',
      packages=['pkview', 'pkview.QtInherit', 'pkview.analysis', 'pkview.annotation', 'pkview.libs',
                'pkview.analysis.pkmodel_cpp', 'pkview.icons'],
      include_package_data=True,
      data_files=[('pkview/icons/', ['pkview/icons/picture.png',
                                       'pkview/icons/pencil.png',
                                       'pkview/icons/clear.png',
                                       'pkview/icons/edit.png',
                                       'pkview/icons/clustering.png',
                                       'pkview/icons/main_icon.png',
                                       'pkview/icons/flag.png',
                                       'pkview/icons/voxel.png'])],
      #install_requires=['skimage', 'scikit-learn', 'numpy', 'scipy'],
      install_requires=['scikit-image', 'scikit-learn', 'numpy', 'scipy', 'pyqtgraph'],
      classifiers=["Programming Language :: Python :: 2.7"],
      ext_modules=cythonize([extensions], language="c++"),
      scripts=["pkviewer2"])

