"""
Run all the examples
"""

import sys
import os
import glob

script_dir = os.path.abspath(os.path.dirname(__file__))

qpdir = os.path.abspath(os.path.join(script_dir, os.pardir, os.pardir))
os.chdir(qpdir)

examples = glob.glob(os.path.join(qpdir, "examples", "batch_scripts", "*.yaml"))
for ex in sorted(examples):
    print("**** Running example: %s" % ex)
    os.system("python -u qp.py --batch=%s" % ex)

