"""
Quantiphyse - Widgets for generating T1 map from VFA images

Copyright (c) 2013-2018 University of Oxford
"""

import os.path
import re

from PySide import QtGui

from quantiphyse.gui.widgets import QpWidget, TitleWidget
from quantiphyse.data import load
from quantiphyse.utils import QpException

from .process import T10Process

class NumberInput(QtGui.QHBoxLayout):
    """
    Edit box which only accepts numbers
    """
    def __init__(self, text, initial_val):
        super(NumberInput, self).__init__()
        self.text = text
        self.val = initial_val

        label = QtGui.QLabel(self.text)
        self.addWidget(label)
        self.edit = QtGui.QLineEdit(str(self.val))
        self.addWidget(self.edit)
        self.edit.editingFinished.connect(self._changed)
        self.addStretch(1)
        self.valid = True

    def _changed(self):
        try:
            self.val = float(self.edit.text())
            self.valid = True
        except ValueError:
            self.valid = False
            QtGui.QMessageBox.warning(None, "Invalid value", "%s must be a number" % self.text, QtGui.QMessageBox.Close)
            self.edit.setFocus()
            self.edit.selectAll()

class SourceImageList(QtGui.QVBoxLayout):
    """
    List of VFA source images
    """

    def __init__(self, header_text, val_range=None):
        super(SourceImageList, self).__init__()

        self.header_text = header_text
        self.val_range = val_range
        self.dir = None
        self.table = QtGui.QTableWidget()
        self.table.setColumnCount(2)
        self.table.setSelectionBehavior(QtGui.QAbstractItemView.SelectRows)
        self.table.setHorizontalHeaderLabels(["Filename", header_text])
        header = self.table.horizontalHeader()
        header.setResizeMode(0, QtGui.QHeaderView.Stretch)
        self.addWidget(self.table)

        bbox = QtGui.QHBoxLayout()
        b1 = QtGui.QPushButton('Add')
        b1.clicked.connect(self._add)
        bbox.addWidget(b1)
        b2 = QtGui.QPushButton('Remove')
        b2.clicked.connect(self._remove)
        bbox.addWidget(b2)
        self.addLayout(bbox)

    def _check_file(self, filename):
        """
        Check that filename is a valid FA image. It must be
        3D (currently - 4D may be possible but must be handled differently)
        and must have shape consistent with the main volume
        """
        try:
            f = load(filename)
            if len(f.grid.shape) not in (3, 4):
                QtGui.QMessageBox.warning(None, "Invalid file", "File must be 3D or 4D volumes",
                                          QtGui.QMessageBox.Close)
                return 0
        except QpException:
            QtGui.QMessageBox.warning(None, "Invalid file", "Files must be NIFTI volumes",
                                      QtGui.QMessageBox.Close)
            return 0

        return f.nvols

    def _load_image(self, filename):
        # Try to guess the value from the filename - if it ends in a number, go with that
        self.dir, name = os.path.split(filename)
        name = name.split(".")[0]
        m = re.search(r"(\d+).*$", name)
        if m is not None:
            guess = m.group(1)
        else:
            guess = ""

        while 1:
            text, result = QtGui.QInputDialog.getText(None, "Enter value", "Enter %s" % self.header_text, text=guess)
            if result:
                try:
                    val = float(text)
                    if self.val_range and (val < self.val_range[0] or val > self.val_range[1]):
                        QtGui.QMessageBox.warning(None, "Invalid value", "Must be in range %s" % str(self.val_range),
                                                  QtGui.QMessageBox.Close)
                    else:
                        self.table.insertRow(0)
                        self.table.setItem(0, 0, QtGui.QTableWidgetItem(filename))
                        self.table.setItem(0, 1, QtGui.QTableWidgetItem(text))
                        break
                except ValueError:
                    QtGui.QMessageBox.warning(None, "Invalid value", "Must be a number", QtGui.QMessageBox.Close)
            else:
                break

    def _load_multi_images(self, filename, n):
        guess = ""
        while 1:
            text, result = QtGui.QInputDialog.getText(None, "Enter values",
                                                      "Enter %s as a series of %i comma-separated values" % (self.header_text, n),
                                                      text=guess)
            if result:
                try:
                    fas = [float(v) for v in text.split(",")]
                    if len(fas) != n:
                        QtGui.QMessageBox.warning(None, "Wrong number of values",
                                                  "Must enter %i values, you entered %i" % (n, len(fas)),
                                                  QtGui.QMessageBox.Close)
                        guess = text
                    else:
                        self.table.insertRow(0)
                        self.table.setItem(0, 0, QtGui.QTableWidgetItem(filename))
                        self.table.setItem(0, 1, QtGui.QTableWidgetItem(text))
                        break
                except ValueError:
                    QtGui.QMessageBox.warning(None, "Invalid value", "Must be a series of comma-separated numbers",
                                              QtGui.QMessageBox.Close)
            else:
                break

    def _add(self):
        if self.ivm.main is None:
            QtGui.QMessageBox.warning(None, "No image", "Load an image volume before generating T1 map",
                                      QtGui.QMessageBox.Close)
            return

        if self.dir is None and self.ivm.main.fname is not None:
            self.dir = os.path.dirname(self.ivm.main.fname)

        filename, _ = QtGui.QFileDialog.getOpenFileName(None, "Open image", dir=self.dir)
        if filename:
            nvols = self._check_file(filename)
            if nvols == 1:
                self._load_image(filename)
            else:
                self._load_multi_images(filename, nvols)

    def _remove(self):
        row = self.table.currentRow()
        self.table.removeRow(row)

    def get_images(self):
        """
        :return: Tuple of (sequence of data names, sequence of flip angles in data)
        """
        vols = []
        vals = []
        for i in range(self.table.rowCount()):
            filename = self.table.item(i, 0).text()
            file_vals = [float(v) for v in self.table.item(i, 1).text().split(",")]
            # NB need to pass main volume affine to ensure consistant orientation
            vol = load(filename)
            vol.name = "fa%i" % file_vals[0]
            self.ivm.add(vol)
            # FIXME need to check dimensions against volume?
            vols.append(vol.name)
            vals.append(file_vals)
        return vols, vals

class T10Widget(QpWidget):
    """
    Generate T1 map from variable flip angle images
    """
    def __init__(self, **kwargs):
        super(T10Widget, self).__init__(name="VFA-T1", desc="Generate T1 map from variable flip angle images", icon="t10", 
                                        group="T1", **kwargs)

    def init_ui(self):
        layout = QtGui.QVBoxLayout()
        self.setLayout(layout)

        layout.addWidget(TitleWidget(self, help="t1"))
       
        fabox = QtGui.QGroupBox()
        fabox.setTitle("Flip angle images")
        self.fatable = SourceImageList("Flip angle", val_range=[0, 90])
        fabox.setLayout(self.fatable)
        self.trinp = NumberInput("TR (ms)", 4.108)
        self.fatable.addLayout(self.trinp)
        layout.addWidget(fabox)
        
        self.preclin = QtGui.QCheckBox("Use B0 correction (Preclinical)")
        self.preclin.stateChanged.connect(self._preclin_changed)
        self.preclin.setChecked(False)
        layout.addWidget(self.preclin)

        self.preclinGroup = QtGui.QGroupBox("")
        self.preclinGroup.setTitle("B0 correction")
        self.preclinGroup.setVisible(False)
        self.trtable = SourceImageList("TR (ms)")
        self.preclinGroup.setLayout(self.trtable)
        self.fainp = NumberInput("Flip angle (AFI)", 64)
        self.trtable.addLayout(self.fainp)

        hbox = QtGui.QHBoxLayout()
        self.smooth = QtGui.QCheckBox("Gaussian smoothing: ")
        self.smooth.stateChanged.connect(self._smooth_changed)
        hbox.addWidget(self.smooth)
        hbox.addWidget(QtGui.QLabel("sigma"))
        self.sigma = QtGui.QDoubleSpinBox()
        self.sigma.setValue(0.5)
        self.sigma.setMinimum(0)
        self.sigma.setSingleStep(0.1)
        self.sigma.setDecimals(2)
        hbox.addWidget(self.sigma)
        hbox.addWidget(QtGui.QLabel(", truncate at"))
        self.truncate = QtGui.QDoubleSpinBox()
        self.truncate.setValue(3)
        self.truncate.setMinimum(0)
        self.truncate.setSingleStep(0.1)
        self.truncate.setDecimals(1)
        hbox.addWidget(self.truncate)
        hbox.addWidget(QtGui.QLabel("st.devs"))
        self._smooth_changed()
        hbox.addStretch(1)
        self.trtable.addLayout(hbox)

        layout.addWidget(self.preclinGroup)

        hbox = QtGui.QHBoxLayout()
        self.clamp = QtGui.QCheckBox("Clamp T1 values between")
        self.clamp.stateChanged.connect(self._clamp_changed)
        self.clamp.setChecked(False)
        hbox.addWidget(self.clamp)
        self.clampMin = QtGui.QDoubleSpinBox()
        self.clampMin.setValue(0)
        hbox.addWidget(self.clampMin)
        hbox.addWidget(QtGui.QLabel("and"))
        self.clampMax = QtGui.QDoubleSpinBox()
        self.clampMax.setValue(5)
        hbox.addWidget(self.clampMax)
        self._clamp_changed()
        hbox.addStretch(1)
        layout.addLayout(hbox)

        hbox = QtGui.QHBoxLayout()
        self.gen = QtGui.QPushButton('Generate T1 map', self)
        self.gen.clicked.connect(self._generate)
        hbox.addWidget(self.gen)
        hbox.addStretch(1)
        layout.addLayout(hbox)

        self.fatable.ivm = self.ivm
        self.trtable.ivm = self.ivm

        self.process = T10Process(self.ivm)
        
    def _smooth_changed(self):
        self.sigma.setEnabled(self.smooth.isChecked())
        self.truncate.setEnabled(self.smooth.isChecked())

    def _preclin_changed(self):
        self.preclinGroup.setVisible(self.preclin.isChecked())

    def _clamp_changed(self):
        self.clampMin.setEnabled(self.clamp.isChecked())
        self.clampMax.setEnabled(self.clamp.isChecked())

    def _generate(self):
        if self.ivm.main is None:
            QtGui.QMessageBox.warning(self, "No volume", "Load a volume before generating T1 map", QtGui.QMessageBox.Close)
            return
        elif not self.trinp.valid:
            QtGui.QMessageBox.warning(self, "Invalid TR", "TR value is invalid", QtGui.QMessageBox.Close)
            return
        elif self.preclin.isChecked() and not self.fainp.valid:
            QtGui.QMessageBox.warning(self, "Invalid FA", "FA value for B0 correction is invalid", QtGui.QMessageBox.Close)
            return

        options = {"tr" : self.trinp.val}

        fa_vols, fa_angles = self.fatable.get_images()
        if not fa_vols:
            QtGui.QMessageBox.warning(self, "No FA images", "Load FA images before generating T1 map",
                                      QtGui.QMessageBox.Close)
            return

        vfa = {}
        for vol, fa in zip(fa_vols, fa_angles):
            vfa[vol] = fa
        options["vfa"] = vfa
        
        if self.preclin.isChecked():
            options["fa-afi"] = self.fainp.val

            afi_vols, afi_trs = self.trtable.get_images()
            if not afi_vols:
                QtGui.QMessageBox.warning(self, "No AFI images", "Load AFI images before using B0 correction",
                                          QtGui.QMessageBox.Close)
                return
            afi = {}
            for vol, tr in zip(afi_vols, afi_trs):
                afi[vol] = tr
            options["afi"] = afi

        if self.smooth.isChecked():
            options["smooth"] = {"sigma" : self.sigma.value(), "truncate" : self.truncate.value()}
        if self.clamp.isChecked():
            options["clamp"] = {"min" : self.clampMin.value(), "max" : self.clampMax.value()}

        self.process.run(options)
        