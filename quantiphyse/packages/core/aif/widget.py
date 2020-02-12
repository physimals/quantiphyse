"""
Quantiphyse - AIF widget

Copyright (c) 2013-2018 University of Oxford
"""
try:
    from PySide import QtGui, QtCore, QtGui as QtWidgets
except ImportError:
    from PySide2 import QtGui, QtCore, QtWidgets

import numpy as np

from quantiphyse.data.extras import NumberListExtra
from quantiphyse.gui.widgets import QpWidget, TitleWidget
from quantiphyse.gui.dialogs import TextViewerDialog
from quantiphyse.gui.pickers import PickMode
from quantiphyse.gui.plot import Plot
from quantiphyse.gui.options import OptionBox, DataOption, NumericOption, BoolOption, ChoiceOption, TextOption

class AifWidget(QpWidget):
    """
    Widget which allows the user to define an arterial input function from signal data
    """
    def __init__(self, **kwargs):
        super(AifWidget, self).__init__(name="Arterial Input Function", icon="aif",
                                        desc="Tool for defining an AIF from measured data", group="Utilities", **kwargs)
        self._aif = []
        self._aif_points = []

    def init_ui(self):
        vbox = QtGui.QVBoxLayout()
        self.setLayout(vbox)

        title = TitleWidget(self)
        vbox.addWidget(title)

        self._options = OptionBox("Options")
        self._options.add("Signal data", DataOption(self.ivm), key="data")
        self._clear_btn = QtGui.QPushButton("Clear points")
        self._options.add("Method", ChoiceOption(["Pick points", "Use existing ROI"], ["points", "roi"]), self._clear_btn, key="method")
        self._options.add("ROI", DataOption(self.ivm, data=False, rois=True), key="roi")
        self._view_btn = QtGui.QPushButton("View")
        self._view_btn.setEnabled(False)
        self._save_btn = QtGui.QPushButton("Save")
        self._save_btn.setEnabled(False)
        self._options.add("AIF name", TextOption("aif"), self._view_btn, self._save_btn, key="output-name")
        self._options.option("method").sig_changed.connect(self._method_changed)
        self._options.option("data").sig_changed.connect(self._recalc_aif)
        self._options.option("roi").sig_changed.connect(self._recalc_aif)
        self._clear_btn.clicked.connect(self._clear_btn_clicked)
        self._save_btn.clicked.connect(self._save_btn_clicked)
        self._view_btn.clicked.connect(self._view_btn_clicked)
        vbox.addWidget(self._options)

        self._plot = Plot(qpo=None, parent=self, title="AIF", display_mode=False)
        self._plot.set_xlabel("Volume")
        self._plot.set_ylabel("Signal")
        vbox.addWidget(self._plot)

        vbox.addStretch(1)

    def activate(self):
        self.ivl.sig_selection_changed.connect(self._selection_changed)
        self._method_changed()

    def deactivate(self):
        self.ivl.sig_selection_changed.disconnect(self._selection_changed)
        self.ivl.set_picker(PickMode.SINGLE)

    @property
    def qpdata(self):
        return self.ivm.data.get(self._options.option("data").value, None)

    @property
    def roi(self):
        return self.ivm.data.get(self._options.option("roi").value, None)

    @property
    def method(self):
        return self._options.option("method").value

    def _method_changed(self):
        self._options.set_visible("roi", self.method == "roi")
        self._clear_btn.setVisible(self.method == "points")
        if self.method == "roi":
            self.ivl.set_picker(PickMode.SINGLE)
        else:
            self.ivl.set_picker(PickMode.MULTIPLE)
            self._selection_changed()
        self._recalc_aif()

    def _clear_btn_clicked(self):
        if self.method == "points":
            self.ivl.set_picker(PickMode.MULTIPLE)
            self._selection_changed() # FIXME should be signalled by picker

    def _save_btn_clicked(self):
        name = self._options.option("output-name").value
        extra = NumberListExtra(name, self._aif)
        self.ivm.add_extra(name, extra)
        self._save_btn.setEnabled(False)

    def _view_btn_clicked(self):
        aiftxt = ", ".join([str(v) for v in self._aif])
        TextViewerDialog(self, title="AIF data", text=aiftxt).exec_()

    def _selection_changed(self):
        if self.method == "roi":
            return
        
        self._aif_points = []
        for _col, points in self.ivl.picker.selection().items():
            self._aif_points += list(points)
        self._recalc_aif()

    def _recalc_aif(self):
        self._aif = []
        self._save_btn.setEnabled(True)
        self._view_btn.setEnabled(True)
        if self.qpdata is not None:
            if self.method == "roi":
                self._calc_aif_roi()
            else:
                self._calc_aif_points()
        self._update_plot()

    def _calc_aif_roi(self):
        if self.roi is None:
            return

        points = self.qpdata.raw()[self.roi.raw() > 0]
        if len(points) > 0:
            aif = None
            for sig in points:
                if aif is None:
                    aif = np.zeros([len(sig)], dtype=np.float32)
                aif += sig
            self._aif = aif / len(points)

    def _calc_aif_points(self):
        aif = None
        num_points = 0
        for point in self._aif_points:
            sig = self.qpdata.timeseries(point, grid=self.ivl.grid)
            self.debug("AIF signal: %s", sig)
            if aif is None:
                aif = np.zeros([len(sig)], dtype=np.float32)
            aif += sig
            num_points += 1

        if num_points > 0:
            self._aif = aif / num_points

    def _update_plot(self):
        self._plot.clear()
        self._plot.add_line(self._aif, name="AIF")
