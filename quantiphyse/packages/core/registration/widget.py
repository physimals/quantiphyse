"""
Quantiphyse - Widgets for data registration and motion correction

Copyright (c) 2013-2018 University of Oxford
"""
import traceback

try:
    from PySide import QtGui, QtCore, QtGui as QtWidgets
except ImportError:
    from PySide2 import QtGui, QtCore, QtWidgets

from quantiphyse.data import QpData
from quantiphyse.gui.widgets import QpWidget, RunWidget, TitleWidget, RunButton
from quantiphyse.gui.options import OptionBox, Option, DataOption, ChoiceOption, NumericOption, TextOption, OutputNameOption
from quantiphyse.utils import get_plugins

class RegWidget(QpWidget):
    """
    Generic registration / motion correction widget 
    """
    def __init__(self, **kwargs):
        super(RegWidget, self).__init__(name="Registration", icon="reg", 
                                        desc="Registration and Motion Correction", 
                                        group="Registration", **kwargs)
        self.reg_methods = []
        for method in get_plugins("reg-methods"):
            try:
                self.reg_methods.append(method(self.ivm))
            except:
                traceback.print_exc()
                self.warn("Failed to create registration method: %s", method)
                
    def init_ui(self):
        layout = QtGui.QVBoxLayout()
        self.setLayout(layout)

        title = TitleWidget(self, title="Registration and Motion Correction", help="reg")
        layout.addWidget(title)

        if not self.reg_methods:
            layout.addWidget(QtGui.QLabel("No registration methods found"))
            layout.addStretch(1)
            return

        self.options = OptionBox("General Options")
        self.options.add("Mode", ChoiceOption(["Registration", "Motion Correction"], ["reg", "moco"]), key="mode")
        self.options.add("Method", ChoiceOption([method.display_name for method in self.reg_methods], self.reg_methods), key="method")
        self.options.add("Registration data", DataOption(self.ivm), key="reg")
        self.options.add("Reference data", DataOption(self.ivm), key="ref")
        self.options.add("Reference volume", ChoiceOption(["Middle volume", "Mean volume", "Specified volume"], ["median", "mean", "idx"]), key="ref-vol")
        self.options.add("Reference volume index", NumericOption(intonly=True), key="ref-idx")
        self.options.add("Output space", ChoiceOption(["Reference", "Registration", "Transformed"], ["ref", "reg", "trans"]), key="output-space")
        self.options.add("Output name", OutputNameOption(src_data=self.options.option("reg"), suffix="_reg"), key="output-name", checked=True)
        self.options.add("Also apply transform to", DataOption(self.ivm, multi=True), key="add-reg")
        self.options.add("Save transformation", TextOption(), key="save-transform", checked=True, default=False)
        
        self.options.option("mode").sig_changed.connect(self._update_option_visibility)
        self.options.option("method").sig_changed.connect(self._method_changed)
        self.options.option("ref").sig_changed.connect(self._update_option_visibility)
        self.options.option("ref-vol").sig_changed.connect(self._update_option_visibility)
        self.options.option("reg").sig_changed.connect(self._update_option_visibility)
        layout.addWidget(self.options)

        # Create the options boxes for reg methods - only one visible at a time!
        self.opt_boxes = {}
        for method in self.reg_methods:
            hbox = QtGui.QHBoxLayout()
            opt_box = QtGui.QGroupBox()
            opt_box.setTitle(method.display_name)
            vbox = QtGui.QVBoxLayout()
            opt_box.setLayout(vbox)
            vbox.addWidget(method.interface())
            hbox.addWidget(opt_box)
            opt_box.setVisible(False)
            layout.addLayout(hbox)
            self.opt_boxes[method.name] = opt_box

        layout.addWidget(RunWidget(self))
        layout.addStretch(1)
        self._method_changed()

    def _method_changed(self):
        method = self.options.option("method").value
        for name, box in self.opt_boxes.items():
            box.setVisible(name == method.name)
        self.options.option("save-transform").value = "%s_trans" % method.name
        self._update_option_visibility()

    def _update_option_visibility(self):
        mode = self.options.option("mode").value
        regdata = self.ivm.data.get(self.options.option("reg").value, None)
        refdata = self.ivm.data.get(self.options.option("ref").value, None)
        refvol = self.options.option("ref-vol").value

        nvols_reg, nvols_ref = 1, 1
        if regdata is not None:
            nvols_reg = regdata.nvols
            
        if mode == "moco" and regdata is not None:
            nvols_ref = regdata.nvols
        elif mode == "reg" and refdata is not None:
            nvols_ref = refdata.nvols

        self.options.set_visible("ref", mode == "reg")
        self.options.set_visible("ref-vol", nvols_ref > 1)
        self.options.set_visible("ref-idx", nvols_ref > 1 and refvol == "idx")
        self.options.set_visible("add-reg", nvols_reg == 1 and mode == "reg")
        self.options.set_visible("output-space", mode == "reg")
        
        if nvols_ref > 1:
            self.options.option("ref-idx").setLimits(0, nvols_ref-1)
            self.options.option("ref-idx").value = int(nvols_ref/2)

    def processes(self):
        options = self.options.values()
        if options.get("ref-vol", None) == "idx":
            options["ref-vol"] = options.pop("ref-idx")
        
        method = options.pop("method")
        options["method"] = method.name
        options.update(method.options())

        return {
            "Reg" : options,
        }

class TransformOption(Option, QtGui.QComboBox):
    """ 
    Option for choosing previously calculated registration transforms. 
    These may be stored as data sets or Extras
    """
    sig_changed = QtCore.Signal()

    def __init__(self, ivm):
        QtGui.QComboBox.__init__(self)
        self.ivm = ivm
        self._data_changed()
        self.ivm.sig_all_data.connect(self._data_changed)
        self.ivm.sig_extras.connect(self._data_changed)
        self.currentIndexChanged.connect(self._changed)

    @property
    def value(self):
        """ 
        Name of currently selected transform
        """
        return self.currentText()

    def _data_changed(self):
        self.blockSignals(True)
        try:
            current = self.value
            self.clear()

            idx, current_idx = 0, 0
            items = list(self.ivm.data.values()) + list(self.ivm.extras.values())
            for item in items:
                if "QpReg" in item.metadata:
                    self.addItem(item.name)
                    if item.name == current:
                        current_idx = idx
                    idx += 1

            # Make sure names are visible even with drop down arrow
            width = self.minimumSizeHint().width()
            self.setMinimumWidth(width+50)
        finally:
            self.blockSignals(False)
        
        # Set to same item selected beforehand and make sure
        # sig_changed is always emitted
        self.setCurrentIndex(current_idx)
        self._changed()
       
    def _changed(self):
        self.sig_changed.emit()

class TransformDetails(QtGui.QGroupBox):
    """
    Widget displaying information about a selected transformation
    """

    def __init__(self):
        QtGui.QGroupBox.__init__(self, "Transform details")
        grid = QtGui.QGridLayout()
        self.setLayout(grid)
        
        self._name = QtGui.QLineEdit()
        grid.addWidget(QtGui.QLabel("Transform name"), 0, 0)
        grid.addWidget(self._name, 0, 1)

        self._method = QtGui.QLineEdit()
        grid.addWidget(QtGui.QLabel("Registration method"), 1, 0)
        grid.addWidget(self._method, 1, 1)

        self._type = QtGui.QLineEdit()
        grid.addWidget(QtGui.QLabel("Transform type"), 2, 0)
        grid.addWidget(self._type, 2, 1)

        self._edit = QtGui.QPlainTextEdit()
        self._edit.setReadOnly(True)
        grid.addWidget(self._edit, 3, 0, 1, 2)

    @property
    def transform(self):
        """ The transform object """
        return self._transform

    @transform.setter
    def transform(self, transform):
        self._transform = transform
        self._name.setText(self._transform.name)
        self._method.setText(self._transform.metadata.get("QpReg", "<unknown>"))
        if isinstance(transform, QpData):
            self._type.setText("Image (e.g. warp field)")
            self._edit.setVisible(False)
        else:
            self._type.setText("Non-image (e.g. matrix)")
            self._edit.setVisible(True)
            doc = self._edit.document()
            font = doc.defaultFont()
            font.setFamily("Courier New")
            font.setPointSize(8)
            doc.setDefaultFont(font)
            self._edit.setPlainText(str(transform))

class ApplyTransform(QpWidget):
    """
    Widget for applying previously calculated transformations
    """
    def __init__(self, **kwargs):
        super(ApplyTransform, self).__init__(name="Apply Transform", icon="reg", 
                                             desc="Apply previously calculated transformations", 
                                             group="Registration", **kwargs)
        self.reg_methods = []
        for method in get_plugins("reg-methods"):
            try:
                self.reg_methods.append(method(self.ivm))
            except:
                traceback.print_exc()
                self.warn("Failed to create registration method: %s", method)

    def init_ui(self):
        layout = QtGui.QVBoxLayout()
        self.setLayout(layout)

        title = TitleWidget(self, help="reg")
        layout.addWidget(title)

        if not self.reg_methods:
            layout.addWidget(QtGui.QLabel("No registration methods found"))
            layout.addStretch(1)
            return

        self.options = OptionBox("General Options")
        self.options.add("Transform", TransformOption(self.ivm), key="transform")
        self.options.add("Apply to data", DataOption(self.ivm), key="data")
        self.options.add("Interpolation", ChoiceOption(["Nearest neighbour", "Linear", "Spline"], [0, 1, 3], default=1), key="interp-order")
        self.options.add("Output name", OutputNameOption(src_data=self.options.option("data"), suffix="_reg"), key="output-name")
        self.options.option("transform").sig_changed.connect(self._transform_changed)
        layout.addWidget(self.options)

        self.details = TransformDetails()
        layout.addWidget(self.details)

        layout.addWidget(RunButton(self))
        layout.addStretch(1)
        self._transform_changed()

    def processes(self):
        return {
            "ApplyTransform" : self.options.values(),
        }

    def activate(self):
        self._transform_changed()

    def _transform_changed(self):
        trans_name = self.options.option("transform").value
        transform = self.ivm.data.get(trans_name, None)
        if transform is None or "QpReg" not in transform.metadata:
            transform = self.ivm.extras.get(trans_name, None)

        if transform is not None and "QpReg" in transform.metadata:
            self.details.transform = transform
