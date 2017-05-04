"""
Author: Martin Craig <martin.craig@eng.ox.ac.uk>
Copyright (c) 2016-2017 University of Oxford, Martin Craig
"""

from __future__ import division, unicode_literals, absolute_import, print_function

import sys, os, warnings
import time
import traceback

import nibabel as nib
import numpy as np
import pyqtgraph as pg
from PySide import QtCore, QtGui

from ..QtInherit import HelpButton
from pkview.analysis import Process
from pkview.analysis.fab import FabberProcess
from pkview.QtInherit.dialogs import error_dialog
from pkview.volumes.volume_management import Volume, Roi, Overlay
from pkview.widgets import PkWidget

try:
    from fabber import FabberRunData, find_fabber
    from fabber.views import *
    from fabber.dialogs import ModelOptionsDialog, MatrixEditDialog, LogViewerDialog
except:
    # Stubs to prevent startup error - warning will occur if Fabber is used
    warnings.warn("Failed to import Fabber API - widget will be disabled")
    traceback.print_exc()
    OPT_VIEW={}
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

CITE = """
<i>Chappell, M.A., Groves, A.R., Woolrich, M.W.
"Variational Bayesian inference for a non-linear forward model"
IEEE Trans. Sig. Proc., 2009, 57(1), 223-236</i>
"""

class PriorsView(OptionsView):
    """
    More user-friendly view of prior options rather than PSP_byname etc.
    """
    def __init__(self, **kwargs):
        OptionsView.__init__(self, **kwargs)
        self.priors = []
        self.prior_widgets = []
        self.overlays = []
        self.params = []
        self.updating_widgets = False
        self.updating_rundata = False
        
    def do_update(self):
        try:
            params = FabberLib(rundata=self.rundata).get_model_params(self.rundata)
        except FabberException, e:
            # get_model_params can fail if model options not properly set. Repopulate with empty
            # parameter set - will check again when options change
            params = []

        if set(params) != set(self.params):
            self.params = params
            self.repopulate()
        else: 
            self.update_from_rundata()

    def get_widgets(self, idx):
        type_combo = QtGui.QComboBox()
        type_combo.addItem("Model default", "")
        type_combo.addItem("Image Prior", "I")
        type_combo.setSizeAdjustPolicy(QtGui.QComboBox.AdjustToContents)
        type_combo.currentIndexChanged.connect(self.changed)
        
        image_combo = QtGui.QComboBox()
        for overlay in self.overlays:
            image_combo.addItem(overlay)
        image_combo.setSizeAdjustPolicy(QtGui.QComboBox.AdjustToContents)
        image_combo.currentIndexChanged.connect(self.changed)
        
        cb = QtGui.QCheckBox()
        cb.stateChanged.connect(self.changed)
        edit = QtGui.QLineEdit()
        edit.editingFinished.connect(self.changed)
        
        return type_combo, QtGui.QLabel("Image: "), image_combo, cb, QtGui.QLabel("Custom precision: "), edit

    def update_from_rundata(self):
        if not self.updating_rundata:
            prior_idx=1
            used_params = []
            while "PSP_byname%i" % prior_idx in self.rundata:
                param = self.rundata["PSP_byname%i" % prior_idx]
                if param in self.params:
                    idx = self.params.index(param)
                    type_combo, l2, image_combo, cb, l3, edit = self.prior_widgets[idx]
                    used_params.append(param)

                    ptype = self.rundata.get("PSP_byname%i_type" % prior_idx, "")
                    image = self.rundata.get("PSP_byname%i_image" % prior_idx, "")
                    prec = self.rundata.get("PSP_byname%i_prec" % prior_idx, "")

                    type_combo.setCurrentIndex(type_combo.findData(ptype))
                    image_combo.setCurrentIndex(image_combo.findText(image))
                    edit.setText(prec)
                
                prior_idx += 1
            
            for idx, param in enumerate(self.params):
                if param not in used_params:
                    type_combo, l2, image_combo, cb, l3, edit = self.prior_widgets[idx]
                    type_combo.setCurrentIndex(0)

            self.update_widgets()

    def update_widgets(self):
         for idx, param in enumerate(self.params):
            type_combo, l2, image_combo, cb, l3, edit = self.prior_widgets[idx]
        
            prior_type = type_combo.itemData(type_combo.currentIndex())
            need_image = (prior_type == "I")
            l2.setEnabled(need_image)
            image_combo.setEnabled(need_image)

            cb.setEnabled(prior_type != "")
            have_prec = (prior_type != "") and cb.isChecked()

            l3.setEnabled(have_prec)
            edit.setEnabled(have_prec)

    def changed(self):
        if not self.updating_widgets:
            self.updating_rundata=True
            self.update_widgets()
            self.update_rundata() 
            self.updating_rundata=False

    def update_rundata(self):
        prior_idx=1
        for idx, param in enumerate(self.params):
            type_combo, l2, image_combo, cb, l3, edit = self.prior_widgets[idx]
        
            prior_type = type_combo.itemData(type_combo.currentIndex())
            need_image = (prior_type == "I")
            need_prec = cb.isChecked()
            
            if prior_type != "":
                self.rundata["PSP_byname%i" % prior_idx] = param
                self.rundata["PSP_byname%i_type" % prior_idx] = prior_type
                if need_image:
                    self.rundata["PSP_byname%i_image" % prior_idx] = image_combo.currentText()
                else:
                    del self.rundata["PSP_byname%i_image" % prior_idx] 
                if need_prec:
                    self.rundata["PSP_byname%i_prec" % prior_idx] = edit.text()
                else:
                    del self.rundata["PSP_byname%i_prec" % prior_idx] 
                prior_idx += 1

        while "PSP_byname%i" % prior_idx in self.rundata:
            del self.rundata["PSP_byname%i" % prior_idx]
            del self.rundata["PSP_byname%i_type" % prior_idx]
            del self.rundata["PSP_byname%i_image" % prior_idx]
            del self.rundata["PSP_byname%i_prec" % prior_idx]
            prior_idx += 1

        #self.rundata.dump(sys.stdout)
        
    def repopulate(self):
        self.updating_widgets=True
        self.clear()
        self.dialog.grid.setSpacing(20)
        self.prior_widgets = []
        
        self.dialog.modelLabel.setText("Model parameter priors")
        self.dialog.descLabel.setText("Describes optional prior information about each model parameter")
        
        if len(self.params) == 0:
            self.dialog.grid.addWidget(QtGui.QLabel("No parameters found! Make sure model is properly configured"))

        for idx, param in enumerate(self.params):
            self.prior_widgets.append(self.get_widgets(idx))
        
            self.dialog.grid.addWidget(QtGui.QLabel("%s: " % param), idx, 0)
            for col, w in enumerate(self.prior_widgets[idx]):
                self.dialog.grid.addWidget(w, idx, col+1)

        self.update_from_rundata()
        self.update_widgets()
        self.dialog.grid.setAlignment(QtCore.Qt.AlignTop)
        self.dialog.adjustSize()
        self.updating_widgets=False
        
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

    def do_update(self):
        OptionView.do_update(self)
        if self.key in self.rundata:
            idx = self.combo.findText(self.rundata[self.key])
            self.combo.setCurrentIndex(idx)

    def add(self, grid, row):
        OptionView.add(self, grid, row)
        grid.addWidget(self.combo, row, 1)

class FabberWidget(PkWidget):
    """
    Widget for running Fabber model fitting
    """

    """ Signal emitted when async Fabber finished"""
    sig_finished = QtCore.Signal(tuple)

    def __init__(self, **kwargs):
        super(FabberWidget, self).__init__(name="Fabber", icon="fabber", 
                                           desc="Fabber Bayesian model fitting",
                                           **kwargs)
        mainGrid = QtGui.QVBoxLayout()
        self.setLayout(mainGrid)

        try:
            self.fabber_lib = find_fabber()[1]
            if self.fabber_lib is None:
                mainGrid.addWidget(QtGui.QLabel("Fabber core library not found.\n\n You must install FSL and Fabber to use this widget"))
                return
        except:
            mainGrid.addWidget(QtGui.QLabel("Could not load Fabber Python API.\n\n You must install FSL and Fabber to use this widget"))
            return

        self.ivm.sig_all_overlays.connect(self.overlays_changed)

        # Options box
        optionsBox = QtGui.QGroupBox()
        optionsBox.setTitle('Options')
        optionsBox.setSizePolicy(QtGui.QSizePolicy.MinimumExpanding, QtGui.QSizePolicy.MinimumExpanding)
        grid = QtGui.QGridLayout()
        optionsBox.setLayout(grid)

        grid.addWidget(QtGui.QLabel("Extra models library"), 2, 0)
        self.modellibCombo = QtGui.QComboBox(self)
        self.modellibCombo.setSizeAdjustPolicy(QtGui.QComboBox.AdjustToContents)
        grid.addWidget(self.modellibCombo, 2, 1)
        self.modellibChangeBtn = QtGui.QPushButton('Choose External library', self)
        grid.addWidget(self.modellibChangeBtn, 2, 2)

        grid.addWidget(QtGui.QLabel("Forward model"), 3, 0)
        self.modelCombo = QtGui.QComboBox(self)
        self.modelCombo.setSizeAdjustPolicy(QtGui.QComboBox.AdjustToContents)
        grid.addWidget(self.modelCombo, 3, 1)
        self.modelOptionsBtn = QtGui.QPushButton('Model Options', self)
        grid.addWidget(self.modelOptionsBtn, 3, 2)
        
        grid.addWidget(QtGui.QLabel("Inference method"), 4, 0)
        self.methodCombo = QtGui.QComboBox(self)
        self.methodCombo.setSizeAdjustPolicy(QtGui.QComboBox.AdjustToContents)
        grid.addWidget(self.methodCombo, 4, 1)
        self.methodOptionsBtn = QtGui.QPushButton('Inference Options', self)
        grid.addWidget(self.methodOptionsBtn, 4, 2)
        
        grid.addWidget(QtGui.QLabel("Parameter priors"), 5, 0)
        self.priorsBtn = QtGui.QPushButton('Edit', self)
        grid.addWidget(self.priorsBtn, 5, 2)
        
        grid.addWidget(QtGui.QLabel("General Options"), 6, 0)
        self.generalOptionsBtn = QtGui.QPushButton('Edit', self)
        grid.addWidget(self.generalOptionsBtn, 6, 2)
        
        # Run box
        runBox = QtGui.QGroupBox()
        runBox.setTitle('Running')
        runBox.setSizePolicy(QtGui.QSizePolicy.MinimumExpanding, QtGui.QSizePolicy.MinimumExpanding)
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

        hbox = QtGui.QHBoxLayout()
        self.savefilesCb = QtGui.QCheckBox("Save copy of output data")
        hbox.addWidget(self.savefilesCb)
        self.saveFolderEdit = QtGui.QLineEdit()
        hbox.addWidget(self.saveFolderEdit)
        btn = QtGui.QPushButton("Choose folder")
        btn.clicked.connect(self.chooseOutputFolder)
        hbox.addWidget(btn)
        self.savefilesCb.stateChanged.connect(self.saveFolderEdit.setEnabled)
        self.savefilesCb.stateChanged.connect(btn.setEnabled)
        vbox.addLayout(hbox)

        # Load/save box
        fileBox = QtGui.QGroupBox()
        fileBox.setTitle('Load/Save options')
        fileBox.setSizePolicy(QtGui.QSizePolicy.MinimumExpanding, QtGui.QSizePolicy.MinimumExpanding)
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
        
        hbox = QtGui.QHBoxLayout()
        hbox.addWidget(QtGui.QLabel('<font size="5">Fabber Bayesian Model Fitting</font>'))
        hbox.addStretch(1)
        hbox.addWidget(HelpButton(self, "fabber"))
        mainGrid.addLayout(hbox)
        
        cite = QtGui.QLabel(CITE)
        cite.setWordWrap(True)
        mainGrid.addWidget(cite)

        mainGrid.addWidget(QtGui.QLabel(""))
        mainGrid.addWidget(optionsBox)
        mainGrid.addWidget(runBox)
        mainGrid.addWidget(fileBox)
        mainGrid.addStretch(1)

        # Register our custom view to handle image options
        OPT_VIEW["IMAGE"] = ImageOptionView
        OPT_VIEW["TIMESERIES"] = ImageOptionView

        # Keep references to the option dialogs so we can update any image option views as overlays change
        self.modelOpts = ModelOptionsView(dialog=ModelOptionsDialog(self), btn=self.modelOptionsBtn, mat_dialog=MatrixEditDialog(self), desc_first=True)
        self.methodOpts = MethodOptionsView(dialog=ModelOptionsDialog(self), btn=self.methodOptionsBtn, mat_dialog=MatrixEditDialog(self), desc_first=True)
        self.generalOpts = OptionsView(dialog=ModelOptionsDialog(self), btn=self.generalOptionsBtn, mat_dialog=MatrixEditDialog(self), desc_first=True)
        self.priors = PriorsView(dialog=ModelOptionsDialog(self), btn=self.priorsBtn)

        self.views = [
            ModelMethodView(modelCombo=self.modelCombo, methodCombo=self.methodCombo),
            self.modelOpts, self.methodOpts, self.generalOpts, self.priors,
#            ChooseFileView("fabber_lib", changeBtn=self.libChangeBtn, edit=self.libEdit,
#                           dialogTitle="Choose core library", defaultDir=os.path.dirname(self.fabber_lib)),
            ChooseModelLib(changeBtn=self.modellibChangeBtn, combo=self.modellibCombo),
        ]

        self.generalOpts.ignore("output", "data", "mask", "data<n>", "overwrite", "method", "model", "help",
                                "listmodels", "listmethods", "link-to-latest", "data-order", "dump-param-names",
                                "loadmodels")
        self.rundata = FabberRunData()
        self.rundata["fabber_lib"] = self.fabber_lib
        self.rundata["save-mean"] = ""
        self.reset()

        self.process = FabberProcess(self.ivm)
        self.process.sig_finished.connect(self.run_finished_gui)
        self.process.sig_progress.connect(self.update_progress)

    def chooseOutputFolder(self):
        outputDir = QtGui.QFileDialog.getExistingDirectory(self, 'Choose directory to save output')
        if outputDir:
            self.saveFolderEdit.setText(outputDir)

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
        self.priors.overlays = overlays
        self.priors.repopulate()

    def start_task(self):
        """
        Start running the PK modelling on button click
        """
        img = self.ivm.vol
        roi = self.ivm.current_roi

        if img is None:
            error_dialog("No data loaded")
            return

        if roi is None:
            error_dialog("No ROI loaded - can only run Fabber with an ROI")
            return

        # set the progress value
        self.progress.setValue(0)
        self.runBtn.setEnabled(False)
        self.logBtn.setEnabled(False)

        self.process.run(self.rundata)

    def run_finished_gui(self, status, results, log):
        """
        Callback called when an async fabber run completes
        """
        self.log = log
        if status == Process.SUCCEEDED:
            save_files = self.savefilesCb.isChecked()     
            if save_files:
                save_folder = self.saveFolderEdit.text()       
                for ovl in results[0].data:
                    self.ivm.overlays[ovl].save_nifti(os.path.join(save_folder, ovl.name))
                    logfile = open(os.path.join(save_folder, "logfile"), "w")
                    logfile.write(self.log)
                    logfile.close()
        else:
            QtGui.QMessageBox.warning(None, "Fabber error", "Fabber failed to run:\n\n" + str(results),
                                      QtGui.QMessageBox.Close)

        self.runBtn.setEnabled(True)
        self.logBtn.setEnabled(status == Process.SUCCEEDED)

    def update_progress(self, complete):
        self.progress.setValue(100*complete)

    def view_log(self):
         self.logview = LogViewerDialog(log=self.log, parent=self)
         self.logview.show()
         self.logview.raise_()
