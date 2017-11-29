# -*- mode: python -*-
import sys
import os
import struct
import subprocess
import re
import shutil
import platform

# See below for full explanation...
OSX_LIBPNG_HACK = True

pkgdir = os.path.abspath(os.path.dirname(SPEC))
sys.path.append(pkgdir)
qpdir = os.path.abspath(os.path.join(pkgdir, os.pardir))
distdir = os.path.join(qpdir, "dist")

# This is copied from update_version for now until we sort out how to import it...
def get_std_version():
    """ 
    Get standardized version string in form maj.min.patch-release
    """
    v = subprocess.check_output('git describe --dirty', shell=True).strip(" \n")
    p = re.compile("v?(\d+\.\d+\.\d+(-\d+)?).*")
    m = p.match(v)
    if m is not None:
        return  m.group(1)
    else:
        raise RuntimeError("Failed to parse version string %s" % v)

# Update version info from git tags and get standardized version for packages
version_str = get_std_version()
if len(version_str.split("-", 1)) > 0:
    # This is a snapshot, name accordingly (real version is still embeddd in the python)
    version_str_orig = version_str
    version_str = "snapshot"

# Generic configuration
bin_files = [
]

hidden_imports = [
    'skimage.segmentation', 
    'sklearn.metrics', 
    'quantiphyse.analysis.overlay_analysis',
    'quantiphyse.analysis.feat_pca',
]

added_files = [
    (os.path.join(qpdir, 'quantiphyse/icons'), 'icons'), 
    (os.path.join(qpdir, 'quantiphyse/resources'), 'resources'), 
    (os.path.join(qpdir, 'src'), 'src'),
    (os.path.join(qpdir, 'quantiphyse/packages'), 'packages')
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

fsldir = os.environ.get("FSLDIR")
sys.path.append("%s/lib/python/" % os.environ["FSLDIR"])
hidden_imports.append('fabber')

# Platform-specific configuration
platform_package = None
archive_method="zip"
osx_bundle = False
block_cipher = None

# 32 bit or 64 bit
bits = struct.calcsize("P") * 8

if sys.platform.startswith("win"):
    sysname="win32"
    import create_msi
    platform_package = create_msi.create_msi
    home_dir = os.environ.get("USERPROFILE", "")
    anaconda_dir='%s/AppData/Local/Continuum/Anaconda2/' % home_dir
    bin_files.append(('%s/Library/bin/mkl_avx2.dll' % anaconda_dir, '.' ))
    #bin_files.append(('%s/Library/bin/mkl_def.dll' % anaconda_dir, '.' ))
    bin_files.append(("%s/bin/fabber*.dll" % fsldir, "fabber/bin"))
    bin_files.append(("%s/bin/fabber.exe" % fsldir, "fabber/bin"))

    if bits == 32:
        # Possible bug in setuptools makes this necessary on 32 bit Anaconda
        hidden_imports += ['appdirs', 'packaging', 'packaging.version',
                           'packaging.specifiers', 'packaging.utils',
                           'packaging.requirements', 'packaging.markers'],
elif sys.platform.startswith("linux"):
    sysname=platform.linux_distribution()[0].split()[0].lower()
    import create_deb
    platform_package = create_deb.create_deb
    archive_method="gztar"
    hidden_imports.append('FileDialog')
    hidden_imports.append('pywt._extensions._cwt')
    bin_files.append(("%s/lib/libfabber*.so" % fsldir, "fabber/lib"))
    bin_files.append(("%s/bin/fabber" % fsldir, "fabber/bin"))
elif sys.platform.startswith("darwin"):
    sysname="osx"
    import create_dmg
    platform_package = create_dmg.create_dmg
    osx_bundle = True
    home_dir = os.environ.get("HOME", "")
    anaconda_dir='%s/anaconda2/' % home_dir
    bin_files.append(('%s/lib/libmkl_mc.dylib' % anaconda_dir, '.' ))
    bin_files.append(('%s/lib/libmkl_avx2.dylib' % anaconda_dir, '.' ))
    bin_files.append(('%s/lib/libmkl_avx.dylib' % anaconda_dir, '.' ))
    bin_files.append(('%s/lib/libpng16.16.dylib' % anaconda_dir, '.' ))
    bin_files.append(("%s/lib/libfabber*.dylib" % fsldir, "fabber/lib"))
    bin_files.append(("%s/bin/fabber" % fsldir, "fabber/bin"))

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
    app = BUNDLE(coll,
            name='quantiphyse.app',
            icon='%s/quantiphyse/icons/pk.png' % qpdir,
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

sys.stdout.write("Creating compressed archive...")
sys.stdout.flush()
shutil.make_archive("%s/quantiphyse-%s-%s" % (distdir, version_str, sysname), 
                    archive_method, "%s/quantiphyse" % distdir)
print("DONE")

if platform_package is not None:
    sys.stdout.write("Creating platform-specific package...")
    sys.stdout.flush()
    platform_package(distdir, pkgdir, version_str_orig, sysname, version_str)
    print("DONE")
