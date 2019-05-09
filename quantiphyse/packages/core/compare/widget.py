"""
Quantiphyse - Widgets for comparing data sets

Copyright (c) 2013-2018 University of Oxford
"""

try:
    from PySide import QtGui, QtCore, QtGui as QtWidgets
except ImportError:
    from PySide2 import QtGui, QtCore, QtWidgets
  
import pyqtgraph as pg
import numpy as np

from quantiphyse.gui.widgets import QpWidget, TitleWidget, OverlayCombo, NumericOption, ChoiceOption
from quantiphyse.utils import QpException

class CompareDataWidget(QpWidget):
    """
    Compare two data sets
    """
    def __init__(self, **kwargs):
        QpWidget.__init__(self, name="Compare Data", icon="compare.png", 
                          desc="Compare two data sets", group="Visualisation", **kwargs)
        
    def init_ui(self):
        vbox = QtGui.QVBoxLayout()
        self.setLayout(vbox)

        title = TitleWidget(self, batch_btn=False, help="compare")
        vbox.addWidget(title)

        hbox = QtGui.QHBoxLayout()
        hbox.addWidget(QtGui.QLabel("Compare "))
        self.d1_combo = OverlayCombo(self.ivm)
        self.d1_combo.currentIndexChanged.connect(self._update_data)
        hbox.addWidget(self.d1_combo)
        hbox.addWidget(QtGui.QLabel(" with "))
        self.d2_combo = OverlayCombo(self.ivm)
        self.d2_combo.currentIndexChanged.connect(self._update_data)
        hbox.addWidget(self.d2_combo)
        hbox.addStretch(1)
        vbox.addLayout(hbox)

        hbox = QtGui.QHBoxLayout()
        hbox.addWidget(QtGui.QLabel("Within ROI "))
        self.roi_combo = OverlayCombo(self.ivm, rois=True, data=False, none_option=True)
        self.roi_combo.currentIndexChanged.connect(self._update_data)
        hbox.addWidget(self.roi_combo)
        hbox.addStretch(1)
        vbox.addLayout(hbox)

        hbox = QtGui.QHBoxLayout()
        gbox = QtGui.QGroupBox("Options")
        grid = QtGui.QGridLayout()
        gbox.setLayout(grid)

        self.id_cb = QtGui.QCheckBox("Include identity line")
        grid.addWidget(self.id_cb, 0, 0)
        self.sample_cb = QtGui.QCheckBox("Sample values")
        self.sample_cb.setChecked(True)
        self.sample_cb.stateChanged.connect(self._update_data)
        self.sample_cb.stateChanged.connect(self._update_gui)
        grid.addWidget(self.sample_cb, 1, 0)
        self.sample_spin = QtGui.QSpinBox()
        self.sample_spin.setMinimum(10)
        self.sample_spin.setMaximum(10000000)
        self.sample_spin.setSingleStep(100)
        self.sample_spin.setValue(1000)
        self.sample_spin.valueChanged.connect(self._update_data)
        grid.addWidget(self.sample_spin, 1, 1)
        self.warn_label = QtGui.QLabel("WARNING: plotting all values may take a long time")
        self.warn_label.setStyleSheet("QLabel { color : red; }")
        self.warn_label.setVisible(False)
        grid.addWidget(self.warn_label, 2, 0)
        self.plot_mode = ChoiceOption("Plot mode", grid, 3, choices=["Scatter", "Heat map"])
        self.plot_mode.combo.currentIndexChanged.connect(self._plot_mode_changed)
        self.bins = NumericOption("Bins", grid, 3, xpos=2, minval=20, default=50, intonly=True)
        self.bins.label.setVisible(False)
        self.bins.spin.setVisible(False)
        self.run_btn = QtGui.QPushButton("Update")
        self.run_btn.clicked.connect(self._run)
        grid.addWidget(self.run_btn, 4, 0)
        hbox.addWidget(gbox)
        hbox.addStretch(1)
        vbox.addLayout(hbox)

        hbox = QtGui.QHBoxLayout()
        win = pg.GraphicsLayoutWidget()
        win.setBackground(background=None)
        self.plot = win.addPlot(enableAutoRange=True)
        self.plot.clear() # Unsure why this is necessary
        hbox.addWidget(win)
        
        self.hist = pg.HistogramLUTWidget()
        self.hist.setVisible(False)
        self.hist.setBackground(None)
        self.hist.gradient.loadPreset("thermal")
        hbox.addWidget(self.hist) 
        vbox.addLayout(hbox)

        self._update_gui()
        self._update_data()
    
    def _plot_mode_changed(self, idx):
        self.bins.label.setVisible(idx == 1)
        self.bins.spin.setVisible(idx == 1)
        self.sample_cb.setChecked(idx == 0)
        self._update_gui()
        self._update_data()

    def _update_gui(self):
        self.sample_spin.setEnabled(self.sample_cb.isChecked())

    def _update_data(self):
        name1 = self.d1_combo.currentText()
        name2 = self.d2_combo.currentText()
        roi_name = self.roi_combo.currentText()
        qpd1 = self.ivm.data.get(name1, None)
        qpd2 = self.ivm.data.get(name2, None)
        roi = self.ivm.rois.get(roi_name, None)

        if qpd1 is not None and qpd2 is not None:
            current_vol = self.ivl.focus()[3]
            d1 = qpd1.volume(current_vol)
            d2 = qpd2.resample(qpd1.grid).volume(current_vol)
            
            if roi is not None:
                roi_data = roi.resample(qpd1.grid).raw()
                d1 = d1[roi_data > 0]
                d2 = d2[roi_data > 0]
            else:
                d1 = d1.reshape(-1)
                d2 = d2.reshape(-1)

            if self.sample_cb.isChecked():
                n_samples = self.sample_spin.value()
                idx = np.random.choice(np.arange(len(d1)), n_samples)
                d1 = np.take(d1, idx)
                d2 = np.take(d2, idx)
                self.warn_label.setVisible(False)
            else:
                # Warn about plotting all data in scatter mode
                self.warn_label.setVisible(self.plot_mode.combo.currentIndex() == 0)
                        
            self.d1 = d1
            self.d2 = d2
            self.run_btn.setEnabled(True)
        else:
            self.run_btn.setEnabled(False)

    def _run(self):
        self.plot.clear() 
        self.plot.setLabel('bottom', self.d1_combo.currentText())
        self.plot.setLabel('left', self.d2_combo.currentText())
        if self.plot_mode.combo.currentIndex() == 0:
            self.plot.setAspectLocked(False)
            self.hist.setVisible(False)
            self.plot.plot(self.d1, self.d2, pen=None, symbolBrush=(200, 200, 200), symbolPen='k', symbolSize=5.0)
        else:
            heatmap, xedges, yedges = np.histogram2d(self.d1, self.d2, bins=self.bins.value())
            rect = QtCore.QRectF(xedges[0], yedges[0], xedges[-1]-xedges[0], yedges[-1]-yedges[0])
            img = pg.ImageItem(heatmap)
            img.setRect(rect)
            #self.plot.setAspectLocked(True)
            self.hist.setVisible(True)
            self.hist.setImageItem(img)
            self.plot.addItem(img)

        if self.id_cb.isChecked():
            real_min = max(self.d1.min(), self.d2.min())
            real_max = min(self.d1.max(), self.d2.max())
            pen = pg.mkPen((255, 255, 255), style=QtCore.Qt.DashLine)
            self.plot.plot([real_min, real_max], [real_min, real_max], pen=pen, width=2.0)
