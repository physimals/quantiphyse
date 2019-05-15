# -*- mode: python -*-
import sys
import os
import struct
import shutil
import platform

# See below for full explanation...
OSX_LIBPNG_HACK = False

pkgdir = os.path.abspath(os.path.dirname(SPEC))
qpdir = os.path.abspath(os.path.join(pkgdir, os.pardir))
distdir = os.path.join(qpdir, "dist")

# Generic configuration
bin_files = [
]

# Hidden imports are used by plugins but not referenced in main code
hidden_imports = [
    'deprecation',
    'faulthandler',
    'fsl',
    'fsl.data',
    'fsl.data.atlases',
    'fsl.data.image',
    'fsl.wrappers',
    'oxasl',
    'oxasl_ve',
    'oxasl_enable',
    'fabber',
    'quantiphyse.processes.feat_pca',
    'quantiphyse.utils.cmdline',
    'quantiphyse.test.widget_test',
    'quantiphyse.gui.options',
    'quantiphyse.gui.plot',
    'scipy._lib.messagestream',
    'skimage.segmentation', 
    'sklearn.metrics',
    'sphinx',
    'sphinx.transforms.post_transforms.code',
    'sphinx.transforms.post_transforms.compat',
    'pywt._extensions._cwt',
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
    # Issue #19 - FIXME hardcoded path
    bin_files.append(('/home/ibmeuser/.conda/envs/qp/lib/libiomp5.so', '.' ))
elif sys.platform.startswith("darwin"):
    osx_bundle = True
    home_dir = os.environ.get("HOME", "")
    anaconda_dir='%s/anaconda2/' % home_dir
    bin_files.append(('%s/lib/libmkl_mc.dylib' % anaconda_dir, '.' ))
    bin_files.append(('%s/lib/libmkl_avx2.dylib' % anaconda_dir, '.' ))
    bin_files.append(('%s/lib/libmkl_avx.dylib' % anaconda_dir, '.' ))
    bin_files.append(('%s/lib/libpng16.16.dylib' % anaconda_dir, '.' ))
    hidden_imports.append("_sysconfigdata")

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
    # Note that this requires ImageMagick to be installed for icon support
    import distutils.spawn
    if not distutils.spawn.find_executable("convert"):
        print("Could not find 'convert' - ImageMagick required for icons")
        icon = None
    else:    
        imgdir = os.path.join(pkgdir, "images")
        base_icon = os.path.join(qpdir, "quantiphyse", "icons", "main_icon.png")
        iconset_dir = os.path.join(imgdir, "qp.iconset")
        os.system("rm -rf %s" % iconset_dir)
        os.makedirs(iconset_dir)

        os.system("convert -resize 16x16 %s %s/icon_16x16.png" % (base_icon, iconset_dir))
        os.system("convert -resize 32x32 %s %s/icon_16x16@2x.png" % (base_icon, iconset_dir))
        os.system("convert -resize 32x32 %s %s/icon_32x32.png" % (base_icon, iconset_dir))
        os.system("convert -resize 64x64 %s %s/icon_32x32@2x.png" % (base_icon, iconset_dir))
        os.system("convert -resize 128x128 %s %s/icon_128x128.png" % (base_icon, iconset_dir))
        os.system("convert -resize 256x256 %s %s/icon_128x128@2x.png" % (base_icon, iconset_dir))
        os.system("convert -resize 256x256 %s %s/icon_256x256.png" % (base_icon, iconset_dir))
        os.system("convert -resize 512x512 %s %s/icon_256x256@2x.png" % (base_icon, iconset_dir))
        os.system("convert -resize 512x512 %s %s/icon_512x512.png" % (base_icon, iconset_dir))
        os.system("convert -resize 1024x1024 %s %s/icon_512x512@2x.png" % (base_icon, iconset_dir))
        os.system("iconutil -c icns %s" % iconset_dir)
        icon = os.path.join(imgdir, "qp.icns")

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

if sys.platform.startswith("linux"):
    # Issue #83: Remove the libdrm library as it causes GL error on Ubuntu
    libfile = os.path.join(distdir, "quantiphyse", "libdrm.so.2")
    os.remove(libfile)

