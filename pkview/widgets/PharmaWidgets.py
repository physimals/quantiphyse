"""

Author: Benjamin Irving (benjamin.irv@gmail.com)
Copyright (c) 2013-2015 University of Oxford, Benjamin Irving

"""

from __future__ import division, unicode_literals, absolute_import, print_function

import time

import numpy as np
import pyqtgraph as pg
from PySide import QtCore, QtGui

from pkview.QtInherit.dialogs import error_dialog
from ..QtInherit import HelpButton
from pkview.analysis import Process
from pkview.analysis.pk import PkModellingProcess
from pkview.widgets import PkWidget

class PharmaWidget(PkWidget):
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
        if self.ivm.vol is None:
            error_dialog("No data loaded")
            return

        if self.ivm.current_roi is None:
            error_dialog("No ROI loaded - required for Pk modelling")
            return

        if "T10" not in self.ivm.overlays:
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

class PharmaView(PkWidget):
    """
    View original data and generated signal curves side by side (just reverse the scale)
    """

    def __init__(self, **kwargs):
        super(PharmaView, self).__init__(name="Model Curve", desc="Display model enhancement curves", icon="pk", **kwargs)

    def init_ui(self):
        main_vbox = QtGui.QVBoxLayout()
        self.setStatusTip("Click points on the 4D volume to see actual and predicted curve")

        win = pg.GraphicsLayoutWidget()
        win.setBackground(background=None)
        self.plot = win.addPlot(title="Model / Data Curves")
        main_vbox.addWidget(win)

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
        self.norm_frames.valueChanged.connect(self.replot_curves)
        self.norm_frames.setEnabled(False)
        hbox2.addWidget(self.norm_frames)
        hbox2.addWidget(QtGui.QLabel("frames as baseline"))
        hbox2.addStretch(1)
        vbox.addLayout(hbox2)

        opts_box.setLayout(vbox)
        hbox.addWidget(opts_box)
        hbox.addStretch()
        main_vbox.addLayout(hbox)

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
        main_vbox.addWidget(params_box)

        self.setLayout(main_vbox)

        # initial plot colour
        self.plot_color = (255, 0, 0)
        self.plot_color2 = (0, 255, 0)

        self.curve1 = None
    
    def activate(self):
        self.ivl.sig_focus_changed.connect(self.replot_curves)
        self.replot_curves()

    def deactivate(self):
        self.ivl.sig_focus_changed.disconnect(self.replot_curves)

    def options_changed(self, opts):
        self.replot_curves()

    def sig_enh_changed(self, opts):
        self.norm_frames.setEnabled(self.sig_en_cb.isChecked())
        self.replot_curves()

    def replot_curves(self, pos=None):
        self._plot()
        self._update_table()

    def _update_table(self):
        """
        Set the overlay parameter values in the table based on the current point clicked
        """
        overlay_vals = self.ivm.get_overlay_value_curr_pos()
        for ii, ovl in enumerate(overlay_vals.keys()):
            if self.ivm.overlays[ovl].ndim == 3:
                self.values_table.setVerticalHeaderItem(ii, QtGui.QStandardItem(ovl))
                self.values_table.setItem(ii, 0, QtGui.QStandardItem(str(np.around(overlay_vals[ovl], 10))))

    def _plot(self):
        """
        Plot the curve / curves
        """
        sig, sig_ovl = self.ivm.get_current_enhancement()

        values = np.array(sig, dtype=np.double)

        # Setting x-values
        xx = self.opts.t_scale
        frames1 = self.norm_frames.value()

        if self.sig_en_cb.isChecked():
            # Show signal enhancement for main data, rather than raw values
            m1 = np.mean(values[:frames1])
            if m1 != 0: values = values / m1 - 1

        self.plot.clear()
        self.curve1 = self.plot.plot(xx, values, pen=None, symbolBrush=(200, 200, 200), symbolPen='k', symbolSize=5.0)
        self.curve2 = self.plot.plot(xx, values, pen=self.plot_color, width=4.0)

        for ovl, sig_values in sig_ovl.items():
            if self.sig_en_cb.isChecked():
                m1 = np.mean(sig_values[:frames1])
                if m1 != 0: sig_values = sig_values / m1 - 1
            self.plot.plot(xx, sig_values, pen=None, symbolBrush=(200, 200, 200), symbolPen='k', symbolSize=5.0)
            self.plot.plot(xx, sig_values, pen=self.plot_color2, width=4.0)

        if self.sig_en_cb.isChecked():
            self.plot.setLabel('left', "Signal Enhancement")
        else:
            self.plot.setLabel('left', "Signal")
        self.plot.setLabel('bottom', self.opts.t_type, units=self.opts.t_unit)
        #self.plot.setLogMode(x=False, y=False)


