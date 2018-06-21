#!/bin/env python

import os
import sys
import subprocess
import re

def update_version(package_name, rootdir):
    # Full version includes the Git commit hash
    full_version = subprocess.check_output('git describe --dirty', shell=True).strip(" \n")
    vfile = open(os.path.join(rootdir, package_name, "_version.py"), "w")
    vfile.write("__version__='%s'" % full_version)
    vfile.close()

    # Standardized version in form major.minor.patch-build
    p = re.compile("v?(\d+\.\d+(\.\d+)?(-\d+)?).*")
    m = p.match(full_version)
    if m is not None:
        std_version = m.group(1)
    else:
        raise RuntimeError("Failed to parse version string %s" % full_version)

    return full_version, std_version
    
if __name__ == '__main__':
    script_dir = os.path.dirname(__file__)
    qpdir = os.path.abspath(os.path.join(script_dir, os.pardir))
    print("Version updated to %s" % update_version("quantiphyse", qpdir)[0])
