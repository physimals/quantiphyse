"""
Run all the examples
"""

import sys
import os
import glob

script_dir = os.path.abspath(os.path.dirname(__file__))

qpdir = os.path.abspath(os.path.join(script_dir, os.pardir, os.pardir))

examples = glob.glob(os.path.join(qpdir, "examples", "*.yaml"))
for ex in examples:
    print("**** Running example: %s" % ex)
    os.system("python %s/qp.py --batch=%s" % (qpdir, ex))
