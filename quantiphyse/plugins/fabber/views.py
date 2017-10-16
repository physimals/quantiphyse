import sys, os
import traceback
import re
import warnings

from PySide import QtCore, QtGui

from ...utils.exceptions import QpException

# Current overlays list from the IVM object. Global so that all the ImageOptionView instances
# can see what overlays to offer as options
CURRENT_OVERLAYS = []

try:
    from fabber import View, FabberException, FabberLib, find_fabber
except:
    # Stub to prevent import failure if Fabber not available
    warnings.warn("Failed to import Fabber API - widget will be disabled")
    traceback.print_exc()
    class View:
        pass

NUMBERED_OPTIONS_MAX=20
        
def get_label(text, size=None, bold=False, italic=False):
    label = QtGui.QLabel(text)
    font = label.font()
    font.setBold(bold)
    font.setItalic(italic)
    if size: font.setPointSize(size)
    label.setFont(font)
    return label

class OptionView(View):
    def __init__(self, opt, **kwargs):
        View.__init__(self, [opt["name"],], **kwargs)
        self.key = opt["name"]
        self.dtype = opt["type"]
        self.req = not opt["optional"]
        self.default = opt["default"]
        self.desc = opt["description"]
        self.dependents = []
        self.desc_first = kwargs.get("desc_first", False)
        self.label = get_label(opt["name"], size=10)
        self.desclabel = get_label(opt["description"], size=10)
        self.desclabel.setToolTip("--%s" % self.key)
        self.desclabel.resize(400, self.desclabel.height())
        self.desclabel.setWordWrap(True)
        if self.req:
            self.enable_cb = None
        else:
            self.enable_cb = QtGui.QCheckBox()
            self.enable_cb.stateChanged.connect(self.state_changed)
            self.widgets.append(self.enable_cb)
        self.widgets.append(self.label)
        self.widgets.append(self.desclabel)

    def add_dependent(self, dep):
        if not self.enable_cb: return
        self.dependents.append(dep)
        checked = self.enable_cb.checkState() == QtCore.Qt.CheckState.Checked
        dep.set_visible(checked)
        if not checked: dep.enable_cb.setChecked(False)

    def set_visible(self, visible=True, widgets=None):
        if widgets is None: widgets = self.widgets
        for widget in widgets:
                widget.setVisible(visible)

    def state_changed(self):
        # This function is only called if we have a checkbox
        checked = self.enable_cb.checkState() == QtCore.Qt.CheckState.Checked
        self.set_enabled(checked)
        self.enable_cb.setEnabled(True)
        
        for dep in self.dependents:
            dep.set_visible(checked)
            if not checked: dep.enable_cb.setChecked(False)

        if checked:
            self.changed()
        else:
            del self.rundata[self.key]
        
    def changed(self):
        self.rundata[self.key] = ""
        
    def do_update(self):
        if not self.req:
            if not self.key in self.rundata:
                self.enable_cb.setCheckState(QtCore.Qt.CheckState.Unchecked)
            else:
                self.enable_cb.setCheckState(QtCore.Qt.CheckState.Checked)

            self.set_enabled(self.enable_cb.checkState() == QtCore.Qt.CheckState.Checked)
            self.enable_cb.setEnabled(True)
       
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

class IntegerOptionView(OptionView):
    def __init__(self, opt, **kwargs):
        OptionView.__init__(self, opt, **kwargs)
        self.sb = QtGui.QSpinBox()
        self.sb.valueChanged.connect(self.changed)
        self.widgets.append(self.sb)
    
    def changed(self):
        val = str(self.sb.value())
        self.rundata[self.key] = val
        
    def do_update(self):
        OptionView.do_update(self)
        if self.key in self.rundata:
            self.sb.setValue(int(self.rundata[self.key]))

    def add(self, grid, row):
        OptionView.add(self, grid, row)
        grid.addWidget(self.sb, row, 1)

class StringOptionView(OptionView):
    def __init__(self, opt, **kwargs):
        OptionView.__init__(self, opt, **kwargs)
        self.edit = QtGui.QLineEdit()
        self.edit.editingFinished.connect(self.changed)
        self.widgets.append(self.edit)
        
    def changed(self):
        # Note that this signal is triggered when the widget
        # is enabled/disabled!
        if self.edit.isEnabled():
            self.rundata[self.key] = self.edit.text()

    def do_update(self):
        OptionView.do_update(self)
        if self.key in self.rundata:
            self.text = self.rundata[self.key]
            self.edit.setText(self.text)
        
    def add(self, grid, row):
        OptionView.add(self, grid, row)
        grid.addWidget(self.edit, row, 1)
        
class FileOptionView(StringOptionView):
    def __init__(self, opt, **kwargs):
        StringOptionView.__init__(self, opt, **kwargs)
        self.hbox = QtGui.QHBoxLayout()
        self.hbox.addWidget(self.edit)
        self.btn = QtGui.QPushButton("Choose")
        self.hbox.addWidget(self.btn)
        self.widgets.append(self.btn)
        self.btn.clicked.connect(self.choose_file)
    
    def choose_file(self):
        dialog = QtGui.QFileDialog()
        dialog.setFileMode(QtGui.QFileDialog.AnyFile)
        if dialog.exec_():
            fname = dialog.selectedFiles()[0]
            self.edit.setText(fname)
            self.changed()

    def add(self, grid, row):
        OptionView.add(self, grid, row)
        grid.addLayout(self.hbox, row, 1)

class MatrixFileOptionView(FileOptionView):
    def __init__(self, opt, **kwargs):
        FileOptionView.__init__(self, opt, **kwargs)
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
            print(mat, desc)
            self.mat_dialog.set_matrix(mat, desc)
            if self.mat_dialog.exec_():
                mat, desc = self.mat_dialog.get_matrix()
                if ascii:
                    self.write_ascii(fname, mat, desc)
                else:
                    self.write_vest(fname, mat, desc)
        except:
            traceback.print_exc()

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

class ModelMethodView(View):
    def __init__(self, **kwargs):
        View.__init__(self, ["fabber", "model", "method", "loadmodels"], **kwargs)
        self.models = None
        self.methods = None
        self.modelCombo.currentIndexChanged.connect(self.model_changed)
        self.methodCombo.currentIndexChanged.connect(self.method_changed)
        self.auto_load_models = kwargs.get("auto_load_models", False)
        
    def model_changed(self):
        self.rundata["model"] = self.modelCombo.currentText()
        
    def method_changed(self):
        self.rundata["method"] = self.methodCombo.currentText()

    def do_update(self):
        if self.rundata.changed("fabber", "loadmodels"):
            self.modelCombo.clear()
            self.models = FabberLib(rundata=self.rundata, auto_load_models=self.auto_load_models).get_models()
            for model in self.models:
                self.modelCombo.addItem(model)
        
            self.methodCombo.clear()
            self.methods = FabberLib(rundata=self.rundata).get_methods()
            for method in self.methods:
                self.methodCombo.addItem(method)
                
        if "model" in self.rundata:
            cmodel = self.rundata["model"]
            for idx, model in enumerate(self.models):
                if cmodel == model:
                    self.modelCombo.setCurrentIndex(idx)

        if "method" in self.rundata:
            cmethod = self.rundata["method"]
            for idx, method in enumerate(self.methods):
                if cmethod == method:
                    self.methodCombo.setCurrentIndex(idx)

OPT_VIEW = {
    "INT" : IntegerOptionView,
    "BOOL": OptionView,
    "FILE": FileOptionView,
    "IMAGE": ImageOptionView,
    "TIMESERIES" : ImageOptionView,
    "MVN": FileOptionView,
    "MATRIX": MatrixFileOptionView,
    "": StringOptionView,
}

def get_option_view(opt, **kwargs):
    if opt["type"] in OPT_VIEW:
        return OPT_VIEW[opt["type"]](opt, **kwargs)
    else:
        return OPT_VIEW[""](opt, **kwargs)

class OptionsView(View):
    def __init__(self, **kwargs):
        View.__init__(self, [], **kwargs)
        self.views = {}
        self.ignore_opts = set()
        self.btn.clicked.connect(self.show)
        self.desc_first = kwargs.get("desc_first", False)
        if hasattr(self, "dialog"):
            self.grid = self.dialog.grid
            self.title_label = self.dialog.modelLabel
            self.desc_label = self.dialog.descLabel

    def show(self):
        self.dialog.show()
        self.dialog.raise_()

    def ignore(self, *opts):
        for opt in opts:
            self.ignore_opts.add(opt)

    def del_layout(self, layout):
        while True:
            w = layout.takeAt(0)
            if w is None:
                break
            elif w.widget() is None:
                self.del_layout(w)    
            else:
                w.widget().deleteLater()
                
    def clear(self):
        self.del_layout(self.grid)
        self.views = {}

    def add_opts(self, opts, startrow):
        row = 0
        for opt in opts:
            if opt["name"].find("<n>") >= 0:
                # This is a numbered option. Create one for each
                opt_base=opt["name"][:opt["name"].find("<n>")]
                opt_suffix = opt["name"][opt["name"].find("<n>") + 3:]
                for n in range(1, NUMBERED_OPTIONS_MAX+1):
                    newopt = dict(opt)
                    newopt["name"] = "%s%i%s" % (opt_base, n, opt_suffix)
                    view = get_option_view(newopt, desc_first=self.desc_first)
                    view.mat_dialog = self.mat_dialog
                    if n > 1:
                        prev.add_dependent(view)

                    view.add(self.grid, row + startrow)
                    self.views[newopt["name"]] = view
                    prev = view
                    row += 1
            else:
                view = get_option_view(opt, desc_first=self.desc_first)
                view.mat_dialog = self.mat_dialog
                view.add(self.grid, row+startrow)
                self.views[opt["name"]] = view
                row += 1
        return row

    def do_update(self):
        if self.rundata.changed("fabber"):
            self.clear()
            self.opts, self.desc = FabberLib(rundata=self.rundata).get_options()
            self.opts = [opt for opt in self.opts if opt["name"] not in self.ignore_opts]
            if len(self.opts) == 0:
                msgBox = QtGui.QMessageBox()
                msgBox.setText("Could not get options from Fabber - check the path to the executable")
                msgBox.exec_()
            self.title = "Fabber General Options"
            self.desc = "These options are not specific to a particular model or inference method"
            self.create_views()

        for view in self.views.values():
            view.update(self.rundata)

    def create_views(self):
        req = [opt for opt in self.opts if not opt["optional"]]
        nonreq = [opt for opt in self.opts if opt["optional"]]
        
        if hasattr(self, "title_label"): self.title_label.setText(self.title)
        if hasattr(self, "desc_label"): self.desc_label.setText(self.desc)
        
        if req:
            label = get_label("Mandatory options", size=12, bold=True)
            self.grid.addWidget(label, 0, 0)
            self.add_opts(req, 1)
        if nonreq:
            label = get_label("Non-mandatory options", size=12, bold=True)
            self.grid.addWidget(label, len(req)+1, 0)
            self.add_opts(nonreq, len(req)+2)

        self.grid.setAlignment(QtCore.Qt.AlignTop)
        if hasattr(self, "dialog"): self.dialog.adjustSize()
        
class ComponentOptionsView(OptionsView):
    """
    Options dialog for model or method
    """
    def __init__(self, otype, text, **kwargs):
        OptionsView.__init__(self, **kwargs)
        self.type = otype
        self.text = text
        self.value = ""
        self.auto_load_models = kwargs.get("auto_load_models", False)

    def do_update(self):
        value = self.rundata.get(self.type,"")
        if self.rundata.changed("fabber") or self.value != value:
            self.value = value
            self.clear()
            if self.value != "":
                args = {self.type : self.value}
                self.opts, self.desc = FabberLib(rundata=self.rundata, auto_load_models=self.auto_load_models).get_options(**args)
                self.opts = [opt for opt in self.opts if opt["name"] not in self.ignore_opts]
                self.title = "%s: %s" % (self.text, self.value)
                self.create_views()

        for view in self.views.values():
            view.update(self.rundata)
   
class ModelOptionsView(ComponentOptionsView):
    """
    Options dialog for model
    """
    def __init__(self, **kwargs):
        ComponentOptionsView.__init__(self, "model", "Forward Model", **kwargs)

    def do_update(self):
        ComponentOptionsView.do_update(self)
        self.btn.setText("%s model options" % self.value.upper())

class MethodOptionsView(ComponentOptionsView):
    """
    Options dialog for inference method
    """
    def __init__(self, **kwargs):
        ComponentOptionsView.__init__(self, "method", "Inference Method", **kwargs)

    def do_update(self):
        ComponentOptionsView.do_update(self)
        self.btn.setText("%s method options" % self.value.upper())
   
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
        self.grid.setSpacing(20)
        self.prior_widgets = []
        
        self.dialog.modelLabel.setText("Model parameter priors")
        self.dialog.descLabel.setText("Describes optional prior information about each model parameter")
        
        if len(self.params) == 0:
            self.grid.addWidget(QtGui.QLabel("No parameters found! Make sure model is properly configured"))

        for idx, param in enumerate(self.params):
            self.prior_widgets.append(self.get_widgets(idx))
        
            self.grid.addWidget(QtGui.QLabel("%s: " % param), idx, 0)
            for col, w in enumerate(self.prior_widgets[idx]):
                self.grid.addWidget(w, idx, col+1)

        self.update_from_rundata()
        self.update_widgets()
        self.grid.setAlignment(QtCore.Qt.AlignTop)
        self.dialog.adjustSize()
        self.updating_widgets=False
        
class ChooseFileView(View):
    def __init__(self, opt, **kwargs):
        self.defaultDir = ""
        self.dialogTitle = "Choose a file"
        self.opt = opt
        View.__init__(self, [opt,], **kwargs)
        self.changeBtn.clicked.connect(self.choose_file)
        
    def do_update(self):
        if self.opt in self.rundata:
            self.edit.setText(self.rundata[self.opt])

    def choose_file(self):
        fname = QtGui.QFileDialog.getOpenFileName(None, self.dialogTitle, self.defaultDir)[0]
        if fname:
            self.edit.setText(fname)
            self.rundata[self.opt] = fname
            self.defaultDir = os.path.dirname(fname)

class FileView(View):
    def __init__(self, **kwargs):
        View.__init__(self, [], **kwargs)
        
        if self.runBtn: self.runBtn.clicked.connect(self.run)
        if self.runQuickBtn: self.runQuickBtn.clicked.connect(self.run_quick)
        self.saveBtn.clicked.connect(self.save)
        self.saveAsBtn.clicked.connect(self.save_as)
        self.changed = None
        
    def save(self):
        self.rundata.save()
    
    def save_as(self):
        # fixme choose file name
        # fixme overwrite
        # fixme clone data
        fname = QtGui.QFileDialog.getSaveFileName()[0]
        self.rundata.set_file(fname)
        self.rundata.save()
        
    def run(self, focus=None):
        try:
            self.rundata.run(focus=focus)
        except:
            print sys.exc_info()
            QtGui.QMessageBox.warning(None, "Fabber error", str(sys.exc_info()[1]))
            
    def run_quick(self):
        self.run()
    
    def do_update(self):
        self.edit.setText(self.rundata.get_filename())
        if self.changed is None:
            self.changed = False
        else:
            self.changed = True
        
        self.saveBtn.setEnabled(self.changed)
        self.runBtn.setEnabled("data" in self.rundata)
        self.runQuickBtn.setEnabled("data" in self.rundata)
        
        
