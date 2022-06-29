.. _install:

Installation of Quantiphyse
===========================

This page describes the recommended installation method for Quantiphyse.

There are a number of other ways you can install the application - see 
:ref:`install_expert`, however unless
you have a good working knowledge of Python and virtual environments we 
recommend you use this method which has been tested on a number of platforms.

If you find a problem with these instructions, please report it using the
`Issue Tracker <https://github.com/physimals/quantiphyse/issues>`_.

.. note::
    To use some plugins you'll need to have a working ``FSL`` installation. For more 
    information go to `FSL installation <https://fsl.fmrib.ox.ac.uk/fsl/fslwiki/FslInstallation>`_.

Installing Anaconda
-------------------

Anaconda (`<https://www.anaconda.org>`_) is an easy to install distribution of Python which
importantly includes the ``conda`` tool for installing packages in isolated environments. 

You will need to install the Anaconda environment before using any of these recipes.
When selecting a Python version, chose version 3.

Once Anaconda is installed and the ``conda`` tool is working, follow the instructions below:

.. note::
    If you have FSL installed, you already have ``conda`` installed in ``$FSLDIR/fslpython/bin/``
    You can still install Anaconda separately but alternatively you can add this directory
    to your PATH and use the `conda` there.

Installing Quantiphyse in a Conda environment
---------------------------------------------

.. note::
    In the future we hope to put Quantiphyse into conda itself so the whole
    process can consist of ``conda install quantiphyse``.  

We recommend Python 3.7 as a reasonably up to date version of Python for which dependencies are generally widely
available. While Quantiphyse should be compatible with newer Python releases sometimes it is difficult to get
matching versions of important dependencies such as Numpy.

To create a Python 3.7 environment and install Quantiphyse use the following commands::

    conda create -n qp python=3.7
    conda activate qp
    pip install quantiphyse

On Mac you will also need to do::

    pip install pyobjc

This installs the basic Quantiphyse app - you should be able to run it by typing 'quantiphyse' at
the command line.

.. note::
    For recent versions of Mac OS (e.g. Big Sur, Monterey) it is necessary to set the following environment variable
    before running Quantiphyse: ``export QT_MAC_WANTS_LAYER=1``.

.. note::
    PySide2 is not currently available for M1-based Macs. It is possible to install Quantiphyse by using
    the Rosetta terminal to emulate an i386 environment. You will need to install Miniconda/Anaconda within Rosetta and then
    use that version of Conda to create an environment for Quantiphyse and then follow the instructions above.

Installing plugins
------------------

To install plugins use pip, for example this is to install all current pure-python plugins::

    pip install quantiphyse-cest quantiphyse-asl quantiphyse-qbold quantiphyse-dsc quantiphyse-fsl quantiphyse-sv quantiphyse-datasim

Installing plugins requiring compilation
----------------------------------------

A few plugins contain C/C++ code and not just Python. Currently these plugins are::

    quantiphyse-t1 quantiphyse-dce quantiphyse-deeds

To install these you may need to ensure you have a working build environment, as follows:

Windows
~~~~~~~

Install Visual C++ tools for Python 3 from: https://visualstudio.microsoft.com/downloads/#build-tools-for-visual-studio-2019

Mac
~~~

Install command line tools from: https://anansewaa.com/install-command-line-tools-on-macos-catalina/

Once the build environment is installed you can ``pip install`` the plugins as normal.
