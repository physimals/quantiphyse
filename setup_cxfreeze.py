"""
Setup.py for cx_freeze

Run:
python setup_cxfreeze.py build

issues:
currently saves the icons in the wrong folder and needs to be manually moved

"""

from cx_Freeze import setup, Executable

# Dependencies are automatically detected, but it might need
# fine tuning.

buildOptions = dict(packages=['scipy', 'sklearn', 'skimage', 'pyqtgraph'], excludes=['PyQt4', 'Tkinter'],
                    include_files=['pkview/icons'])
# removed sklearn and numpy from includes... should still work

import sys
base = 'Win32GUI' if sys.platform == 'win32' else None

executables = [
    Executable('pkviewer2.py', base=base)
]

setup(name='PKView',
      version='0.13',
      description='pCT and DCE-MRI viewer and analysis tool',
      author='Benjamin Irving',
      author_email='benjamin.irving@eng.ox.ac.uk',
      url='www.birving.com',
      options=dict(build_exe=buildOptions),
      executables=executables)
