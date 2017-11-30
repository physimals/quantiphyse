"""

Author: Benjamin Irving (benjamin.irv@gmail.com)
Copyright (c) 2013-2015 University of Oxford, Benjamin Irving

"""

from __future__ import division, unicode_literals, absolute_import, print_function

import numpy as np
from sklearn.metrics import pairwise

import pyqtgraph as pg
from PySide import QtCore, QtGui

from quantiphyse.gui.widgets import QpWidget, HelpButton, BatchButton, OverlayCombo, RoiCombo, NumericOption
from quantiphyse.utils import get_pencol, debug

from .kmeans import KMeansPCAProcess, KMeans3DProcess

class ClusteringWidget(QpWidget):
    """
    Widget for doing K-means clustering on 3D or 4D data
    """

    def __init__(self, **kwargs):
        super(ClusteringWidget, self).__init__(name="Data Clustering", icon="clustering", desc="Generate clusters from 3D or 4D data", group="DEFAULT", position=2, **kwargs)

    def init_ui(self):
        self.process_4d = KMeansPCAProcess(self.ivm)
        self.process_3d = KMeans3DProcess(self.ivm)
        layout = QtGui.QVBoxLayout()
        self.setLayout(layout)

        hbox = QtGui.QHBoxLayout()
        hbox.addWidget(QtGui.QLabel('<font size="5">Data Clustering</font>'))
        hbox.addStretch(1)
        hbox.addWidget(BatchButton(self))
        hbox.addWidget(HelpButton(self, "curve_cluster"))
        layout.addLayout(hbox)
        
        DESC = """
<i>Performs clustering of 3D or 4D data using the K-means algorithm.
PCA reduction is used on 4D data to extract representative curves
"""
        desc = QtGui.QLabel(DESC)
        desc.setWordWrap(True)
        layout.addWidget(desc)

        gbox = QtGui.QGroupBox()
        gbox.setTitle('Clustering options')

        grid = QtGui.QGridLayout()
        gbox.setLayout(grid)

        # Data to cluster
        grid.addWidget(QtGui.QLabel("Data"), 0, 0)
        self.data_combo = OverlayCombo(self.ivm)
        self.data_combo.currentIndexChanged.connect(self.data_changed)
        grid.addWidget(self.data_combo, 0, 1)

        grid.addWidget(QtGui.QLabel("ROI"), 1, 0)
        self.roi_combo = RoiCombo(self.ivm, none_option=True)
        grid.addWidget(self.roi_combo, 1, 1)

        # Number of clusters inside the ROI
        self.n_clusters = NumericOption("Number of clusters", grid, xpos=2, ypos=0, minval=2, maxval=20, default=4, intonly=True)
        self.n_clusters.spin.setToolTip("")

        # Number of PCA modes
        self.n_pca = NumericOption("Number of PCA modes", grid, xpos=2, ypos=1, minval=1, maxval=10, default=3, intonly=True)
        self.n_pca.spin.setToolTip("")

        # Output ROI name
        grid.addWidget(QtGui.QLabel("Output name"), 2, 0)
        self.output_name = QtGui.QLineEdit("clusters")
        grid.addWidget(self.output_name, 2, 1)
        layout.addWidget(gbox)

        # Run clustering button
        hbox = QtGui.QHBoxLayout()
        self.run_btn = QtGui.QPushButton('Run', self)
        self.run_btn.clicked.connect(self.run_clustering)
        hbox.addWidget(self.run_btn)
        hbox.addStretch(1)
        layout.addLayout(hbox)

        # Plot window, showing representative curves for 4D data
        self.show_curves_btn = QtGui.QPushButton('Show representative curves', self)
        self.show_curves_btn.clicked.connect(self.show_curves)
        layout.addWidget(self.show_curves_btn)
        self.plotwin = pg.GraphicsLayoutWidget()
        self.plotwin.setBackground(background=None)
        self.plot = self.plotwin.addPlot(title="Cluster representative curves")
        self.plotwin.setVisible(False)        
        layout.addWidget(self.plotwin)

        # Statistics
        self.show_count_btn = QtGui.QPushButton('Show voxel counts', self)
        self.show_count_btn.clicked.connect(self.show_counts)
        layout.addWidget(self.show_count_btn)
        self.stats_gbox = QtGui.QGroupBox()
        self.stats_gbox.setTitle('Voxel count')

        self.count_table = QtGui.QStandardItemModel()
        self.count_view = QtGui.QTableView()
        self.count_view.resizeColumnsToContents()
        self.count_view.setModel(self.count_table)

        hbox = QtGui.QHBoxLayout()
        hbox.addWidget(self.count_view)
        self.stats_gbox.setLayout(hbox)
        self.stats_gbox.setVisible(False)
        layout.addWidget(self.stats_gbox)

        # Merge regions
        self.show_merge_btn = QtGui.QPushButton('Show merge options', self)
        self.show_merge_btn.clicked.connect(self.show_merge)
        layout.addWidget(self.show_merge_btn)
        
        self.merge_gbox = QtGui.QGroupBox()
        self.merge_gbox.setTitle('Merge regions')
        vbox = QtGui.QVBoxLayout()
        self.merge_gbox.setLayout(vbox)

        hbox = QtGui.QHBoxLayout()
        self.merge_btn = QtGui.QPushButton('Merge', self)
        self.merge_btn.clicked.connect(self.run_merge)
        hbox.addWidget(self.merge_btn)
        hbox.addWidget(QtGui.QLabel('Merge region '))
        self.merge_region1 = QtGui.QLineEdit('1', self)
        hbox.addWidget(self.merge_region1)
        hbox.addWidget(QtGui.QLabel(' with '))
        self.merge_region2 = QtGui.QLineEdit('2', self)
        hbox.addWidget(self.merge_region2)
        vbox.addLayout(hbox)

        hbox = QtGui.QHBoxLayout()
        self.auto_merge_btn = QtGui.QPushButton('AutoMerge', self)
        self.auto_merge_btn.clicked.connect(self.run_automerge)
        hbox.addWidget(self.auto_merge_btn)
        hbox.addStretch(1)
        vbox.addLayout(hbox)

        self.merge_gbox.setVisible(False)
        layout.addWidget(self.merge_gbox)

        layout.addStretch(1)

    def activate(self):
        self.ivl.sig_focus_changed.connect(self.focus_changed)
        self.ivm.sig_current_roi.connect(self.current_roi_changed)
        self.ivm.sig_main_data.connect(self.main_data_changed)
        self.data_changed()

    def deactivate(self):
        self.ivl.sig_focus_changed.disconnect(self.focus_changed)
        self.ivm.sig_current_roi.disconnect(self.current_roi_changed)
        self.ivm.sig_main_data.disconnect(self.main_data_changed)

    def current_roi_changed(self, roi):
        if roi is not None and roi.name != self.output_name.text():
            self.roi_combo.setCurrentIndex(self.roi_combo.findText(roi.name))
        
    def main_data_changed(self, data):
        if data is not None:
            idx = self.data_combo.findText(data.name)
        else:
            idx = 0
        self.data_combo.setCurrentIndex(idx)

    def data_changed(self):
        data = self.ivm.data.get(self.data_combo.currentText(), None)
        if data is not None:
            is4d = data.nvols > 1
            debug("Number of vols", data.nvols, is4d)
            self.n_pca.label.setVisible(is4d)
            self.n_pca.spin.setVisible(is4d)
            self.show_curves_btn.setVisible(is4d)
            self.plotwin.setVisible(is4d and self.plotwin.isVisible())
            self.auto_merge_btn.setEnabled(is4d)
        self.run_btn.setEnabled(data is not None)

    def focus_changed(self, pos):
        self.update_voxel_count()

    def show_curves(self):
        if self.plotwin.isVisible():
            self.plotwin.setVisible(False)
            self.show_curves_btn.setText("Show representative curves")
        else:
            self.plotwin.setVisible(True)
            self.show_curves_btn.setText("Hide representative curves")
            
    def show_counts(self):
        if self.stats_gbox.isVisible():
            self.stats_gbox.setVisible(False)
            self.show_count_btn.setText("Show voxel counts")
        else:
            self.stats_gbox.setVisible(True)
            self.show_count_btn.setText("Hide voxel counts")
        
    def show_merge(self):
        if self.merge_gbox.isVisible():
            self.merge_gbox.setVisible(False)
            self.show_merge_btn.setText("Show merge_options")
        else:
            self.merge_gbox.setVisible(True)
            self.show_merge_btn.setText("Hide merge options")
        
    def batch_options(self):
        options = {
                "data" : self.data_combo.currentText(),
                "roi" :  self.roi_combo.currentText(),
                "n-clusters" : self.n_clusters.spin.value(),
                "output-name" : self.output_name.text(),
                "invert-roi" : False,
            }

        if self.n_pca.label.isVisible():
            # 4D PCA options
            pname = "KMeansPCA"
            options["n-pca"] = self.n_pca.spin.value()
            options["reduction"] = "pca"
            options["norm-data"] = True
        else:
            pname = "KMeans"

        return pname, options

    def run_clustering(self):
        """
        Run kmeans clustering using normalised PCA modes
        """
        options = self.batch_options()[1]
        data = self.ivm.data.get(options["data"], None)
        if data.nvols > 1:
            p = self.process_4d
        else:
            p = self.process_3d

        try:
            self.run_btn.setDown(True)
            self.run_btn.setDisabled(True)
            p.run(options)
            self.update_voxel_count()
            self.update_plot()
        finally:
            # enable button again
            self.run_btn.setDown(False)
            self.run_btn.setDisabled(False)

    def update_voxel_count(self):
        self.count_table.clear()
        self.count_table.setVerticalHeaderItem(0, QtGui.QStandardItem("Slice"))
        self.count_table.setVerticalHeaderItem(1, QtGui.QStandardItem("Volume"))

        roi = self.ivm.rois.get(self.output_name.text(), None)
        if roi is not None:
            for cc, ii in enumerate(roi.regions):
                self.count_table.setHorizontalHeaderItem(cc, QtGui.QStandardItem("Region " + str(ii)))

                # Slice count
                voxel_count_slice = np.sum(roi.std()[:, :, self.ivm.cim_pos[2]] == ii)
                self.count_table.setItem(0, cc, QtGui.QStandardItem(str(np.around(voxel_count_slice))))

                # Volume count
                voxel_count = np.sum(roi.std() == ii)
                self.count_table.setItem(1, cc, QtGui.QStandardItem(str(np.around(voxel_count))))
        
    def reset_graph(self):
        """
        Reset and clear the graph
        """
        self.plotwin.removeItem(self.plot)
        self.plot = self.plotwin.addPlot(title="Cluster representative curves")
        self.plot.setLabel('left', "Signal Enhancement")
        self.plot.setLabel('bottom', self.opts.t_type, units=self.opts.t_unit)

    def update_plot(self):
        """
        Plot the cluster curves
        :return:
        """
        # Clear graph
        self.reset_graph()
        data = self.ivm.data.get(self.data_combo.currentText(), None)
        roi = self.ivm.rois.get(self.output_name.text(), None)
        if roi is not None and data is not None and data.nvols > 1:
            # Generate mean curve for each cluster
            self._generate_cluster_means(roi, data)

            # TODO need to work on fixing the scaling in a similar way to the normalisation of the overlay
            num_clus = roi.regions.max()
            le1 = self.plot.addLegend()

            # Plotting using single or multiple plots
            for idx, region in enumerate(roi.regions):
                if np.sum(self.curves[region]) == 0:
                    continue

                pencol = get_pencol(roi, region)
                name1 = "Region " + str(region)
                curve = self.plot.plot(pen=pencol, width=8.0, name=name1)
                xx = np.arange(len(self.curves[region]))
                curve.setData(xx, self.curves[region])

    def run_merge(self):
        m1 = int(self.merge_region1.text())
        m2 = int(self.merge_region2.text())
        self._merge(m1, m2)

    def run_automerge(self):
        # Use PCA features or true curves?
        # Mean features from each cluster
        # Distance matrix between features
        if len(self.curves) < 2: return

        curvemat = np.zeros((len(self.curves), self.ivm.main.nvols))
        row_region = {}
        idx = 0
        for region, curve in self.curves.items():
            row_region[idx] = region
            curvemat[idx, :] = curve
            idx += 1
        distmat = pairwise.euclidean_distances(curvemat)
        distmat[distmat == 0] = np.inf
        loc1 = np.where(distmat == distmat.min())[0]
        self._merge(row_region[loc1[0]], row_region[loc1[1]])

    def _generate_cluster_means(self, roi, data):
        """
        Generate the mean curves for each cluster
        Returns:
        """
        regions = roi.regions

        self.curves = {}
        for region in regions:
            mean = np.median(data.std()[roi.std() == region], axis=0)
            self.curves[region] = mean

    def _merge(self, m1, m2):
        roi = self.ivm.rois.get(self.output_name.text(), None)
        if roi is not None:
            roi = roi.std()
            roi[roi == m1] = m2

            # signal the change
            self.ivm.add_roi(roi, name=self.output_name.text(), make_current=True)

            # replot
            self.update_plot()
            self.update_voxel_count()

QP_WIDGETS = [ClusteringWidget]
QP_PROCESSES = [KMeans3DProcess, KMeansPCAProcess]