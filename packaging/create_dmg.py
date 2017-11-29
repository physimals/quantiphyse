"""
Create a DMG package for OSX based systems

This is a single-file disk image which contains the app bundle
"""
import os, sys
import shutil
import subprocess

DMG_SUBDIR = "dmg"

def create_dmg(distdir, pkgdir, version_str, sysname, version_str_display=None):
    if version_str_display == None:
        version_str_display = version_str

    formatting_values = {
        "version_str" : version_str,
        "version_str_display" : version_str_display,
        "bundle_dir" : os.path.join(distdir, "Quantiphyse.app"),
        "dmg_name" : os.path.join(distdir, "quantiphyse-%s.dmg" % version_str_display)
    }

    os.system('hdiutil create -volname Quantiphyse -srcfolder %(bundle_dir)s -ov -format UDZO %(dmg_name)s' % formatting_values)

if __name__ == "__main__":
    # Get absolute paths to the packaging dir and the root Quantiphyse dir
    pkgdir = os.path.abspath(os.path.dirname(__file__))
    qpdir = os.path.abspath(os.path.join(pkgdir, os.pardir))
    sys.path.append(qpdir)
    import update_version

    create_dmg(os.path.join(qpdir, "dist"), pkgdir,
               update_version.get_std_version(), 
               "osx")
