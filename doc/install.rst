Installation of Quantiphyse
===========================

Quantiphyse is in PyPi and therefore *in principle* if you have Python, installation 
is as simple as::

    pip install quantiphyse

In practice it is often *not* as simple as this. There are a couple of reasons for this:

 - Quantiphyse required ``cython`` and ``numpy`` to build it's own extensions. On
   Linux you may need to manually install these first (for Mac and Windows binary
   wheels are available which avoid this).
 - ``PySide`` (the library we use for the user interface) needs to be compiled against
   a rather old version of QT. Alternatively a binary version of this library can
   be installed but a suitable package isn't always available for every version of Python.
   
Below are a number of 'recipes' for different platforms which have been verified to 
work. 

Windows
-------

On Windows we strongly recommend using the Anaconda python distribution 
to install Python - see instructions below.

Mac OSX
-------

On Mac we recommend either the Anaconda python distribution - see below -
or Homebrew. The system python has difficulties installing ``PySide`` due to the old
version of Qt that is required.

Linux
-----

On Linux, Anaconda remains a good choice, however a few other possiblities exist.


Using a virtualenv
~~~~~~~~~~~~~~~~~~

This example is intended for Linux or Mac. It creates a virtual python environment
and installs Quantiphyse from pip::

    virtualenv $HOME/venvs/qp
    pip install cython numpy
    pip install quantiphyse


Installation using Anaconda
---------------------------

Anaconda (`<https://www.anaconda.org>`_) is an easy to install distribuction of Python which
also includes the ``conda`` tool for installing packages. We find ``conda`` generally better than 
``pip`` for dependency management and binary packages such as ``pyside``. Anaconda can
be installed on Windows, Mac and Linux.

You will need to install the Anaconda environment before using any of these recipes.
When selecting a Python version, ``Python 2.7`` is the version on which Quantiphyse
has been most tested, however you can also use ``python 3.x``. We intend to make
Quantiphyse compatible with both version of Python for the foreseeable future
although we intend to move to Python 3 as the main development platform.

Once installed, use the following commands from a command prompt::

    conda create -n qp
    conda activate qp
    conda install cython numpy
    pip install quantiphyse
    conda install PySide --force
    pip install quantiphyse-cest
    ... repeat for other plugins as required

In the future we hope to put Quantiphyse into conda itself so the whole
process can consist of ``conda install quantiphyse``.  




