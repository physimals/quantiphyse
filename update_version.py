#!/bin/env python

import os
import sys
import subprocess
import re

def update_version():
    script_dir = os.path.dirname(__file__)
    qpdir = os.path.abspath(os.path.join(script_dir, "quantiphyse"))

    version = subprocess.check_output('git describe --dirty').strip(" \n")

    vfile = open(os.path.join(qpdir, "_version.py"), "w")
    vfile.write("__version__='%s'" % version)
    vfile.close()
    return version

def get_std_version():
    """ 
    Get standardized version string in form maj.min.patch-release
    """
    v = update_version()
    p = re.compile("v?(\d+\.\d+\.\d+-\d+).*")
    m = p.match(v)
    if m is not None:
        return  m.group(1)
    else:
        raise RuntimeError("Failed to parse version string %s" % version)

if __name__ == '__main__':
    print("Version updated to %s" % update_version())
