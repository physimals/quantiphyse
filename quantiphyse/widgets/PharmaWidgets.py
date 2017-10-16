"""

Author: Benjamin Irving (benjamin.irv@gmail.com)
Copyright (c) 2013-2015 University of Oxford, Benjamin Irving

"""

from __future__ import division, unicode_literals, absolute_import, print_function

import time

import numpy as np
from matplotlib import cm
import pyqtgraph as pg
from PySide import QtCore, QtGui

from ..gui.dialogs import error_dialog
from ..gui.widgets import HelpButton
from ..analysis import Process
from ..analysis.pk import PkModellingProcess
from ..utils import get_col
from . import QpWidget

class PharmaWidget(QpWidget):
    """
    Widget for Pharmacokinetic modelling
    """

    def __init__(self, **kwargs):
        super(PharmaWidget, self).__init__(name="PK Modelling", desc="Pharmacokinetic Modelling", icon="pk", **kwargs)

    def init_ui(self):
        main_vbox = QtGui.QVBoxLayout()
        
        hbox = QtGui.QHBoxLayout()
        hbox.addWidget(QtGui.QLabel('<font size="5">PK Modelling</font>'))
        hbox.addStretch(1)
        hbox.addWidget(HelpButton(self, "pk"))
        main_vbox.addLayout(hbox)

        # Inputs
        param_box = QtGui.QGroupBox()
        param_box.setTitle('Parameters')
        input_grid = QtGui.QGridLayout()
        input_grid.addWidget(QtGui.QLabel('R1'), 0, 0)
        self.valR1 = QtGui.QLineEdit('3.7', self)
        input_grid.addWidget(self.valR1, 0, 1)
        input_grid.addWidget(QtGui.QLabel('R2'), 1, 0)
        self.valR2 = QtGui.QLineEdit('4.8', self)
        input_grid.addWidget(self.valR2, 1, 1)
        input_grid.addWidget(QtGui.QLabel('Flip Angle (degrees)'), 2, 0)
        self.valFA = QtGui.QLineEdit('12.0', self)
        input_grid.addWidget(self.valFA, 2, 1)
        input_grid.addWidget(QtGui.QLabel('TR (ms)'), 3, 0)
        self.valTR = QtGui.QLineEdit('4.108', self)
        input_grid.addWidget(self.valTR, 3, 1)
        input_grid.addWidget(QtGui.QLabel('TE (ms)'), 4, 0)
        self.valTE = QtGui.QLineEdit('1.832', self)
        input_grid.addWidget(self.valTE, 4, 1)
        input_grid.addWidget(QtGui.QLabel('delta T (s)'), 5, 0)
        self.valDelT = QtGui.QLineEdit('12', self)
        input_grid.addWidget(self.valDelT, 5, 1)
        input_grid.addWidget(QtGui.QLabel('Estimated Injection time (s)'), 6, 0)
        self.valInjT = QtGui.QLineEdit('30', self)
        input_grid.addWidget(self.valInjT, 6, 1)
        input_grid.addWidget(QtGui.QLabel('Ktrans/kep percentile threshold'), 7, 0)
        self.thresh1 = QtGui.QLineEdit('100', self)
        input_grid.addWidget(self.thresh1, 7, 1)
        input_grid.addWidget(QtGui.QLabel('Dose (mM/kg) (preclinical only)'), 8, 0)
        self.valDose = QtGui.QLineEdit('0.6', self)
        input_grid.addWidget(self.valDose, 8, 1)
        param_box.setLayout(input_grid)
        hbox = QtGui.QHBoxLayout()
        hbox.addWidget(param_box)
        hbox.addStretch(2)
        main_vbox.addLayout(hbox)

        # Model choice
        aif_choice = QtGui.QGroupBox()
        aif_choice.setTitle('Pharmacokinetic model choice')
        hbox = QtGui.QHBoxLayout()
        hbox.addWidget(QtGui.QLabel('AIF choice'))
        self.combo = QtGui.QComboBox(self)
        self.combo.addItem("Clinical: Toft / OrtonAIF (3rd) with offset")
        self.combo.addItem("Clinical: Toft / OrtonAIF (3rd) no offset")
        self.combo.addItem("Preclinical: Toft / BiexpAIF (Heilmann)")
        self.combo.addItem("Preclinical: Ext Toft / BiexpAIF (Heilmann)")
        hbox.addWidget(self.combo)
        hbox.addStretch(1)
        aif_choice.setLayout(hbox)
        main_vbox.addWidget(aif_choice)

        # Run button and progress
        run_box = QtGui.QGroupBox()
        run_box.setTitle('Running')
        hbox = QtGui.QHBoxLayout()
        but_gen = QtGui.QPushButton('Run modelling', self)
        but_gen.clicked.connect(self.start_task)
        hbox.addWidget(but_gen)
        self.prog_gen = QtGui.QProgressBar(self)
        self.prog_gen.setStatusTip('Progress of Pk modelling. Be patient. Progress is only updated in chunks')
        hbox.addWidget(self.prog_gen)
        run_box.setLayout(hbox)
        main_vbox.addWidget(run_box)

        main_vbox.addStretch()
        self.setLayout(main_vbox)

        self.process = PkModellingProcess(self.ivm)
        self.process.sig_finished.connect(self.finished)
        self.process.sig_progress.connect(self.progress)

    def start_task(self):
        """
        Start running the PK modelling on button click
        """
        if self.ivm.main is None:
            error_dialog("No data loaded")
            return

        if self.ivm.current_roi is None:
            error_dialog("No ROI loaded - required for Pk modelling")
            return

        if "T10" not in self.ivm.data:
            error_dialog("No T10 map loaded - required for Pk modelling")
            return

        options = {}
        options["r1"] = float(self.valR1.text())
        options["r2"] = float(self.valR2.text())
        options["dt"] = float(self.valDelT.text())
        options["tinj"] = float(self.valInjT.text())
        options["tr"] = float(self.valTR.text())
        options["te"] = float(self.valTE.text())
        options["fa"] = float(self.valFA.text())
        options["ve-thresh"] = float(self.thresh1.text())
        options["dose"] = float(self.valDose.text())
        options["model"] = self.combo.currentIndex() + 1

        self.prog_gen.setValue(0)
        self.process.run(options)

    def progress(self, progress):
        self.prog_gen.setValue(100*progress)

    def finished(self, status, output):
        """ GUI updates on process completion """
        if status != Process.SUCCEEDED:
            QtGui.QMessageBox.warning(None, "PK error", "PK modelling failed:\n\n" + str(output),
                                      QtGui.QMessageBox.Close)

class ModelCurves(QpWidget):
    """
    View original data and generated signal curves side by side
    """

    def __init__(self, **kwargs):
        super(ModelCurves, self).__init__(name="Model Curve", desc="Display model enhancement curves", icon="curve_view", **kwargs)
        self.data_enabled = {}
        self.updating = False

    def init_ui(self):
        self.cmap = getattr(cm, 'gist_rainbow')

        main_vbox = QtGui.QVBoxLayout()
        self.setStatusTip("Click points on the 4D volume to see actual and predicted curve")

        win = pg.GraphicsLayoutWidget()
        win.setBackground(background=None)
        self.plot = win.addPlot(title="Model / Data Curves")
        main_vbox.addWidget(win)

        # Curve options
        hbox = QtGui.QHBoxLayout()
        opts_box = QtGui.QGroupBox()
        opts_box.setTitle('Curve options')
        vbox = QtGui.QVBoxLayout()

        # Signal enhancement (normalised)
        hbox2 = QtGui.QHBoxLayout()
        self.sig_en_cb = QtGui.QCheckBox('Plot signal enhancement using first', self)
        self.sig_en_cb.stateChanged.connect(self.sig_enh_changed)
        hbox2.addWidget(self.sig_en_cb)
        self.norm_frames = QtGui.QSpinBox()
        self.norm_frames.setValue(3)
        self.norm_frames.setMinimum(1)
        self.norm_frames.setMaximum(100)
        self.norm_frames.valueChanged.connect(self.update)
        self.norm_frames.setEnabled(False)
        hbox2.addWidget(self.norm_frames)
        hbox2.addWidget(QtGui.QLabel("frames as baseline"))
        hbox2.addStretch(1)
        vbox.addLayout(hbox2)

        # Y-axis scale
        hbox2 = QtGui.QHBoxLayout()
        self.auto_y_cb = QtGui.QCheckBox('Automatic Y axis scale', self)
        self.auto_y_cb.setChecked(True)
        self.auto_y_cb.stateChanged.connect(self.auto_y_changed)
        hbox2.addWidget(self.auto_y_cb)
        self.min_lbl = QtGui.QLabel("Min")
        self.min_lbl.setEnabled(False)
        hbox2.addWidget(self.min_lbl)
        self.min_spin = QtGui.QDoubleSpinBox()
        self.min_spin.setMinimum(-1e20)
        self.min_spin.setMaximum(1e20)
        self.min_spin.valueChanged.connect(self.update)
        self.min_spin.setEnabled(False)
        hbox2.addWidget(self.min_spin)
        self.max_lbl = QtGui.QLabel("Max")
        self.max_lbl.setEnabled(False)
        hbox2.addWidget(self.max_lbl)
        self.max_spin = QtGui.QDoubleSpinBox()
        self.max_spin.setMinimum(-1e20)
        self.max_spin.setMaximum(1e20)
        self.max_spin.valueChanged.connect(self.update)
        self.max_spin.setEnabled(False)
        hbox2.addWidget(self.max_spin)
        hbox2.addStretch(1)
        vbox.addLayout(hbox2)

        opts_box.setLayout(vbox)
        hbox.addWidget(opts_box)
        hbox.addStretch()
        main_vbox.addLayout(hbox)

        hbox = QtGui.QHBoxLayout()

        # Table showing RMS deviation
        rms_box = QtGui.QGroupBox()
        rms_box.setTitle('Timeseries data')
        vbox = QtGui.QVBoxLayout()
        self.rms_table = QtGui.QStandardItemModel()
        self.rms_table.itemChanged.connect(self.data_table_changed)
        tview = QtGui.QTableView()
        tview.resizeColumnsToContents()
        tview.setModel(self.rms_table)
        vbox.addWidget(tview)
        rms_box.setLayout(vbox)
        hbox.addWidget(rms_box)

        # Table showing value of model parameters
        params_box = QtGui.QGroupBox()
        params_box.setTitle('Overlay values at current position')
        vbox2 = QtGui.QVBoxLayout()
        self.values_table = QtGui.QStandardItemModel()
        tview = QtGui.QTableView()
        tview.resizeColumnsToContents()
        tview.setModel(self.values_table)
        vbox2.addWidget(tview)
        params_box.setLayout(vbox2)
        hbox.addWidget(params_box)

        main_vbox.addLayout(hbox)
        self.setLayout(main_vbox)
    
    def activate(self):
        self.ivm.sig_all_data.connect(self.update_minmax)
        self.ivl.sig_focus_changed.connect(self.update)
        self.update_minmax(self.ivm.data.keys())

    def deactivate(self):
        self.ivm.sig_all_data.disconnect(self.update_minmax)
        self.ivl.sig_focus_changed.disconnect(self.update)

    def options_changed(self, opts):
        if hasattr(self, "plot"):
            # Have we been initialized?
            self.update()

    def sig_enh_changed(self, ch):
        self.norm_frames.setEnabled(ch)
        self.update()

    def auto_y_changed(self, ch):
        self.min_lbl.setEnabled(not ch)
        self.min_spin.setEnabled(not ch)
        self.max_lbl.setEnabled(not ch)
        self.max_spin.setEnabled(not ch)
        self.update()

    def update_minmax(self, ovls):
        dmin, dmax, first = 0, 100, True
        for name in ovls:
            ovl = self.ivm.data[name].std()
            if first or ovl.min() < dmin: dmin = ovl.min()
            if first or ovl.max() > dmax: dmax = ovl.max()
            first = False
        self.min_spin.setValue(dmin)
        self.max_spin.setValue(dmax)
        self.update()

    def update(self, pos=None):
        self._update_table()
        self._update_rms_table()
        self._plot()

    def _update_table(self):
        """
        Set the overlay parameter values in the table based on the current point clicked
        """
        self.values_table.clear()
        self.values_table.setHorizontalHeaderItem(0, QtGui.QStandardItem("Value"))
        overlay_vals = self.ivm.get_data_value_curr_pos()
        for ii, ovl in enumerate(sorted(overlay_vals.keys())):
            if self.ivm.data[ovl].ndim == 3:
                self.values_table.setVerticalHeaderItem(ii, QtGui.QStandardItem(ovl))
                self.values_table.setItem(ii, 0, QtGui.QStandardItem(str(np.around(overlay_vals[ovl], 10))))

    def _update_rms_table(self):
        try:
            self.updating = True # Hack to prevent plot being refreshed during table update
            self.rms_table.clear()
            self.rms_table.setHorizontalHeaderItem(1, QtGui.QStandardItem("RMS (Position)"))
            #self.rms_table.setHorizontalHeaderItem(2, QtGui.QStandardItem("RMS (mean)"))
            idx = 0
            for name in sorted(self.ivm.data.keys()):
                ovl = self.ivm.data[name]
                pos = self.ivm.cim_pos
                if ovl.ndim == 4 and ovl.nvols == self.ivm.main.nvols:
                    #rms = np.sqrt(np.mean(np.square(self.ivm.main.std() - ovl.std()), 3))
                    #if self.ivm.current_roi is not None:
                    #    rms[self.ivm.current_roi.std() == 0] = 0
                    #    mean_rms = np.mean(rms[self.ivm.current_roi.std() > 0])
                    #else:
                    #    mean_rms = np.mean(rms)
                    pos_curve = ovl.std()[pos[0], pos[1], pos[2],:]
                    main_curve = self.ivm.main.std()[pos[0], pos[1], pos[2],:]
                    pos_rms = np.sqrt(np.mean(np.square(main_curve - pos_curve)))
                    name_item = QtGui.QStandardItem(name)
                    name_item.setCheckable(True)
                    name_item.setEditable(False)
                    if name not in self.data_enabled:
                        self.data_enabled[name] = QtCore.Qt.Checked
                    name_item.setCheckState(self.data_enabled[name])
                    self.rms_table.setItem(idx, 0, name_item)
                    item = QtGui.QStandardItem(str(np.around(pos_rms, 10)))
                    item.setEditable(False)
                    self.rms_table.setItem(idx, 1, item)
                    #item = QtGui.QStandardItem(str(np.around(mean_rms, 10)))
                    #item.setEditable(False)
                    #self.rms_table.setItem(idx, 2, item)
                    idx += 1
        finally:
            self.updating = False

    def data_table_changed(self, item):
        if not self.updating:
            # A checkbox has been toggled
            self.data_enabled[item.text()] = item.checkState()
            self._plot()

    def _plot(self):
        """
        Plot the curve / curves
        """
        self.plot.clear()
        if self.auto_y_cb.isChecked():
            self.plot.enableAutoRange()
        else: 
            self.plot.disableAutoRange()
            self.plot.setYRange(self.min_spin.value(), self.max_spin.value())

        # Replaces any existing legend
        if self.plot.legend: self.plot.legend.scene().removeItem(self.plot.legend)
        legend = self.plot.addLegend()

        sig, sig_ovl = self.ivm.get_current_enhancement()

        # Get x scale
        xx = self.opts.t_scale
        frames1 = self.norm_frames.value()
        self.plot.setLabel('bottom', self.opts.t_type, units=self.opts.t_unit)

        if self.sig_en_cb.isChecked():
            self.plot.setLabel('left', "Signal Enhancement")
        else:
            self.plot.setLabel('left', "Signal")

        # Plot each data item
        idx, n_ovls = 0, len(sig_ovl)
        for ovl, sig_values in sig_ovl.items():
            if self.data_enabled[ovl] == QtCore.Qt.Checked:
                if self.sig_en_cb.isChecked():
                    # Show signal enhancement rather than raw values
                    m1 = np.mean(sig_values[:frames1])
                    if m1 != 0: sig_values = sig_values / m1 - 1
                    
                self.plot.plot(xx, sig_values, pen=None, symbolBrush=(200, 200, 200), symbolPen='k', symbolSize=5.0)
                line = self.plot.plot(xx, sig_values, pen=get_col(self.cmap, idx, n_ovls), width=4.0)
                legend.addItem(line, ovl)
                idx += 1

QP_WIDGETS = [PharmaWidget, ModelCurves]
