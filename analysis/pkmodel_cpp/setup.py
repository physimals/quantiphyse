
# Cython compile instructions

from distutils.core import setup
from Cython.Build import cythonize

# Use python setup.py build --inplace
# to compile

setup(
    name = "pkapp",
    ext_modules = cythonize('*.pyx'),
)