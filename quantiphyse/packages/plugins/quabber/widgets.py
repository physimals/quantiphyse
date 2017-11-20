import os
import traceback

from PySide import QtCore, QtGui

from quantiphyse.gui.widgets import OverlayCombo

from quantiphyse.utils import debug
from quantiphyse.utils.exceptions import QpException

def get_label(text="", size=None, bold=False, italic=False):
    label = QtGui.QLabel(text)
    font = label.font()
    font.setBold(bold)
    font.setItalic(italic)
    label.setFont(font)
    if size: label.setStyleSheet("QLabel{ font: %ipx }" % size)
    return label

class OptionWidget(QtCore.QObject):
    def __init__(self, opt, **kwargs):
        super(OptionWidget, self).__init__()
        self.key = opt["name"]
        self.dtype = opt["type"]
        self.req = not opt["optional"]
        self.default = opt["default"]
        self.desc = opt["description"]
        self.rundata = kwargs.get("rundata", {})
        self.ivm = kwargs.get("ivm", None)
        self.desc_first = kwargs.get("desc_first", False)
        self.dependents = []
        self.widgets = []

        # Basic label
        self.label = get_label(opt["name"])
        self.widgets.append(self.label)

        # Description label
        self.desclabel = get_label(opt["description"])
        self.desclabel.setToolTip("--%s" % self.key)
        self.desclabel.resize(400, self.desclabel.height())
        self.desclabel.setWordWrap(True)
        self.widgets.append(self.desclabel)

        # For non-mandatory options, provide a checkbox to enable them
        if self.req:
            self.enable_cb = None
            self.checked = True
        else:
            self.enable_cb = QtGui.QCheckBox()
            self.enable_cb.stateChanged.connect(self._checkbox_toggled)
            self.widgets.append(self.enable_cb)
            self.checked = False

    def update(self, rundata):
        val = rundata.get(self.key, None)
        if val is not None:
            self.set_value(val)
            if self.enable_cb is not None:
                self.enable_cb.setChecked(True)
        else:
            self.set_value(self.default)
            if self.enable_cb is not None:
                self.enable_cb.setChecked(False)
        # Make sure visibility is updated even if state is unchanged
        if self.enable_cb is not None: self._checkbox_toggled()

    def set_value(self, value):
        # Override to display the current option value in some form
        pass
    
    def get_value(self):
        # Override to retrieve the current option value from the UI widgets
        return ""

    def update_rundata(self):
        if self.checked:
            self.rundata[self.key] = self.get_value()
        elif self.key in self.rundata:
            del self.rundata[self.key]
        debug(self.rundata)

    def add_dependent(self, dep):
        if not self.enable_cb: return
        self.dependents.append(dep)
        dep.set_visible(self.checked)
        if not self.checked: dep.enable_cb.setChecked(False)

    def add(self, grid, row):
        if self.desc_first:
            label = self.desclabel
        else:
            label = self.label
            grid.addWidget(self.desclabel, row, 2)

        if self.req:
            grid.addWidget(label, row, 0)
        else:
            hbox = QtGui.QHBoxLayout()
            hbox.addWidget(self.enable_cb)
            hbox.addWidget(label, row)
            grid.addLayout(hbox, row, 0)

    def set_visible(self, visible=True):
        for widget in self.widgets:
             widget.setVisible(visible)

    def set_enabled(self, enabled=True):
        for widget in self.widgets:
             widget.setEnabled(enabled)
        # Checkbox is always enabled!
        if self.enable_cb is not None: self.enable_cb.setEnabled(True)

    def _checkbox_toggled(self):
        # This function is only called if we have a checkbox
        self.checked = self.enable_cb.checkState() == QtCore.Qt.CheckState.Checked
        self.set_enabled(self.checked)
        
        for dep in self.dependents:
            dep.set_visible(self.checked)
            if not self.checked: dep.enable_cb.setChecked(False)

        self.update_rundata()
        
class IntegerOptionWidget(OptionWidget):
    def __init__(self, opt, **kwargs):
        OptionWidget.__init__(self, opt, **kwargs)
        self.sb = QtGui.QSpinBox()
        self.sb.valueChanged.connect(self.update_rundata)
        self.widgets.append(self.sb)
    
    def get_value(self):
        return str(self.sb.value())
        
    def set_value(self, val):
        if val == "":
            self.sb.setValue(int(self.default))
        else:
            self.sb.setValue(int(val))

    def add(self, grid, row):
        OptionWidget.add(self, grid, row)
        grid.addWidget(self.sb, row, 1)

class StringOptionWidget(OptionWidget):
    def __init__(self, opt, **kwargs):
        OptionWidget.__init__(self, opt, **kwargs)
        self.edit = QtGui.QLineEdit()
        self.edit.editingFinished.connect(self.update_rundata)
        self.widgets.append(self.edit)
            
    def get_value(self):
        return self.edit.text()
        
    def set_value(self, val):
        self.edit.setText(val)

    def add(self, grid, row):
        OptionWidget.add(self, grid, row)
        grid.addWidget(self.sb, row, 1)
        
    def add(self, grid, row):
        OptionWidget.add(self, grid, row)
        grid.addWidget(self.edit, row, 1)

class FileOptionWidget(StringOptionWidget):
    def __init__(self, opt, **kwargs):
        StringOptionWidget.__init__(self, opt, **kwargs)
        self.hbox = QtGui.QHBoxLayout()
        self.hbox.addWidget(self.edit)
        self.btn = QtGui.QPushButton("Choose")
        self.hbox.addWidget(self.btn)
        self.widgets.append(self.btn)
        self.btn.clicked.connect(self._choose_file)
    
    def _choose_file(self):
        dialog = QtGui.QFileDialog()
        dialog.setFileMode(QtGui.QFileDialog.AnyFile)
        if dialog.exec_():
            fname = dialog.selectedFiles()[0]
            self.edit.setText(fname)
            self.update_rundata()

    def add(self, grid, row):
        OptionWidget.add(self, grid, row)
        grid.addLayout(self.hbox, row, 1)

class MatrixFileOptionWidget(FileOptionWidget):
    def __init__(self, opt, **kwargs):
        FileOptionWidget.__init__(self, opt, **kwargs)
        self.editBtn = QtGui.QPushButton("Edit")
        self.hbox.addWidget(self.editBtn)
        self.widgets.append(self.editBtn)
        self.editBtn.clicked.connect(self.edit_file)
    
    def read_vest(self, fname):
        f = None
        in_matrix = False
        mat = []
        try:
            f = open(fname, "r")
            lines = f.readlines()
            nx, ny = 0, 0
            for line in lines:
                if in_matrix:
                    nums = [float(num) for num in line.split()]
                    if len(nums) != nx: raise Exception ("Incorrect number of x values")
                    mat.append(nums)
                elif line.startswith("/Matrix"):
                  if nx == 0 or ny == 0: raise Exception("Missing /NumWaves or /NumPoints")
                  in_matrix = True
                elif line.startswith("/NumWaves"):
                  parts = line.split()
                  if len(parts) == 1: raise Exception("No number following /NumWaves")
                  nx = int(parts[1])
                elif line.startswith("/NumPoints") or line.startswith("/NumContrasts"):
                  parts = line.split()
                  if len(parts) == 1: raise Exception("No number following /NumPoints")
                  ny = int(parts[1])
            if len(mat) != ny:
                raise Exception("Incorrect number of y values")      
        finally:
            if f is not None: f.close()

        if not in_matrix: 
            raise QpException("File '%s' does not contain a VEST matrix" % fname)
        else:
            return mat, ""

    def read_ascii(self, fname):
        f = None
        in_matrix = False
        mat = []
        desc = ""
        try:
            f = open(fname, "r")
            lines = f.readlines()
            nx = 0
            for line in lines:
                if line.strip().startswith("#"):
                    desc += line.lstrip("#")
                else:
                    row = [float(n) for n in line.split()]
                    if not in_matrix:
                        nx = len(row)
                        in_matrix = True
                    elif len(row) != nx:
                        raise Exception("Incorrect number of x values: %s" % line)
                    mat.append(row)
        finally:
            if f is not None: f.close()

        return mat, desc

    def write_vest(self, fname, m, desc=""):
        f = None
        try:
            f = open(fname, "w")
            nx, ny = len(m), len(m[0])
            f.write("/NumWaves %i\n" % nx)
            f.write("/NumPoints %i\n" % ny)
            f.write("/Matrix\n")
            for row in m:
                for item in row:
                    f.write("%f " % item)
                f.write("\n")
        finally:
            if f is not None: f.close()

    def write_ascii(self, fname, m, desc=""):
        f = None
        try:
            f = open(fname, "w")
            for line in desc.splitlines():
                f.write("#%s\n" % line)
            for row in m:
                f.write(" ".join([str(v) for v in row]))
                f.write("\n")
        finally:
            if f is not None: f.close()

    def edit_file(self):
        fname = self.edit.text()
        if fname.strip() == "":
            msgBox = QtGui.QMessageBox()
            msgBox.setText("Enter a filename")
            msgBox.setStandardButtons(QtGui.QMessageBox.Ok)
            msgBox.exec_()
            return
        elif not os.path.exists(fname):
            msgBox = QtGui.QMessageBox()
            msgBox.setText("File does not exist - create?")
            msgBox.setStandardButtons(QtGui.QMessageBox.Ok | QtGui.QMessageBox.Cancel)
            msgBox.setDefaultButton(QtGui.QMessageBox.Ok)
            ret = msgBox.exec_()
            if ret != QtGui.QMessageBox.Ok:
                return
            open(fname, "a").close()

        try:
            try:
                mat, desc = self.read_vest(fname)
                ascii = False
            except:
                mat, desc = self.read_ascii(fname)
                ascii = True
            self.mat_dialog.set_matrix(mat, desc)
            if self.mat_dialog.exec_():
                mat, desc = self.mat_dialog.get_matrix()
                if ascii:
                    self.write_ascii(fname, mat, desc)
                else:
                    self.write_vest(fname, mat, desc)
        except:
            traceback.print_exc()

class ImageOptionWidget(OptionWidget):
    """
    OptionWidget subclass which allows image options to be chosen
    from the current list of overlays
    """
    def __init__(self, opt, **kwargs):
        OptionWidget.__init__(self, opt, **kwargs)
        self.combo = OverlayCombo(self.ivm, static_only=True)
        self.widgets.append(self.combo)

    def get_value(self):
        return self.combo.currentText()

    def set_value(self, val):
        idx = self.combo.findText(val)
        self.combo.setCurrentIndex(idx)

    def add(self, grid, row):
        OptionWidget.add(self, grid, row)
        grid.addWidget(self.combo, row, 1)

OPT_VIEW = {
    "INT" : IntegerOptionWidget,
    "BOOL": OptionWidget,
    "FILE": FileOptionWidget,
    "IMAGE": ImageOptionWidget,
    "TIMESERIES" : ImageOptionWidget,
    "MVN": FileOptionWidget,
    "MATRIX": MatrixFileOptionWidget,
}

def get_option_widget(opt, **kwargs):
    return OPT_VIEW.get(opt["type"], StringOptionWidget)(opt, **kwargs)
   