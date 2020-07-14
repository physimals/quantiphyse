"""
Quantiphyse installation/upgrade script

Intended to work on Mac and Linux. Windows problem because
we can't assume Python installed.

Should run with any python >= 2.7 and without any dependencies
outside the standard library.
"""
import sys
import os
import subprocess

MAIN_PKG = "quantiphyse"
PLUGINS = "quantiphyse-cest quantiphyse-asl quantiphyse-qbold quantiphyse-dce quantiphyse-dsc quantiphyse-t1 quantiphyse-fsl quantiphyse-sv quantiphyse-perfsim"

# These are things that we may want to upgrade if the user has
# old version of them lying around
DEPS_TO_UPGRADE = "oxasl oxasl-mp oxasl-ve oxasl-enable pyfab"

# Python 2/3 compatibility
try:
    input = raw_input
except NameError: 
    pass

def main():
    print("\nWelcome to Quantiphyse installation")
    print("===================================\n")
    if mac():
        print("I see you have an Apple Mac")
        install_mac_linux()
    elif linux():
        print("I see you are using Linux")
        install_mac_linux()
    elif win():
        sys.stderr.write("Windows installation is not currently supported by this script")
        sys.exit(1)
    else:
        sys.stderr.write("Unknown platform: %s" % sys.platform)
        sys.exit(1)

def mac():
    return sys.platform.startswith("darwin")

def linux():
    return sys.platform.startswith("linux")
    
def win():
    return sys.platform.startswith("win")
    
def boolstr(str, default_accept=False):
    if str.strip() == "":
        return default_accept
    else:
        return str.lower() in ("y", "yes", "yep", "ok")

def install_mac_linux():
    choices = []
    existing = []

    fsldir, version, qpversion = find_fsl()
    if fsldir:
        print("FSL found at %s (v%s)" % (fsldir, version))
        pythonexe = os.path.join(fsldir, "bin", "fslpython")
        if os.path.isfile(pythonexe):
            choices.append(("FSL python (may require admin permissions)", "fsl", pythonexe))
            recommended = len(choices) - 1
            if qpversion:
                existing.append((qpversion, "FSL python", "fsl", pythonexe))
        else:
            print(" - WARNING could not find $FSLDIR/bin/fslpython, you may have a broken FSL installation")

    conda, envs = find_conda()
    if conda:
        print("Conda found at %s (%i environments found)" % (conda, len(envs)))
        choices.append(("New conda environment", "condanew", conda))
        recommended = len(choices) - 1
        if len(envs) > 0:
            choices.append(("Existing conda environment", "condaold", conda))
        for envname in envs.keys():
            envdir, qpversion = envs[envname]
            if fsldir and envdir.startswith(fsldir):
                continue
            if qpversion:
                existing.append((qpversion, "Conda environment: %s" % envname, "condaup", envdir))

    if "--include-system" in sys.argv:
        pythonexes = find_system()
        for exe, version, qpversion in pythonexes:
            choices.append(("System python: %s (may require admin permissions)" % exe, "system", exe))
            if qpversion:
                existing.append((qpversion, "System python", "system", exe))

    uninstall = False
    if "--uninstall" in sys.argv:
        valid = False
        while existing and not valid:
            print("\nType number to uninstall existing Quantiphyse installation")
            for idx, existingqp in enumerate(existing):
                qpversion, name, pytype, install_data = existingqp
                print("%i: %s %s (Quantiphyse %s)" % (idx+1, name, install_data, qpversion))
            print("%i: Don't remove" % (len(existing)+1))
            choice = input()
            try:
                choice = int(choice)
                if choice >= 1 and choice <= len(existing)+1:
                    valid = True
            except:
                pass

            if valid and choice <= len(existing):
                qpversion, name, pytype, install_data = existing[choice-1]
                print("\nUninstalling Quantiphyse from %s %s" % (pytype, install_data))
                uninstall = True
            else:
                print("Aborted\n")
                sys.exit(0)

    upgrade = False
    if not uninstall:
        valid = False
        while existing and not valid:
            print("\nExisting Quantiphyse installations found - type number to upgrade or install new")
            for idx, existingqp in enumerate(existing):
                qpversion, name, pytype, install_data = existingqp
                print("%i: %s %s (Quantiphyse %s)" % (idx+1, name, install_data, qpversion))
            print("%i: Don't upgrade - create a new installation" % (len(existing)+1))
            choice = input()
            try:
                choice = int(choice)
                if choice >= 1 and choice <= len(existing)+1:
                    valid = True
            except:
                pass

        if valid and choice <= len(existing):
            qpversion, name, pytype, install_data = existing[choice-1]
            print("\nUpgrading Quantiphyse in %s %s" % (pytype, install_data))
            upgrade = True

    if not upgrade and not uninstall:
        valid = False
        while not valid:
            print("\nInstallation choices - type number to choose [%i]:" % (recommended+1))
            for idx, choice in enumerate(choices):
                print("%i: %s %s" % (idx+1, choice[0], "(recommended - default)" if idx == recommended else ""))
            choice = input()
            if choice == "":
                choice = recommended+1
            try:
                choice = int(choice)
                if choice >= 1 and choice <= len(choices):
                    valid = True
                    name, pytype, install_data = choices[choice-1]
            except:
                pass

            if not valid:
                print("Type a number between 1 and %i" % len(choices))

    if pytype == "fsl":
        qpexe = fslpython_install(install_data, uninstall=uninstall)
    elif pytype == "condanew":
        qpexe = conda_install_new(install_data, envs)
    elif pytype == "condaold":
        qpexe = conda_install_existing(install_data, envs)
    elif pytype == "condaup":
        qpexe = conda_install(install_data, uninstall=uninstall)
    elif pytype == "system":
        install(install_data, user=True, uninstall=uninstall)
        qpexe = os.path.join(os.path.dirname(install_data), "quantiphyse")
    else:
        qpexe = None

    if not qpexe:
        sys.stderr.write("Installation aborted\n")
        sys.exit(1)

    if not uninstall:
        print("\nQuantiphyse executable is %s" % qpexe)
        if pytype != "system":
            accept = boolstr(input("\nDo you want to create an executable in /usr/local/bin? (may require admin permissions) [yes]: "), True)
            if accept:
                if os.path.exists("/usr/local/bin"):
                    accept = boolstr(input("/usr/local/bin/quantiphyse already exists - overwrite? [yes]: "), True)
                if accept:
                    retcode = os.system("sudo rm -f /usr/local/bin/quantiphyse")
                    retcode = retcode + os.system("sudo ln -s %s /usr/local/bin/quantiphyse" % qpexe)
                    if retcode != 0:
                        print("Failed to create /usr/local/bin/quantiphyse")
                    else:
                        print("/usr/local/bin/quantiphyse created")
                else:
                    print("/usr/local/bin/quantiphyse already exists: Not overwritten")
            else:
                print("/usr/local/bin/quantiphyse: Not created")

def fslpython_install(pythonexe, **kwargs):
    accept = boolstr(input("Installing into %s - OK? [yes]: " % pythonexe), True)
    if accept:
        # FIXME check fslpy version > 1.13 and uninstall user version if so
        install(pythonexe, sudo=True, **kwargs)
        # FIXME is this always right
        return os.path.join(os.environ["FSLDIR"], "fslpython", "envs", "fslpython", "bin", "quantiphyse")

def conda_install_new(condaexe, envs):
    default_envname = "qp"
    idx = 2
    while default_envname in envs.keys():
        default_envname = "qp%i" % idx
        idx += 1

    envname = input("Type name for new environment or hit ENTER to accept default [%s]: " % default_envname)
    if not envname:
        envname = default_envname
    accept = input("Installing into a new Conda environment named '%s' - is this OK? [yes]: " % envname)
    accept = boolstr(accept, True)
    if accept:
        # There is a bug with python 3.8 and pyside 5.13 and we need the latter
        # on Mac because pyside 5.15 has a bug that stops buttons working 
        # (gotta love computers...)
        os.system("%s create -n %s python=3.7 -y" % (condaexe, envname))
        conda, envs = find_conda()
        if envname not in envs.keys():
            sys.stderr.write("ERROR: Failed to create new conda environment\n")
            sys.exit(1)
        
        return conda_install(envs[envname][0])

def conda_install_existing(condaexe, envs):
    print("\nSelect environment to use")
    for idx, envname in enumerate(envs.keys()):
        print("%i: %s (%s)" % (idx+1, envname, envs[envname]))
    envdir = None
    while envdir is None:
        envname = input()
        if envname in envs:
            envdir = envs[envname]
        else:
            try:
                envidx = int(envname)
                if envidx > 0 and envidx <= len(envs.keys()):
                    envname = list(envs.keys())[envidx-1]
                    envdir = envs[envname][0]
            except:
                pass
        if envdir is None:
            print("Type the name or number of the environment you want to use")
    return conda_install(envdir)

def conda_install(envdir, **kwargs):
    pythonexe=os.path.join(envdir, "bin", "python")
    install(pythonexe, **kwargs)
    return os.path.join(envdir, "bin", "quantiphyse")

def install(pythonexe, **kwargs):
    print("Using %s" % pythonexe)
    uninstall = kwargs.get("uninstall", False)
    install_pip(pythonexe, MAIN_PKG, **kwargs)
    install_pip(pythonexe, PLUGINS, **kwargs)
    if not uninstall:
        install_pip(pythonexe, DEPS_TO_UPGRADE, **kwargs)
    if mac() and not uninstall:
        install_pip(pythonexe, "pyobjc", **kwargs)
        install_pip(pythonexe, "pyside2==5.13", **kwargs)

def file_contents(fname):
    f = open(fname)
    contents = f.read()
    try:
        return contents.decode("utf-8")
    except:
        return contents

def cmd_output(cmdargs):
    output = ""
    try:
        output = subprocess.check_output(cmdargs, stderr=subprocess.STDOUT)
        return output.decode('utf-8')
    except:
        return output

def possible_fsldir(fsldir):
    return (
        os.path.isdir(fsldir) 
        and os.path.isfile(os.path.join(fsldir, "bin", "fslmaths"))
        and os.path.isfile(os.path.join(fsldir, "fslpython", "envs", "fslpython", "bin", "python"))
    )

def find_conda():
    guesses = []

    if "CONDA_EXE" in os.environ:
        guesses.append(os.environ["CONDA_EXE"])

    if "FSLDIR" in os.environ:
        guesses.append(os.path.join(os.environ["FSLDIR"], "fslpython", "bin", "conda"))

    for condaexe in guesses:
        if os.path.isfile(condaexe):
            envs = {}
            envlist = cmd_output([condaexe, "env", "list"])
            for line in envlist.splitlines():
                envinfo = line.split()
                if len(envinfo) > 1 and envinfo[0].strip()[0] != '#':
                    envs[envinfo[0].strip()] = (envinfo[-1].strip(), None)

            for envname in envs.keys():
                envdir = envs[envname][0]
                pythonexe=os.path.join(envdir, "bin", "python")
                version = quantiphyse_installed(pythonexe)
                if version:
                    envs[envname] = (envdir, version)

            return condaexe, envs

    return None, None

def find_fsl():
    guesses = [
        "/usr/local/fsl",
        "/opt/fsl",
    ]
    if "FSLDIR" in os.environ:
        guesses.insert(0, os.environ["FSLDIR"])
    
    for fsldir in guesses:
        if possible_fsldir(fsldir):
            version = file_contents(os.path.join(fsldir, "etc", "fslversion"))
            qpversion = quantiphyse_installed(os.path.join(fsldir, "bin", "fslpython"))
            return fsldir, version, qpversion
    return None, None, None

def find_system():
    guesses = [
        "/usr/bin/python3",
        "/usr/bin/python",
        "/usr/bin/python2",
        "/usr/local/bin/python3",
        "/usr/local/bin/python",
        "/usr/local/bin/python2",
    ]
    exes = []
    for pythonexe in guesses:
        if os.path.isfile(pythonexe):
            version = cmd_output([pythonexe, "--version"]).strip()
            if version.startswith("Python"):
                qpversion = quantiphyse_installed(pythonexe)
                exes.append((pythonexe, version, qpversion))

    return exes

def quantiphyse_installed(pythonexe):
    output = cmd_output([pythonexe, "-c", "import quantiphyse; print(quantiphyse.__version__)"])
    return output.strip()

def install_pip(pythonexe, pkgs, user=False, force=False, sudo=False, uninstall=False):
    if uninstall:
        cmd = "uninstall"
        flags = ""
    else:
        cmd = "install"
        flags = "install --upgrade --upgrade-strategy only-if-needed"
    if user:
        flags += " --user"
    if force:
        flags += " --force-reinstall"
    if sudo:
        pythonexe = "sudo " + pythonexe
    cmd = "%s -m pip %s %s %s" % (pythonexe, cmd, pkgs, flags)
    print(cmd)
    ret = os.system(cmd)
    if ret != 0:
        sys.stderr.write("ERROR installing pip packages\n")
        sys.exit(1)

if __name__ == "__main__":
    main()
