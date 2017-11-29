import os, sys

pkgdir = os.path.abspath(os.path.dirname(__file__))
qpdir = os.path.abspath(os.path.join(pkgdir, os.pardir))
sys.path.append(qpdir)

os.system("rm -rf %s/dist" % qpdir)
os.system("python %s/update_version.py" % pkgdir)
print("Building extensions")
os.system("python %s/setup.py build_ext --inplace --force 2>%s/build.err 1>%s/build.log" % (qpdir, pkgdir, pkgdir))
print("Freezing code and creating packages")
os.system("pyinstaller -y %s/quantiphyse.spec 2>%s/freeze.err 1>%s/freeze.log" % (pkgdir, pkgdir, pkgdir))
