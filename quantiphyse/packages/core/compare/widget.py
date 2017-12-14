from PySide import QtGui, QtCore
import pyqtgraph as pg
import numpy as np

from quantiphyse.gui.widgets import QpWidget, TitleWidget, OverlayCombo, NumericOption
from quantiphyse.utils import debug, warn
from quantiphyse.utils.exceptions import QpException

class CompareDataWidget(QpWidget):
    """
    Compare two data sets
    """
    def __init__(self, **kwargs):
        QpWidget.__init__(self, name="Compare Data", icon="compare.png", 
                          desc="Compare two data sets", group="Analysis", **kwargs)
        
    def init_ui(self):
        vbox = QtGui.QVBoxLayout()
        self.setLayout(vbox)

        title = TitleWidget(self)
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
        self.run_btn = QtGui.QPushButton("Go")
        self.run_btn.clicked.connect(self._run)
        hbox.addWidget(self.run_btn)
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
                
        hbox.addWidget(gbox)
        hbox.addStretch(1)
        vbox.addLayout(hbox)

        win = pg.GraphicsLayoutWidget()
        win.setBackground(background=None)
        self.plot = win.addPlot()
        vbox.addWidget(win)
        
        vbox.addStretch(1)  
        self._update_gui()
    
    def _update_gui(self):
        self.sample_spin.setEnabled(self.sample_cb.isChecked())

    def _update_data(self):
        name1 = self.d1_combo.currentText()
        name2 = self.d2_combo.currentText()
        d1, d2 = None, None
        if name1 in self.ivm.data:
            qpd1 = self.ivm.data[name1]
            d1 = qpd1.std()
        if name2 in self.ivm.data:
            qpd2 = self.ivm.data[name2]
            d2 = qpd2.std()

        roi = self.roi_combo.currentText()
        roi_data = None
        if roi in self.ivm.rois:
            roi_data = self.ivm.rois[roi].std()

        if d1 is not None and d2 is not None:
            if qpd1.nvols != qpd2.nvols:
                current_vol = self.ivm.cim_pos[3]
                if qpd1.nvols == 1: d1 = np.expand_dims(d1, 3)
                if qpd2.nvols == 1: d2 = np.expand_dims(d2, 3)
                d1 = d1[:,:,:,min(qpd1.nvols-1, current_vol)]
                d2 = d2[:,:,:,min(qpd2.nvols-1, current_vol)]
            if roi_data is not None:
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
                self.warn_label.setVisible(True)
                        
        self.d1 = d1
        self.d2 = d2
        self.run_btn.setEnabled(self.d1 is not None and self.d2 is not None)

    def _run(self):
        self.plot.clear() 
        self.plot.plot(self.d1, self.d2, pen=None, symbolBrush=(200, 200, 200), symbolPen='k', symbolSize=5.0)
        if self.id_cb.isChecked():
            real_min = max(self.d1.min(), self.d2.min())
            real_max = min(self.d1.max(), self.d2.max())
            pen=pg.mkPen((255, 255, 255), style=QtCore.Qt.DashLine)
            self.plot.plot([real_min, real_max], [real_min, real_max], pen=pen, width=2.0)
