.. _install:

Installation of Quantiphyse
===========================

Quantiphyse is in PyPi. If you have Python and 'pip' working, installation 
*may* be as simple as::

    pip install quantiphyse

In practice it *not* always as simple as this. So, below are a number of 'recipes' 
for different platforms which have been verified to work. If you find a problem with 
one of these recipes, please report it using the
`Issue Tracker <https://github.com/ibme-qubic/quantiphyse/issues>`_.

.. note::
    To use some plugins you'll need to have a working ``FSL`` installation. For more 
    information go to `FSL installation <https://fsl.fmrib.ox.ac.uk/fsl/fslwiki/FslInstallation>`_.

.. note::
    Installable packages for Windows, Mac and Ubuntu are also available from 
    `OUI <https://process.innovation.ox.ac.uk/software/>`_. These are
    generally slightly behind the latest version however installation may be more straightforward.

.. contents:: Platforms
    :local:

FSL
---

If you have FSL v6 or later you can install Quantiphyse into the ``fslpython`` environment::

    fslpython -m pip install quantiphyse --user

And for the plugins::

    fslpython -m pip install quantiphyse-cest quantiphyse-asl quantiphyse-qbold quantiphyse-dce quantiphyse-dsc quantiphyse-t1 quantiphyse-fsl quantiphyse-sv quantiphyse-perfsim --user

Some of the plugins may require build tools to be installed. If you get issues, see the additional requirements above for your platform (e.g. Ubuntu, Centos).

Ubuntu 16.04
------------

From a terminal window::

    sudo easy_install pip

Now install the application::

    pip install quantiphyse --user

The recipe above just installs the main application. To install plugins use::

    pip install quantiphyse-cest quantiphyse-asl quantiphyse-qbold quantiphyse-dce quantiphyse-dsc quantiphyse-t1 quantiphyse-fsl quantiphyse-sv quantiphyse-perfsim --user

Alternatively, you can use `Anaconda`_ in Ubuntu.

Ubuntu 18.04
------------

From a terminal window::

    sudo apt install python-pip

Now install the application::

    pip install quantiphyse --user

The recipe above just installs the main application. To install plugins use::

    pip install quantiphyse-cest quantiphyse-asl quantiphyse-qbold quantiphyse-dce quantiphyse-dsc quantiphyse-t1 quantiphyse-fsl quantiphyse-sv quantiphyse-perfsim --user

.. note::
    In some cases on Ubuntu 18.04 you may find that 'quantiphyse' will not run from
    the command line until you have either logged out and back in again or run
    ``source $HOME/.profile`` at the command prompt.

Alternatively, you can use `Anaconda`_ in Ubuntu.

Centos 7
--------

This recipe was tested in a Gnome Desktop installation. Open a terminal window and
use the following::

    sudo easy_install pip
    pip install quantiphyse --user

The recipe above just installs the main application. To install plugins use::

    sudo yum install gcc-c++ python-devel
    sudo pip install setuptools --upgrade
    pip install quantiphyse-cest quantiphyse-asl quantiphyse-qbold quantiphyse-dce quantiphyse-dsc quantiphyse-t1 quantiphyse-fsl quantiphyse-sv quantiphyse-perfsim --user

Alternatively, you can use `Anaconda`_ in Centos.

Mac OSX
-------

`Anaconda`_ has been the usual method we have used to install Quantiphyse on Mac due
to poor support for recent versions of Python on Mac.

However, on recent releases of OSX (e.g. Mojave) you can install Quantiphyse into the
system Python::

    pip install quantiphyse --user

And for the plugins::

    pip install quantiphyse-cest quantiphyse-asl quantiphyse-qbold quantiphyse-dce quantiphyse-dsc quantiphyse-t1 quantiphyse-fsl quantiphyse-sv quantiphyse-perfsim --user

The only issue with this is that the Quantiphyse executable is installed in a location which is not
in the user's PATH - typically ``$HOME/Library/Python2.7/bin/``. So you either need to run
Quantiphyse from that folder, or add this folder to your PATH by editing ``$HOME/.bash_profile``::

    export PATH=$PATH:$HOME/Library/Python2.7/bin/

Note that currently we do not have an easy way of adding Quantiphyse to the dock - one method
is to create an Automator application which runs the executable.

If you have experience of installation using Homebrew please
contact us with your recipe and we can add it here.

Windows
-------

On Windows we strongly recommend using `Anaconda`_. Note that FSL is not available natively
for Windows which will restrict the functionality of some of the plugins. 

We have not yet tested Quantiphyse with FSL installed in the Windows Subsystem for Linux - 
please let us know if you have tried this.

Use of virtualenv
-----------------

``virtualenv`` is a tool for creating isolated Python environments. It can be preferable to installing
applications in the system Python environment. You can use ``virtualenv`` on most platforms - for example
to install into Ubuntu use::

    sudo apt install python-virtualenv

Once installed you have to create and 'activate' the environment before installing applications::

    virtualenv $HOME/venvs/qp
    source $HOME/venvs/qp/bin/activate
    pip install quantiphyse

To install Quantiphyse plugins use::

    pip install quantiphyse-cest quantiphyse-asl quantiphyse-qbold quantiphyse-dce quantiphyse-dsc quantiphyse-t1 quantiphyse-fsl quantiphyse-sv quantiphyse-perfsim --user

When you have finished using a virtualenv you must 'deactivate' it by simply running::

    deactivate

To run an application installed in a virtualenv it must be activated first, e.g.::

    source $HOME/venvs/qp/bin/activate
    quantiphyse

.. note::
    Some Quantiphyse plugins require a C++ compiler to build extensions. You may need to install this
    before you can install the plugins. See the Ubuntu and Centos sections above for examples of how
    to install a C++ compiler on these platforms. 

Anaconda
--------

Anaconda (`<https://www.anaconda.org>`_) is an easy to install distribution of Python which
also includes the ``conda`` tool for installing packages. 

You will need to install the Anaconda environment before using any of these recipes.
When selecting a Python version, ``Python 2.7`` is the version on which Quantiphyse
has been most tested, however you can also use ``python 3.x``. We intend to make
Quantiphyse compatible with both version of Python for the foreseeable future
although we are currently moving to Python 3 as the main development platform.

Once Anaconda is installed, follow the instructions in the relevant section below:

.. note::
    In the future we hope to put Quantiphyse into conda itself so the whole
    process can consist of ``conda install quantiphyse``.  

Anaconda Python 2.7
~~~~~~~~~~~~~~~~~~~

On Windows you must first install Visual C++ for Python 2.7 from:

http://aka.ms/vcpython27
    
Then use the following commands::

    conda create -n qp python=2.7
    conda activate qp
    conda install -c conda-forge cython funcsigs matplotlib nibabel numpy pillow pyside2 pyyaml requests scipy scikit-learn scikit-image setuptools six pandas deprecation
    pip install pyqtgraph-qp
    pip install quantiphyse --no-deps

This installs the basic Quantiphyse app. To install plugins use pip, for example this is to install all current
plugins::

    pip install quantiphyse-cest quantiphyse-asl quantiphyse-qbold quantiphyse-dce quantiphyse-dsc quantiphyse-t1 quantiphyse-fsl quantiphyse-sv quantiphyse-perfsim 

On Mac you will also need to do::

    pip install pyobjc

Anaconda Python 3.x
~~~~~~~~~~~~~~~~~~~

On Windows you must first install Visual C++ tools for Python 3 from:

https://visualstudio.microsoft.com/downloads/#build-tools-for-visual-studio-2019

Then use the following commands::

    conda create -n qp python=3
    conda activate qp
    conda install -c conda-forge cython funcsigs matplotlib nibabel numpy pillow pyside2 pyyaml requests scipy scikit-learn scikit-image setuptools six pandas deprecation
    pip install pyqtgraph-qp
    pip install quantiphyse --no-deps

This installs the basic Quantiphyse app. To install plugins use pip, for example this is to install all current
plugins::

    pip install quantiphyse-cest quantiphyse-asl quantiphyse-qbold quantiphyse-dce quantiphyse-dsc quantiphyse-t1 quantiphyse-fsl quantiphyse-sv quantiphyse-perfsim 

On Mac you will also need to do::

    pip install pyobjc

Anaconda Python 3.x (dependencies from pip)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

This variation takes dependencies from ``pip`` rather than conda. Normally it is preferable to use
``conda`` for dependencies as you can run into problems when using different package managers for the
same package. However you may want to try this recipe if the previous ones do not work for you.
(but please `tell us as well <https://github.com/ibme-qubic/quantiphyse/issues>`_ so we can fix 
the instructions!)::

On Windows you must first install Visual C++ tools for Python 3 from:

https://visualstudio.microsoft.com/downloads/#build-tools-for-visual-studio-2019

Then use the following commands::

    conda create -n qp python=3
    conda activate qp
    pip install quantiphyse

This installs the basic Quantiphyse app. To install plugins use pip, for example this is to install all current
plugins::

    pip install quantiphyse-cest quantiphyse-asl quantiphyse-qbold quantiphyse-dce quantiphyse-dsc quantiphyse-t1 quantiphyse-fsl quantiphyse-sv quantiphyse-perfsim 

On Mac you will also need to do::

    pip install pyobjc

Docker image
------------

This is a new and currently experimental method of running Quantiphyse.

If you've not used Docker before, it's a means of running applications in an isolated environment with pre-installed 
dependencies - rather like a virtual machine but using the existing operating system rather than needing one
of its own.

The easiest way to try Quantiphyse through docker is to first install docker itself - e.g. on Ubuntu you'd do::

    sudo apt install docker

Then clone the github repository:

https://github.com/ibme-qubic/quantiphyse-docker

and run the script::

    python quantiphyse-docker.py

This will download and run a Quantiphyse image. Although you need Python to run the script it does not use
anything outside the standard library so any version should do.

Currently the Quantiphyse docker image does not have its own copy of FSL - instead it tries to use the one
installed on your machine currently. This will only work if your machine is binary compatible with Ubuntu. Centos
should be OK, but Mac is not, so you will not be able to use FSL functionality on Mac. We hope to offer an FSL-included
version in the future.

Please let us know if you try this method and how you get on with it.
