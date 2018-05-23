# -*- mode: python -*-
import sys
import os
import struct
import shutil
import platform

# See below for full explanation...
OSX_LIBPNG_HACK = True

pkgdir = os.path.abspath(os.path.dirname(SPEC))
qpdir = os.path.abspath(os.path.join(pkgdir, os.pardir))
distdir = os.path.join(qpdir, "dist")

# Generic configuration
bin_files = [
]

# Hidden imports are used by plugins but not reference in main code
hidden_imports = [
    'skimage.segmentation', 
    'sklearn.metrics',
    'scipy._lib.messagestream',
    'quantiphyse.processes.feat_pca',
    'quantiphyse.utils.cmdline',
    'quantiphyse.test.widget_test',
    'quantiphyse.gui.options',
    'quantiphyse.gui.plot',
]

added_files = [
    (os.path.join(qpdir, 'quantiphyse/icons'), 'icons'), 
    (os.path.join(qpdir, 'quantiphyse/resources'), 'resources'), 
    (os.path.join(qpdir, 'src'), 'src'),
    (os.path.join(qpdir, 'quantiphyse/packages/core'), 'packages/core'),
    (os.path.join(qpdir, 'packaging/plugins-empty'), 'packages/plugins'),
]

runtime_hooks=[
]

excludes = [
    'tcl',
    'tk',
    'tkinter',
    '_tkinter',
    'matplotlib.backends',
    'pkgres',
    'mplconfig',
    'mpldata',
    'mpl-data',
    'wx',
]

# Platform-specific configuration
osx_bundle = False
block_cipher = None

# 32 bit or 64 bit
bits = struct.calcsize("P") * 8

if sys.platform.startswith("win"):
    home_dir = os.environ.get("USERPROFILE", "")
    anaconda_dir='%s/AppData/Local/Continuum/Anaconda2/' % home_dir
    bin_files.append(('%s/Library/bin/mkl_avx2.dll' % anaconda_dir, '.' ))
    #bin_files.append(('%s/Library/bin/mkl_def.dll' % anaconda_dir, '.' ))

    if bits == 32:
        # Possible bug in setuptools makes this necessary on 32 bit Anaconda
        hidden_imports += ['appdirs', 'packaging', 'packaging.version',
                           'packaging.specifiers', 'packaging.utils',
                           'packaging.requirements', 'packaging.markers'],
elif sys.platform.startswith("linux"):
    hidden_imports.append('FileDialog')
    hidden_imports.append('pywt._extensions._cwt')
elif sys.platform.startswith("darwin"):
    osx_bundle = True
    home_dir = os.environ.get("HOME", "")
    anaconda_dir='%s/anaconda2/' % home_dir
    bin_files.append(('%s/lib/libmkl_mc.dylib' % anaconda_dir, '.' ))
    bin_files.append(('%s/lib/libmkl_avx2.dylib' % anaconda_dir, '.' ))
    bin_files.append(('%s/lib/libmkl_avx.dylib' % anaconda_dir, '.' ))
    bin_files.append(('%s/lib/libpng16.16.dylib' % anaconda_dir, '.' ))

a = Analysis([os.path.join(qpdir, 'qp.py')],
             pathex=[],
             binaries=bin_files,
             datas=added_files,
             hiddenimports=hidden_imports,
             runtime_hooks=runtime_hooks,
             hookspath=['packaging/hooks'],
             excludes=excludes,
             win_no_prefer_redirects=False,
             win_private_assemblies=False,
             cipher=block_cipher)

pyz = PYZ(a.pure, a.zipped_data,
          cipher=block_cipher)

exe = EXE(pyz,
            a.scripts,
            exclude_binaries=True,
            name='quantiphyse',
            debug=False,
            strip=False,
            upx=False,
            console=False,
            icon='quantiphyse/icons/main_icon.ico')

coll = COLLECT(exe,
                a.binaries,
                a.zipfiles,
                a.datas,
                strip=False,
                upx=False,
                name='quantiphyse')

if osx_bundle:
    os.system("iconutil -c icns %s/images/qp.iconset" % pkgdir)
    app = BUNDLE(coll,
            name='quantiphyse.app',
            icon='%s/images/qp.icns' % pkgdir,
            bundle_identifier=None)

if sys.platform.startswith("darwin") and OSX_LIBPNG_HACK:
    # This is a total hack for OSX which on my build system
    # seems to bundle the wrong version of libpng. So we need 
    # to copy the right one into the dist. This is clearly
    # not portable and should be replaced by either a portable
    # solution or a fix to the underlying problem
    libpng = os.path.join(os.environ["HOME"], "anaconda2/lib/libpng16.16.dylib")
    dest = os.path.join(distdir, "quantiphyse/")
    shutil.copy(libpng, dest)
    if osx_bundle:
        dest = os.path.join(distdir, "quantiphyse.app/Contents/MacOS/")
        shutil.copy(libpng, dest)
