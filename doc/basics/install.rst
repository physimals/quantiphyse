.. _install:

Installation of Quantiphyse
===========================

Quantiphyse is in PyPi and therefore *in principle* if you have Python, installation 
is as simple as::

    pip install quantiphyse

In practice it is often *not* as simple as this. The main reason is ``PySide`` 
(the library we use for the user interface). This needs to be compiled against
a rather old version of the QT GUI library which requires separate installation. 

Alternatively a binary version of PySide can
be installed but a suitable package isn't available for every version of Python.
   
Below are a number of 'recipes' for different platforms which have been verified to 
work. If you find a problem with one of these recipes, please report it using the
`Issue Tracker <https://github.com/ibme-qubic/quantiphyse/issues>`_.

.. note::
    To use some plugins you'll need to have a working ``FSL`` installation. For more 
    information go to `FSL installation <https://fsl.fmrib.ox.ac.uk/fsl/fslwiki/FslInstallation>`_.

.. contents:: Platforms
    :local:

Ubuntu 16.04 / 18.04
--------------------

From a terminal window::

    sudo apt install libqt4-dev qt4-qmake cmake python-dev python-setuptools

To install pip on Ubuntu 16.04::

    sudo easy_install pip

On Ubuntu 18.04::

    sudo apt install python-pip

Now install the application:

    pip install quantiphyse --user

The last step will take a while! The PySide GUI library is being built - the 
terminal will show::

    Running setup.py install for PySide ... |

Go get a coffee and come back later.

The recipe above just installs the main application. To install plugins use::

    pip install quantiphyse-cest quantiphyse-asl quantiphyse-cest quantiphyse-dce quantiphyse-dsc quantiphyse-t1 quantiphyse-fsl quantiphyse-sv --user
    pip install deprecation==1.2 --user

The last step corrects a startup problem caused by a dependency - see the :ref:`faq` for
more information. 

Alternatively, you can use `Anaconda`_ in Ubuntu. 

You can also use the method above in a virtualenv or a Conda environment. To do this:

 - Run the first ``sudo apt install`` command above
 - Create and activate a Conda or virtual environment, e.g. as described in the `Anaconda`_ section
 - Run the ``pip install`` commands above

This is a slightly better method as it keeps Quantiphyse and all it's dependencies in an isolated
environment, however it does mean you will need to activate the environment in order to run 
Quantiphyse.

Centos 7
--------

This recipe was tested in a Gnome Desktop installation. Open a terminal window and use the following::

    sudo yum install qt-devel cmake python-devel gcc gcc-c++
    sudo easy_install pip
    pip install cython numpy six==1.10.0 setuptools --upgrade --user
    pip install quantiphyse --user

The last step will take a while! The PySide GUI library is being built - the 
terminal will show::

    Running setup.py install for PySide ... |

Go watch some cat videos and come back later. 

The recipe above just installs the main application. To install plugins use::

    pip install quantiphyse-cest quantiphyse-asl quantiphyse-cest quantiphyse-dce quantiphyse-dsc quantiphyse-t1 quantiphyse-fsl --user
    pip install deprecation==1.2 --user

The last step corrects a startup problem caused by a dependency - see the :ref:`faq` for
more information. 

Alternatively, you can use `Anaconda`_ in Ubuntu.

Windows
-------

On Windows we strongly recommend using the Anaconda python distribution 
to install Python - see `Anaconda`_ below.

Mac OSX
-------

On Mac we recommend either the Anaconda python distribution - see 
`Anaconda`_ or `Homebrew`_. The system python has 
difficulties installing ``PySide`` due to the old version of Qt that 
is required.

Homebrew
--------

To be completed...

Anaconda
--------

Anaconda (`<https://www.anaconda.org>`_) is an easy to install distribuction of Python which
also includes the ``conda`` tool for installing packages. We find ``conda`` generally better than 
``pip`` for dependency management and binary packages such as ``pyside``. Anaconda can
be installed on Windows, Mac and Linux.

You will need to install the Anaconda environment before using any of these recipes.
When selecting a Python version, ``Python 2.7`` is the version on which Quantiphyse
has been most tested, however you can also use ``python 3.x``. We intend to make
Quantiphyse compatible with both version of Python for the foreseeable future
although we are currently moving to Python 3 as the main development platform.

Once installed, use the following commands from a command prompt::

    conda create -n qp
    conda activate qp
    conda config --add channels conda-forge
    conda install cython funcsigs matplotlib nibabel numpy pillow pyqtgraph pyside pyyaml requests scipy scikit-learn scikit-image setuptools six pandas deprecation
    pip install quantiphyse --no-deps

This installs the basic Quantiphyse app. To install plugins use pip, for example this is to install all current
plugins::

    pip install quantiphyse-cest quantiphyse-asl quantiphyse-cest quantiphyse-dce quantiphyse-dsc quantiphyse-t1 quantiphyse-fsl quantiphyse-sv
    pip install deprecation==1.2

The last step corrects a startup problem caused by a dependency - see the :ref:`faq` for
more information.

In the future we hope to put Quantiphyse into conda itself so the whole
process can consist of ``conda install quantiphyse``.  




