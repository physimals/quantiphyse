import os.path
import re
import numpy as np

from PySide import QtGui
import nibabel as nib
from scipy.ndimage.filters import gaussian_filter

from pkview.analysis.t1_model import t10_map
from pkview.volumes.volume_management import Volume, Overlay, Roi
from pkview.widgets import PkWidget

def run_batch(case, params):
    fa_vols, fas = [], []
    for fname, fa in params["vfa"].items():
        vol = Volume(fname, fname=case.get_filepath(fname))
        if isinstance(fa, list):
            for i, a in enumerate(fa):
                fas.append(a)
                fa_vols.append(vol.data[:,:,:,i])
        else:
            fas.append(fa)
            fa_vols.append(vol.data)

    if "afi" in params:
        # We are doing a B0 correction (preclinical)
        afi_vols, trs = [], []
        for fname, tr in params["afi"].items():
            vol = Volume(fname, fname=case.get_filepath(fname))
            if isinstance(tr, list):
                for i, a in enumerate(tr):
                    trs.append(a)
                    afi_vols.append(vol.data[:,:,:,i])
            else:
                trs.append(tr)
                afi_vols.append(vol.data)

        fa_afi = params["fa-afi"]
        T10 = t10_map(fa_vols, fas, TR=params["tr"], afi_vols=afi_vols, fa_afi=fa_afi, TR_afi=trs)
        if "smooth" in params:
            T10 = gaussian_filter(T10, sigma=params["smooth"].get("sigma", 0.5), 
                                  truncate=params["smooth"].get("truncate", 3))
    else:
        T10 = t10_map(fa_vols, fas, params["tr"])

    if "clamp" in params:
        np.clip(T10, params["clamp"]["min"], params["clamp"]["max"], out=T10)
    case.ivm.add_overlay(Overlay(name="T10", data=T10))
    return ""
    
class NumberInput(QtGui.QHBoxLayout):
    def __init__(self, text, initial_val):
        super(NumberInput, self).__init__()
        self.text = text
        self.val = initial_val

        label = QtGui.QLabel(self.text)
        self.addWidget(label)
        self.edit = QtGui.QLineEdit(str(self.val))
        self.addWidget(self.edit)
        self.edit.editingFinished.connect(self.changed)
        self.addStretch(1)
        self.valid = True

    def changed(self):
        try:
            self.val = float(self.edit.text())
            self.valid = True
        except:
            self.valid = False
            QtGui.QMessageBox.warning(None, "Invalid value", "%s must be a number" % self.text, QtGui.QMessageBox.Close)
            self.edit.setFocus()
            self.edit.selectAll()

class SourceImageList(QtGui.QVBoxLayout):
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
        b1.clicked.connect(self.add)
        bbox.addWidget(b1)
        b2 = QtGui.QPushButton('Remove')
        b2.clicked.connect(self.remove)
        bbox.addWidget(b2)
        self.addLayout(bbox)

    def check_file(self, filename):
        """
        Check that filename is a valid FA image. It must be
        3D (currently - 4D may be possible but must be handled differently)
        and must have shape consistent with the main volume
        """
        try:
            f = Overlay(name=filename, fname=filename, affine=self.ivm.vol.affine)
            if len(f.shape) not in (3, 4):
                QtGui.QMessageBox.warning(None, "Invalid file", "File must be 3D or 4D volumes",
                                          QtGui.QMessageBox.Close)
                return []

            if f.shape[:3] != self.ivm.vol.shape[:3]:
                QtGui.QMessageBox.warning(None, "Invalid file", "File dimensions must match the loaded volume",
                                          QtGui.QMessageBox.Close)
                return []
        except:
            QtGui.QMessageBox.warning(None, "Invalid file", "Files must be NIFTI volumes",
                                      QtGui.QMessageBox.Close)
            return []

        return f.shape

    def load_image(self, filename):
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
                except:
                    QtGui.QMessageBox.warning(None, "Invalid value", "Must be a number", QtGui.QMessageBox.Close)
            else:
                break

    def load_multi_images(self, filename, n):
        guess=""
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
                except:
                    QtGui.QMessageBox.warning(None, "Invalid value", "Must be a series of comma-separated numbers",
                                              QtGui.QMessageBox.Close)
            else:
                break

    def add(self):
        if self.ivm.vol is None:
            QtGui.QMessageBox.warning(None, "No image", "Load an image volume before generating T10 map",
                                      QtGui.QMessageBox.Close)
            return

        if self.dir is None:
            self.dir = self.ivm.vol.dir

        filename, junk = QtGui.QFileDialog.getOpenFileName(None, "Open image", dir=self.dir)
        if filename:
            dims = self.check_file(filename)
            if len(dims) == 3:
                self.load_image(filename)
            elif len(dims) == 4:
                self.load_multi_images(filename, dims[3])

    def remove(self):
        row = self.table.currentRow()
        self.table.removeRow(row)
        fa_angles = []

    def get_images(self):
        vols = []
        vals = []
        for i in range(self.table.rowCount()):
            filename = self.table.item(i, 0).text()
            file_vals = [float(v) for v in self.table.item(i, 1).text().split(",")]
            # NB need to pass main volume affine to ensure consistant orientation
            img = Overlay(filename, fname=filename, affine=self.ivm.vol.affine)
            vol = img.data
            if len(file_vals) == 1:
                # FIXME need to check dimensions against volume?
                vols.append(vol)
                vals.append(file_vals[0])
            else:
                for i, val in enumerate(file_vals):
                    subvol=vol[...,i]
                    vols.append(subvol)
                    vals.append(val)
        return vols, vals

class T10Widget(PkWidget):
    """
    Run T10 analysis on 3 input volumes
    """
    def __init__(self, **kwargs):
        super(T10Widget, self).__init__(name="T10", desc="Generate T10 map", icon="t10", **kwargs)
        layout = QtGui.QVBoxLayout()
        self.setLayout(layout)

        layout.addWidget(QtGui.QLabel("<font size=5>T10 map generation</font>"))

        fabox = QtGui.QGroupBox()
        fabox.setTitle("Flip angle images")
        self.fatable = SourceImageList("Flip angle", val_range=[0, 90])
        fabox.setLayout(self.fatable)
        self.trinp = NumberInput("TR (ms)", 4.108)
        self.fatable.addLayout(self.trinp)
        layout.addWidget(fabox)
        
        self.preclin = QtGui.QCheckBox("Use B0 correction (Preclinical)")
        self.preclin.stateChanged.connect(self.preclin_changed)
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
        self.smooth.stateChanged.connect(self.smooth_changed)
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
        self.smooth_changed()
        hbox.addStretch(1)
        self.trtable.addLayout(hbox)

        layout.addWidget(self.preclinGroup)

        hbox = QtGui.QHBoxLayout()
        self.clamp = QtGui.QCheckBox("Clamp T10 values between")
        self.clamp.stateChanged.connect(self.clamp_changed)
        self.clamp.setChecked(False)
        hbox.addWidget(self.clamp)
        self.clampMin = QtGui.QDoubleSpinBox()
        self.clampMin.setValue(0)
        hbox.addWidget(self.clampMin)
        hbox.addWidget(QtGui.QLabel("and"))
        self.clampMax = QtGui.QDoubleSpinBox()
        self.clampMax.setValue(5)
        hbox.addWidget(self.clampMax)
        self.clamp_changed()
        hbox.addStretch(1)
        layout.addLayout(hbox)

        hbox = QtGui.QHBoxLayout()
        self.gen = QtGui.QPushButton('Generate T1 map', self)
        self.gen.clicked.connect(self.generate)
        hbox.addWidget(self.gen)
        hbox.addStretch(1)
        layout.addLayout(hbox)

        self.fatable.ivm = self.ivm
        self.trtable.ivm = self.ivm

    def smooth_changed(self):
        self.sigma.setEnabled(self.smooth.isChecked())
        self.truncate.setEnabled(self.smooth.isChecked())

    def preclin_changed(self):
        self.preclinGroup.setVisible(self.preclin.isChecked())

    def clamp_changed(self):
        self.clampMin.setEnabled(self.clamp.isChecked())
        self.clampMax.setEnabled(self.clamp.isChecked())

    def generate(self):
        if self.ivm.vol is None:
            QtGui.QMessageBox.warning(self, "No volume", "Load a volume before generating T10 map", QtGui.QMessageBox.Close)
            return
        elif not self.trinp.valid:
            QtGui.QMessageBox.warning(self, "Invalid TR", "TR value is invalid", QtGui.QMessageBox.Close)
            return
        elif self.preclin.isChecked() and not self.fainp.valid:
            QtGui.QMessageBox.warning(self, "Invalid FA", "FA value for B0 correction is invalid", QtGui.QMessageBox.Close)
            return

        fa_vols, fa_angles = self.fatable.get_images()
        if len(fa_vols) == 0:
            QtGui.QMessageBox.warning(self, "No FA images", "Load FA images before generating T10 map",
                                      QtGui.QMessageBox.Close)
            return

        # TR is expected in seconds but UI asks for it in ms
        tr = self.trinp.val / 1000

        if self.preclin.isChecked():
            afi_vols, afi_trs = self.trtable.get_images()
            if len(afi_vols) == 0:
                QtGui.QMessageBox.warning(self, "No AFI images", "Load AFI images before using B0 correction",
                                          QtGui.QMessageBox.Close)
                return
            fa_afi = self.fainp.val
            T10 = t10_map(fa_vols, fa_angles, TR=tr,
                      afi_vols=afi_vols, fa_afi=fa_afi, TR_afi=afi_trs)
            if self.smooth.isChecked():
                T10 = gaussian_filter(T10, sigma=self.sigma.value(), truncate=self.truncate.value())
        else:
            T10 = t10_map(fa_vols, fa_angles, TR=tr)

        if self.clamp.isChecked():
            np.clip(T10, self.clampMin.value(), self.clampMax.value(), out=T10)

        self.ivm.add_overlay(Overlay(name="T10", data=T10), make_current=True)
