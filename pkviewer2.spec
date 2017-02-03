# -*- mode: python -*-
import sys
import os
import struct

# See if we are 32 bit or 64 bit
bits = struct.calcsize("P") * 8

# Whether to build single-file executable or folder
onefile = True

# Generic configuration
block_cipher = None
bin_files = []
hidden_imports = []
added_files = [('pkview/icons', 'icons'), ('pkview/resources', 'resources')]

# Platform-specific configuration
if sys.platform.startswith("win"):
    home_dir = os.environ.get("USERPROFILE", "")
    anaconda_dir='%s/AppData/Local/Continuum/Anaconda2/' % home_dir
    bin_files.append(('%s/Library/bin/mkl_avx2.dll' % anaconda_dir, '.' ))
    #bin_files.append(('%s/Library/bin/mkl_def.dll' % anaconda_dir, '.' ))

    if bits == 32:
        # Possible bug in setuptools makes this necessary on 32 bit Anaconda
        hiddenimports += ['appdirs', 'packaging', 'packaging.version',
                          'packaging.specifiers', 'packaging.utils',
                          'packaging.requirements', 'packaging.markers'],
elif sys.platform.startswith("linux"):
    pass
elif sys.platform.startswith("darwin"):
    pass

a = Analysis(['pkviewer2.py'],
             pathex=[],
             binaries=bin_files,
             datas=added_files,
             hiddenimports=hidden_imports,
             hookspath=['hooks'],
             runtime_hooks=[],
             excludes=[],
             win_no_prefer_redirects=False,
             win_private_assemblies=False,
             cipher=block_cipher)

pyz = PYZ(a.pure, a.zipped_data,
          cipher=block_cipher)

if onefile:
    exe = EXE(pyz,
              a.scripts,
              a.binaries,
              a.zipfiles,
              a.datas,
              name='pkviewer2',
              strip=False,
              debug=False,
              upx=False,
              console=False,
              icon='pkview/icons/main_icon.ico')
else:
    exe = EXE(pyz,
              a.scripts,
              exclude_binaries=True,
              name='pkviewer2',
              debug=False,
              strip=False,
              upx=False,
              console=False,
              icon='pkview/icons/main_icon.ico')

    coll = COLLECT(exe,
                   a.binaries,
                   a.zipfiles,
                   a.datas,
                   strip=False,
                   upx=True,
                   name='pkviewer2')
