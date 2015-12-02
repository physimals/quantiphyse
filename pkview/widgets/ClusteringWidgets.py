"""

Author: Benjamin Irving (benjamin.irv@gmail.com)
Copyright (c) 2013-2015 University of Oxford, Benjamin Irving

"""

from __future__ import division, unicode_literals, absolute_import, print_function

from PySide import QtCore, QtGui
import pyqtgraph as pg
import numpy as np

from pkview.analysis.kmeans import KMeans

from pkview.subclassing_of_qt_fns.QtSubclass import QGroupBoxB


class CurveClusteringWidget(QtGui.QWidget):
    """
    Widget for clustering the tumour into various regions
    """

    #emit reset command
    sig_emit_reset = QtCore.Signal(bool)

    def __init__(self):
        super(CurveClusteringWidget, self).__init__()

        #self.setStatusTip("Click points on the 4D volume to see time curve")

        self.win1 = pg.GraphicsWindow(title="Basic plotting examples")
        self.win1.setBackground(background=None)
        self.p1 = self.win1.addPlot(title="Cluster representative curves")

        #Run clustering button
        self.b1 = QtGui.QPushButton('Run', self)
        self.b1.clicked.connect(self.run_clustering)

        # Number of clusters inside the ROI
        self.combo = QtGui.QSpinBox(self)
        self.combo.setRange(2, 20)
        self.combo.setValue(4)
        #self.combo.activated[str].connect(self.emit_cchoice)
        self.combo.setToolTip("Set the color of the enhancement curve when a point is clicked on the image. "
                         "Allows visualisation of multiple enhancement curves of different colours")

        # Number of PCA modes
        self.combo2 = QtGui.QSpinBox(self)
        self.combo2.setRange(1, 10)
        self.combo2.setValue(3)
        # self.combo.activated[str].connect(self.emit_cchoice)
        self.combo2.setToolTip("Set the color of the enhancement curve when a point is clicked on the image. "
                         "Allows visualisation of multiple enhancement curves of different colours")


        l03 = QtGui.QHBoxLayout()
        l03.addWidget(self.b1)
        l03.addStretch(1)

        space1 = QtGui.QLabel('')

        l01 = QtGui.QHBoxLayout()
        l01.addWidget(QtGui.QLabel('Number of clusters:'))
        l01.addWidget(self.combo)
        l01.addStretch(1)

        l02 = QtGui.QHBoxLayout()
        l02.addWidget(QtGui.QLabel('Normalised PCA modes (Advanced):'))
        l02.addWidget(self.combo2)
        l02.addStretch(1)

        l04 = QtGui.QVBoxLayout()
        l04.addLayout(l01)
        l04.addLayout(l02)

        g01 = QGroupBoxB()
        g01.setLayout(l04)
        g01.setTitle('Clustering options')

        l05 = QtGui.QHBoxLayout()
        l05.addLayout(l03)
        l05.addWidget(g01)

        l1 = QtGui.QVBoxLayout()
        l1.addLayout(l05)
        l1.addWidget(space1)
        l1.addWidget(self.win1)
        l1.addStretch(1)
        self.setLayout(l1)

        # Initialisation
        # Volume management widget
        self.ivm = None
        self.km = None

    def add_image_management(self, image_vol_management):

        """
        Adding image management
        """
        self.ivm = image_vol_management

    def run_clustering(self):
        """
        Run kmeans clustering using normalised PCA modes
        """

        # Check that pkmodelling can be run
        if self.ivm.get_image() is None:
            m1 = QtGui.QMessageBox()
            m1.setText("The image doesn't exist! Please load.")
            m1.setWindowTitle("PkView")
            m1.exec_()
            return

        if self.ivm.get_roi() is None:
            m1 = QtGui.QMessageBox()
            m1.setWindowTitle("PkView")
            m1.setText("The Image or ROI doesn't exist! Please load.")
            m1.exec_()
            return

        # Disable button
        self.b1.setDown(1)
        self.b1.setDisabled(1)

        img1 = self.ivm.get_image()
        roi1 = self.ivm.get_roi()

        self.km = KMeans(img1, region1=roi1)

        self.km.run_single(n_clusters=self.combo.value(), opt_normdata=1, n_pca_components=self.combo2.value())

        #self.km.plot(slice1=30)
        label1, self.label1_cent = self.km.get_label_image()

        self.ivm.set_overlay(choice1='loaded', ovreg=label1)
        self.ivm.set_current_overlay(choice1='loaded')
        self.sig_emit_reset.emit(1)
        # This previous step should generate a color map which can then be used in the following steps.

        self._plot()

        print("Done!")
        # enable button again
        self.b1.setDown(0)
        self.b1.setDisabled(0)

    def reset_graph(self):
        """
        Reset and clear the graph
        """
        self.win1.removeItem(self.p1)
        self.p1 = self.win1.addPlot(title="Cluster representative curves")
        self.p1.setLabel('left', "Signal Enhancement")
        self.p1.setLabel('bottom', "Temporal position")

    def _plot(self):
        """
        Plot the 4 cluster curves
        :return:
        """
        # Clear graph
        self.reset_graph()
        curve1 = []

        xx = np.arange(self.label1_cent.shape[1])
        num_clus = self.label1_cent.shape[0]

        lut = self.ivm.cmap
        lut_sec = np.around(lut.shape[0]/(num_clus-1))

        # Plotting using single or multiple plots
        for ii in range(num_clus):
            if ii < num_clus-1:
                pen1 = lut[ii * lut_sec, :3]
            else:
                pen1 = lut[-1, :3]

            curve1.append(self.p1.plot(pen=pen1, width=8.0))
            curve1[ii].setData(xx, self.label1_cent[ii, :])
