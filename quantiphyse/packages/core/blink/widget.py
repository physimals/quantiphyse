"""
Quantiphyse - Widgets for comparing data sets

Copyright (c) 2013-2020 University of Oxford

Licensed under the Apache License, Version 2.0 (the "License");
you may not use this file except in compliance with the License.
You may obtain a copy of the License at

    http://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and
limitations under the License.
"""

from PySide2 import QtWidgets, QtCore

from quantiphyse.gui.options import OptionBox, DataOption, ChoiceOption, NumericOption
from quantiphyse.gui.widgets import QpWidget, TitleWidget

class BlinkWidget(QpWidget):
    """
    Compare two data sets using blink comparator
    """
    def __init__(self, **kwargs):
        QpWidget.__init__(self, name="Blink comparator", icon="compare.png",
                          desc="Compare two data sets visually by switching between views",
                          group="Visualisation", **kwargs)

    def init_ui(self):
        vbox = QtWidgets.QVBoxLayout()
        self.setLayout(vbox)

        title = TitleWidget(self, batch_btn=False, help="blink")
        vbox.addWidget(title)

        self.options = OptionBox("Options")
        self.options.add("Data 1", DataOption(self.ivm), key="data1")
        self.options.add("ROI 1", DataOption(self.ivm, data=False, rois=True, none_option=True), key="roi1")
        self.options.add("Data 2", DataOption(self.ivm), key="data2")
        self.options.add("ROI 2", DataOption(self.ivm, data=False, rois=True, none_option=True), key="roi2")
        self.options.add("Mode", ChoiceOption(choices=["Auto", "Manual"], default="Manual"), key="mode")
        self.options.option("mode").sig_changed.connect(self._mode_changed)
        self.options.add("Frequency (s)", NumericOption(minval=0.5, maxval=10, decimals=1, default=1), key="frequency")
        self.options.option("frequency").sig_changed.connect(self._freq_changed)
        self.options.add("")
        for data_option in ("data1", "data2", "roi1", "roi2"):
            self.options.option(data_option).sig_changed.connect(self._data_changed)
        vbox.addWidget(self.options)

        self.button = QtWidgets.QPushButton("Toggle")
        self.button.clicked.connect(self._button_clicked)
        vbox.addWidget(self.button)

        vbox.addStretch(1)

        self.running = False
        self.visible_view = 0

        #  Can't use singleshot because needs to be cancelable
        self._timer = QtCore.QTimer()
        self._timer.setInterval(1000)
        self._timer.setSingleShot(True)
        self._timer.timeout.connect(self._do_blink)

    def _data_changed(self):
        self._update_view(toggle=False)

    def _mode_changed(self):
        mode = self.options.option("mode").value
        self.options.option("frequency").setEnabled(mode == "Auto")
        if mode == "Auto":
            self.button.setText("Start")
        else:
            self.button.setText("Toggle")

    def _freq_changed(self):
        self._stop()
        freq = self.options.option("frequency").value
        self._timer.setInterval(freq * 1000)

    def _button_clicked(self):
        mode = self.options.option("mode").value
        if mode == "Manual":
            self._update_view()
        elif not self.running:
            self._start()
        else:
            self._stop()

    def _start(self):
        self.button.setText("Stop")
        self.running = True
        self._timer.start()

    def _stop(self):
        self.button.setText("Start")
        self.running = False
        self._timer.stop()

    def _do_blink(self):
        self._update_view()
        self._timer.start()

    def _update_view(self, toggle=True):
        if toggle:
            self.visible_view = 1 - self.visible_view
        data_key, roi_key = f"data{self.visible_view+1}", f"roi{self.visible_view+1}"
        data_name = self.options.option(data_key).value
        roi_name = self.options.option(roi_key).value
        self.ivm.set_current_data(data_name)
        if roi_name:
            self.ivm.set_current_roi(roi_name)
