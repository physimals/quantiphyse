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

from pkview import error_dialog
from pkview.QtInherit.QtSubclass import QGroupBoxB
from pkview.analysis import MultiProcess
from pkview.volumes.volume_management import Volume, Roi, Overlay
from pkview.utils import yaml_loader, save_file
from pkview.widgets import PkWidget

try:
    if "FSLDIR" in os.environ: sys.path.append("%s/lib/python/" % os.environ["FSLDIR"])
    if "FABBERDIR" in os.environ: sys.path.append("%s/lib/python/" % os.environ["FABBERDIR"])
    from fabber import FabberRunData, FabberLib, FabberException, find_fabber
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

TITLE = """
<p><font size="5">Fabber Bayesian model fitting</font></p>

<p>Please cite:</p>
<p><i>Chappell, M.A., Groves, A.R., Woolrich, M.W., "Variational Bayesian inference for a non-linear forward model", IEEE Trans. Sig. Proc., 2009, 57(1), 223-236</i>
</p>
"""
class FabberProcess(MultiProcess):

    """ Signal emitted to track progress"""
    sig_progress = QtCore.Signal(int, int)

    def __init__(self, rundata, vol, roi, **overlays):
        N = vol.data.shape[0]
        input_args = [rundata, vol.data, roi.data]
        for key, value in overlays.items():
            input_args.append(key)
            input_args.append(value.data)
        MultiProcess.__init__(self, N, _run_fabber, input_args)

        # Callbacks to update GUI during processing
        self.voxels_todo = np.count_nonzero(roi.data)
        self.voxels_done = [0, ] * N

    def progress(self):
        if self.queue.empty(): return
        while not self.queue.empty():
            id, v, nv = self.queue.get()
            self.voxels_done[id] = v
        cv = sum(self.voxels_done)
        self.sig_progress.emit(cv, self.voxels_todo)

    def get_output(self):
        log, output = "", {}
        if not self.failed:
            log = "\n\n".join([o.log for o in self.output])
            for key in self.output[0].data:
                recombined_item = np.concatenate([self.output[i].data[key] for i in range(self.n)], 0)
                output[key] = Overlay(name=key, data=recombined_item)

        return log, output

def fabber_batch(yaml_file):
    """
    Run Fabber in batch mode using the specified YAML file. eg6_fabber.yaml gives an examples
    """
    yaml = yaml_loader(yaml_file)

    output_folder = yaml["OutputFolder"]

    rundata = FabberRunData()
    for key in yaml["Options"]:
        val = yaml["Options"][key]
        if val is None: val = ""
        rundata[key] = str(val)

    overlays = {}
    if "Overlays" in yaml:
        for key in yaml["Overlays"]:
            overlays[key] = Overlay(key, fname=yaml["Overlays"][key])

    subjs = yaml["Subjects"]
    for subj in subjs:
        vol = Volume("data", fname=subjs[subj]["Folder"] + subjs[subj]["Data"])
        roi = Roi("roi", fname=subjs[subj]["Folder"] + subjs[subj]["Roi"])

        process = FabberProcess(rundata, vol, roi, **overlays)
        process.run(sync=True)

        try:
            os.makedirs(output_folder + "/" + subj)
        except OSError, e:
            warnings.warn(str(e))

        log, data = process.get_output()
        for key, ovl in data.items():
            ovl.copy_header(vol.nifti_header)
            ovl.save_nifti(fname=output_folder + "/" + subj + "/" + key + ".nii")

        f = open(output_folder + "/" + subj + "/logfile", "w")
        f.write(log)
        f.close()

def _make_fabber_progress_cb(id, queue):
    def progress_cb(voxel, nvoxels):
        if (voxel % 100 == 0) or (voxel == nvoxels):
            queue.put((id, voxel, nvoxels))

    return progress_cb

def _run_fabber(id, queue, rundata, main_data, roi, *overlays):
    """
    Function to run Fabber as a separate process
    """
    try:
        #print("Running, id=", id, "shape=", main_data.shape)
        data = {"data" : main_data}
        n = 0
        while n < len(overlays):
            data[overlays[n]] = overlays[n+1]
            n += 2
        lib = FabberLib(rundata=rundata, auto_load_models=True)
        run = lib.run_with_data(rundata, data, roi, progress_cb=_make_fabber_progress_cb(id, queue))
        return id, True, run
    except FabberException, e:
        print(e)
        return id, False, e
    except:
        print(sys.exc_info()[0])
        return id, False, sys.exc_info()[0]

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
        optionsBox = QGroupBoxB()
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
        runBox = QGroupBoxB()
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
        fileBox = QGroupBoxB()
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
        title_label = QtGui.QLabel(TITLE)
        title_label.setWordWrap(True)
        mainGrid.addWidget(title_label)
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

        # Pass in input data. To enable the multiprocessing module to split our volumes
        # up automatically we have to pass the arguments as a single list. This consists of
        # rundata, main data, roi and then each of the used overlays, name followed by data
        input_args = [self.rundata, img.data, roi.data]
        overlays = {}
        for dialog in (self.methodOpts, self.modelOpts, self.methodOpts):
            for view in dialog.views.values():
                if isinstance(view, ImageOptionView) and view.combo.isEnabled():
                    ov = view.combo.currentText()
                    overlays[ov] = self.ivm.overlays[ov]

        self.process = FabberProcess(self.rundata, img, roi, **overlays)
        self.process.sig_finished.connect(self.run_finished_gui)
        self.process.sig_progress.connect(self.update_progress)
        self.process.run()
        self.runBtn.setEnabled(False)
        self.logBtn.setEnabled(False)

    def run_finished_gui(self, success, results):
        """
        Callback called when an async fabber run completes
        """
        if success:
            print("finished success")
            self.log, output = self.process.get_output()
            print("got output")
            first = True
            save_files = self.savefilesCb.isChecked()
            save_folder = self.saveFolderEdit.text()
            for ovl in output.values():
                print(ovl.name, ovl.shape)
                #print(key, recombined_item.shape)
                self.ivm.add_overlay(ovl, make_current=first)
                if save_files:
                    ovl.save_nifti(os.path.join(save_folder, ovl.name))
                    logfile = open(os.path.join(save_folder, "logfile"), "w")
                    logfile.write(self.log)
                    logfile.close()
                first = False
            self.runs = results
        else:
            # If one process fails, they all fail
            QtGui.QMessageBox.warning(None, "Fabber error", "Fabber failed to run:\n\n" + str(results),
                                      QtGui.QMessageBox.Close)

        self.runBtn.setEnabled(True)
        self.logBtn.setEnabled(success)

    def update_progress(self, done, todo):
        print("total of %i done of %i" % (done, todo))
        if todo > 0:
            percent = 100 * float(done) / todo
            self.progress.setValue(percent)

    def view_log(self):
         self.logview = LogViewerDialog(log=self.log, parent=self)
         self.logview.show()
         self.logview.raise_()
