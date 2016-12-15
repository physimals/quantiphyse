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
#        self.init_multiproc()

        self.ivm = None

        # Options box
        grid = QtGui.QGridLayout()
        
        grid.addWidget(QtGui.QLabel("Executable"), 1, 0)
        self.execEdit = QtGui.QLineEdit(self)
        grid.addWidget(self.execEdit, 1, 1)
        self.execChangeBtn = QtGui.QPushButton('Change', self)
        grid.addWidget(self.execChangeBtn, 1, 2)
        
        grid.addWidget(QtGui.QLabel("Forward model"), 2, 0)
        self.modelCombo = QtGui.QComboBox(self)
        grid.addWidget(self.modelCombo, 2, 1)
        self.modelOptionsBtn = QtGui.QPushButton('Options', self)
        grid.addWidget(self.modelOptionsBtn, 2, 2)
        
        grid.addWidget(QtGui.QLabel("Inference method"), 3, 0)
        self.methodCombo = QtGui.QComboBox(self)
        grid.addWidget(self.methodCombo, 3, 1)
        self.methodOptionsBtn = QtGui.QPushButton('Options', self)
        grid.addWidget(self.methodOptionsBtn, 3, 2)
        
        grid.addWidget(QtGui.QLabel("General Options"), 4, 0)
        self.generalOptionsBtn = QtGui.QPushButton('Edit', self)
        grid.addWidget(self.generalOptionsBtn, 4, 2)
        
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

        # Check for updates from the process
#        self.timer = QtCore.QTimer()
#        self.timer.timeout.connect(self.CheckProg)
		
	self.fabdata = FabberImageData()
	
	self.views = [
          self.fabdata,
          ModelMethodView(modelCombo=self.modelCombo, methodCombo=self.methodCombo),
	  ComponentOptionsView("model", "Forward model", dialog=ModelOptionsDialog(), btn=self.modelOptionsBtn, mat_dialog=MatrixEditDialog()),
	  ComponentOptionsView("method", "Inference method", dialog=ModelOptionsDialog(), btn=self.methodOptionsBtn, mat_dialog=MatrixEditDialog()),
	  OptionsView(dialog=ModelOptionsDialog(), btn=self.generalOptionsBtn, mat_dialog=MatrixEditDialog()),	
	  ExecView(execChangeBtn=self.execChangeBtn, execEdit=self.execEdit),
	]
		
	self.new()
	#self.openBtn.clicked.connect(self.open)
	#self.newBtn.clicked.connect(self.new)

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

    def init_multiproc(self):
	pass
        # Set up the background process

#        self.queue = multiprocessing.Queue()
#        self.pool = multiprocessing.Pool(processes=2, initializer=pool_init, initargs=(self.queue,))

    def start_task(self):
        """
        Start running the PK modelling on button click
        """
        # Check that pkmodelling can be run
        if self.ivm.get_image() is None:
            m1 = QtGui.QMessageBox()
            m1.setWindowTitle("PkView")
            m1.setText("The image doesn't exist! Please load before running Fabber modelling")
            m1.exec_()
            return

        if self.ivm.get_roi() is None:
            m1 = QtGui.QMessageBox()
            m1.setWindowTitle("PkView")
            m1.setText("The Image or ROI doesn't exist! Please load before running Fabber modelling")
            m1.exec_()
            return

#        if self.ivm.get_T10() is None:
#            m1 = QtGui.QMessageBox()
#            m1.setText("The T10 map doesn't exist! Please load before running Pk modelling")
#            m1.exec_()
#            return

#        self.timer.start(1000)

        # get volumes to process

        img1 = self.ivm.get_image()
        roi1 = self.ivm.get_roi()
#        t101 = self.ivm.get_T10()

        lib = FabberLib()
        self.fab.clear_option("data")
        self.fab.clear_option("mask")
        
#        self.fab.set_option("data", self.ivm.image_file1)
#        if roi1 is not None:
#            self.fab.set_option("mask", self.ivm.roi_file1)
        
        ret, data, log, err = lib.run(self.fab.options, img1, roi1, {}, ["mean_c0", "mean_c1", "mean_c2", "modelfit"])
        print(log)
        
        first = True
        for key, item in data.items():
            print(key, item.shape)
            if len(item.shape) == 3:
                print("overlay")
                self.ivm.set_overlay(choice1=key, ovreg=item, force=True)
                if first: 
                    self.ivm.set_current_overlay(choice1=key)
                    first = False
            elif key.lower() == "modelfit":
                print("modelfit")
                self.ivm.set_estimated(item)
                
        self.sig_emit_reset.emit(1)

        

