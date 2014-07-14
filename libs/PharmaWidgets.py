from __future__ import division, unicode_literals, absolute_import, print_function
from PySide import QtCore, QtGui
import numpy as np
import pyqtgraph as pg
from scipy.interpolate import UnivariateSpline

import multiprocessing,multiprocessing.pool
import time

from libs.AnalysisWidgets import QGroupBoxB
from analysis.pkmodel_cpp.pk import PyPk


class PharmaWidget(QtGui.QWidget):

    """
    Widget for generating Pharmacokinetics
    Bass class
        - GUI framework
        - Buttons
        - Multiprocessing
    """

    #emit reset command
    sig_emit_reset = QtCore.Signal(bool)

    def __init__(self):
        super(PharmaWidget, self).__init__()
        self.init_multiproc()

        self.ivm = None

        # progress of generation
        self.prog_gen = QtGui.QProgressBar(self)
        self.prog_gen.setStatusTip('Progress of Pk modelling. Be patient. Progress is only updated in chunks')

        # generate button
        but_gen = QtGui.QPushButton('Run modelling', self)
        but_gen.clicked.connect(self.start_task)

        #Inputs
        p1 = QtGui.QLabel('R1')
        self.valR1 = QtGui.QLineEdit('3.7', self)
        p2 = QtGui.QLabel('R2')
        self.valR2 = QtGui.QLineEdit('4.8', self)
        p3 = QtGui.QLabel('Flip Angle')
        self.valFA = QtGui.QLineEdit('12.0', self)
        p4 = QtGui.QLabel('TR (s)')
        self.valTR = QtGui.QLineEdit('4.108', self)
        p5 = QtGui.QLabel('TE (s)')
        self.valTE = QtGui.QLineEdit('1.832', self)
        p6 = QtGui.QLabel('delta T (s)')
        self.valDelT = QtGui.QLineEdit('12', self)

        # AIF
        # Select plot color
        self.combo = QtGui.QComboBox(self)
        self.combo.addItem("Clinical: Toft / OrtonAIF (3rd) with offset")
        self.combo.addItem("Clinical: Toft / OrtonAIF (3rd) no offset")
        self.combo.addItem("Preclinical: Toft / BiexpAIF (Heilmann)")
        self.combo.addItem("Preclinical: Ext Toft / BiexpAIF (Heilmann)")

        #self.combo.activated[str].connect(self.emit_cchoice)
        #self.combo.setToolTip("Set the color of the enhancement curve when a point is clicked on the image. "
        #                 "Allows visualisation of multiple enhancement curves of different colours")

        #LAYOUTS
        # Progress
        l01 = QtGui.QHBoxLayout()
        l01.addWidget(but_gen)
        l01.addWidget(self.prog_gen)

        f01 = QGroupBoxB()
        f01.setTitle('Running')
        f01.setLayout(l01)

        # Inputs
        l02 = QtGui.QGridLayout()
        l02.addWidget(p1, 0, 0)
        l02.addWidget(self.valR1, 0, 1)
        l02.addWidget(p2, 1, 0)
        l02.addWidget(self.valR2, 1, 1)
        l02.addWidget(p3, 2, 0)
        l02.addWidget(self.valFA, 2, 1)
        l02.addWidget(p4, 3, 0)
        l02.addWidget(self.valTR, 3, 1)
        l02.addWidget(p5, 4, 0)
        l02.addWidget(self.valTE, 4, 1)
        l02.addWidget(p6, 5, 0)
        l02.addWidget(self.valDelT, 5, 1)

        f02 = QGroupBoxB()
        f02.setTitle('Parameters')
        f02.setLayout(l02)

        l03 = QtGui.QHBoxLayout()
        l03.addWidget(f02)
        l03.addStretch(2)

        l04 = QtGui.QHBoxLayout()
        l04.addWidget(QtGui.QLabel('AIF choice'))
        l04.addWidget(self.combo)
        l04.addStretch(1)

        f03 = QGroupBoxB()
        f03.setTitle('Pharmacokinetic model choice')
        f03.setLayout(l04)

        l0 = QtGui.QVBoxLayout()
        l0.addLayout(l03)
        l0.addWidget(f03)
        l0.addWidget(f01)
        l0.addStretch()

        self.setLayout(l0)

        # Check for updates from the process
        self.timer = QtCore.QTimer()
        self.timer.timeout.connect(self.CheckProg)

    def add_image_management(self, image_vol_management):

        """
        Adding image management
        """

        self.ivm = image_vol_management

    def init_multiproc(self):

        # Set up the background process

        self.queue = multiprocessing.Queue()
        self.pool = multiprocessing.Pool(processes=2, initializer=pool_init, initargs=(self.queue,))

    def start_task(self):

        """
        Start running the PK modelling on button click
        """

        # Check that pkmodelling can be run
        if self.ivm.get_image() is None:
            m1 = QtGui.QMessageBox()
            m1.setText("The image doesn't exist! Please load before running Pk modelling")
            m1.exec_()
            return

        if self.ivm.get_roi() is None:
            m1 = QtGui.QMessageBox()
            m1.setText("The Image or ROI doesn't exist! Please load before running Pk modelling")
            m1.exec_()
            return

        if self.ivm.get_T10() is None:
            m1 = QtGui.QMessageBox()
            m1.setText("The T10 map doesn't exist! Please load before running Pk modelling")
            m1.exec_()
            return

        self.timer.start(1000)

        # get volumes to process

        img1 = self.ivm.get_image()
        roi1 = self.ivm.get_roi()
        t101 = self.ivm.get_T10()

        # Extract the text from the line edit options

        R1 = float(self.valR1.text())
        R2 = float(self.valR2.text())
        DelT = float(self.valDelT.text())
        TR = float(self.valTR.text())
        TE = float(self.valTE.text())
        FA = float(self.valFA.text())

        # getting model choice from list
        model_choice = self.combo.currentIndex() + 1

        baseline1 = np.mean(img1[:, :, :, :3], axis=-1)

        # Convert to list of enhancing voxels
        img1vec = np.reshape(img1, (-1, img1.shape[-1]))
        T10vec = np.reshape(t101, (-1))
        self.roi1vec = np.array(np.reshape(roi1, (-1)), dtype=bool)
        baseline1 = np.reshape(baseline1, (-1))

        # Make sure the type is correct
        img1vec = np.array(img1vec, dtype=np.double)
        T101vec = np.array(T10vec, dtype=np.double)
        roi1vec = np.array(self.roi1vec, dtype=bool)

        print("subset")
        # Subset within the ROI and
        img1sub = img1vec[roi1vec, :]
        T101sub = T101vec[roi1vec]
        baseline1sub = baseline1[roi1vec]

        # Normalisation of the image (put normalised image in the volume management part)
        img1sub = img1sub / (np.tile(np.expand_dims(baseline1sub, axis=-1), (1, img1.shape[-1])) + 0.001) - 1

        # start separate processor
        self.result = self.pool.apply_async(func=run_pk, args=(img1sub, T101sub, R1, R2, DelT, TR, TE, FA,
                                                               model_choice))
        # set the progress value
        self.prog_gen.setValue(0)

    def CheckProg(self):

        """
        Check the progress regularly and update volumes when progress reaches 100%
        """

        if self.queue.empty():
                return

        # unpack the queue
        num_row, progress = self.queue.get()
        self.prog_gen.setValue(progress)

        if progress == 100:
            # Stop checking once progress reaches 100%
            self.timer.stop()

            # Get results from the process
            var1 = self.result.get()

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

            #estimated_curve1 = np.zeros(img1vec.shape)
            #estimated_curve1[roi1v, :] = var1[1]

            residual1 = np.zeros((roi1v.shape[0]))
            residual1[roi1v] = var1[0]

            # Convert to list of enhancing voxels
            Ktrans1vol = np.reshape(Ktrans1, (self.ivm.img_dims[:-1]))
            ve1vol = np.reshape(ve1, (self.ivm.img_dims[:-1]))
            offset1vol = np.reshape(offset1, (self.ivm.img_dims[:-1]))
            vp1vol = np.reshape(vp1, (self.ivm.img_dims[:-1]))
            kep1vol = np.reshape(kep1, (self.ivm.img_dims[:-1]))

            # Pass overlay maps to the volume management
            self.ivm.set_overlay(choice1='Ktrans', ovreg=Ktrans1vol)
            self.ivm.set_overlay(choice1='ve', ovreg=ve1vol)
            self.ivm.set_overlay(choice1='kep', ovreg=kep1vol)
            self.ivm.set_overlay(choice1='offset', ovreg=offset1vol)
            self.ivm.set_overlay(choice1='vp', ovreg=vp1vol)
            self.ivm.set_current_overlay(choice1='Ktrans')
            self.sig_emit_reset.emit(1)


def run_pk(img1sub, t101sub, r1, r2, delt, tr1, te1, dce_flip_angle, model_choice):

    """
    Simple function interface to run the c++ pk modelling code
    Run from a multiprocess call
    """

    print("pk modelling worker started")

    t1 = np.arange(0, img1sub.shape[-1])*delt
    t1 = t1/60.0

    Dose = 0.1

    dce_TR = tr1/1000.0
    dce_TE = te1/1000.0

    ub = [10, 1, 0.5, 0.5]
    lb = [0, 0.05, -0.5, 0]

    print("contiguous")
    # contiguous array
    img1sub = np.ascontiguousarray(img1sub)
    t101sub = np.ascontiguousarray(t101sub)
    t1 = np.ascontiguousarray(t1)

    Pkclass = PyPk(t1, img1sub, t101sub)
    Pkclass.set_bounds(ub, lb)
    Pkclass.set_parameters(r1, r2, dce_flip_angle, dce_TR, dce_TE, Dose)

    # Initialise fitting
    Pkclass.rinit(model_choice)

    # Iteratively process 5000 points at a time
    # (this can be performed as a multiprocess soon)

    size_step = 5000
    size_tot = img1sub.shape[0]
    steps1 = np.around(size_tot/size_step)
    num_row = 1.0  # Just a placeholder for the meanwhile

    print("Number of steps: ", steps1)
    for ii in range(int(steps1)):
        progress = float(ii) / float(steps1) * 100
        print(progress)

        run_pk.queue.put((num_row, progress))
        time.sleep(0.2)  # sleeping seems to allow queue to be flushed out correctly
        x = Pkclass.run(5000)
        print(x)

    print("Done")

    # Get outputs
    res1 = np.array(Pkclass.get_residual())
    fcurve1 = np.array(Pkclass.get_fitted_curve())
    params2 = np.array(Pkclass.get_parameters())

    # final update to progress bar
    run_pk.queue.put((num_row, 100))
    time.sleep(0.2)  # sleeping seems to allow queue to be flushed out correctly
    return res1, fcurve1, params2


def pool_init(queue):
    # see http://stackoverflow.com/a/3843313/852994
    # In python every function is an object so this is a quick and dirty way of adding a variable
    # to a function for easy access later. Prob better to create a class out of compute?
    run_pk.queue = queue


class PharmaView(QtGui.QWidget):

    """
    View True and generated signal curves side by side (just reverse the scale)
    """

    def __init__(self):
        super(PharmaView, self).__init__()

        self.setStatusTip("Click points on the 4D volume to see time curve")

        self.win1 = pg.GraphicsWindow(title="Basic plotting examples")
        self.win1.setVisible(True)
        self.p1 = self.win1.addPlot(title="Signal enhancement curve")
        self.reset_graph()

        #Signal enhancement (normalised)
        self.cb3 = QtGui.QCheckBox('Signal enhancement', self)
        self.cb3.toggle()
        self.cb3.stateChanged.connect(self.reset_graph)

        # input temporal resolution
        self.text1 = QtGui.QLineEdit('1.0', self)
        self.text1.returnPressed.connect(self.replot_graph)


        l02 = QtGui.QHBoxLayout()
        l02.addWidget(QtGui.QLabel("Temporal resolution (s)"))
        l02.addWidget(self.text1)
        l02.addStretch(1)

        l04 = QtGui.QVBoxLayout()
        l04.addLayout(l02)
        l04.addWidget(self.cb3)

        g01 = QGroupBoxB()
        g01.setLayout(l04)
        g01.setTitle('Curve options')

        l05 = QtGui.QHBoxLayout()
        l05.addWidget(g01)
        l05.addStretch()

        l1 = QtGui.QVBoxLayout()
        l1.addWidget(self.win1)
        l1.addLayout(l05)
        l1.addStretch(1)
        self.setLayout(l1)

        # initial plot colour
        self.plot_color = (200, 200, 200)

    def _plot(self, values1):

        """
        Plot the curve / curves
        """
        #Make window visible and populate
        self.win1.setVisible(True)

        values1 = np.array(values1, dtype=np.double)
        values2 = np.copy(values1)

        # Setting x-values
        xres = float(self.text1.text())
        xx = xres * np.arange(len(values1))

        if self.values2_mean is None:
            self.values2_mean = np.zeros((1, len(xx)))

        if self.cb3.isChecked() is True:
            m1 = np.mean(values1[:3])
            values1 = values1 / m1 - 1
            values2 = np.copy(values1)

        # Plotting using single or multiple plots
        if self.curve1 is None:
            self.curve1 = self.p1.plot(pen=None, symbolBrush=(200, 200, 200), symbolPen='k', symbolSize=5.0)
            self.curve2 = self.p1.plot(pen=self.plot_color, width=4.0)
        self.curve2.setData(xx, values2, pen=self.plot_color)
        self.curve1.setData(xx, values1)

        self.p1.setLabel('left', "Signal Enhancement")
        self.p1.setLabel('bottom', "Time", units='s')
        #self.p1.setLogMode(x=False, y=False)

    @QtCore.Slot()
    def replot_graph(self):
        self.reset_graph()
        #other stuff

    @QtCore.Slot()
    def reset_graph(self):
        """
        Reset and clear the graph
        """
        self.win1.removeItem(self.p1)
        self.p1 = self.win1.addPlot(title="Signal enhancement curve")
        self.curve1 = None
        self.curve2 = None
        self.curve_mean = None
        self.curve_count = 0
        self.values2_mean = None

    @QtCore.Slot(np.ndarray)
    def sig_mouse(self, values1):
        """
        Get signal from mouse click
        """
        self._plot(values1)
