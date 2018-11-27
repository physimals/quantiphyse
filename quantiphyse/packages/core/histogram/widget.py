"""
Quantiphyse - Histogram widget

Copyright (c) 2013-2018 University of Oxford
"""
from PySide import QtGui

from quantiphyse.gui.widgets import QpWidget, TitleWidget
from quantiphyse.gui.plot import Plot
from quantiphyse.gui.options import OptionBox, DataOption, NumericOption, BoolOption, ChoiceOption

from .process import HistogramProcess
    
class HistogramWidget(QpWidget):
    """
    Widget which displays data histograms
    """
    def __init__(self, **kwargs):
        super(HistogramWidget, self).__init__(name="Histogram", icon="hist",
                                              desc="Display histograms from data", group="Analysis", **kwargs)
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
        self.options.add("Y-axis scale", ChoiceOption(["Count", "Probability"]), key="yscale")
        self.options.add("Number of bins", NumericOption(minval=5, maxval=500, default=100, intonly=True), key="bins")
        self.options.add("Min value", NumericOption(minval=0, maxval=500, default=0), key="min")
        self.options.add("Max value", NumericOption(minval=0, maxval=500, default=100), key="max")
        self.options.option("yscale").sig_changed.connect(self._yscale_changed)
        vbox.addWidget(self.options)

        self.plot = Plot(qpo=None, parent=self, title="Data histogram", display_mode=False)
        self.plot.set_xlabel("Data value")
        self.plot.set_ylabel("Count")
        vbox.addWidget(self.plot)

        vbox.addStretch(1)

    def activate(self):
        self.ivm.sig_all_data.connect(self._data_changed)
        self.options.option("data").sig_changed.connect(self._data_changed)
        self.options.sig_changed.connect(self._update)
        self._data_changed()

    def deactivate(self):
        self.ivm.sig_all_data.disconnect(self._data_changed)
        self.options.option("data").sig_changed.disconnect(self._data_changed)
        self.options.sig_changed.disconnect(self._update)

    def processes(self):
        opts = self.options.values()
        if not opts.pop("allvols", False):
            opts["vol"] = self.ivl.focus()[3]

        return {
            "Histogram" : opts
        }

    def _yscale_changed(self):
        self.plot.set_ylabel(self.options.option("yscale").value)

    def _data_changed(self):
        if self._updating: return
        self._updating = True
        try:
            data_names = self.options.option("data").value
            vol = None
            if self.options.option("allvols").value:
                vol = self.ivl.focus()[3]
            dmin, dmax, multivol = None, None, False
            for data_name in data_names:
                qpdata = self.ivm.data[data_name]
                multivol = multivol or qpdata.nvols > 1
                _dmin, _dmax = qpdata.range(vol=vol)
                if dmin is None or dmin > _dmin:
                    dmin = _dmin
                if dmax is None or dmax > dmax:
                    dmax = _dmax
            
            if dmin is not None and dmax is not None:
                self.options.option("min").value = dmin
                self.options.option("min").setLimits(dmin, dmax)
                self.options.option("max").value = dmax
                self.options.option("max").setLimits(dmin, dmax)
                
            self.options.set_visible("allvols", multivol)
            self._update()
        finally:
            self._updating = False

    def _update(self):
        opts = self.processes()["Histogram"]
        if opts["data"]:
            HistogramProcess(self.ivm).run(opts)
            self.plot.clear()
            histogram = self.ivm.extras.get("histogram", None)
            if histogram is not None:
                for idx, name in enumerate(histogram.col_headers[3:]):
                    xvalues = [row[2] for row in histogram.arr]
                    yvalues = [row[idx+3] for row in histogram.arr]
                    self.plot.add_line(yvalues, name=name, xvalues=xvalues)
