"""
Master build script for Quantiphyse packages

This creates :

 - A directory ``dist/quantiphyse`` containing a frozen executable ``quantiphyse`` and
   all required dependencies
 - An archived copy of this directory in ``dist`` (``.zip`` on Mac/Windows, ``.tar.gz`` on Linux)
 - A platform-specific package in ``dist`` (``.msi`` on Windows, ``.dmg`` on Mac, ``.deb`` on Linux)
 
Options:
 - ``--snapshot`` Names packages using version string 'snapshot' rather than embedding the version number
 - ``--maxi`` Bundles plugins and Fabber code
"""
import os, sys
import shutil
import glob

# Set up basic directories and platform-specific settings
PACKAGING_DIR = os.path.abspath(os.path.dirname(__file__))
ROOT_DIR = os.path.abspath(os.path.join(PACKAGING_DIR, os.pardir))
DIST_DIR = os.path.join(ROOT_DIR, "dist")
PACKAGE_NAME = "quantiphyse"
sys.path.append(ROOT_DIR)

ARCHIVE_METHOD="zip"
PLATFORM_PACKAGE_BUILDFN=None
if sys.platform.startswith("win"):
    platform="win32"
    import create_msi
    PLATFORM_PACKAGE_BUILDFN = create_msi.create_msi
elif sys.platform.startswith("linux"):
    #distro=platform.linux_distribution()[0].split()[0].lower()
    platform="linux"
    ARCHIVE_METHOD="gztar"
    import create_deb
    PLATFORM_PACKAGE_BUILDFN = create_deb.create_deb
elif sys.platform.startswith("darwin"):
    platform="osx"
    import create_dmg
    PLATFORM_PACKAGE_BUILDFN = create_dmg.create_dmg

def bundle_plugins():
    # Bundle plugins when creating a maxi-package
    plugins = {
        "quantiphyse-asl" : "quantiphyse_basil", 
        "quantiphyse-cest" : "quanticest", 
        "quantiphyse-dce" : "quantiphyse_dce",
        "quantiphyse-dsc" : "quantiphyse_dsc", 
        "qp-deeds" : "quantiphyse_deeds", 
        "quantiphyse-fabber" : "quantiphyse_fabber",
        "quantiphyse-fsl" : "quantiphyse_fsl",
        "quantiphyse-t1" : "quantiphyse_t1", 
    }
    
    print("  - Bundling plugins...")
    for name, module in plugins.items():
        print("    - %s" % name)
        plugindir = os.path.join(ROOT_DIR, os.pardir, name)
        cwd_orig = os.getcwd()
        os.chdir(plugindir)
        os.system("python setup.py build 2>>%s/build.err 1>>%s/build.out" % (PACKAGING_DIR, PACKAGING_DIR))
        built_module_dirs = glob.glob(os.path.join(plugindir, "build", "lib*"))
        if len(built_module_dirs) != 1:
            raise RuntimeError("More than one build directory found", built_module_dirs)
        built_module = os.path.join(built_module_dirs[0], module)
        shutil.copytree(built_module, "%s/%s/packages/plugins/%s" % (DIST_DIR, PACKAGE_NAME, module))
        if platform == "osx":
            # Need to put it into he OSX bundle as well
            shutil.copytree(built_module, "%s/%s.app/Contents/Resources/packages/plugins/%s" % (DIST_DIR, PACKAGE_NAME, module))            
        os.chdir(cwd_orig)
    print("  - DONE\n")
    
def bundle_fabber():
    # Bundle Fabber libraries/executables when creating a maxi-package
    print("  - Bundling Fabber code...")
    fabberdir = os.path.join(DIST_DIR, PACKAGE_NAME, "fabberdir")
    bindir = os.path.join(fabberdir, "bin")
    libdir = os.path.join(fabberdir, "lib")
    os.makedirs(bindir)
    os.makedirs(libdir)

    import fabber
    main_lib, main_exe, model_libs, model_exes = fabber.find_fabber()
    for f in [main_lib,] + list(model_libs.values()):
        shutil.copy(f, libdir)
        print("    - %s -> %s" % (f, libdir))
    for f in [main_exe,] + list(model_exes.values()):
        shutil.copy(f, bindir)
        print("    - %s -> %s" % (f, bindir))
    print("  - DONE\n")

# Clean up any previous distribution
shutil.rmtree("%s/dist" % ROOT_DIR, ignore_errors=True)

# Get the version number in standard format
from update_version import update_version
full_version, std_version = update_version(PACKAGE_NAME, ROOT_DIR)
version_pkg_fname = std_version
if "--snapshot" in sys.argv:
    version_pkg_fname = "snapshot"

# Make sure version number and license is embedded in module
os.system("python setup.py build 2>%s/build.err 1>%s/build.log" % (PACKAGING_DIR, PACKAGING_DIR))

# Freeze the main application
sys.stdout.write("Freezing code...")
sys.stdout.flush()
os.system("pyinstaller -y %s/%s.spec 2>%s/freeze.err 1>%s/freeze.log" % (PACKAGING_DIR, PACKAGE_NAME, PACKAGING_DIR, PACKAGING_DIR))
print("DONE")

if "--maxi" in sys.argv:
    print("Creating a maxi-package")
    version_pkg_fname += "-maxi"
    bundle_fabber()
    bundle_plugins()

# Create a simple archive package
sys.stdout.write("Creating compressed archive...")
sys.stdout.flush()
shutil.make_archive("%s/%s-%s-%s" % (DIST_DIR, PACKAGE_NAME, version_pkg_fname, platform), 
                    ARCHIVE_METHOD, "%s/%s" % (DIST_DIR, PACKAGE_NAME))
print("DONE")

# Create a platform-specific package
if PLATFORM_PACKAGE_BUILDFN is not None:
    sys.stdout.write("Creating platform-specific package...")
    sys.stdout.flush()
    PLATFORM_PACKAGE_BUILDFN(DIST_DIR, PACKAGING_DIR, std_version, platform, version_pkg_fname)
    print("DONE")
