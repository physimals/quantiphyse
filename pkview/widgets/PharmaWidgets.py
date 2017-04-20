"""

Author: Benjamin Irving (benjamin.irv@gmail.com)
Copyright (c) 2013-2015 University of Oxford, Benjamin Irving

"""

from __future__ import division, unicode_literals, absolute_import, print_function

import time

import numpy as np
import pyqtgraph as pg
from PySide import QtCore, QtGui

from pkview import error_dialog
from pkview.QtInherit.QtSubclass import QGroupBoxB
from pkview.analysis import MultiProcess
from pkview.analysis.pk_model import PyPk
from pkview.volumes.volume_management import Overlay, Roi
from pkview.widgets import PkWidget

class PkModellingProcess(MultiProcess):

    """ Signal emitted to track progress"""
    sig_progress = QtCore.Signal(int)

    def __init__(self, *args):
        N = 1
        MultiProcess.__init__(self, N, run_pk, args)

    def progress(self):
        if self.queue.empty(): return
        while not self.queue.empty():
            num_row, progress = self.queue.get()
        self.sig_progress.emit(progress)

def run_pk(id, queue, img1sub, t101sub, r1, r2, delt, injt, tr1, te1, dce_flip_angle, dose, model_choice):
    """
    Simple function to run the c++ pk modelling code. Must be a function to work with multiprocessing
    
        img1sub:
        t101sub:
        r1:
        r2:
        delt:
        injt:
        tr1:
        te1:
        dce_flip_angle:
        dose:
        model_choice:
    """
    print("pk modelling worker started")
    try:
        t1 = np.arange(0, img1sub.shape[-1])*delt
        # conversion to minutes
        t1 = t1/60.0

        injtmins = injt/60.0

        Dose = dose

        # conversion to seconds
        dce_TR = tr1/1000.0
        dce_TE = te1/1000.0

        #specify variable upper bounds and lower bounds
        ub = [10, 1, 0.5, 0.5]
        lb = [0, 0.05, -0.5, 0]

        # contiguous array
        img1sub = np.ascontiguousarray(img1sub)
        t101sub = np.ascontiguousarray(t101sub)
        t1 = np.ascontiguousarray(t1)

        Pkclass = PyPk(t1, img1sub, t101sub)
        Pkclass.set_bounds(ub, lb)
        Pkclass.set_parameters(r1, r2, dce_flip_angle, dce_TR, dce_TE, Dose)

        # Initialise fitting
        # Choose model type and injection time
        Pkclass.rinit(model_choice, injtmins)

        # Iteratively process 5000 points at a time
        # (this can be performed as a multiprocess soon)

        size_step = max(1, np.around(img1sub.shape[0]/5))
        size_tot = img1sub.shape[0]
        steps1 = np.around(size_tot/size_step)
        num_row = 1.0  # Just a placeholder for the meanwhile

        print("Number of voxels per step: ", size_step)
        print("Number of steps: ", steps1)
        queue.put((num_row, 1))
        for ii in range(int(steps1)):
            if ii > 0:
                progress = float(ii) / float(steps1) * 100
                # print(progress)
                queue.put((num_row, progress))

            time.sleep(0.2)  # sleeping seems to allow queue to be flushed out correctly
            x = Pkclass.run(size_step)
            # print(x)

        print("Done")

        # Get outputs
        res1 = np.array(Pkclass.get_residual())
        fcurve1 = np.array(Pkclass.get_fitted_curve())
        params2 = np.array(Pkclass.get_parameters())

        # final update to progress bar
        queue.put((num_row, 100))
        time.sleep(0.2)  # sleeping seems to allow queue to be flushed out correctly
        return id, True, (res1, fcurve1, params2)
    except:
        print("PK worker error: %s" % sys.exc_info()[0])
        return id, False, sys.exc_info()[0]

class PharmaWidget(PkWidget):
    """
    Widget for Pharmacokinetic modelling
    """

    def __init__(self, **kwargs):
        super(PharmaWidget, self).__init__(name="PK Modelling", desc="Pharmacokinetic Modelling", icon="pk", **kwargs)

        main_vbox = QtGui.QVBoxLayout()

        # Inputs
        param_box = QGroupBoxB()
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
        aif_choice = QGroupBoxB()
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
        run_box = QGroupBoxB()
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

        # get volumes to process
        img1 = self.ivm.vol.data
        roi1 = self.ivm.current_roi.data
        t101 = self.ivm.overlays["T10"].data

        #slices = self.ivm.current_roi.get_bounding_box(ndims=self.ivm.vol.ndims)
        #roi_slices = slices[:self.ivm.current_roi.ndims]
        #img1 = self.ivm.vol.data[slices]
        #roi1 = self.ivm.current_roi.data[roi_slices]
        #t101 = self.ivm.overlays["T10"].data[roi_slices]

        # Extract the text from the line edit options

        R1 = float(self.valR1.text())
        R2 = float(self.valR2.text())
        DelT = float(self.valDelT.text())
        InjT = float(self.valInjT.text())
        TR = float(self.valTR.text())
        TE = float(self.valTE.text())
        FA = float(self.valFA.text())
        self.thresh1val= float(self.thresh1.text())
        Dose = float(self.valDose.text())

        # getting model choice from list
        model_choice = self.combo.currentIndex() + 1

        # Baseline defaults to time points prior to injection
        baseline_tpts = int(1 + InjT / DelT)
        print("First %i time points used for baseline normalisation" % baseline_tpts)
        self.baseline = np.mean(img1[:, :, :, :baseline_tpts], axis=-1)

        # Convert to list of enhancing voxels
        img1vec = np.reshape(img1, (-1, img1.shape[-1]))
        T10vec = np.reshape(t101, (-1))
        self.roi1vec = np.array(np.reshape(roi1, (-1)), dtype=bool)
        self.baseline = np.reshape(self.baseline, (-1))

        # Make sure the type is correct
        img1vec = np.array(img1vec, dtype=np.double)
        T101vec = np.array(T10vec, dtype=np.double)
        roi1vec = np.array(self.roi1vec, dtype=bool)

        # Subset within the ROI 
        img1sub = img1vec[roi1vec, :]
        T101sub = T101vec[roi1vec]
        self.baseline = self.baseline[roi1vec]

        # Normalisation of the image
        img1sub = img1sub / (np.tile(np.expand_dims(self.baseline, axis=-1), (1, img1.shape[-1])) + 0.001) - 1

        # start separate processor
        self.process = PkModellingProcess(img1sub, T101sub, R1, R2, DelT, InjT, TR, TE, FA, Dose, model_choice)
        self.process.sig_finished.connect(self.Finished)
        self.process.sig_progress.connect(self.CheckProg)
        self.process.run()

        # set the progress value
        self.prog_gen.setValue(0)

    def CheckProg(self, progress):
        """
        Check the progress regularly and update volumes when progress reaches 100%
        """
        self.prog_gen.setValue(progress)

    def Finished(self, success, output):
        if success:
            # Only one worker - get its output
            var1 = output[0]

            #make sure that we are accessing whole array
            roi1v = np.array(self.roi1vec, dtype=bool)

            #Params: Ktrans, ve, offset, vp
            Ktrans1 = np.zeros((roi1v.shape[0]))
            Ktrans1[roi1v] = var1[2][:, 0] * (var1[2][:, 0] < 2.0) + 2 * (var1[2][:, 0] > 2.0)

            ve1 = np.zeros((roi1v.shape[0]))
            ve1[roi1v] = var1[2][:, 1] * (var1[2][:, 1] < 2.0) + 2 * (var1[2][:, 1] > 2.0)
            ve1 *= (ve1 > 0)

            kep1p = Ktrans1 / (ve1 + 0.001)
            kep1p[np.logical_or(np.isnan(kep1p), np.isinf(kep1p))] = 0
            kep1p *= (kep1p > 0)
            kep1 = kep1p * (kep1p < 2.0) + 2 * (kep1p >= 2.0)

            offset1 = np.zeros((roi1v.shape[0]))
            offset1[roi1v] = var1[2][:, 2]

            vp1 = np.zeros((roi1v.shape[0]))
            vp1[roi1v] = var1[2][:, 3]

            sig = (var1[1] + 1) * (np.tile(np.expand_dims(self.baseline, axis=-1), (1, self.ivm.vol.shape[-1])))

            estimated_curve1 = np.zeros((roi1v.shape[0], self.ivm.vol.shape[-1]))
            estimated_curve1[roi1v, :] = sig
    
            residual1 = np.zeros((roi1v.shape[0]))
            residual1[roi1v] = var1[0]

            # Convert to list of enhancing voxels
            Ktrans1vol = np.reshape(Ktrans1, (self.ivm.vol.shape[:-1]))
            ve1vol = np.reshape(ve1, (self.ivm.vol.shape[:-1]))
            offset1vol = np.reshape(offset1, (self.ivm.vol.shape[:-1]))
            vp1vol = np.reshape(vp1, (self.ivm.vol.shape[:-1]))
            kep1vol = np.reshape(kep1, (self.ivm.vol.shape[:-1]))
            estimated1vol = np.reshape(estimated_curve1, self.ivm.vol.shape)

            #thresholding according to upper limit
            p = np.percentile(Ktrans1vol, self.thresh1val)
            Ktrans1vol[Ktrans1vol > p] = p
            p = np.percentile(kep1vol, self.thresh1val)
            kep1vol[kep1vol > p] = p

            #slices = self.ivm.current_roi.get_bounding_box(ndims=self.ivm.vol.ndims)
            #roi_slices = slices[:self.ivm.current_roi.ndims]
            
            # Pass overlay maps to the volume management
            self.ivm.add_overlay(Overlay('Ktrans', data=Ktrans1vol), make_current=True)
            self.ivm.add_overlay(Overlay('ve', data=ve1vol))
            self.ivm.add_overlay(Overlay('kep', data=kep1vol))
            self.ivm.add_overlay(Overlay('offset', data=offset1vol))
            self.ivm.add_overlay(Overlay('vp', data=vp1vol))
            self.ivm.add_overlay(Overlay("Model curves", data=estimated1vol))
            
    def add_ovl(self, name, data, slices):
        newdata = np.zeros(self.ivm.vol.data.shape[:len(slices)])
        newdata[slices] = data
        self.ivm.add_overlay(Overlay(name, data=newdata), make_current=False)

class PharmaView(PkWidget):
    """
    View original data and generated signal curves side by side (just reverse the scale)
    """

    def __init__(self, **kwargs):
        super(PharmaView, self).__init__(name="Model Curve", desc="Display model enhancement curves", icon="pk", **kwargs)

        main_vbox = QtGui.QVBoxLayout()
        self.setStatusTip("Click points on the 4D volume to see actual and predicted curve")

        win = pg.GraphicsLayoutWidget()
        win.setBackground(background=None)
        self.plot = win.addPlot(title="Model / Data Curves")
        main_vbox.addWidget(win)

        hbox = QtGui.QHBoxLayout()
        opts_box = QGroupBoxB()
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
        params_box = QGroupBoxB()
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
        self.ivl.sig_mouse_click.connect(self.replot_curves)
        self.replot_curves()

    def deactivate(self):
        self.ivl.sig_mouse_click.disconnect(self.replot_curves)

    def options_changed(self, opts):
        self.replot_curves()

    def sig_enh_changed(self, opts):
        self.norm_frames.setEnabled(self.sig_en_cb.isChecked())
        self.replot_curves()

    def replot_curves(self, data=None):
        self._plot()
        self._update_table()

    def _update_table(self):
        """
        Set the overlay parameter values in the table based on the current point clicked
        """
        overlay_vals = self.ivm.get_overlay_value_curr_pos()
        for ii, ovl in enumerate(overlay_vals.keys()):
            if self.ivm.overlays[ovl].ndims == 3:
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


