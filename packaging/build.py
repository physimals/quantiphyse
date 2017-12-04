"""
Master build script for Quantiphyse packages

Can specify:
  --snapshot to name packages as 'snapshot' rather than embedding the version number
  --maxi to bundle selected plugins (Basically the Fabber frontends)
"""
import os, sys
import shutil

pkgdir = os.path.abspath(os.path.dirname(__file__))
rootdir = os.path.abspath(os.path.join(pkgdir, os.pardir))
distdir = os.path.join(rootdir, "dist")
package_name = "quantiphyse"

sys.path.append(rootdir)

archive_method="zip"
build_platform_package=None
if sys.platform.startswith("win"):
    platform="win32"
    import create_msi
    build_platform_package = create_msi.create_msi
elif sys.platform.startswith("linux"):
    #distro=platform.linux_distribution()[0].split()[0].lower()
    platform="linux"
    archive_method="gztar"
    import create_deb
    build_platform_package = create_deb.create_deb
elif sys.platform.startswith("darwin"):
    platform="osx"
    import create_dmg
    build_platform_package = create_dmg.create_dmg

os.system("rm -rf %s/dist" % rootdir)

from update_version import update_version
full_version, std_version = update_version(package_name, rootdir)

sys.stdout.write("Building extensions...")
sys.stdout.flush()
os.system("python %s/setup.py build_ext --inplace --force 2>%s/build.err 1>%s/build.log" % (rootdir, pkgdir, pkgdir))
print("DONE")

sys.stdout.write("Freezing code...")
sys.stdout.flush()
os.system("pyinstaller -y %s/%s.spec 2>%s/freeze.err 1>%s/freeze.log" % (pkgdir, package_name, pkgdir, pkgdir))
print("DONE")

if "--maxi" in sys.argv:
    print("Creating a maxi-package")
    # This is necessarily a bit of a hack but so is the concept of a maxi-package
    plugins = ["fabber-ap", "basil-qp", "quanticest"]
    for plugin in plugins:
        sys.stdout.write("  - Building and bundling %s..." % plugin)
        sys.stdout.flush()
        plugindir = os.path.join(rootdir, os.pardir, plugin)
        os.system("python %s/packaging/build.py" % plugindir)
        shutil.copytree("%s/dist/%s" % (plugin, plugin), 
                        "%s/%s/packages/plugins/%s" % (rootdir, package_name, plugin))
        if platform == "osx":
            # Need to put it into he OSX bundle as well
            shutil.copytree("%s/dist/%s" (plugin, plugin), 
                            "%s/%s.app/Contents/Resources/packages/plugins/%s" % (rootdir, package_name, plugin))            
        print("DONE")

version_pkg_fname = std_version
if "--snapshot" in sys.argv:
    version_pkg_fname = "snapshot"
    
sys.stdout.write("Creating compressed archive...")
sys.stdout.flush()
shutil.make_archive("%s/%s-%s-%s" % (distdir, package_name, version_pkg_fname, platform), 
                    archive_method, "%s/%s" % (distdir, package_name))
print("DONE")

if build_platform_package is not None:
    sys.stdout.write("Creating platform-specific package...")
    sys.stdout.flush()
    build_platform_package(distdir, pkgdir, std_version, platform, version_pkg_fname)
    print("DONE")
