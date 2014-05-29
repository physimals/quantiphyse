from __future__ import division, unicode_literals, absolute_import, print_function
from PySide import QtCore, QtGui
import numpy as np

import multiprocessing, multiprocessing.pool
import time

from libs.AnalysisWidgets import QGroupBoxB
from analysis.pkmodel_cpp.pk import PyPk


class PharmaWidget(QtGui.QWidget):

    """
    Widget for generating pharmacokinetics
    Bass class
        - GUI framework
        - Buttons
        - Multiprocessing
    """

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
        p1in = QtGui.QLineEdit('3.7', self)
        p2 = QtGui.QLabel('R2')
        p2in = QtGui.QLineEdit('4.8', self)
        p3 = QtGui.QLabel('Flip Angle')
        p3in = QtGui.QLineEdit('12.0', self)
        p4 = QtGui.QLabel('TR (s)')
        p4in = QtGui.QLineEdit('4.108', self)
        p5 = QtGui.QLabel('TE (s)')
        p5in = QtGui.QLineEdit('1.832', self)
        p6 = QtGui.QLabel('delta T (s)')
        p6in = QtGui.QLineEdit('12', self)
        p7 = QtGui.QLabel('T10 (s)')
        p7in = QtGui.QLineEdit('1.0', self)

        # AIF
        # Select plot color
        combo = QtGui.QComboBox(self)
        combo.addItem("Clinical : Orton AIF (3rd model)")
        combo.addItem("Preclinical : Biexponential model (Heilmann)")
        #combo.activated[str].connect(self.emit_cchoice)
        #combo.setToolTip("Set the color of the enhancement curve when a point is clicked on the image. "
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
        l02.addWidget(p1in, 0, 1)
        l02.addWidget(p2, 1, 0)
        l02.addWidget(p2in, 1, 1)
        l02.addWidget(p3, 2, 0)
        l02.addWidget(p3in, 2, 1)
        l02.addWidget(p4, 3, 0)
        l02.addWidget(p4in, 3, 1)
        l02.addWidget(p5, 4, 0)
        l02.addWidget(p5in, 4, 1)
        l02.addWidget(p6, 5, 0)
        l02.addWidget(p6in, 5, 1)
        l02.addWidget(p7, 6, 0)
        l02.addWidget(p7in, 6, 1)

        f02 = QGroupBoxB()
        f02.setTitle('Parameters')
        f02.setLayout(l02)

        l03 = QtGui.QHBoxLayout()
        l03.addWidget(f02)
        l03.addStretch(2)

        l04 = QtGui.QHBoxLayout()
        l04.addWidget(QtGui.QLabel('AIF choice'))
        l04.addWidget(combo)
        l04.addStretch(1)

        f03 = QGroupBoxB()
        f03.setTitle('AIF options')
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
        self.pool = multiprocessing.Pool(processes=4, initializer=pool_init, initargs=(self.queue,))

    def start_task(self):
        self.timer.start(1000)

        self.pool.apply_async(func=compute, args=(1,))
        self.prog_gen.setValue(0)

    def CheckProg(self):
        if self.queue.empty():
                return
        # unpack the queue
        num_row, progress = self.queue.get()
        self.prog_gen.setValue(progress)


def compute(num_row):
    print("worker started at %d" % num_row)
    random_number = 10
    for second in range(random_number):
        progress = float(second) / float(random_number) * 100
        compute.queue.put((num_row, progress,))
        time.sleep(1)

    # put in the queue
    compute.queue.put((num_row, 100))


def pool_init(queue):
    # see http://stackoverflow.com/a/3843313/852994
    # In python every function is an object so this is a quick and dirty way of adding a variable
    # to a function for easy access later. Prob better to create a class out of compute?
    compute.queue = queue


def run_pk(img1, t10, r1, r2, delt, tr1, te1):

    """
    Simple function interface to run the c++ pk modelling code
    Run from a multiprocess call
    """
    print("worker started")


    T10 = np.ones(img1.shape[:3])

    baseline1 = np.mean(img1[:, :, :, :3], axis=-1)
    img1 = img1 / (np.tile(np.expand_dims(baseline1, axis=-1), (1, 1, img1.shape[-1])) + 0.001) - 1

    # Convert to list of enhancing voxels
    img1vec = np.reshape(img1, (-1, img1.shape[-1]))
    T10vec = np.reshape(T10, (-1))

    t1 = np.arange(0, img1.shape[-1])*delt
    t1 = t1 /60.0

    Dose = 0.1

    dce_flip_angle = 12.0
    dce_TR = tr1/1000.0
    dce_TE = te1/1000.0

    ub = [10, 1, 0.5, 0.5]
    lb = [0, 0.05, -0.5, 0]

    AIFin = [2.65, 1.51, 22.40, 0.23, 0]


    # Subset
    #img1sub = np.ascontiguousarray(np.array(img1vec[:11410, :], dtype=np.double))
    #T10sub = np.ascontiguousarray(T10vec[:11410], dtype=np.double)
    #t1 = np.ascontiguousarray(t1, dtype=np.double)

    # Subset
    img1sub = np.ascontiguousarray(img1vec)
    T10sub = np.ascontiguousarray(T10vec)
    t1 = np.ascontiguousarray(t1)

    Pkclass = PyPk(t1, img1sub, T10sub)
    Pkclass.set_bounds(ub, lb)
    Pkclass.set_AIF(AIFin)
    Pkclass.set_parameters(r1, r2, dce_flip_angle, dce_TR, dce_TE, Dose)

    Pkclass.rinit(1)

    #TODO Loop and update queue with progress

    x = Pkclass.run(5000)
    print(x)
    x = Pkclass.run(5000)
    print(x)

    # Get outputs
    res1 = np.array(Pkclass.get_residual())
    fcurve1 = np.array(Pkclass.get_fitted_curve())
    params2 = np.array(Pkclass.get_parameters())

    #TODO Convert to 3D and 4D volumes
