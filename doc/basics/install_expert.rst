.. _install_expert:

Other options for Quantiphyse installation
==========================================

Quantiphyse is in PyPi. So, in general, if you have Python and ``pip`` working, installation 
*may* be as simple as::

    pip install quantiphyse

In practice it *not* always as simple as this. Below are a number of 'recipes' 
for different platforms which we believe to work. However we cannot guarantee that these
will work in all cases.

.. note::
    These instructions are intended for experienced users with a good knowledge of Python
    environments and packages. If this is not you then please stick to the standard
    instructions in :ref:`install`

.. note::
    To use some plugins you'll need to have a working ``FSL`` installation. For more 
    information go to `FSL installation <https://fsl.fmrib.ox.ac.uk/fsl/fslwiki/FslInstallation>`_.

.. contents:: Platforms
    :local:

FSL
---

If you have FSL v6 or later you can install Quantiphyse using ``fslpython``::

    fslpython -m pip install quantiphyse --user

And for the plugins::

    fslpython -m pip install quantiphyse-cest quantiphyse-asl quantiphyse-qbold quantiphyse-dce quantiphyse-dsc quantiphyse-t1 quantiphyse-fsl quantiphyse-sv quantiphyse-datasim quantiphyse-deeds --user

Some of the plugins may require build tools to be installed. If you get issues, see the additional requirements above for your platform (e.g. Ubuntu, Centos).

.. warning::
    In general we do not recommed using ``--user`` with ``pip``. It will install packages in your home
    directory but they will be visible to *any* python environment with the same version as the one you
    used to do the install. This often causes problems if you also have other Python environments
    on your system (e.g. from Conda).

Ubuntu 16.04 - System python
----------------------------

From a terminal window::

    sudo easy_install pip

Now install the application::

    pip install quantiphyse --user

The recipe above just installs the main application. To install plugins use::

    pip install quantiphyse-cest quantiphyse-asl quantiphyse-qbold quantiphyse-dce quantiphyse-dsc quantiphyse-t1 quantiphyse-fsl quantiphyse-sv quantiphyse-datasim quantiphyse-deeds --user

.. note::
    See also the previous comments on the use of ``--user``

Ubuntu 18.04 - System python
----------------------------

From a terminal window::

    sudo apt install python-pip

Now install the application::

    pip install quantiphyse --user

The recipe above just installs the main application. To install plugins use::

    pip install quantiphyse-cest quantiphyse-asl quantiphyse-qbold quantiphyse-dce quantiphyse-dsc quantiphyse-t1 quantiphyse-fsl quantiphyse-sv quantiphyse-datasim quantiphyse-deeds --user

.. note::
    In some cases on Ubuntu 18.04 you may find that 'quantiphyse' will not run from
    the command line until you have either logged out and back in again or run
    ``source $HOME/.profile`` at the command prompt.

.. note::
    See also the previous comments on the use of ``--user``

Centos 7 - System python
------------------------

This recipe was tested in a Gnome Desktop installation. Open a terminal window and
use the following::

    sudo easy_install pip
    pip install quantiphyse --user

The recipe above just installs the main application. To install plugins use::

    sudo yum install gcc-c++ python-devel
    sudo pip install setuptools --upgrade
    pip install quantiphyse-cest quantiphyse-asl quantiphyse-qbold quantiphyse-dce quantiphyse-dsc quantiphyse-t1 quantiphyse-fsl quantiphyse-sv quantiphyse-datasim quantiphyse-deeds --user

.. note::
    See also the previous comments on the use of ``--user``

Mac OSX
-------

`Anaconda`_ has been the usual method we have used to install Quantiphyse on Mac due
to poor support for recent versions of Python on Mac.

However, on recent releases of OSX (e.g. Mojave) it may be possible to install Quantiphyse into the
system Python using::

    pip install quantiphyse --user

And for the plugins::

    pip install quantiphyse-cest quantiphyse-asl quantiphyse-qbold quantiphyse-dce quantiphyse-dsc quantiphyse-t1 quantiphyse-fsl quantiphyse-sv quantiphyse-datasim quantiphyse-deeds --user

.. note::
    Installation into ``fslpython`` is likely to be a more reliable method on Mac if you 
    have FSL. While the above method has worked for some users, we have also had issues with
    incompatible Numpy and Scipy packages that may cause problems with the system python on Mac.
    See also the previous comments on the use of ``--user``

One issue with this is that the Quantiphyse executable is installed in a location which is not
in the user's PATH - typically ``$HOME/Library/Python2.7/bin/``. So you either need to run
Quantiphyse from that folder, or add this folder to your PATH by editing ``$HOME/.bash_profile``::

    export PATH=$PATH:$HOME/Library/Python2.7/bin/

Note that currently we do not have an easy way of adding Quantiphyse to the dock - one method
is to create an Automator application which runs the executable.

If you have experience of installation using Homebrew please
contact us with your recipe and we can add it here.

Windows
-------

On Windows we strongly recommend using `Anaconda`_. 

FSL does not run natively on Windows, however it can be installed in the *Windows Subsystem for Linux* (WSL).
If you have FSL installed in Windows and Quantiphyse installed in Anaconda you will need to set ``FSLDIR``
to be a UNC path to the FSLDIR in WSL. You can do this from one of the FSL widgets in Quantiphyse. You
will need to browse to the location ``\\wsl$\`` and from there select your WSL distribution folder
(e.g. ``Ubuntu-18.04``) and then the FSL location in that distribution (e.g. ``/usr/local/fsl``). Once
done, Quantiphyse will use the FSL applications installed in WSL transparently.

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

    pip install quantiphyse-cest quantiphyse-asl quantiphyse-qbold quantiphyse-dce quantiphyse-dsc quantiphyse-t1 quantiphyse-fsl quantiphyse-sv quantiphyse-datasim quantiphyse-deeds --user

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
When selecting a Python version, ``Python 3.7`` is the version on which Quantiphyse
has been most tested, however you can also use other versions. We no longer guarantee
that the application will run under Python 2.7 although we are not aware of any 
incompatibilities within quantiphyse itself.

Once Anaconda is installed, follow the instructions in the relevant section below:

.. note::
    In the future we hope to put Quantiphyse into conda itself so the whole
    process can consist of ``conda install quantiphyse``.  

Anaconda Python 3.7
~~~~~~~~~~~~~~~~~~~

We recommend Python 3.7 as a reasonably up to date version of Python for which dependencies are generally widely
available. While Quantiphyse should be compatible with newer Python releases sometimes it is difficult to get
matching versions of important dependencies such as Numpy.

On Windows you must first install Visual C++ tools for Python 3 from:

https://visualstudio.microsoft.com/downloads/#build-tools-for-visual-studio-2019

Then use the following commands::

    conda create -n qp python=3.7
    conda activate qp
    conda install -c conda-forge cython funcsigs matplotlib nibabel numpy pillow pyside2 pyyaml requests scipy scikit-learn scikit-image setuptools six pandas deprecation
    pip install pyqtgraph-qp
    pip install quantiphyse --no-deps

This installs the basic Quantiphyse app. To install plugins use pip, for example this is to install all current
plugins::

    pip install quantiphyse-cest quantiphyse-asl quantiphyse-qbold quantiphyse-dce quantiphyse-dsc quantiphyse-t1 quantiphyse-fsl quantiphyse-sv quantiphyse-datasim quantiphyse-deeds 

On Mac you will also need to do::

    pip install pyobjc

Anaconda Python 3.7 (dependencies from pip)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

This variation takes dependencies from ``pip`` rather than conda. Normally it is preferable to use
``conda`` for dependencies as you can run into problems when using different package managers for the
same package. However you may want to try this recipe if the previous ones do not work for you.
(but please `tell us as well <https://github.com/physimals/quantiphyse/issues>`_ so we can fix 
the instructions!)::

On Windows you must first install Visual C++ tools for Python 3 from:

https://visualstudio.microsoft.com/downloads/#build-tools-for-visual-studio-2019

Then use the following commands::

    conda create -n qp python=3.7
    conda activate qp
    pip install quantiphyse

This installs the basic Quantiphyse app. To install plugins use pip, for example this is to install all current
plugins::

    pip install quantiphyse-cest quantiphyse-asl quantiphyse-qbold quantiphyse-dce quantiphyse-dsc quantiphyse-t1 quantiphyse-fsl quantiphyse-sv quantiphyse-datasim quantiphyse-deeds 

On Mac you will also need to do::

    pip install pyobjc

Anaconda Python 2.7
~~~~~~~~~~~~~~~~~~~

Quantiphyse is compatible with the widely used Python 2.7, although this is now getting rather old
and is no longer recommended unless you have a special need for it.

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

    pip install quantiphyse-cest quantiphyse-asl quantiphyse-qbold quantiphyse-dce quantiphyse-dsc quantiphyse-t1 quantiphyse-fsl quantiphyse-sv quantiphyse-datasim quantiphyse-deeds 

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

https://github.com/physimals/quantiphyse-docker

and run the script::

    python quantiphyse-docker.py

This will download and run a Quantiphyse image. Although you need Python to run the script it does not use
anything outside the standard library so any version should do.

Currently the Quantiphyse docker image does not have its own copy of FSL - instead it tries to use the one
installed on your machine currently. This will only work if your machine is binary compatible with Ubuntu. Centos
should be OK, but Mac is not, so you will not be able to use FSL functionality on Mac. We hope to offer an FSL-included
version in the future.

Please let us know if you try this method and how you get on with it.
