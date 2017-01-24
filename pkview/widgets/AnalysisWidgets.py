"""

Author: Benjamin Irving (benjamin.irv@gmail.com)
Copyright (c) 2013-2015 University of Oxford, Benjamin Irving

"""

from __future__ import division, unicode_literals, print_function, absolute_import

import numpy as np
import pyqtgraph as pg
from PySide import QtCore, QtGui
from scipy.interpolate import UnivariateSpline

from pkview.QtInherit.QtSubclass import QGroupBoxB
from pkview.ImageView import PickMode
from ..QtInherit import HelpButton

class SEPlot:
    def __init__(self, sig, **kwargs):
        self.sig = np.copy(np.array(sig, dtype=np.double))
        self.pen = kwargs.get("pen", (255, 255, 255))
        self.symbolBrush = kwargs.get("symbolBrush", (200, 200, 200))
        self.symbolPen = kwargs.get("symbolPen", "k")
        self.symbolSize = kwargs.get("symbolSize", 5.0)

        self.line = None
        self.pts = None

    def plot(self, plotwin, sigenh, smooth, xres):
        if sigenh:
            m = np.mean(self.sig[:3])
            pt_values = self.sig / m - 1
        else:
            pt_values = self.sig

        if smooth:
            wsize = 3
            cwin1 = np.ones(wsize)/wsize
            r1 = range(len(pt_values))
            #tolerance does not scale by data value to scale input
            s = UnivariateSpline(r1, pt_values/pt_values.max(), s=0.1, k=4)
            knots1 = s.get_knots()
            print("Number of knots in B-spline smoothing: ", len(knots1))
            line_values = s(r1)*pt_values.max()
        else:
            line_values = pt_values

        xx = xres * np.arange(len(pt_values))
        if self.line is not None:
            self.remove(plotwin)

        self.line = plotwin.plot(xx, line_values, pen=self.pen, width=4.0)
        self.pts = plotwin.plot(xx, pt_values, pen=None, symbolBrush=self.symbolBrush, symbolPen=self.symbolPen,
                                symbolSize=self.symbolSize)

    def remove(self, plotwin):
        if self.line is not None:
            plotwin.removeItem(self.line)
            plotwin.removeItem(self.pts)
            self.line, self.pts = None, None

class SECurve(QtGui.QWidget):

    """
    Side widgets for plotting SE curves
    """

    sig_add_pnt = QtCore.Signal(tuple)
    sig_clear_pnt = QtCore.Signal(bool)

    def __init__(self, local_file_path):
        super(SECurve, self).__init__()

        self.colors = {'grey':(200, 200, 200), 'red':(255, 0, 0), 'green':(0, 255, 0), 'blue':(0, 0, 255),
                       'orange':(255, 140, 0), 'cyan':(0, 255, 255), 'brown':(139, 69, 19)}

        #Local file path
        self.local_file_path = local_file_path

        self.setStatusTip("Click points on the 4D volume to see time curve")

        title1 = QtGui.QLabel("<font size=5> Voxelwise analysis </font>")
        bhelp = HelpButton(self, self.local_file_path)
        lhelp = QtGui.QHBoxLayout()
        lhelp.addWidget(title1)
        lhelp.addStretch(1)
        lhelp.addWidget(bhelp)

        self.win1 = pg.GraphicsWindow(title="Basic plotting examples")
        self.win1.setVisible(True)
        self.win1.setBackground(background=None)
        self.p1 = None

        # Take a local region mean to reduce noise
        self.cb1 = QtGui.QCheckBox('Smooth curves', self)
        self.cb1.stateChanged.connect(self.replot_graph)

        #cb1.toggle()
        self.cb2 = QtGui.QCheckBox('Multiple curves', self)
        self.cb2.stateChanged.connect(self.multi_curves)

        #Signal enhancement (normalised)
        self.cb3 = QtGui.QCheckBox('Signal enhancement', self)
        self.cb3.stateChanged.connect(self.replot_graph)

        #Show mean
        self.cb4 = QtGui.QCheckBox('Show mean', self)
        self.cb4.stateChanged.connect(self.replot_graph)

        #Clear curves button
        b1icon = QtGui.QIcon(self.local_file_path + '/icons/clear.svg')
        b1 = QtGui.QPushButton(self)
        b1.setIcon(b1icon)
        b1.setIconSize(QtCore.QSize(14, 14))
        b1.setToolTip("Clear curves")
        b1.clicked.connect(self.clear_graph)

        # input temporal resolution
        self.text1 = QtGui.QLineEdit('1.0', self)
        self.text1.editingFinished.connect(self.replot_graph)

        # Select plot color
        combo = QtGui.QComboBox(self)
        for col in self.colors.keys():
            combo.addItem(col)
        combo.setCurrentIndex(combo.findText("grey"))
        combo.activated[str].connect(self.plot_col_changed)
        combo.setToolTip("Set the color of the enhancement curve when a point is clicked on the image. "
                         "Allows visualisation of multiple enhancement curves of different colours")

        l03 = QtGui.QHBoxLayout()
        l03.addStretch(1)
        l03.addWidget(b1)

        space1 = QtGui.QLabel('')

        l01 = QtGui.QHBoxLayout()
        l01.addWidget(QtGui.QLabel('Plot color'))
        l01.addWidget(combo)
        l01.addStretch(1)

        l02 = QtGui.QHBoxLayout()
        l02.addWidget(QtGui.QLabel("Temporal resolution (s)"))
        l02.addWidget(self.text1)
        l02.addStretch(1)

        l04 = QtGui.QVBoxLayout()
        l04.addLayout(l01)
        l04.addLayout(l02)
        l04.addWidget(self.cb1)
        l04.addWidget(self.cb2)
        l04.addWidget(self.cb3)
        l04.addWidget(self.cb4)

        g01 = QGroupBoxB()
        g01.setLayout(l04)
        g01.setTitle('Curve options')

        l05 = QtGui.QHBoxLayout()
        l05.addWidget(g01)
        l05.addStretch()

        l1 = QtGui.QVBoxLayout()
        l1.addLayout(lhelp)
        l1.addLayout(l03)
        l1.addWidget(self.win1)
        l1.addWidget(space1)
        l1.addLayout(l05)
        l1.addStretch(1)
        self.setLayout(l1)

        self.ivm = None

    def add_image_management(self, ivm):
        self.ivm = ivm

    def add_image_view(self, ivl):
        self.ivl = ivl
        self.ivl.sig_sel_changed.connect(self.sel_changed)
        self.plot_col_changed("grey")
        self.clear_graph()

    def get_plots_by_color(self, col):
        return [plt for plt in self.plots.values() if plt.pen == col]

    def update_mean(self):
        for col in self.colors.values():
            plts = self.get_plots_by_color(col)
            if col in self.mean_plots:
                self.mean_plots[col].remove(self.p1)
            if len(plts) > 1:
                mean_values = np.stack([plt.sig for plt in plts], axis=1)
                mean_values = np.squeeze(np.mean(mean_values, axis=1))
                plt = SEPlot(mean_values, pen=pg.mkPen(col, style=QtCore.Qt.DashLine), symbolBrush=col, symbolPen='k', symbolSize=10.0)
                plt.plot(self.p1, self.cb3.isChecked(), self.cb1.isChecked(), float(self.text1.text()))
                self.mean_plots[col] = plt

    @QtCore.Slot()
    def replot_graph(self):
        self.win1.removeItem(self.p1)
        self.p1 = self.win1.addPlot(title="Signal enhancement curve")
        for plt in self.plots.values():
            plt.plot(self.p1, self.cb3.isChecked(), self.cb1.isChecked(), float(self.text1.text()))
        if self.cb4.isChecked():
            self.update_mean()

    @QtCore.Slot()
    def clear_graph(self):
        """
        Reset and clear the graph
        """
        self.win1.setVisible(True)
        if self.p1 is not None: self.win1.removeItem(self.p1)
        self.p1 = self.win1.addPlot(title="Signal enhancement curve")
        self.p1.setLabel('left', "Signal Enhancement")
        self.p1.setLabel('bottom', "Time", units='s')
        self.plots = {}
        self.mean_plots = {}
        # Reset the list of picked points
        if self.ivl.pickmode == PickMode.MULTIPLE:
            self.ivl.set_pickmode(PickMode.MULTIPLE)

    @QtCore.Slot()
    def multi_curves(self, state):
        if state:
            self.ivl.set_pickmode(PickMode.MULTIPLE)
        else:
            self.ivl.set_pickmode(PickMode.SINGLE)
            self.clear_graph()

    @QtCore.Slot(np.ndarray)
    def sel_changed(self, sel):
        """
        Get signal from mouse click
        """
        pickmode, points = sel
        for point in points:
            if point not in self.plots:
                if self.ivm.vol.ndims == 3:
                    # FIXME this should take into account which window the picked point was from
                    warnings.warning("3D image so just calculating cross image profile")
                    sig = self.ivm.vol.data[point[0], :, point[2]]
                elif self.ivm.vol.ndims == 4:
                    sig = self.ivm.vol.data[point[0], point[1], point[2], :]
                else:
                    warnings.warning("Image is not 3D or 4D")
                    continue
                plt = SEPlot(sig, pen=self.ivl.pick_col)
                plt.plot(self.p1, self.cb3.isChecked(), self.cb1.isChecked(), float(self.text1.text()))
                self.plots[point] = plt

        for point in self.plots.keys():
            if point not in points:
                self.plots[point].remove(self.p1)
                del self.plots[point]

        if self.cb4.isChecked(): self.update_mean()

    @QtCore.Slot(str)
    def plot_col_changed(self, text):
        self.ivl.pick_col = self.colors.get(text, (255, 255, 255))

class ColorOverlay1(QtGui.QWidget):

    """
    Color overlay interaction
    """

    # Signals
    # emit colormap choice
    sig_choose_cmap = QtCore.Signal(str)
    # emit alpha value
    sig_set_alpha = QtCore.Signal(int)
    # emit reset command
    sig_emit_reset = QtCore.Signal(bool)
    # emit a change in range
    sig_range_change = QtCore.Signal(int)

    def __init__(self, local_file_path):
        super(ColorOverlay1, self).__init__()

        self.setStatusTip("Load a ROI and overlay to analyse statistics")

        self.local_file_path = local_file_path

        title1 = QtGui.QLabel("<font size=5> Overlay statistics </font>")
        bhelp = HelpButton(self, self.local_file_path)
        lhelp = QtGui.QHBoxLayout()
        lhelp.addWidget(title1)
        lhelp.addStretch(1)
        lhelp.addWidget(bhelp)

        self.win1 = pg.GraphicsWindow()
        self.win1.setVisible(False)
        self.plt1 = self.win1.addPlot(title="Overlay histogram")

        # Analysis and volume management objects
        self.ia = None
        self.ivm = None

        self.tabmod1 = QtGui.QStandardItemModel()
        self.tabmod1ss = QtGui.QStandardItemModel()

        self.tab1 = QtGui.QTableView()
        self.tab1.resizeColumnsToContents()
        self.tab1.setModel(self.tabmod1)
        self.tab1.setVisible(False)

        self.tab1ss = QtGui.QTableView()
        self.tab1ss.resizeColumnsToContents()
        self.tab1ss.setModel(self.tabmod1ss)
        self.tab1ss.setVisible(False)

        l02 = QtGui.QHBoxLayout()
        self.butgen = QtGui.QPushButton("Show")
        self.butgen.setToolTip("Show standard statistics for the overlay values in each ROI")
        self.butgen.clicked.connect(self.show_overlay_stats)

        regenHbox3 = QtGui.QHBoxLayout()
        self.regenBtn3 = QtGui.QPushButton("Recalculate")
        self.regenBtn3.clicked.connect(self.generate_overlay_stats)
        regenHbox3.addWidget(self.regenBtn3)
        regenHbox3.addStretch(1)
        self.regenBtn3.setVisible(False)

        l02.addWidget(self.butgen)
        #l02.addWidget(buthide)
        l02.addStretch(1)

        l02ss = QtGui.QHBoxLayout()
        self.butgenss = QtGui.QPushButton("Show")
        self.butgenss.setToolTip("Show standard statistics for the current slice")
        self.butgenss.clicked.connect(self.show_overlay_stats_current_slice)

        regenHbox2 = QtGui.QHBoxLayout()
        self.regenBtn2 = QtGui.QPushButton("Recalculate")
        self.regenBtn2.clicked.connect(self.generate_overlay_stats_current_slice)
        regenHbox2.addWidget(self.regenBtn2)
        regenHbox2.addStretch(1)
        self.regenBtn2.setVisible(False)

        l02ss.addWidget(self.butgenss)
        #l02ss.addWidget(buthidess)
        l02ss.addStretch(1)

        l03 = QtGui.QHBoxLayout()

        self.butgen2 = QtGui.QPushButton("Show")
        self.butgen2.setToolTip("Show a histogram of the overlay values in each ROI")
        self.butgen2.clicked.connect(self.show_histogram)

        regenHbox = QtGui.QHBoxLayout()
        self.regenBtn = QtGui.QPushButton("Recalculate")
        self.regenBtn.clicked.connect(self.generate_histogram)
        regenHbox.addWidget(self.regenBtn)
        regenHbox.addStretch(1)
        self.regenBtn.setVisible(False)

        l03.addWidget(self.butgen2)
        #l03.addWidget(buthide2)
        l03.addStretch(1)

        nbinsLabel = QtGui.QLabel("Number of bins")
        l03.addWidget(nbinsLabel)

        self.nbinsSpin = QtGui.QSpinBox()
        self.nbinsSpin.setMaximum(100)
        self.nbinsSpin.setMinimum(5)
        self.nbinsSpin.setValue(30)
        l03.addWidget(self.nbinsSpin)

        minLabel = QtGui.QLabel("Min value")
        l03.addWidget(minLabel)

        self.minSpin = QtGui.QSpinBox()
        # Silly numbers for max and min because seems to be no way to have
        # a spin box without a range
        self.minSpin.setMaximum(100000000)
        self.minSpin.setMinimum(-100000000)
        l03.addWidget(self.minSpin)

        maxLabel = QtGui.QLabel("Max value")
        l03.addWidget(maxLabel)

        self.maxSpin = QtGui.QSpinBox()
        self.maxSpin.setMaximum(100000000)
        self.maxSpin.setMinimum(-100000000)
        l03.addWidget(self.maxSpin)

        l07 = QtGui.QVBoxLayout()
        l07.addLayout(l03)
        l07.addWidget(self.win1)
        l07.addLayout(regenHbox)
        l07.addStretch(1)

        # Hide histogram for the meanwhile
        f02 = QGroupBoxB()
        f02.setTitle('Overlay Histogram')
        f02.setLayout(l07)
        f02.setVisible(True)

        l08 = QtGui.QVBoxLayout()
        l08.addLayout(l02)
        l08.addWidget(self.tab1)
        l08.addLayout(regenHbox3)
        l08.addStretch(1)

        f03 = QGroupBoxB()
        f03.setTitle('Overlay Statistics')
        f03.setLayout(l08)

        l08ss = QtGui.QVBoxLayout()
        l08ss.addLayout(l02ss)
        l08ss.addWidget(self.tab1ss)
        l08ss.addLayout(regenHbox2)
        l08ss.addStretch(1)

        f03ss = QGroupBoxB()
        f03ss.setTitle('Overlay Statistics - Current Slice')
        f03ss.setLayout(l08ss)

        l1 = QtGui.QVBoxLayout()
        l1.addLayout(lhelp)
        l1.addWidget(f03)
        l1.addWidget(f03ss)

        l1.addWidget(f02)
        l1.addStretch(1)
        self.setLayout(l1)

    def show_overlay_stats(self):
        if self.tab1.isVisible():
            self.tab1.setVisible(False)
            self.regenBtn3.setVisible(False)
            self.butgen.setText("Show")
        else:
            self.generate_overlay_stats()
            self.tab1.setVisible(True)
            self.regenBtn3.setVisible(True)
            self.butgen.setText("Hide")

    def show_overlay_stats_current_slice(self):
        if self.tab1ss.isVisible():
            self.tab1ss.setVisible(False)
            self.regenBtn2.setVisible(False)
            self.butgenss.setText("Show")
        else:
            self.generate_overlay_stats_current_slice()
            self.tab1ss.setVisible(True)
            self.regenBtn2.setVisible(True)
            self.butgenss.setText("Hide")

    def add_analysis(self, image_analysis):
        """
        Reference to image analysis class
        """
        self.ia = image_analysis

    def update_spin_minmax(self, spin, range):
        spin.setMinimum(range[0])
        spin.setMaximum(range[1])

    def reset_spins(self):
        # Min and max set for overlay choice
        ov = self.ivm.current_overlay
        if ov:
            self.minSpin.setValue(ov.range[0])
            self.maxSpin.setValue(ov.range[1])

    def add_image_management(self, image_vol_management):
        """
        Adding image management
        """
        self.ivm = image_vol_management
        self.ivm.sig_current_overlay.connect(self.overlay_changed)
        self.reset_spins()

    def overlay_changed(self, overlay):
        """
        Update image data views
        """
        self.reset_spins()

    @QtCore.Slot()
    def generate_overlay_stats(self):
        # Clear the previous labels
        self.tabmod1.clear()

        # get analysis from analysis object
        stats1, roi_labels, hist1, hist1x = self.ia.get_roi_stats()

        self.tabmod1.setVerticalHeaderItem(0, QtGui.QStandardItem("Mean"))
        self.tabmod1.setVerticalHeaderItem(1, QtGui.QStandardItem("Median"))
        self.tabmod1.setVerticalHeaderItem(2, QtGui.QStandardItem("Variance"))
        self.tabmod1.setVerticalHeaderItem(3, QtGui.QStandardItem("Min"))
        self.tabmod1.setVerticalHeaderItem(4, QtGui.QStandardItem("Max"))

        for ii in range(len(stats1['mean'])):
            self.tabmod1.setHorizontalHeaderItem(ii, QtGui.QStandardItem("ROI label " + str(roi_labels[ii])))
            self.tabmod1.setItem(0, ii, QtGui.QStandardItem(str(np.around(stats1['mean'][ii], 2))))
            self.tabmod1.setItem(1, ii, QtGui.QStandardItem(str(np.around(stats1['median'][ii], 2))))
            self.tabmod1.setItem(2, ii, QtGui.QStandardItem(str(np.around(stats1['std'][ii], 2))))
            self.tabmod1.setItem(3, ii, QtGui.QStandardItem(str(np.around(stats1['min'][ii], 2))))
            self.tabmod1.setItem(4, ii, QtGui.QStandardItem(str(np.around(stats1['max'][ii], 2))))

    @QtCore.Slot()
    def generate_overlay_stats_current_slice(self):
        # Clear the previous labels
        self.tabmod1ss.clear()

        # get analysis from analysis object
        stats1, roi_labels, hist1, hist1x = self.ia.get_roi_stats_ss()

        self.tabmod1ss.setVerticalHeaderItem(0, QtGui.QStandardItem("Mean"))
        self.tabmod1ss.setVerticalHeaderItem(1, QtGui.QStandardItem("Median"))
        self.tabmod1ss.setVerticalHeaderItem(2, QtGui.QStandardItem("Variance"))
        self.tabmod1ss.setVerticalHeaderItem(3, QtGui.QStandardItem("Min"))
        self.tabmod1ss.setVerticalHeaderItem(4, QtGui.QStandardItem("Max"))

        for ii in range(len(stats1['mean'])):
            self.tabmod1ss.setHorizontalHeaderItem(ii, QtGui.QStandardItem("ROI label " + str(roi_labels[ii])))
            self.tabmod1ss.setItem(0, ii, QtGui.QStandardItem(str(np.around(stats1['mean'][ii], 2))))
            self.tabmod1ss.setItem(1, ii, QtGui.QStandardItem(str(np.around(stats1['median'][ii], 2))))
            self.tabmod1ss.setItem(2, ii, QtGui.QStandardItem(str(np.around(stats1['std'][ii], 2))))
            self.tabmod1ss.setItem(3, ii, QtGui.QStandardItem(str(np.around(stats1['min'][ii], 2))))
            self.tabmod1ss.setItem(4, ii, QtGui.QStandardItem(str(np.around(stats1['max'][ii], 2))))

    def show_histogram(self):
        if self.win1.isVisible():
            self.win1.setVisible(False)
            self.regenBtn.setVisible(False)
            self.butgen2.setText("Show")
        else:
            self.generate_histogram()
            self.win1.setVisible(True)
            self.regenBtn.setVisible(True)
            self.butgen2.setText("Hide")

    @QtCore.Slot()
    def generate_histogram(self):
        if (self.ivm.current_roi is None) or (self.ivm.current_overlay is None):
            m1 = QtGui.QMessageBox()
            m1.setWindowTitle("Histogram")
            m1.setText("Histogram requires a ROI and overlay to be loaded")
            m1.exec_()
            return

        # get analysis from analysis object
        bins = self.nbinsSpin.value()
        hist_range = (self.minSpin.value(), self.maxSpin.value())
        stats1, roi_labels, hist1, hist1x = self.ia.get_roi_stats(hist_bins=bins, hist_range=hist_range)

        self.win1.removeItem(self.plt1)
        self.plt1 = self.win1.addPlot(title="")

        for ii in range(len(stats1['mean'])):
            # FIXME This is basically duplicated from ImageView - not ideal
            val = roi_labels[ii]
            pencol = self.ivm.current_roi.get_pencol(val)
            curve = pg.PlotCurveItem(hist1x[ii], hist1[ii], stepMode=True, pen=pg.mkPen(pencol))
            self.plt1.addItem(curve)

    def __plot(self, values1):
        self.curve.setData(values1)

    @QtCore.Slot(np.ndarray)
    def sig_mouse(self, values1):
        self.__plot(values1)


