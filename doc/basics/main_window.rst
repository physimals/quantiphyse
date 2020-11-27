.. _orientation:

========================
Main interface functions
========================

The Main Window
===============

The main window is quite busy, below is an overview of the main functions:

.. image:: /screenshots/overview.png

Below we will describe the main functions accessible from the main window.

Loading and Saving Data
=======================

File Formats
------------

This software package works with NIFTI volumes. Some builds may contain experimental support for
folders of DICOM files, however this is not well tested.

Alternative packages which are able to convert DICOM files to NIFTI include the following: 

 - `itk-snap <http://www.itksnap.org/pmwiki/pmwiki.php>`_
 - `dcm2nii <https://www.nitrc.org/plugins/mwiki/index.php/dcm2nii:MainPage>`_
 - Or the batch version which allows a number of volumes to be converted 
   `dcm2niibatch <https://github.com/rordenlab/dcm2niix>`_

Loading data using Drag and Drop
--------------------------------

.. image:: /screenshots/drag_drop_choice.png
    :align: right

You can drag and drop single or multiple files onto the main window to load data. You will be prompted to 
choose the type of data:
    
The suggested name is derived from the file name but is modified to ensure that it is a valid name
(data names must be valid Python variable names) and does not clash with any existing data.

If you choose a name which is the same as an existing data set, you will be asked if you wish to overwrite
the existing data. 

When dropping multiple files you will be asked to choose the type of each one. If you select *cancel* 
the data file will not be loaded.

Loading data using the menu
---------------------------

.. image:: /screenshots/file_menu.png
    :align: right
    
The ``File -> Load Data`` menu option can be used to load data files:

You will be prompted to choose the file type (data or ROI) and name in the same was as drag/drop.

Saving Data
-----------

The following menu options are used for saving data:

- File -> Save current data
- File -> Save current ROI

So, to save a data set you need to make it the current data, using the Overlay menu or the Volumes
widget. Similarly to save an ROI you need to make it the current ROI. Saving the main data can be 
done by selecting it as the current overlay.

Save a screen shot or plot
--------------------------

- Right click on an image or plot
- Click *Export*
- A view box will appear with the various format options. 
- *svg* format will allow editing of the layers and nodes in inkscape or another vector graphics viewer. 

.. image:: /screenshots/export_image.png

The Volumes List
================

After loading data it will appear in a list on the ``Volumes`` widget, which is always visible
by default:

.. image:: /screenshots/volume_list.png

The icon on the left indicates whether the data is visible or not: |main_data| indicates that this
is the main data (and will appear as a greyscale background), |visible| indicates that this
data item is visible, either as an ROI or an overlay on top of the background. The icon next 
to the data name shows whether it is an |roi_data| ROI or a |data| data set.

Underneath the volumes list are a set of icons which can be used to modify the currently selected
data set:

 - |delete| Delete the selected data set
 - |save| Save the selected data set to a Nifti file
 - |reload| Reload the selected data set from its source file. This is useful when viewing the results
   of an analysis done outside Quantiphyse
 - |rename| Rename the selected data set within Quantiphyse. Note that this does not create or rename
   any files on disk unless you subsequently save the data set
 - |set_main| Set this data set to be the main (reference) data set
 - |toggle_roi| Toggle between treating this volume as a data set or as an ROI. Note that to set a
   data set to be an ROI it must be integer only and 3D. This is useful when you accidentally load
   an ROI as a data set.

In addition the following buttons control the viewer as a whole:

|multi_view| Toggle between single view mode and multi view mode
----------------------------------------------------------------

By default Quantiphyse starts in *single-view mode*. In this mode, the main data is displayed as
a greyscale background and in addition one ROI and one additional dataset can be overlaid on top.
This is a simple and practical way of viewing data that works well in most cases. 

However we also support a *multi-view mode* where any number of data sets can be overlaid on top
of the main data. Clicking on the 'visible' column for a data set in the list toggles its visibility
and data sets higher up in the list overlay those below. In multi-view mode, two additional arrow
buttons appear allowing data sets to be moved up and down in the volumes list.

|view_options| Change general view options
------------------------------------------

.. image:: /screenshots/view_options_window.png

The following options are available for the viewer:

 - Orientation: By default Quantiphyse uses the 'radiological' view convention where the right
   hand side of the data is displayed on the left of the screen (as if viewing the patient from
   the end of the bed). Alternatively the 'neurological' convention where patient right is displayed
   on the right of the screen is also supported.
 - Crosshairs showing the currently selected view position may be hidden if desired
 - Similarly the view orientation labels (e.g. R/L for right/left) can be shown or hidden
 - The greyscale background display of the main data set can be turned on or off
 - In single view mode ROIs can be displayed on top of data sets or beneath them. In multi-view
   mode viewing order is user-specified according to the position of the data in the volumes list
 - The interpolation used when non-orthogonal data is displayed can be selected

.. |main_data| image:: /screenshots/main_data.png
.. |visible| image:: /screenshots/visible.png
.. |roi_data| image:: /screenshots/roi_data.png
.. |data| image:: /screenshots/data.png
.. |delete| image:: /screenshots/delete_data.png
.. |save| image:: /screenshots/save_data.png
.. |reload| image:: /screenshots/reload_data.png
.. |set_main| image:: /screenshots/set_main.png
.. |rename| image:: /screenshots/rename_data.png
.. |toggle_roi| image:: /screenshots/toggle_roi.png
.. |multi_view| image:: /screenshots/multi_view.png
.. |view_options| image:: /screenshots/view_options.png

The Navigation Bar
==================

The navigation bar is below the main image viewer and allows the current viewing position, current
ROI and current data to be changed:

.. image:: /screenshots/navigation.png

Using Widgets
=============

.. image:: /screenshots/widget_tab.png
    :align: right

*Widgets* appear to the right of the viewer window. Most widgets are accessed from the 'Widgets' menu above the viewer. 

When selected, a widget will appear with a tab to the right of the viewer. You can switch between opened widgets by
clicking on the tabs. A widget opened from the menu can be closed by clicking on the X in the top right of its tab.

Widgets may have very different user interfaces depending on what they do, however there are a number of common elements:

|help| Help button
------------------

.. |help| image:: /screenshots/help_button.png

This opens the online documentation page relevant to the widget. Internet access is required.

|options| Options button
------------------------

.. |options| image:: /screenshots/options_button.png

This shows any extended options the widget may have. It is typically used by widgets which display plots as that limits the
space available for options.

|batch| Batch button
--------------------

.. |batch| image:: /screenshots/batch_button.png

This displays the batch code required to perform the widget's processing, using the currently selected options. This can be useful
when building batch files from interactive exploration. It is only supported by widgets which provide image processing functions.

|cite| Citation
---------------

.. |cite| image:: /screenshots/cite.png

Many widgets are based around novel data processing techniques. The citation provides a reference to a published paper which can
be used to find out more information about the underlying method. If you publish work using a widget with a citation, you should
at the very least reference the paper given.

.. image:: /screenshots/citation.png

Clicking on the citation button performs an internet search for the paper.
