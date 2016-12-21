"""

Author: Benjamin Irving (benjamin.irv@gmail.com)
Copyright (c) 2013-2015 University of Oxford, Benjamin Irving

"""

from __future__ import division, unicode_literals, absolute_import, print_function

import multiprocessing
import multiprocessing.pool
import time

import nibabel as nib
import numpy as np
import pyqtgraph as pg
from PySide import QtCore, QtGui

from pkview.QtInherit.QtSubclass import QGroupBoxB
from pkview.analysis.pk_model import PyPk

# FIXME FSLDIR
import sys, os
sys.path.append("%s/lib/python/" % os.environ["HOME"])
print("Appended %s/lib/python/" % os.environ["HOME"])
from pyfab.views import *
from pyfab.imagedata import FabberImageData
from pyfab.model import FabberRunData
from pyfab.ui import ModelOptionsDialog, MatrixEditDialog
from pyfab.fabber import FabberLib

# Current overlays list from the IVM object. Global so that all the ImageOptionView instances
# can see what overlays to offer as options
CURRENT_OVERLAYS = []

class ImageOptionView(OptionView):
    def __init__(self, opt, **kwargs):
        OptionView.__init__(self, opt, **kwargs)
        self.combo = QtGui.QComboBox()
        self.combo.currentIndexChanged.connect(self.changed)
        self.update_list()
        self.widgets.append(self.combo)
        #self.hbox = QHBoxLayout()
        #self.hbox.addWidget(self.edit)
        #self.btn = QPushButton("Choose")
        #self.hbox.addWidget(self.btn)
        #self.widgets.append(self.btn)
        #self.btn.clicked.connect(self.choose_file)

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
        # from the list
        if self.combo.isEnabled():
            self.fab.set_option(self.key, self.combo.currentText())

    def do_update(self):
        OptionView.do_update(self)
        if self.fab.options.has_key(self.key):
            idx = self.combo.findText(self.fab.options[self.key])
            self.combo.setCurrentIndex(idx)

    def add(self, grid, row):
        OptionView.add(self, grid, row)
        grid.addWidget(self.combo, row, 1)

class FabberWidget(QtGui.QWidget):

    """
    Widget for generating running Fabber model fitting
    Bass class
        - GUI framework
        - Buttons
        - Multiprocessing
    """

    #emit reset command
    sig_emit_reset = QtCore.Signal(bool)

    def __init__(self):
        super(FabberWidget, self).__init__()

        self.ivm = None

        # Options box
        grid = QtGui.QGridLayout()
        
        grid.addWidget(QtGui.QLabel("Fabber core library"), 1, 0)
        self.libEdit = QtGui.QLineEdit(self)
        grid.addWidget(self.libEdit, 1, 1)
        self.libChangeBtn = QtGui.QPushButton('Change', self)
        grid.addWidget(self.libChangeBtn, 1, 2)

        grid.addWidget(QtGui.QLabel("Fabber models library"), 2, 0)
        self.modellibEdit = QtGui.QLineEdit(self)
        grid.addWidget(self.modellibEdit, 2, 1)
        self.modellibChangeBtn = QtGui.QPushButton('Change', self)
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
        
        optionsBox = QGroupBoxB()
        optionsBox.setTitle('Fabber Model Fitting')
        optionsBox.setLayout(grid)
        
        # Run box
        runHbox = QtGui.QHBoxLayout()

        runBtn = QtGui.QPushButton('Run modelling', self)
        runBtn.clicked.connect(self.start_task)
        runHbox.addWidget(runBtn)

        self.progress = QtGui.QProgressBar(self)
        self.progress.setStatusTip('Progress of Fabber model fitting. Be patient. Progress is only updated in chunks')
        runHbox.addWidget(self.progress)
        
        runBox = QGroupBoxB()
        runBox.setTitle('Running')
        runBox.setLayout(runHbox)
 
        # Main layout 
        
        mainVbox = QtGui.QVBoxLayout()
        mainVbox.addWidget(optionsBox)
        mainVbox.addWidget(runBox)
        mainVbox.addStretch()

        self.setLayout(mainVbox)

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
            ChooseFileView("fabber", changeBtn=self.libChangeBtn, edit=self.libEdit),
            ChooseFileView("loadmodels", changeBtn=self.modellibChangeBtn, edit=self.modellibEdit),
        ]

        self.generalOpts.ignore("output", "data", "mask", "data<n>", "overwrite", "method", "model", "help",
                                "listmodels", "listmethods", "link-to-latest", "data-order", "dump-param-names")
        self.new()
        self.fab.set_option("fabber", "/home/martinc/dev/fabber_core/Debug/libfabbercore_shared.so")
        self.fab.set_option("save-mean")

    def add_views(self):	
        for view in self.views: self.fab.add_view(view)

    def refresh(self, fab):
        self.fab = fab
        self.add_views()

    def new(self):
        # fixme unsaved changes
        self.refresh(FabberRunData())
	
    def open(self):
        filename = QFileDialog.getOpenFileName()[0]
        if filename: self.refresh(FabberRunData(filename))
		
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
        img = self.ivm.get_image()
        roi = self.ivm.get_current_roi()

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

        s = img.shape
        lib = FabberLib(self.fab, lib=self.fab.options["fabber"])
        data = {"data" : img}
        # Pass in overlays - FIXME should only pass in those that are being used!
        for ov in CURRENT_OVERLAYS:
            data[ov] = self.ivm.overlay_all[ov]

        run = lib.run_with_data(s[0], s[1], s[2], roi, data, ["mean_c0", "mean_c1", "mean_c2", "modelfit"])
        print(run.log)
        
        first = True
        for key, item in run.data.items():
            print(key, item.shape)
            if len(item.shape) == 3:
                print("overlay")
                self.ivm.set_overlay(name=key, data=item, force=True)
                if first: 
                    self.ivm.set_current_overlay(key)
                    first = False
            elif key.lower() == "modelfit":
                print("modelfit")
                self.ivm.set_estimated(item)
                
        self.sig_emit_reset.emit(1)

        

