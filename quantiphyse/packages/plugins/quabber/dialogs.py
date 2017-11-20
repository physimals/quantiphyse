import sys

from PySide import QtGui, QtCore

from quantiphyse.utils import debug
from quantiphyse.gui.widgets import OverlayCombo

from .widgets import get_option_widget, get_label

NUMBERED_OPTIONS_MAX=20

def _del(rundata, key):
    if key in rundata: del rundata[key]

class GenericOptionsDialog(QtGui.QDialog):
    def __init__(self, parent=None, title="Options", desc="", **kwargs):
        super(GenericOptionsDialog, self).__init__(parent)
        
        vbox = QtGui.QVBoxLayout()
        self.setLayout(vbox)

        self.title_label = get_label(size=20)
        vbox.addWidget(self.title_label)
        
        self.desc_label = get_label(bold=True, italic=True)
        vbox.addWidget(self.desc_label)

        self.scrollArea = QtGui.QScrollArea()
        self.scrollArea.setHorizontalScrollBarPolicy(QtCore.Qt.ScrollBarAlwaysOff)
        self.scrollArea.setWidgetResizable(True)
        self.scrollArea.setMinimumHeight(500)
        self.scrollAreaContents = QtGui.QWidget()
        self.grid = QtGui.QGridLayout(self.scrollAreaContents)
        self.scrollArea.setWidget(self.scrollAreaContents)
        vbox.addWidget(self.scrollArea)

        self.buttonBox = QtGui.QDialogButtonBox()
        self.buttonBox.setOrientation(QtCore.Qt.Horizontal)
        self.buttonBox.setStandardButtons(QtGui.QDialogButtonBox.Close)
        self.buttonBox.accepted.connect(self.accept)
        self.buttonBox.rejected.connect(self.reject)
        vbox.addWidget(self.buttonBox)

    def fit_width(self):
        w = self.scrollAreaContents.minimumSizeHint().width() + self.scrollArea.verticalScrollBar().width()
        self.scrollArea.setMinimumWidth(max(w, 600))
        
class OptionsDialog(GenericOptionsDialog):

    """ An option has been changed """
    sig_changed = QtCore.Signal(str)

    def __init__(self, parent=None, title="Options", desc="", **kwargs):
        super(OptionsDialog, self).__init__(parent)
        self.set_title(title, desc)
        self.desc_first = kwargs.get("desc_first", False)
        self.ivm = kwargs.get("ivm", None)
        self.rundata = kwargs.get("rundata", None)
        self.ignore_opts = set()
        self.option_widgets = []

    def set_title(self, title, desc=""):
        self.title_label.setText(title)
        self.desc_label.setText(desc)
        
    def set_options(self, opts):
        self._clear_options()
        self.opts = [o for o in opts if o["name"] not in self.ignore_opts]
        self._create_opts_ui()

    def ignore(self, *opts):
        for opt in opts:
            self.ignore_opts.add(opt)

    def _create_opts_ui(self):
        req = [opt for opt in self.opts if not opt["optional"]]
        nonreq = [opt for opt in self.opts if opt["optional"]]
        
        if req:
            label = get_label("Mandatory options", size=12, bold=True)
            self.grid.addWidget(label, 0, 0)
            self._add_opts(req, 1)
        if nonreq:
            label = get_label("Non-mandatory options", size=12, bold=True)
            self.grid.addWidget(label, len(req)+1, 0)
            self._add_opts(nonreq, len(req)+2)

        self.grid.setAlignment(QtCore.Qt.AlignTop)
        self.adjustSize()
        
    def _clear_options(self):
        self._del_layout(self.grid)

    def _del_layout(self, layout):
        while True:
            w = layout.takeAt(0)
            if w is None:
                break
            elif w.widget() is None:
                self._del_layout(w)    
            else:
                w.widget().deleteLater()
                
    def _add_option_widget(self, opt, row):
        w = get_option_widget(opt, rundata=self.rundata, ivm=self.ivm, desc_first=self.desc_first)
        w.update(self.rundata)
        w.add(self.grid, row)
        # Need to keep in scope or they get GC'd! FIXME this suggests the design is rubbish
        self.option_widgets.append(w)
        return w

    def _add_opts(self, opts, startrow):
        row = 0
        for opt in opts:
            if opt["name"].find("<n>") >= 0:
                # This is a numbered option. Create multiple widgets, each dependent on the previous
                opt_base=opt["name"][:opt["name"].find("<n>")]
                opt_suffix = opt["name"][opt["name"].find("<n>") + 3:]
                for n in range(1, NUMBERED_OPTIONS_MAX+1):
                    newopt = dict(opt)
                    newopt["name"] = "%s%i%s" % (opt_base, n, opt_suffix)
                    w = self._add_option_widget(newopt, row+startrow)
                    if n > 1:
                        prev.add_dependent(w)
                    prev = w
            else:
                self._add_option_widget(opt, row+startrow)
            row += 1
            
        return row

class PriorsDialog(OptionsDialog):

    TITLE = "Model parameter priors"
    DESC = "Describes optional prior information about each model parameter"
        
    def __init__(self, parent=None, **kwargs):
        super(PriorsDialog, self).__init__(parent, title=self.TITLE, desc=self.DESC, **kwargs)
        self.priors = []
        self.prior_widgets = []
        self.overlays = []
        self.params = []
        
    def set_params(self, params):
        debug("Params=", params, self.params)
        self.params = params
        self._repopulate()

    def _get_prior_idx(self, param):
        prior_idx = 1
        while "PSP_byname%i" % prior_idx in self.rundata:
            if param == self.rundata["PSP_byname%i" % prior_idx]:
                return prior_idx
            prior_idx += 1
        return -1

    def _get_widgets(self, idx):
        prior_idx = self._get_prior_idx(self.params[idx])
        ptype = self.rundata.get("PSP_byname%i_type" % prior_idx, "N")
        image = self.rundata.get("PSP_byname%i_image" % prior_idx, "")
        mean = self.rundata.get("PSP_byname%i_mean" % prior_idx, "")
        prec = self.rundata.get("PSP_byname%i_prec" % prior_idx, "")

        type_combo = QtGui.QComboBox()
        type_combo.addItem("Normal", "N")
        type_combo.addItem("Image Prior", "I")
        type_combo.addItem("Spatial prior, type M", "M")
        type_combo.addItem("Spatial prior , type P", "P")
        type_combo.addItem("Spatial prior, type m", "m")
        type_combo.addItem("Spatial prior , type p", "p")
        type_combo.addItem("ARD prior", "A")
        type_combo.setSizeAdjustPolicy(QtGui.QComboBox.AdjustToContents)
        type_combo.setCurrentIndex(type_combo.findData(ptype))
        type_combo.currentIndexChanged.connect(self._changed)
        
        image_combo = OverlayCombo(self.ivm, static_only=True)
        image_combo.setSizeAdjustPolicy(QtGui.QComboBox.AdjustToContents)
        if image != "":
            image_combo.setCurrentIndex(image_combo.findText(image))
        image_combo.currentIndexChanged.connect(self._changed)
        
        mean_cb = QtGui.QCheckBox()
        mean_cb.setChecked(ptype != "I" and mean != "")
        mean_cb.stateChanged.connect(self._changed)

        mean_edit = QtGui.QLineEdit(mean)
        mean_edit.editingFinished.connect(self._changed)
        
        prec_cb = QtGui.QCheckBox()
        prec_cb.setChecked(prec != "")
        prec_cb.stateChanged.connect(self._changed)

        prec_edit = QtGui.QLineEdit(prec)
        prec_edit.editingFinished.connect(self._changed)
        
        return (type_combo, 
               QtGui.QLabel("Image: "), 
               image_combo, 
               mean_cb, 
               QtGui.QLabel("Custom mean: "), 
               mean_edit,
               prec_cb, 
               QtGui.QLabel("Custom precision: "), 
               prec_edit)

    def _update_widgets(self):
         for idx, param in enumerate(self.params):
            w = self.prior_widgets[idx]
        
            prior_type = w[0].itemData(w[0].currentIndex())

            # Image overlay selector
            need_image = (prior_type == "I")
            w[1].setEnabled(need_image)
            w[2].setEnabled(need_image)

            # Custom mean
            custom_mean_allowed = prior_type != "I"
            w[3].setEnabled(custom_mean_allowed)
            w[4].setEnabled(custom_mean_allowed and w[3].isChecked())
            w[5].setEnabled(custom_mean_allowed and w[3].isChecked())

            # Custom precision
            custom_prec_allowed = True
            w[6].setEnabled(custom_prec_allowed)
            w[7].setEnabled(custom_prec_allowed and w[6].isChecked())
            w[8].setEnabled(custom_prec_allowed and w[6].isChecked())

    def _changed(self):
        self._update_widgets()
        self._update_rundata()

    def _update_rundata(self):
        prior_idx=1
        for idx, param in enumerate(self.params):
            w = self.prior_widgets[idx]
            prior_type = w[0].itemData(w[0].currentIndex())
            
            # Do we need to set any options for this prior?
            if prior_type != "N" or w[3].isChecked() or w[6].isChecked():
                self.rundata["PSP_byname%i" % prior_idx] = param
                self.rundata["PSP_byname%i_type" % prior_idx] = prior_type
                if prior_type == "I":
                    self.rundata["PSP_byname%i_image" % prior_idx] = w[2].currentText()
                else:
                    _del(self.rundata, "PSP_byname%i_image" % prior_idx)
                if w[3].isChecked() and prior_type != 'I':
                    self.rundata["PSP_byname%i_mean" % prior_idx] = w[5].text()
                else:
                    _del(self.rundata, "PSP_byname%i_mean" % prior_idx)
                if w[6].isChecked():
                    self.rundata["PSP_byname%i_prec" % prior_idx] = w[8].text()
                else:
                    _del(self.rundata, "PSP_byname%i_prec" % prior_idx)
                prior_idx += 1

        # Get rid of any subsequent PSP options that were previously set
        while "PSP_byname%i" % prior_idx in self.rundata:
            _del(self.rundata, "PSP_byname%i" % prior_idx)
            _del(self.rundata, "PSP_byname%i_type" % prior_idx)
            _del(self.rundata, "PSP_byname%i_image" % prior_idx)
            _del(self.rundata, "PSP_byname%i_prec" % prior_idx)
            prior_idx += 1
        
    def _repopulate(self):
        self._clear_options()
        self.grid.setSpacing(20)
        self.prior_widgets = []
        
        if len(self.params) == 0:
            self.grid.addWidget(QtGui.QLabel("No parameters found! Make sure model is properly configured"))

        for idx, param in enumerate(self.params):
            self.prior_widgets.append(self._get_widgets(idx))
        
            self.grid.addWidget(QtGui.QLabel("%s: " % param), idx, 0)
            for col, w in enumerate(self.prior_widgets[idx]):
                self.grid.addWidget(w, idx, col+1)

        self._update_widgets()
        self.grid.setAlignment(QtCore.Qt.AlignTop)
        self.adjustSize()
        