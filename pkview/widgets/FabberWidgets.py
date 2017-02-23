"""
Author: Martin Craig <martin.craig@eng.ox.ac.uk>
Copyright (c) 2016-2017 University of Oxford, Martin Craig
"""

from __future__ import division, unicode_literals, absolute_import, print_function

import sys, os
import time

import nibabel as nib
import numpy as np
import pyqtgraph as pg
from PySide import QtCore, QtGui

from pkview.QtInherit.QtSubclass import QGroupBoxB
from pkview.analysis import MultiProcess
from pkview.volumes.volume_management import Overlay

try:
    if "FSLDIR" in os.environ: sys.path.append("%s/lib/python/" % os.environ["FSLDIR"])
    if "FABBERDIR" in os.environ: sys.path.append("%s/lib/python/" % os.environ["FABBERDIR"])
    from fabber import FabberRunData, FabberLib, FabberException, find_fabber
    from fabber.views import *
    from fabber.imagedata import FabberImageData
    from fabber.dialogs import ModelOptionsDialog, MatrixEditDialog, LogViewerDialog
except:
    # Stub to prevent startup error - warning will occur if Fabber is used
    raise
    class OptionView:
        pass
    class ComponentOptionView:
        pass
    class ModelOptionsDialog:
        pass
    class MatrixEditDialog:
        pass

# Current overlays list from the IVM object. Global so that all the ImageOptionView instances
# can see what overlays to offer as options
CURRENT_OVERLAYS = []

def make_fabber_progress_cb(id, queue):
    def progress_cb(voxel, nvoxels):
        if (voxel % 100 == 0) or (voxel == nvoxels):
            queue.put((id, voxel, nvoxels))

    return progress_cb

def run_fabber(id, queue, rundata, main_data, roi, *overlays):
    """
    Function to run Fabber as a separate process
    """
    try:
        print("Running, id=", id, "shape=", roi.shape)
        #rundata.dump(sys.stdout)
        data = {"data" : main_data}
        n = 0
        while n < len(overlays):
            print(overlays[n], overlays[n+1].shape)
            data[overlays[n]] = overlays[n+1]
            n += 2

        lib = FabberLib(rundata=rundata)
        run = lib.run_with_data(rundata, data, roi, progress_cb=make_fabber_progress_cb(id, queue))
        return id, True, run
    except FabberException, e:
        return id, False, e
    except:
        return id, False, sys.exc_info()[0]

class ImageOptionView(OptionView):
    """
    OptionView subclass which allows image options to be chosen
    from the current list of overlays
    """
    def __init__(self, opt, **kwargs):
        OptionView.__init__(self, opt, **kwargs)
        self.combo = QtGui.QComboBox()
        self.combo.currentIndexChanged.connect(self.changed)
        self.update_list()
        self.widgets.append(self.combo)

    def update_list(self):
        global CURRENT_OVERLAYS
        current = self.combo.currentText()
        self.combo.clear()
        for ov in CURRENT_OVERLAYS:
            self.combo.addItem(ov)
        idx = self.combo.findText(current)
        self.combo.setCurrentIndex(idx)

    def changed(self):
        # Note that this signal is triggered when the widget
        # is enabled/disabled and when overlays are added/removed
        # from the list. So we can't be sure 'fab' is defined
        if self.combo.isEnabled():
            if hasattr(self, "rundata"):
                self.rundata[self.key] = self.combo.currentText()
            print(self.key)

    def do_update(self):
        OptionView.do_update(self)
        if self.key in self.rundata:
            idx = self.combo.findText(self.rundata[self.key])
            self.combo.setCurrentIndex(idx)

    def add(self, grid, row):
        OptionView.add(self, grid, row)
        grid.addWidget(self.combo, row, 1)

class FabberWidget(QtGui.QWidget):
    """
    Widget for running Fabber model fitting
    """

    """ Signal emitted when async Fabber finished"""
    sig_finished = QtCore.Signal(tuple)

    def __init__(self):
        super(FabberWidget, self).__init__()

        mainVbox = QtGui.QVBoxLayout()
        self.setLayout(mainVbox)

        self.ivm = None


        try:
            self.fabber_lib = find_fabber()[1]
            if not self.fabber_lib:
                mainVbox.addWidget(QtGui.QLabel("Fabber core library not found.\n\n You must install FSL and Fabber to use this widget"))
        except:
            mainVbox.addWidget(QtGui.QLabel("Could not load Fabber Python API.\n\n You must install FSL and Fabber to use this widget"))
            return

        # Options box
        optionsBox = QGroupBoxB()
        optionsBox.setTitle('Fabber Model Fitting')
        grid = QtGui.QGridLayout()
        optionsBox.setLayout(grid)

        grid.addWidget(QtGui.QLabel("Fabber core library"), 1, 0)
        self.libEdit = QtGui.QLineEdit(self)
        grid.addWidget(self.libEdit, 1, 1)
        self.libChangeBtn = QtGui.QPushButton('Choose', self)
        grid.addWidget(self.libChangeBtn, 1, 2)

        grid.addWidget(QtGui.QLabel("Fabber models library"), 2, 0)
        self.modellibCombo = QtGui.QComboBox(self)
        grid.addWidget(self.modellibCombo, 2, 1)
        self.modellibChangeBtn = QtGui.QPushButton('Choose', self)
        grid.addWidget(self.modellibChangeBtn, 2, 2)

        grid.addWidget(QtGui.QLabel("Forward model"), 3, 0)
        self.modelCombo = QtGui.QComboBox(self)
        grid.addWidget(self.modelCombo, 3, 1)
        self.modelOptionsBtn = QtGui.QPushButton('Options', self)
        grid.addWidget(self.modelOptionsBtn, 3, 2)
        
        grid.addWidget(QtGui.QLabel("Inference method"), 4, 0)
        self.methodCombo = QtGui.QComboBox(self)
        grid.addWidget(self.methodCombo, 4, 1)
        self.methodOptionsBtn = QtGui.QPushButton('Options', self)
        grid.addWidget(self.methodOptionsBtn, 4, 2)
        
        grid.addWidget(QtGui.QLabel("General Options"), 5, 0)
        self.generalOptionsBtn = QtGui.QPushButton('Edit', self)
        grid.addWidget(self.generalOptionsBtn, 5, 2)

        # Run box
        runBox = QGroupBoxB()
        runBox.setTitle('Running')
        vbox = QtGui.QVBoxLayout()
        runBox.setLayout(vbox)

        hbox = QtGui.QHBoxLayout()
        self.runBtn = QtGui.QPushButton('Run modelling', self)
        self.runBtn.clicked.connect(self.start_task)
        hbox.addWidget(self.runBtn)
        self.progress = QtGui.QProgressBar(self)
        self.progress.setStatusTip('Progress of Fabber model fitting. Be patient. Progress is only updated in chunks')
        hbox.addWidget(self.progress)
        self.logBtn = QtGui.QPushButton('View log', self)
        self.logBtn.clicked.connect(self.view_log)
        self.logBtn.setEnabled(False)
        hbox.addWidget(self.logBtn)
        vbox.addLayout(hbox)

        # Load/save box
        fileBox = QGroupBoxB()
        fileBox.setTitle('Load/Save options')
        vbox = QtGui.QVBoxLayout()
        fileBox.setLayout(vbox)

        hbox = QtGui.QHBoxLayout()
        hbox.addWidget(QtGui.QLabel("Filename"))
        self.fileEdit = QtGui.QLineEdit()
        self.fileEdit.setReadOnly(True)
        hbox.addWidget(self.fileEdit)
        btn = QtGui.QPushButton("Open")
        btn.clicked.connect(self.open_file)
        hbox.addWidget(btn)
        self.saveBtn = QtGui.QPushButton("Save")
        self.saveBtn.clicked.connect(self.save_file)
        self.saveBtn.setEnabled(False)
        hbox.addWidget(self.saveBtn)
        btn = QtGui.QPushButton("Save As")
        btn.clicked.connect(self.save_as_file)
        hbox.addWidget(btn)
        vbox.addLayout(hbox)

        # Main layout
        mainVbox.addWidget(optionsBox)
        mainVbox.addWidget(runBox)
        mainVbox.addWidget(fileBox)
        mainVbox.addStretch()

        # Register our custom view to handle image options
        OPT_VIEW["IMAGE"] = ImageOptionView
        OPT_VIEW["TIMESERIES"] = ImageOptionView

        # Keep references to the option dialogs so we can update any image option views as overlays change
        self.modelOpts = ComponentOptionsView("model", "Forward model", dialog=ModelOptionsDialog(), btn=self.modelOptionsBtn,
                             mat_dialog=MatrixEditDialog())
        self.methodOpts = ComponentOptionsView("method", "Inference method", dialog=ModelOptionsDialog(), btn=self.methodOptionsBtn,
                             mat_dialog=MatrixEditDialog())
        self.generalOpts = OptionsView(dialog=ModelOptionsDialog(), btn=self.generalOptionsBtn, mat_dialog=MatrixEditDialog())

        self.views = [
            ModelMethodView(modelCombo=self.modelCombo, methodCombo=self.methodCombo),
            self.modelOpts, self.methodOpts, self.generalOpts,
            ChooseFileView("fabber", changeBtn=self.libChangeBtn, edit=self.libEdit,
                           dialogTitle="Choose core library", defaultDir=os.path.dirname(self.fabber_lib)),
            ChooseModelLib(changeBtn=self.modellibChangeBtn, combo=self.modellibCombo),
        ]

        self.generalOpts.ignore("output", "data", "mask", "data<n>", "overwrite", "method", "model", "help",
                                "listmodels", "listmethods", "link-to-latest", "data-order", "dump-param-names",
                                "loadmodels")
        self.rundata = FabberRunData()
        self.rundata["fabber"] = self.fabber_lib
        self.rundata["save-mean"] = ""
        self.reset()

        # Callbacks to update GUI during processing
        self.timer = QtCore.QTimer()
        self.timer.timeout.connect(self.update_progress)

    def save_file(self):
        self.rundata.save()

    def save_as_file(self):
        # fixme choose file name
        # fixme overwrite
        # fixme clone data
        fname = QtGui.QFileDialog.getSaveFileName()[0]
        self.rundata.set_file(fname)
        self.rundata.save()
        self.fileEdit.setText(fname)
        self.saveBtn.setEnabled(True)

    def open_file(self):
        filename = QtGui.QFileDialog.getOpenFileName()[0]
        if filename:
            self.fileEdit.setText(filename)
            self.rundata = FabberRunData(filename)
            self.saveBtn.setEnabled(True)
            self.reset()

    def reset(self):
        for view in self.views: self.rundata.add_view(view)

    def add_image_management(self, image_vol_management):
        """
        Adding image management
        """
        self.ivm = image_vol_management
        self.ivm.sig_all_overlays.connect(self.overlays_changed)

    def overlays_changed(self, overlays):
        """
        Update image data views
        """
        global CURRENT_OVERLAYS
        CURRENT_OVERLAYS = overlays
        for dialog in (self.methodOpts, self.modelOpts, self.methodOpts):
            for view in dialog.views.values():
                if isinstance(view, ImageOptionView):
                    view.update_list()

    def start_task(self):
        """
        Start running the PK modelling on button click
        """
        img = self.ivm.vol
        roi = self.ivm.current_roi

        if img is None:
            m1 = QtGui.QMessageBox()
            m1.setWindowTitle("PkView")
            m1.setText("The image doesn't exist! Please load before running Fabber modelling")
            m1.exec_()
            return

        if roi is None:
            m1 = QtGui.QMessageBox()
            m1.setWindowTitle("PkView")
            m1.setText("The ROI doesn't exist! Please load before running Fabber modelling")
            m1.exec_()
            return

        # set the progress value
        self.progress.setValue(0)
        self.timer.start(1000)

        # Pass in input data. To enable the multiprocessing module to split our volumes
        # up automatically we have to pass the arguments as a single list. This consists of
        # rundata, main data, roi and then each of the used overlays, name followed by data
        input_args = [self.rundata, img.data, roi.data]
        used_overlays = set()
        for dialog in (self.methodOpts, self.modelOpts, self.methodOpts):
            for view in dialog.views.values():
                if isinstance(view, ImageOptionView) and view.combo.isEnabled():
                    input_args.append(view.combo.currentText())
                    input_args.append(self.ivm.overlays[ov].data)

        N = img.data.shape[0]
        self.voxels_done = [0, ] * N
        self.voxels_todo = np.count_nonzero(roi.data)
        self.process = MultiProcess(N, run_fabber, input_args)
        self.process.sig_finished.connect(self.run_finished_gui)
        self.process.run()
        self.runBtn.setEnabled(False)
        self.logBtn.setEnabled(False)

    def run_finished_gui(self, success, results):
        """
        Callback called when an async fabber run completes
        """
        print("Finished fabber")

        if success:
            first = True
            for key in results[0].data:
                print(key, results[0].data[key].shape)
                recombined_item = np.concatenate([results[i].data[key] for i in range(len(results))], 0)
                print(key, recombined_item.shape)
                self.ivm.add_overlay(Overlay(name=key, data=recombined_item), make_current=first)
                first = False
            self.runs = results
        else:
            # If one process fails, they all fail
            QtGui.QMessageBox.warning(None, "Fabber error", "Fabber failed to run:\n\n" + str(results),
                                      QtGui.QMessageBox.Close)

        self.timer.stop()
        self.update_progress()
        self.runBtn.setEnabled(True)
        self.logBtn.setEnabled(success)

    def update_progress(self):
        queue = self.process.queue
        if queue.empty(): return
        while not queue.empty():
            id, v, nv = queue.get()
            self.voxels_done[id] = v
        cv = sum(self.voxels_done)
        tv = self.voxels_todo
        print("total of %i done of %i" % (cv, tv, ))
        if tv > 0:
            percent = 100 * float(cv) / tv
            self.progress.setValue(percent)

    def view_log(self):
         fulllog = ""
         for run in self.runs:
             fulllog += run.log + "\n\n"
         self.logview = LogViewerDialog(log=fulllog)
         self.logview.show()
         self.logview.raise_()