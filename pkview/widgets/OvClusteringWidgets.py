"""

Author: Benjamin Irving (benjamin.irv@gmail.com)
Copyright (c) 2013-2015 University of Oxford, Benjamin Irving

"""

from __future__ import division, unicode_literals, absolute_import, print_function

import numpy as np
from PySide import QtCore, QtGui

from pkview import error_dialog
from pkview.QtInherit import HelpButton
from pkview.QtInherit.QtSubclass import QGroupBoxB
from pkview.analysis.kmeans import KMeans3D
from pkview.volumes.volume_management import Roi
from pkview.widgets import PkWidget

#TODO Hide other buttons until the clustering is performed.


class OvCurveClusteringWidget(PkWidget):
    """
    Widget for clustering the tumour into various regions
    """

    # emit reset command
    sig_emit_reset = QtCore.Signal(bool)

    def __init__(self, **kwargs):
        super(OvCurveClusteringWidget, self).__init__(name="Overlay Cluster", icon="clustering", desc="Generate clusters from overlays", **kwargs)

        # self.setStatusTip("Click points on the 4D volume to see time curve")
        title1 = QtGui.QLabel("<font size=5> Clustering of the current overlay </font>")
        bhelp = HelpButton(self)
        lhelp = QtGui.QHBoxLayout()
        lhelp.addWidget(title1)
        lhelp.addStretch(1)
        lhelp.addWidget(bhelp)

        # Run clustering button
        self.b1 = QtGui.QPushButton('Run', self)
        self.b1.clicked.connect(self.run_clustering)

        # Number of clusters inside the ROI
        self.combo = QtGui.QSpinBox(self)
        self.combo.setRange(2, 20)
        self.combo.setValue(4)
        # self.combo.activated[str].connect(self.emit_cchoice)
        self.combo.setToolTip("Set the color of the enhancement curve when a point is clicked on the image. "
                         "Allows visualisation of multiple enhancement curves of different colours")

        l03 = QtGui.QHBoxLayout()
        l03.addWidget(self.b1)
        l03.addStretch(1)

        space1 = QtGui.QLabel('')

        # Options
        l01 = QtGui.QHBoxLayout()
        l01.addWidget(QtGui.QLabel('Number of clusters:'))
        l01.addWidget(self.combo)
        l01.addStretch(1)

        l04 = QtGui.QVBoxLayout()
        l04.addLayout(l01)

        g01 = QGroupBoxB()
        g01.setLayout(l04)
        g01.setTitle('Clustering options')

        l05 = QtGui.QHBoxLayout()
        l05.addLayout(l03)
        l05.addWidget(g01)
        
        self.b4 = QtGui.QPushButton('Advanced options', self)
        self.b4.clicked.connect(self.show_options)

        # Merge options

        self.b2 = QtGui.QPushButton('Merge', self)
        self.b2.clicked.connect(self.run_merge)

        t1 = QtGui.QLabel('Merge region ')
        self.val_m1 = QtGui.QLineEdit('1', self)
        t2 = QtGui.QLabel(' with ')
        self.val_m2 = QtGui.QLineEdit('2', self)

        l_merge = QtGui.QHBoxLayout()
        l_merge.addWidget(self.b2)
        l_merge.addWidget(t1)
        l_merge.addWidget(self.val_m1)
        l_merge.addWidget(t2)
        l_merge.addWidget(self.val_m2)

        self.g_merge = QGroupBoxB()
        self.g_merge.setLayout(l_merge)
        self.g_merge.setTitle('Editing regions')
        self.g_merge.setVisible(False)

        # Statistics

        self.b_stat = QtGui.QPushButton('Run', self)
        self.b_stat.clicked.connect(self.generate_voxel_stats)

        self.tabmod1 = QtGui.QStandardItemModel()
        self.tab1 = QtGui.QTableView()
        self.tab1.resizeColumnsToContents()
        self.tab1.setModel(self.tabmod1)

        l_stats = QtGui.QHBoxLayout()
        l_stats.addWidget(self.b_stat)
        l_stats.addWidget(self.tab1)

        self.g_stats = QGroupBoxB()
        self.g_stats.setLayout(l_stats)
        self.g_stats.setTitle('Voxel count')
        self.g_stats.setVisible(False)

        # Outer layout
        l1 = QtGui.QVBoxLayout()
        l1.addLayout(lhelp)
        l1.addLayout(l05)
        l1.addWidget(space1)
        l1.addWidget(self.b4)
        l1.addWidget(self.g_merge)
        l1.addWidget(self.g_stats)
        l1.addStretch(1)
        self.setLayout(l1)

        # Initialisation
        # Volume management widget
        self.km = None

        self.voxel_count_slice = []
        self.voxel_count = []

    def run_clustering(self):
        """
        Run kmeans clustering using normalised PCA modes
        """

        # Check that pkmodelling can be run
        if self.ivm.vol is None:
            error_dialog("No data loaded")
            return

        if self.ivm.current_roi is None:
            error_dialog("No ROI loaded - required for overlay clustering")
            return

        if self.ivm.current_overlay is None:
            error_dialog("No overlay loaded")
            return

        if self.ivm.current_overlay.ndims != 3:
            error_dialog("Cannot run clustering on 4d overlays")
            return

        # Disable button
        self.b1.setDown(1)
        self.b1.setDisabled(1)

        img1 = self.ivm.current_overlay.data
        roi1 = self.ivm.current_roi.data

        self.km = KMeans3D(img1, region1=roi1)

        self.km.run_single(n_clusters=self.combo.value())

        self.label1, self.label1_cent = self.km.get_label_image()

        self.ivm.add_roi(Roi(name="Overlay clusters", data=self.label1), make_current=True)
        self.sig_emit_reset.emit(1)
        # This previous step should generate a color map which can then be used in the following steps.

        print("Done!")
        # enable button again
        self.b1.setDown(0)
        self.b1.setDisabled(0)

    def _generate_cluster_means(self):

        """
        Generate the mean curves for each cluster
        Returns:

        """
        nimage = np.zeros(self.ivm.vol.shape)
        nimage[self.km.region1] = self.km.voxel_se

        self.labs_un = np.unique(self.label1)
        self.labs_un = self.labs_un[self.labs_un != 0]
        self.label1_cent = np.zeros((self.labs_un.max()+1, nimage.shape[-1]))

        cc = 0
        for ii in self.labs_un:

            mean1 = np.median(nimage[self.label1 == ii], axis=0)
            self.label1_cent[ii, :] = mean1

    def run_merge(self):
        """

        Returns:

        """

        m1 = int(self.val_m1.text())
        m2 = int(self.val_m2.text())

        # relabel
        self.label1[self.label1 == m1] = m2

        # signal the change
        self.ivm.add_roi(Roi(name="clusters", data=self.label1), make_current=True)
        self.sig_emit_reset.emit(1)
        print("Merged")

    def calculate_voxel_count(self):
        """

        Returns:

        """
        self.voxel_count_slice = []
        self.voxel_count = []

        self._generate_cluster_means()

        for ii in self.labs_un:
            # Slice 1 count
            self.voxel_count_slice.append(np.sum(self.label1[:, :, self.ivm.cim_pos[2]] == ii))

            # Volume count
            self.voxel_count.append(np.sum(self.label1 == ii))


    @QtCore.Slot()
    def generate_voxel_stats(self):
        """
        Some initial analysis
        (temporary location before moving analysis into a separate framework)
        """

        # get analysis
        self.calculate_voxel_count()
        self.tabmod1.clear()

        self.tabmod1.setVerticalHeaderItem(0, QtGui.QStandardItem("Slice"))
        self.tabmod1.setVerticalHeaderItem(1, QtGui.QStandardItem("Volume"))

        for cc, ii in enumerate(self.labs_un):

            self.tabmod1.setHorizontalHeaderItem(cc, QtGui.QStandardItem("Region " + str(ii)))
            self.tabmod1.setItem(0, cc, QtGui.QStandardItem(str(np.around(self.voxel_count_slice[cc]))))
            self.tabmod1.setItem(1, cc, QtGui.QStandardItem(str(np.around(self.voxel_count[cc]))))
        
    def show_options(self):
        if self.g_merge.isVisible():
            self.g_merge.setVisible(False)
            self.g_stats.setVisible(False)
        else:
            self.g_merge.setVisible(True)
            self.g_stats.setVisible(True)



