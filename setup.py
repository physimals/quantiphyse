"""
Setup.py for cx_freeze

Run:
python setup.py build to run
"""

from cx_Freeze import setup, Executable

# Dependencies are automatically detected, but it might need
# fine tuning.
buildOptions = dict(packages=[], excludes=[], include_files=['icons'])

import sys
base = 'Win32GUI' if sys.platform == 'win32' else None

executables = [
    Executable('PkView2.py', base=base)
]

setup(name='PkView',
      version='0.1',
      description='Pk viewing and analysis',
      options=dict(build_exe=buildOptions),
      executables=executables)
