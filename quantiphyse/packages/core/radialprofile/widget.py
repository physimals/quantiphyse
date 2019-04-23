"""
Quantiphyse - Radial profile widget

Copyright (c) 2013-2018 University of Oxford
"""
import csv

import six

from PySide import QtGui

from quantiphyse.gui.widgets import QpWidget, TitleWidget
from quantiphyse.gui.plot import Plot
from quantiphyse.gui.options import OptionBox, DataOption, NumericOption, BoolOption

from .process import RadialProfileProcess
    
class RadialProfileWidget(QpWidget):
    """
    Widget which displays radial profile of data
    """
    def __init__(self, **kwargs):
        super(RadialProfileWidget, self).__init__(name="Radial profile", 
                                                  icon="rp",
                                                  desc="Display radial profile of data", 
                                                  group="Analysis", **kwargs)
        self._updating = False

    def init_ui(self):
        vbox = QtGui.QVBoxLayout()
        self.setLayout(vbox)

        title = TitleWidget(self)
        vbox.addWidget(title)

        self.options = OptionBox("Options")
        self.options.add("Data", DataOption(self.ivm, multi=True), key="data")
        self.options.add("Within ROI", DataOption(self.ivm, data=False, rois=True, none_option=True), key="roi")
        self.options.add("All volumes", BoolOption(default=False), key="allvols")
        self.options.add("Number of bins", NumericOption(minval=5, maxval=250, default=50, intonly=True), key="bins")
        vbox.addWidget(self.options)

        self.plot = Plot(qpo=None, parent=self, title="Radial profile", display_mode=False)
        self.plot.set_xlabel("Distance (mm)")
        self.plot.set_ylabel("Mean data value")
        vbox.addWidget(self.plot)

        vbox.addStretch(1)

    def activate(self):
        self.ivm.sig_all_data.connect(self._data_changed)
        self.ivl.sig_focus_changed.connect(self._update)
        self.options.option("data").sig_changed.connect(self._data_changed)
        self.options.sig_changed.connect(self._update)
        self._data_changed()

    def deactivate(self):
        self.ivm.sig_all_data.disconnect(self._data_changed)
        self.ivl.sig_focus_changed.disconnect(self._update)
        self.options.option("data").sig_changed.disconnect(self._data_changed)
        self.options.sig_changed.disconnect(self._update)

    def processes(self):
        opts = self.options.values()
        opts["centre"] = self.ivl.focus()
        if not opts.pop("allvols", False):
            opts["centre"] = opts["centre"][:3]

        return {
            "RadialProfile" : opts
        }

    def _data_changed(self):
        if self._updating: return
        self._updating = True
        try:
            data_names = self.options.option("data").value
            multivol = False
            for data_name in data_names:
                multivol = multivol or self.ivm.data[data_name].nvols > 1
            self.options.set_visible("allvols", multivol)
            self._update()
        finally:
            self._updating = False

    def _update(self):
        process = RadialProfileProcess(self.ivm)
        process.execute(self.processes()["RadialProfile"])
        self._update_plot()

    def _update_plot(self):
        self.plot.clear()
        rp = self.ivm.extras.get("radial-profile", None)
        if rp is not None:
            xvalues = rp.df.index
            for idx, name in enumerate(rp.df.columns):
                yvalues = rp.df.values[:,idx]
                self.plot.add_line(yvalues, name=name, xvalues=xvalues)
