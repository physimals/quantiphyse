"""
Quantiphyse - Widgets for data registration and motion correction

Copyright (c) 2013-2018 University of Oxford
"""
from PySide import QtGui

import numpy as np

from quantiphyse.gui.widgets import QpWidget, RoiCombo, TitleWidget
from quantiphyse.gui.dialogs import TextViewerDialog
from quantiphyse.processes import Process
from quantiphyse.utils import debug, get_plugins, QpException

from .process import RegProcess
    
class RegMethod(object):
    """
    A registration method

    Methods should implement, at a minimum, the ``reg`` method
    Methods which take options should implement ``interface`` and ``options``
    Methods may implement ``moco`` if motion correction is handled differently
    """
    def __init__(self, name):
        self.name = name

    @classmethod
    def apply_transform(cls, reg_data, reg_grid, ref_data, ref_grid, transform, queue):
        """
        Apply a previously calculated transformation to a data set

        :param reg_data: 3D Numpy arrays containing data to apply the transform to.
        :param reg_grid: 4x4 array giving grid-to-world transformation for reg_data. World co-ordinates
                         should be in mm.
        :param ref_data: 3D Numpy array containing reference data. Normally this should not be
                         required, however it is possible that the transform is relative to a particular
                         reference.
        :param ref_grid: 4x4 array giving grid-to-world transformation for ref_data. World co-ordinates
                         should be in mm.
        :param transform: Either an affine matrix transformation or a sequence of 3 warp images each
                          the same shape as 'regdata'. This should be a transformation returned by
                          a previous registration using the same method, the same reference data, and
                          registration data in the same space as reg_data.
        :return Tuple of Numpy array containing transformed data and log output as a string
        """
        raise NotImplementedError("Registration method has not implemented 'apply_transform'")

    @classmethod
    def reg_3d(cls, reg_data, reg_grid, ref_data, ref_grid, options, queue):
        """
        3D Registration

        :param reg_data: 3D Numpy array containing data to register.
        :param reg_grid: 4x4 array giving grid-to-world transformation for reg_data. World co-ordinates
                         should be in mm.
        :param ref_data: 3D Numpy array containing reference data.
        :param ref_grid: 4x4 array giving grid-to-world transformation for ref_data. World co-ordinates
                         should be in mm. If not specified, the same transform as ``reg_grid`` is used.
        :param options: Method options as dictionary
        :param queue: Queue object which method may put progress information on to. Progress 
                      should be given as a number between 0 and 1.

        :return Tuple of three items. 
        
                First, A Numpy array containing registered data

                Second, if options contains ``output-transform : True``, transformation found. 
                This is either an affine matrix transformation or a sequence of 3 warp images, 
                each the same shape as ``regdata`` If ``output-transform`` is not given, returns 
                None instead.

                Third, log information from the registration as a string.
        """
        raise NotImplementedError("Registration method has not implemented 'reg'")

    @classmethod
    def reg_4d(cls, reg_data, reg_grid, ref_data, ref_grid, options, queue):
        """
        4D Registration

        The default implementation simply registers each volume of the data independently. However,
        implementations can supply their own more optimal implementation if appropriate

        :param reg_data: 4D Numpy array containing data to register.
        :param reg_grid: 4x4 array giving grid-to-world transformation for reg_data. World co-ordinates
                         should be in mm.
        :param ref_data: 3D Numpy array containing reference data.
        :param ref_grid: 4x4 array giving grid-to-world transformation for ref_data. World co-ordinates
                         should be in mm. If not specified, the same transform as ``reg_grid`` is used.
        :param options: Method options as dictionary
        :param queue: Queue object which method may put progress information on to. Progress 
                      should be given as a number between 0 and 1.

        :return Tuple of three items. 
        
                First, A Numpy array containing registered data

                Second, if options contains ``output-transform : True``, sequence of transformations
                found, one for each volume in ``reg_data``. Each is either an affine matrix transformation 
                or a sequence of 3 warp images, the same shape as ``regdata`` If ``output-transform`` 
                is not given, returns None instead.

                Third, log information from the registration as a string.
        """
        if reg_data.ndim != 4:
            raise QpException("reg_4d expected 4D data")
        
        out_data = np.zeros(reg_data.shape)
        transforms = []
        log = "Default 4D registration using multiple 3d registrations\n"
        for vol in range(reg_data.shape[-1]):
            log += "Registering volume %i of %i\n" % (vol+1, reg_data.shape[-1])
            debug("Vol %i of %i" % (vol+1, reg_data.shape[-1]))
            if vol == options.get("ignore-idx", -1):
                # Ignore this index (e.g. because it is the same as the ref volume)
                out_data[..., vol] = reg_data[..., vol]
                transforms.append(None)
            else:
                debug("Calling reg_3d", cls, cls.reg_3d)
                vols, transform, vol_log = cls.reg_3d(reg_data[..., vol], reg_grid, ref_data, ref_grid, options, queue)
                out_data[..., vol] = vols
                transforms.append(transform)
                log += vol_log
            queue.put(float(vol)/reg_data.shape[-1])

        # If we are not saving transforms, the list will just be a list of None objects
        if not options.get("save-transforms", False):
            transforms = None

        return out_data, transforms, log

    @classmethod
    def moco(cls, moco_data, moco_grid, ref, ref_grid, options, queue):
        """
        Motion correction
        
        The default implementation uses the ``reg_4d`` function to perform motion correction
        as registration to a common reference, however this function can have a custom
        implementation specific to motion correction if required.
        
        :param moco_data: A single 4D Numpy array containing data to motion correct.
        :param moco_grid: 4x4 array giving grid-to-world transformation for ``moco_data``. 
                          World co-ordinates should be in mm.
        :param ref: Either 3D Numpy array containing reference data, or integer giving 
                    the volume index of ``moco_data`` to use
        :param ref_grid: 4x4 array giving grid-to-world transformation for ref_data. 
                         Ignored if ``ref`` is an integer.
        :param options: Method options as dictionary
        :param queue: Queue object which method may put progress information on to. Progress 
                      should be given as a number between 0 and 1.
        
        :return Tuple of three items. 
        
                First, motion corrected data as a 4D Numpy array in the same space as ``moco_data``
        
                Second, if options contains ``output-transform : True``, sequence of transformations
                found, one for each volume in ``reg_data``. Each is either an affine matrix transformation 
                or a sequence of 3 warp images, the same shape as ``regdata`` If ``output-transform`` 
                is not given, returns None instead.

                Third, log information from the registration as a string.
        """
        if moco_data.ndim != 4:
            raise QpException("Cannot motion correct 3D data")
        
        log = "Default MOCO implementation using multiple 3d registrations\n"
        if isinstance(ref, int):
            if ref >= moco_data.shape[3]:
                raise QpException("Reference volume index of %i, but data has only %i volumes" % (ref, moco_data.nvols))
            ref = moco_data[..., ref]
            ref_grid = moco_grid

        out_data, transforms, moco_log = cls.reg_4d(moco_data, moco_grid, ref, ref_grid, options, queue)
        log += moco_log
        return out_data, transforms, log

    def interface(self):
        """
        Return a QtGui.QWidget() to allow options to be controlled
        """
        return QtGui.QVBoxLayout()
        
    def options(self):
        """
        :return: Dictionary of options currently selected
        """ 
        return {}

class RegWidget(QpWidget):
    """
    Generic registration / motion correction widget 
    """
    def __init__(self, **kwargs):
        super(RegWidget, self).__init__(name="Registration", icon="reg", 
                                        desc="Registration and Motion Correction", 
                                        group="Processing", **kwargs)
        self.reg_methods = [c() for c in get_plugins("reg-methods")]

    def init_ui(self):
        layout = QtGui.QVBoxLayout()
        self.setLayout(layout)

        title = TitleWidget(self, title="Registration and Motion Correction", help="reg")
        layout.addWidget(title)

        if not self.reg_methods:
            layout.addWidget(QtGui.QLabel("No registration methods found"))
            layout.addStretch(1)
            return

        hbox = QtGui.QHBoxLayout()
        gbox = QtGui.QGroupBox()
        gbox.setTitle("General Options")
        grid = QtGui.QGridLayout()

        grid.addWidget(QtGui.QLabel("Mode"), 0, 0)
        self.mode_combo = QtGui.QComboBox()
        self.mode_combo.addItem("Registration")
        self.mode_combo.addItem("Motion Correction")
        self.mode_combo.setCurrentIndex(0)
        self.mode_combo.currentIndexChanged.connect(self.mode_changed)
        grid.addWidget(self.mode_combo, 0, 1)

        grid.addWidget(QtGui.QLabel("Method"), 1, 0)
        self.method_combo = QtGui.QComboBox()
        for method in self.reg_methods:
            self.method_combo.addItem(method.name, method)
        self.method_combo.currentIndexChanged.connect(self.method_changed)
        self.method_combo.setCurrentIndex(self.method_combo.findText(self.reg_methods[0].name))
        grid.addWidget(self.method_combo, 1, 1)

        self.refdata_label = QtGui.QLabel("Reference data")
        grid.addWidget(self.refdata_label, 2, 0)
        self.refdata = QtGui.QComboBox()
        self.refdata.currentIndexChanged.connect(self.refdata_changed)
        grid.addWidget(self.refdata, 2, 1)
        
        self.refvol_label = QtGui.QLabel("Reference volume")
        grid.addWidget(self.refvol_label, 3, 0)
        self.refvol = QtGui.QComboBox()
        self.refvol.addItem("Middle volume")
        self.refvol.addItem("Mean volume")
        self.refvol.addItem("Specified volume")
        self.refvol.currentIndexChanged.connect(self.refvol_changed)
        grid.addWidget(self.refvol, 3, 1)

        self.refidx_label = QtGui.QLabel("Index of reference volume")
        self.refidx_label.setVisible(False)
        grid.addWidget(self.refidx_label, 4, 0)
        self.refidx = QtGui.QSpinBox()
        self.refidx.setMinimum(0)
        self.refidx.setVisible(False)
        grid.addWidget(self.refidx, 4, 1)

        self.regdata_label = QtGui.QLabel("Registration data")
        grid.addWidget(self.regdata_label, 5, 0)
        self.regdata = QtGui.QComboBox()
        self.regdata.currentIndexChanged.connect(self.regdata_changed)
        grid.addWidget(self.regdata, 5, 1)
        
        self.warproi_label = QtGui.QLabel("Linked ROI")
        grid.addWidget(self.warproi_label, 6, 0)
        self.warproi = RoiCombo(self.ivm, none_option=True)
        grid.addWidget(self.warproi, 6, 1)
        
        grid.addWidget(QtGui.QLabel("Replace data"), 7, 0)
        self.replace_cb = QtGui.QCheckBox()
        self.replace_cb.stateChanged.connect(self.replace_changed)
        grid.addWidget(self.replace_cb, 7, 1)
        
        self.name_label = QtGui.QLabel("New data name")
        grid.addWidget(self.name_label, 8, 0)
        self.name_edit = QtGui.QLineEdit()
        grid.addWidget(self.name_edit, 8, 1)

        gbox.setLayout(grid)
        hbox.addWidget(gbox)
        hbox.addStretch(1)
        layout.addLayout(hbox)

        # Create the options boxes for reg methods - only one visible at a time!
        self.opt_boxes = {}
        for method in self.reg_methods:
            hbox = QtGui.QHBoxLayout()
            opt_box = QtGui.QGroupBox()
            opt_box.setTitle(method.name.upper())
            opt_box.setLayout(method.interface())
            hbox.addWidget(opt_box)
            opt_box.setVisible(False)
            layout.addLayout(hbox)
            self.opt_boxes[method.name] = opt_box

        hbox = QtGui.QHBoxLayout()
        self.run_btn = QtGui.QPushButton('Run', self)
        self.run_btn.clicked.connect(self.run)
        hbox.addWidget(self.run_btn)
        self.progress = QtGui.QProgressBar(self)
        self.progress.setStatusTip('Be patient. Progress is only updated in chunks')
        hbox.addWidget(self.progress)
        self.log_btn = QtGui.QPushButton('View log', self)
        self.log_btn.clicked.connect(self.view_log)
        self.log_btn.setEnabled(False)
        hbox.addWidget(self.log_btn)
        layout.addLayout(hbox)

        layout.addStretch(1)

        self.mode = 0
        self.method_changed(0)

    def activate(self):
        if self.reg_methods:
            self.ivm.sig_main_data.connect(self.main_data_changed)
            self.ivm.sig_all_data.connect(self.data_changed)
            self.update()

    def deactivate(self):
        if self.reg_methods:
            self.ivm.sig_main_data.disconnect(self.main_data_changed)
            self.ivm.sig_all_data.disconnect(self.data_changed)

    def data_changed(self):
        self.update()

    def main_data_changed(self):
        self.update()

    def method_changed(self, idx):
        if idx >= 0:
            self.method = self.method_combo.itemData(idx)
            for name, box in self.opt_boxes.items():
                box.setVisible(name == self.method.name)
        else:
            self.method = None

    def mode_changed(self, idx):
        self.mode = idx
        if self.mode == 0:
            self.refdata_label.setText("Reference Data")
        else:
            self.refdata_label.setText("Moving Data")

        self.regdata_label.setVisible(self.mode == 0)
        self.regdata.setVisible(self.mode == 0)
        self.update() # Need to remove 3D data when doing Moco

    def refdata_changed(self, idx):
        if idx >= 0:
            vol = self.ivm.data[self.refdata.currentText()]
            self.refvol_label.setVisible(vol.nvols > 1)
            self.refvol.setVisible(vol.nvols > 1)
            if vol.nvols > 1:
                self.refidx.setMaximum(vol.nvols-1)
                self.refidx.setValue(int(vol.nvols/2))
            self.refvol_changed(self.refvol.currentIndex())
            if self.mode == 1: # MoCo
                self.name_edit.setText("%s_reg" % vol.name)

    def regdata_changed(self, idx):
        if idx >= 0 and self.mode == 0:
            self.name_edit.setText("%s_reg" % self.ivm.data[self.regdata.currentText()].name)

    def refvol_changed(self, idx):
        self.refidx.setVisible(self.refvol.isVisible() and (idx == 2))
        self.refidx_label.setVisible(self.refvol.isVisible() and (idx == 2))

    def replace_changed(self):
        self.name_label.setVisible(not self.replace_cb.isChecked())
        self.name_edit.setVisible(not self.replace_cb.isChecked())

    def update(self):
        ref_data_name = self.refdata.currentText()
        reg_data_name = self.regdata.currentText()
        self.refdata.clear()
        self.regdata.clear()
            
        for ovl in self.ivm.data.values():
            if self.mode == 0 or ovl.nvols > 1: self.refdata.addItem(ovl.name)
            if ovl.nvols == 1: self.regdata.addItem(ovl.name)

        idx = self.refdata.findText(ref_data_name)
        self.refdata.setCurrentIndex(max(0, idx))
        idx = self.regdata.findText(reg_data_name)
        self.regdata.setCurrentIndex(max(0, idx))

    def batch_options(self):
        if self.method is None:
            raise QpException("No registration method has been chosen")

        refdata = self.ivm.data.get(self.refdata.currentText(), None)
        if refdata is None: raise QpException("Reference data not found: '%s'" % self.refdata.currentText())

        options = self.method.options()
        options["method"] = self.method.name
        options["output-name"] = self.name_edit.text()
        
        if refdata.nvols > 1:
            refvol = self.refvol.currentIndex()
            if refvol == 0:
                options["ref-vol"] = "median"
            elif refvol == 1:
                options["ref-vol"] = "mean"
            elif refvol == 2:
                options["ref-vol"] = self.refidx.value()
        
        if self.mode_combo.currentIndex() == 0:
            options["mode"] = "reg"
            options["ref"] = self.refdata.currentText()
            options["reg"] = self.regdata.currentText()
            if self.warproi.currentText() != "<none>":
                options["warp-roi"] = self.warproi.currentText()
        else:
            options["mode"] = "moco"
            options["reg"] = self.refdata.currentText()
        return "Reg", options
        
    def run(self):
        options = self.batch_options()[1]
        process = RegProcess(self.ivm)
        self.progress.setValue(0)
        self.run_btn.setEnabled(False)
        self.log_btn.setEnabled(False)
        process.sig_progress.connect(self.progress_cb)
        process.sig_finished.connect(self.finished_cb)
        process.execute(options)

    def finished_cb(self, status, log, exception):   
        self.log = log
        if status != Process.SUCCEEDED:
            QtGui.QMessageBox.warning(self, "Registration error", "Registration failed to run:\n\n" + str(exception),
                                      QtGui.QMessageBox.Close)

        self.run_btn.setEnabled(True)
        self.log_btn.setEnabled(status == Process.SUCCEEDED)

    def progress_cb(self, complete):
        self.progress.setValue(100*complete)

    def view_log(self):
        self.logview = TextViewerDialog(self, title="Registration Log", text=self.log)
        self.logview.show()
        self.logview.raise_()
