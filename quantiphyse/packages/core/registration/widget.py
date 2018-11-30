"""
Quantiphyse - Widgets for data registration and motion correction

Copyright (c) 2013-2018 University of Oxford
"""
from PySide import QtGui

from quantiphyse.gui.widgets import QpWidget, RunWidget, TitleWidget
from quantiphyse.gui.options import OptionBox, DataOption, ChoiceOption, NumericOption, TextOption
from quantiphyse.utils import get_plugins

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

        self.options = OptionBox("General Options")
        self.options.add("Mode", ChoiceOption(["Registration", "Motion Correction"], ["reg", "moco"]), key="mode")
        self.options.add("Method", ChoiceOption([method.display_name for method in self.reg_methods], self.reg_methods), key="method")
        self.options.add("Registration data", DataOption(self.ivm), key="reg")
        self.options.add("Reference data", DataOption(self.ivm), key="ref")
        self.options.add("Reference volume", ChoiceOption(["Middle volume", "Mean volume", "Specified volume"], ["median", "mean", "idx"]), key="ref-vol")
        self.options.add("Reference volume index", NumericOption(intonly=True), key="ref-idx")
        self.options.add("Output space", ChoiceOption(["Reference", "Registration", "Transformed"], ["ref", "reg", "trans"]), key="output-space")
        self.options.add("Also apply transform to", DataOption(self.ivm, multi=True), key="add-reg")
        self.options.add("Save transformation", TextOption(), key="save-transform", checked=True, default=False)
        
        self.options.option("mode").sig_changed.connect(self._update_option_visibility)
        self.options.option("method").sig_changed.connect(self._update_option_visibility)
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
        self._update_option_visibility()

    def _update_option_visibility(self):
        mode = self.options.option("mode").value
        regdata = self.ivm.data.get(self.options.option("reg").value, None)
        refdata = self.ivm.data.get(self.options.option("ref").value, None)
        refvol = self.options.option("ref-vol").value

        nvols = 1
        if mode == "reg" and refdata is not None:
            nvols = refdata.nvols
        elif regdata is not None:
            nvols = regdata.nvols

        self.options.set_visible("ref", mode == "reg")
        self.options.set_visible("ref-vol", nvols > 1)
        self.options.set_visible("ref-idx", nvols > 1 and refvol == "idx")
        self.options.set_visible("add-reg", nvols == 1 and mode == "reg")
        self.options.set_visible("output-space", mode == "reg")
        
        if nvols > 1:
            self.options.option("ref-idx").setLimits(0, nvols-1)
            self.options.option("ref-idx").value = int(nvols/2)

        method = self.options.option("method").value
        for name, box in self.opt_boxes.items():
            box.setVisible(name == method.name)

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
