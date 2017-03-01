# -*- mode: python -*-
import sys
import os
import struct

# See if we are 32 bit or 64 bit
bits = struct.calcsize("P") * 8

# Whether to build single-file executable or folder
onefile = False
osx_bundle = False

# Generic configuration
block_cipher = None
bin_files = []
hidden_imports = []
added_files = [('pkview/icons', 'icons'), ('pkview/resources', 'resources')]

fsldir = os.environ.get("FSLDIR")
sys.path.append("%s/lib/python/" % os.environ["FSLDIR"])

# Platform-specific configuration
if sys.platform.startswith("win"):
    home_dir = os.environ.get("USERPROFILE", "")
    anaconda_dir='%s/AppData/Local/Continuum/Anaconda2/' % home_dir
    bin_files.append(('%s/Library/bin/mkl_avx2.dll' % anaconda_dir, '.' ))
    #bin_files.append(('%s/Library/bin/mkl_def.dll' % anaconda_dir, '.' ))
    bin_files.append(("%s/bin/fabber*.dll" % fsldir, "fabber/bin"))

    if bits == 32:
        # Possible bug in setuptools makes this necessary on 32 bit Anaconda
        hidden_imports += ['appdirs', 'packaging', 'packaging.version',
                           'packaging.specifiers', 'packaging.utils',
                           'packaging.requirements', 'packaging.markers'],
elif sys.platform.startswith("linux"):
    hidden_imports.append('FileDialog')
    bin_files.append(("%s/lib/libfabber*.so" % fsldir, "fabber/lib"))
elif sys.platform.startswith("darwin"):
    osx_bundle = True
    home_dir = os.environ.get("HOME", "")
    anaconda_dir='%s/anaconda2/' % home_dir
    bin_files.append(('%s/lib/libmkl_avx2.dylib' % anaconda_dir, '.' ))
    bin_files.append(("%s/lib/libfabber*.dylib" % fsldir, "fabber/lib"))

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
                   upx=False,
                   name='pkviewer2')
    if osx_bundle:
        pkdir = os.path.dirname(os.path.abspath(SPEC))
        app = BUNDLE(coll,
             name='pkviewer2.app',
             icon='%s/pkview/icons/pk.png' % pkdir,
             bundle_identifier=None)

