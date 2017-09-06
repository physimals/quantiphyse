"""

Author: Benjamin Irving (benjamin.irv@gmail.com)
Copyright (c) 2013-2015 University of Oxford, Benjamin Irving

"""

from __future__ import division, unicode_literals, absolute_import, print_function

import numpy as np
from PySide import QtCore, QtGui

from ..QtInherit.dialogs import error_dialog
from ..QtInherit import HelpButton, BatchButton
from ..analysis.kmeans import KMeans3DProcess
from . import QpWidget

#TODO Hide other buttons until the clustering is performed.


class OvCurveClusteringWidget(QpWidget):
    """
    Widget for clustering the tumour into various regions
    """

    # emit reset command
    sig_emit_reset = QtCore.Signal(bool)

    def __init__(self, **kwargs):
        super(OvCurveClusteringWidget, self).__init__(name="Overlay Cluster", icon="clustering", desc="Generate clusters from overlays", **kwargs)

        # self.setStatusTip("Click points on the 4D volume to see time curve")
        title1 = QtGui.QLabel("<font size=5> Clustering of the current overlay </font>")
        lhelp = QtGui.QHBoxLayout()
        lhelp.addWidget(title1)
        lhelp.addStretch(1)
        lhelp.addWidget(BatchButton(self))
        lhelp.addWidget(HelpButton(self, "overlay_cluster"))

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

        g01 = QtGui.QGroupBox()
        g01.setLayout(l04)
        g01.setTitle('Clustering options')

        l05 = QtGui.QHBoxLayout()
        l05.addLayout(l03)
        l05.addWidget(g01)

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

        self.g_merge = QtGui.QGroupBox()
        self.g_merge.setLayout(l_merge)
        self.g_merge.setTitle('Editing regions')

        # Statistics
        self.tabmod1 = QtGui.QStandardItemModel()
        self.tab1 = QtGui.QTableView()
        self.tab1.resizeColumnsToContents()
        self.tab1.setModel(self.tabmod1)

        l_stats = QtGui.QHBoxLayout()
        l_stats.addWidget(self.tab1)

        self.g_stats = QtGui.QGroupBox()
        self.g_stats.setLayout(l_stats)
        self.g_stats.setTitle('Voxel count')

        # Outer layout
        l1 = QtGui.QVBoxLayout()
        l1.addLayout(lhelp)
        l1.addLayout(l05)
        l1.addWidget(space1)
        l1.addWidget(self.g_merge)
        l1.addWidget(self.g_stats)
        l1.addStretch(1)
        self.setLayout(l1)

        # Initialisation
        # Volume management widget
        self.process = KMeans3DProcess(self.ivm)

    def activate(self):
        self.ivl.sig_focus_changed.connect(self.focus_changed)

    def deactivate(self):
        self.ivl.sig_focus_changed.disconnect(self.focus_changed)

    def focus_changed(self, pos):
        self.update_voxel_count()

    def batch_options(self):
        options = {
                "n-clusters" : self.combo.value(),
                "invert-roi" : False,
                "output-name" : "overlay_clusters"
            }
        return "KMeans3D", options

    def run_clustering(self):
        """
        Run kmeans clustering on an overlay
        """
        if self.ivm.vol is None:
            error_dialog("No data loaded")
            return

        if self.ivm.current_roi is None:
            error_dialog("No ROI loaded - required for overlay clustering")
            return

        if self.ivm.current_overlay is None:
            error_dialog("No overlay loaded")
            return

        if self.ivm.current_overlay.ndim != 3:
            error_dialog("Cannot run clustering on 4d overlays")
            return

        # Disable button
        self.b1.setDown(1)
        self.b1.setDisabled(1)

        try:
            self.process.run(self.batch_options()[1])
            self.update_voxel_count()
        finally:
            # enable button again
            self.b1.setDown(0)
            self.b1.setDisabled(0)

    def run_merge(self):
        m1 = int(self.val_m1.text())
        m2 = int(self.val_m2.text())

        # relabel
        roi = self.ivm.rois["overlay_clusters"]
        roi[roi == m1] = m2
        
        # signal the change
        self.ivm.add_roi("overlay_clusters", roi, make_current=True)
        self.update_voxel_count()

    def update_voxel_count(self):
        self.tabmod1.clear()
        self.tabmod1.setVerticalHeaderItem(0, QtGui.QStandardItem("Slice"))
        self.tabmod1.setVerticalHeaderItem(1, QtGui.QStandardItem("Volume"))

        if "overlay_clusters" not in self.ivm.rois: return
        
        roi = self.ivm.rois["overlay_clusters"]
        for cc, ii in enumerate(roi.regions):
            self.tabmod1.setHorizontalHeaderItem(cc, QtGui.QStandardItem("Region " + str(ii)))

            # Slice count
            voxel_count_slice = np.sum(roi[:, :, self.ivm.cim_pos[2]] == ii)
            self.tabmod1.setItem(0, cc, QtGui.QStandardItem(str(np.around(voxel_count_slice))))

            # Volume count
            voxel_count = np.sum(roi == ii)
            self.tabmod1.setItem(1, cc, QtGui.QStandardItem(str(np.around(voxel_count))))


