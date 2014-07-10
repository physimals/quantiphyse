from __future__ import division, unicode_literals, absolute_import, print_function
from PySide import QtCore, QtGui
import numpy as np

import multiprocessing, multiprocessing.pool
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

        # start separate processor
        self.result = self.pool.apply_async(func=run_pk, args=(img1, roi1, t101, R1, R2, DelT, TR, TE, FA,
                                                               model_choice))
        #self.pool.apply_async(func=compute, args=(1,))

        # set the progress value
        self.prog_gen.setValue(0)

        # get outputs

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

            # Pass overlay maps to the volume management
            self.ivm.set_overlay(choice1='Ktrans', ovreg=var1[0])
            self.ivm.set_overlay(choice1='ve', ovreg=var1[1])
            self.ivm.set_overlay(choice1='kep', ovreg=var1[2])
            self.ivm.set_overlay(choice1='offset', ovreg=var1[3])
            self.ivm.set_overlay(choice1='vp', ovreg=var1[4])
            self.ivm.set_current_overlay(choice1='Ktrans')
            self.sig_emit_reset.emit(1)


def run_pk(img1, roi1, t10, r1, r2, delt, tr1, te1, dce_flip_angle, model_choice):

    """
    Simple function interface to run the c++ pk modelling code
    Run from a multiprocess call
    """

    print("pk modelling worker started")

    baseline1 = np.mean(img1[:, :, :, :3], axis=-1)
    # Normalisation of the image (put normalised image in the volume management part)
    img1 = img1 / (np.tile(np.expand_dims(baseline1, axis=-1), (1, 1, img1.shape[-1])) + 0.001) - 1

    # Convert to list of enhancing voxels
    img1vec = np.reshape(img1, (-1, img1.shape[-1]))
    T10vec = np.reshape(t10, (-1))
    roi1vec = np.reshape(roi1, (-1))

    # Make sure the type is correct
    img1vec = np.array(img1vec, dtype=np.double)
    T10vec = np.array(T10vec, dtype=np.double)
    roi1vec = np.array(roi1vec, dtype=bool)

    t1 = np.arange(0, img1.shape[-1])*delt
    t1 = t1/60.0

    Dose = 0.1

    dce_TR = tr1/1000.0
    dce_TE = te1/1000.0

    ub = [10, 1, 0.5, 0.5]
    lb = [0, 0.05, -0.5, 0]

    print("subset")
    # Subset within the ROI and
    img1sub = img1vec[roi1vec, :]
    T10sub = T10vec[roi1vec]

    print("contiguous")
    # contiguous array
    img1sub = np.ascontiguousarray(img1sub)
    T10sub = np.ascontiguousarray(T10sub)
    t1 = np.ascontiguousarray(t1)

    Pkclass = PyPk(t1, img1sub, T10sub)
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

    #Params: Ktrans, ve, offset, vp

    Ktrans1 = np.zeros((img1vec.shape[0]))
    Ktrans1[roi1vec] = params2[:, 0] * (params2[:, 0] < 2.0) + 2 * (params2[:, 0] > 2.0)

    ve1 = np.zeros((img1vec.shape[0]))
    ve1[roi1vec] = params2[:, 1] * (params2[:, 1] < 2.0) + 2 * (params2[:, 1] > 2.0)

    kep1p = params2[:, 0] / (params2[:, 1] + 0.001)
    kep1p[np.logical_or(np.isnan(kep1p), np.isinf(kep1p))] = 0
    kep1p *= (kep1p > 0)
    kep1 = np.zeros((img1vec.shape[0]))
    kep1[roi1vec] = kep1p * (kep1p < 2.0) + 2 * (kep1p > 2.0)

    offset1 = np.zeros((img1vec.shape[0]))
    offset1[roi1vec] = params2[:, 2]

    vp1 = np.zeros((img1vec.shape[0]))
    vp1[roi1vec] = params2[:, 3]

    estimated_curve1 = np.zeros(img1vec.shape)
    estimated_curve1[roi1vec, :] = fcurve1

    residual1 = np.zeros((img1vec.shape[0]))
    residual1[roi1vec] = res1

    # Convert to list of enhancing voxels
    Ktrans1vol = np.reshape(Ktrans1, (img1.shape[:-1]))
    ve1vol = np.reshape(ve1, (img1.shape[:-1]))
    offset1vol = np.reshape(offset1, (img1.shape[:-1]))
    vp1vol = np.reshape(vp1, (img1.shape[:-1]))
    kep1vol = np.reshape(kep1, (img1.shape[:-1]))

    # final update to progress bar
    run_pk.queue.put((num_row, 100))
    time.sleep(0.2)  # sleeping seems to allow queue to be flushed out correctly

    return Ktrans1vol, ve1vol, kep1vol, offset1vol, vp1vol

    #TODO Convert to 3D and 4D volumes
    #TODO Send the volumes to the volume management object


def pool_init(queue):
    # see http://stackoverflow.com/a/3843313/852994
    # In python every function is an object so this is a quick and dirty way of adding a variable
    # to a function for easy access later. Prob better to create a class out of compute?
    run_pk.queue = queue