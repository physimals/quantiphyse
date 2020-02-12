"""
Quantiphyse - Widgets which perform data clustering

Copyright (c) 2013-2018 University of Oxford
"""

from __future__ import division, unicode_literals, absolute_import, print_function

import numpy as np
from sklearn.metrics import pairwise

import pyqtgraph as pg
try:
    from PySide import QtGui, QtCore, QtGui as QtWidgets
except ImportError:
    from PySide2 import QtGui, QtCore, QtWidgets

from quantiphyse.data import NumpyData
from quantiphyse.gui.widgets import QpWidget, OverlayCombo, RoiCombo, NumericOption, TitleWidget
from quantiphyse.utils import get_pencol

from .kmeans import KMeansProcess, MeanValuesProcess

class ClusteringWidget(QpWidget):
    """
    Widget for doing K-means clustering on 3D or 4D data
    """

    def __init__(self, **kwargs):
        super(ClusteringWidget, self).__init__(name="KMeans Clustering", icon="clustering", desc="Generate clusters from 3D or 4D data", group="Clustering", position=2, **kwargs)
        self.curves = {}

    def init_ui(self):
        self.process = KMeansProcess(self.ivm)
        layout = QtGui.QVBoxLayout()
        self.setLayout(layout)

        title = TitleWidget(self, help="cluster")
        layout.addWidget(title)
        
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
        self.data_combo.currentIndexChanged.connect(self._data_changed)
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
        self.show_curves_btn.clicked.connect(self._show_curves)
        layout.addWidget(self.show_curves_btn)
        self.plotwin = pg.GraphicsLayoutWidget()
        self.plotwin.setBackground(background=None)
        self.plot = self.plotwin.addPlot(title="Cluster representative curves")
        self.plot.setLabel('left', "Signal Enhancement")
        self.plotwin.setVisible(False)        
        layout.addWidget(self.plotwin)

        # Statistics
        self.show_count_btn = QtGui.QPushButton('Show voxel counts', self)
        self.show_count_btn.clicked.connect(self._show_counts)
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
        self.show_merge_btn.clicked.connect(self._show_merge)
        layout.addWidget(self.show_merge_btn)
        
        self.merge_gbox = QtGui.QGroupBox()
        self.merge_gbox.setTitle('Merge regions')
        vbox = QtGui.QVBoxLayout()
        self.merge_gbox.setLayout(vbox)

        hbox = QtGui.QHBoxLayout()
        self.merge_btn = QtGui.QPushButton('Merge', self)
        self.merge_btn.clicked.connect(self._run_merge)
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
        self.auto_merge_btn.clicked.connect(self._run_automerge)
        hbox.addWidget(self.auto_merge_btn)
        hbox.addStretch(1)
        vbox.addLayout(hbox)

        self.merge_gbox.setVisible(False)
        layout.addWidget(self.merge_gbox)

        layout.addStretch(1)

    def activate(self):
        self.ivl.sig_focus_changed.connect(self._focus_changed)
        self.ivm.sig_current_roi.connect(self._current_roi_changed)
        self.ivm.sig_main_data.connect(self._main_data_changed)
        self._data_changed()

    def deactivate(self):
        self.ivl.sig_focus_changed.disconnect(self._focus_changed)
        self.ivm.sig_current_roi.disconnect(self._current_roi_changed)
        self.ivm.sig_main_data.disconnect(self._main_data_changed)

    def _current_roi_changed(self, roi):
        if roi is not None and roi.name != self.output_name.text():
            self.roi_combo.setCurrentIndex(self.roi_combo.findText(roi.name))
        
    def _main_data_changed(self, data):
        if data is not None:
            idx = self.data_combo.findText(data.name)
        else:
            idx = 0
        self.data_combo.setCurrentIndex(idx)

    def _data_changed(self):
        data = self.ivm.data.get(self.data_combo.currentText(), None)
        if data is not None:
            is4d = data.nvols > 1
            self.debug("Number of vols: %i, 4d=%s", data.nvols, is4d)
            self.n_pca.label.setVisible(is4d)
            self.n_pca.spin.setVisible(is4d)
            self.show_curves_btn.setVisible(is4d)
            self.plotwin.setVisible(is4d and self.plotwin.isVisible())
            self.auto_merge_btn.setEnabled(is4d)
        self.run_btn.setEnabled(data is not None)

    def _focus_changed(self):
        self._update_voxel_count()

    def _show_curves(self):
        if self.plotwin.isVisible():
            self.plotwin.setVisible(False)
            self.show_curves_btn.setText("Show representative curves")
        else:
            self.plotwin.setVisible(True)
            self.show_curves_btn.setText("Hide representative curves")
            
    def _show_counts(self):
        if self.stats_gbox.isVisible():
            self.stats_gbox.setVisible(False)
            self.show_count_btn.setText("Show voxel counts")
        else:
            self.stats_gbox.setVisible(True)
            self.show_count_btn.setText("Hide voxel counts")
        
    def _show_merge(self):
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

        if options["roi"] == "<none>":
            del options["roi"]

        if self.n_pca.label.isVisible():
            # 4D PCA options
            options["n-pca"] = self.n_pca.spin.value()
            options["reduction"] = "pca"
            options["norm-data"] = True

        return "KMeans", options

    def run_clustering(self):
        """
        Run kmeans clustering using normalised PCA modes
        """
        options = self.batch_options()[1]

        self.process.run(options)
        self._update_voxel_count()
        if self.n_pca.label.isVisible():
            self.update_plot()     

    def _update_voxel_count(self):
        self.count_table.clear()
        self.count_table.setVerticalHeaderItem(0, QtGui.QStandardItem("Voxel count"))

        roi = self.ivm.rois.get(self.output_name.text(), None)
        if roi is not None:
            col_idx = 0
            for region, name in roi.regions.items():
                self.count_table.setHorizontalHeaderItem(col_idx, QtGui.QStandardItem(name))

                # Volume count
                voxel_count = np.sum(roi.raw() == region)
                self.count_table.setItem(0, col_idx, QtGui.QStandardItem(str(np.around(voxel_count))))
                col_idx += 1

    def update_plot(self):
        """
        Plot the cluster curves
        :return:
        """
        # Clear graph
        self.plot.clear()
        self.plot.setLabel('bottom', "Volume", "")
        if self.plot.legend is not None:
            # Work around pyqtgraph legend bug - the legend is recreated multiple times!
            # https://stackoverflow.com/questions/42792858/pyqtgraph-delete-persisting-legend-in-pyqt4-gui
            self.plot.legend.scene().removeItem(self.plot.legend)
        data = self.ivm.data.get(self.data_combo.currentText(), None)
        roi = self.ivm.rois.get(self.output_name.text(), None)
        if roi is not None and data is not None and data.nvols > 1:
            # Generate mean curve for each cluster
            self._generate_cluster_means(roi, data)

            self.plot.addLegend()

            # Plotting using single or multiple plots
            for region, name in roi.regions.items():
                if np.sum(self.curves[region]) == 0:
                    continue

                pencol = get_pencol(roi, region)
                curve = self.plot.plot(pen=pencol, width=8.0, name=name)
                xx = np.arange(len(self.curves[region]))
                curve.setData(xx, self.curves[region])

    def _run_merge(self):
        m1 = int(self.merge_region1.text())
        m2 = int(self.merge_region2.text())
        self._merge(m1, m2)

    def _run_automerge(self):
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
        self.curves = {}
        for region in roi.regions:
            roi_data = data.mask(roi, region=region, output_flat=True)
            mean = np.median(roi_data, axis=0)
            self.curves[region] = mean

    def _merge(self, m1, m2):
        roi = self.ivm.rois.get(self.output_name.text(), None)
        if roi is not None:
            roi_data = roi.raw()
            roi_data[roi_data == m1] = m2

            # signal the change
            self.ivm.add(NumpyData(roi_data, grid=roi.grid, name=self.output_name.text(), roi=True), make_current=True)

            # replot
            self.update_plot()
            self._update_voxel_count()

class MeanValuesWidget(QpWidget):
    """
    Convert a data + multi-level ROI into mean values data set
    """
    def __init__(self, **kwargs):
        super(MeanValuesWidget, self).__init__(name="Mean in ROI", icon="meanvals", 
                                               desc="Replace data with its mean value within each ROI region", 
                                               group="ROIs", **kwargs)

        layout = QtGui.QVBoxLayout()

        title = TitleWidget(self, "Generate Mean Values Data", help="mean_values")
        layout.addWidget(title)
        
        desc = QtGui.QLabel("This widget will convert the current data set into a "
                            "new data set in which each ROI region contains the mean "
                            "value for that region.\n\nThis is generally only useful for "
                            "multi-level ROIs such as clusters or supervoxels")
        desc.setWordWrap(True)
        layout.addWidget(desc)

        hbox = QtGui.QHBoxLayout()
        gbox = QtGui.QGroupBox()
        gbox.setTitle("Options")
        grid = QtGui.QGridLayout()
        gbox.setLayout(grid)
        
        grid.addWidget(QtGui.QLabel("Data"), 0, 0)
        self.ovl = OverlayCombo(self.ivm)
        self.ovl.currentIndexChanged.connect(self._data_changed)
        grid.addWidget(self.ovl, 0, 1)
        grid.addWidget(QtGui.QLabel("ROI regions"), 1, 0)
        self.roi = RoiCombo(self.ivm)
        grid.addWidget(self.roi, 1, 1)
        grid.addWidget(QtGui.QLabel("Output name"), 2, 0)
        self.output_name = QtGui.QLineEdit()
        grid.addWidget(self.output_name, 2, 1)

        btn = QtGui.QPushButton('Generate', self)
        btn.clicked.connect(self._generate)
        grid.addWidget(btn, 2, 0)
        hbox.addWidget(gbox)
        hbox.addStretch(1)
        layout.addLayout(hbox)
        layout.addStretch(1)
        self.setLayout(layout)

    def _data_changed(self):
        name = self.ovl.currentText()
        if name:
            self.output_name.setText(name + "_means")

    def batch_options(self):
        options = {
            "roi" : self.roi.currentText(),
            "data" : self.ovl.currentText(),
            "output-name" :  self.output_name.text()
        }
        return "MeanValues", options

    def _generate(self):
        options = self.batch_options()[1]

        if not options["data"]:
            QtGui.QMessageBox.warning(self, "No data selected", "Load data to generate mean values from", QtGui.QMessageBox.Close)
            return
        if not options["roi"]:
            QtGui.QMessageBox.warning(self, "No ROI selected", "Load an ROI for mean value regions", QtGui.QMessageBox.Close)
            return
        
        process = MeanValuesProcess(self.ivm)
        process.run(options)
