"""
Setup.py for cx_freeze

Run:
python setup_cxfreeze.py build

"""

from cx_Freeze import setup, Executable

# Dependencies are automatically detected, but it might need
# fine tuning.
buildOptions = dict(packages=['scipy', 'sklearn', 'skimage', 'pyqtgraph'], excludes=['PyQt4', 'Tkinter'], include_files=['pkview/icons'])

import sys
base = 'Win32GUI' if sys.platform == 'win32' else None

executables = [
    Executable('pkview/pkviewer.py', base=base)
]

setup(name='PkView',
      version='0.1',
      description='Pk viewing and analysis',
      options=dict(build_exe=buildOptions),
      executables=executables)
