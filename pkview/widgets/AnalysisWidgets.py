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
from ..QtInherit import HelpButton


class SECurve(QtGui.QWidget):

    """
    Side widgets for plotting SE curves
    """

    sig_add_pnt = QtCore.Signal(tuple)
    sig_clear_pnt = QtCore.Signal(bool)

    def __init__(self, local_file_path):
        super(SECurve, self).__init__()

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
        self.p1 = self.win1.addPlot(title="Signal enhancement curve")
        self.reset_graph()

        # Take a local region mean to reduce noise
        self.cb1 = QtGui.QCheckBox('Smooth curves', self)
        self.cb1.stateChanged.connect(self.reset_graph)

        #cb1.toggle()
        self.cb2 = QtGui.QCheckBox('Multiple curves', self)
        self.cb2.stateChanged.connect(self.reset_graph)

        #Signal enhancement (normalised)
        self.cb3 = QtGui.QCheckBox('Signal enhancement', self)
        self.cb3.stateChanged.connect(self.reset_graph)

        #Show mean
        self.cb4 = QtGui.QCheckBox('Show mean', self)

        #Clear curves button
        b1icon = QtGui.QIcon(self.local_file_path + '/icons/clear.svg')
        b1 = QtGui.QPushButton(self)
        b1.setIcon(b1icon)
        b1.setIconSize(QtCore.QSize(14, 14))
        b1.setToolTip("Clear curves")
        b1.clicked.connect(self.reset_graph)

        # input temporal resolution
        self.text1 = QtGui.QLineEdit('1.0', self)
        self.text1.returnPressed.connect(self.replot_graph)

        # Select plot color
        combo = QtGui.QComboBox(self)
        combo.addItem("grey")
        combo.addItem("red")
        combo.addItem("blue")
        combo.addItem("green")
        combo.addItem("orange")
        combo.addItem("cyan")
        combo.addItem("brown")
        combo.activated[str].connect(self.emit_cchoice)
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

        # initial plot colour
        self.plot_color = (200, 200, 200)

        self.ivm = None

    def add_image_management(self, image_vol_management):
        """
        Adding image management
        """
        self.ivm = image_vol_management

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

        if self.cb1.isChecked() is True:
            wsize = 3
            cwin1 = np.ones(wsize)/wsize

            r1 = range(len(values1))
            #tolerance does not scale by data value to scale input
            s = UnivariateSpline(r1, values1/values1.max(), s=0.1, k=4)
            knots1 = s.get_knots()
            print("Number of knots in B-spline smoothing: ", len(knots1))
            values2 = s(r1)*values1.max()

            #Previous smoothing method using a convolution
            #values2 = np.convolve(values1, cwin1)
            #values2 = values2[1:-1]

        # Plotting using single or multiple plots
        if self.cb2.isChecked() is False:
            if self.curve1 is None:
                self.curve1 = self.p1.plot(pen=None, symbolBrush=(200, 200, 200), symbolPen='k', symbolSize=5.0)
                self.curve2 = self.p1.plot(pen=self.plot_color, width=4.0)
            self.curve2.setData(xx, values2, pen=self.plot_color)
            self.curve1.setData(xx, values1)

        # Multiple plots
        else:
            #Signal (add point to image
            self.sig_add_pnt.emit(self.plot_color)

            self.p1.plot(xx, values2, pen=self.plot_color, width=4.0)
            self.p1.plot(xx, values1, pen=None, symbolBrush=(200, 200, 200), symbolPen='k', symbolSize=5.0)

            # Plot mean curve as well
            if self.cb4.isChecked() is True:
                if self.curve_mean is None:
                    self.curve_mean = self.p1.plot(pen=(150, 0, 0), symbolBrush=(255, 0, 0), symbolPen='k')

                self.values2_mean[self.curve_count, :] = values2
                #self.curve_count += 1
                self.values2_mean = np.append(self.values2_mean, np.expand_dims(values2, axis=0), axis=0)
                self.curve_mean.setData(xx, np.squeeze(np.mean(self.values2_mean[1:], axis=0)))

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

        # Clear points on graph
        self.sig_clear_pnt.emit(True)

    @QtCore.Slot(np.ndarray)
    def sig_mouse(self, values1):

        """
        Get signal from mouse click
        """

        #Signal emit current enhancement curve to widget
        if len(self.ivm.img_dims) == 3:
            print("3D image so just calculating cross image profile")
            vec_sig = self.ivm.image[self.ivm.cim_pos[0], :, self.ivm.cim_pos[2]]
        elif len(self.ivm.img_dims) == 4:
            vec_sig = self.ivm.image[self.ivm.cim_pos[0], self.ivm.cim_pos[1], self.ivm.cim_pos[2], :]
        else:
            vec_sig = None
            print("Image is not 3D or 4D")

        self._plot(vec_sig)

    @QtCore.Slot(str)
    def emit_cchoice(self, text):
        if text == 'red':
            cvec = (255, 0, 0)
        elif text == 'grey':
            cvec = (200, 200, 200)
        elif text == 'green':
            cvec = (0, 255, 0)
        elif text == 'blue':
            cvec = (0, 0, 255)
        elif text == 'orange':
            cvec = (255, 140, 0)
        elif text == 'cyan':
            cvec = (0, 255, 255)
        elif text == 'brown':
            cvec = (139, 69, 19)
        else:
            cvec = (255, 255, 255)

        self.plot_color = cvec


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

        self.win1 = pg.GraphicsWindow(title="Basic plotting examples")
        self.win1.setVisible(False)
        self.plt1 = self.win1.addPlot(title="Signal enhancement curve")

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
        self.butgen.clicked.connect(self.generate_overlay_stats)
        #buthide = QtGui.QPushButton("Hide")
        #buthide.clicked.connect(self.hide_overlay_stats)

        l02.addWidget(self.butgen)
        #l02.addWidget(buthide)
        l02.addStretch(1)

        l02ss = QtGui.QHBoxLayout()
        self.butgenss = QtGui.QPushButton("Show")
        self.butgenss.setToolTip("Show standard statistics for the current slice")
        self.butgenss.clicked.connect(self.generate_overlay_stats_current_slice)
        #buthidess = QtGui.QPushButton("Hide")
        #buthidess.clicked.connect(self.hide_overlay_stats_current_slice)

        l02ss.addWidget(self.butgenss)
        #l02ss.addWidget(buthidess)
        l02ss.addStretch(1)

        l03 = QtGui.QHBoxLayout()

        self.butgen2 = QtGui.QPushButton("Show")
        self.butgen2.setToolTip("Show a histogram of the overlay values in each ROI")
        self.butgen2.clicked.connect(self.generate_histogram)
        #buthide2 = QtGui.QPushButton("Hide")
        #buthide2.clicked.connect(self.hide_histogram)

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
        l07.addStretch(1)

        # Hide histogram for the meanwhile
        f02 = QGroupBoxB()
        f02.setTitle('Overlay Histogram')
        f02.setLayout(l07)
        f02.setVisible(True)

        l08 = QtGui.QVBoxLayout()
        l08.addLayout(l02)
        l08.addWidget(self.tab1)
        l08.addStretch(1)

        f03 = QGroupBoxB()
        f03.setTitle('Overlay Statistics')
        f03.setLayout(l08)

        l08ss = QtGui.QVBoxLayout()
        l08ss.addLayout(l02ss)
        l08ss.addWidget(self.tab1ss)
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

    def hide_overlay_stats(self):
        self.tab1.setVisible(False)

    def hide_overlay_stats_current_slice(self):
        self.tab1ss.setVisible(False)

    def hide_histogram(self):
        self.win1.setVisible(False)

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
        ov_range = self.ivm.ov_range

        self.minSpin.setValue(ov_range[0])
        self.maxSpin.setValue(ov_range[1])

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
        """
        Some initial analysis
        (temporary location before moving analysis into a separate framework)
        """
        if self.tab1.isVisible():
            self.tab1.setVisible(False)
            self.butgen.setText("Show")
        else:
            self.tab1.setVisible(True)
            self.butgen.setText("Hide")

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
        """
        Some initial analysis
        (temporary location before moving analysis into a separate framework)
        """

        if self.tab1ss.isVisible():
            self.tab1ss.setVisible(False)
            self.butgenss.setText("Show")
        else:
            self.tab1ss.setVisible(True)
            self.butgenss.setText("Hide")

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

    @QtCore.Slot()
    def generate_histogram(self):
        """
        Some initial analysis
        (temporary location before moving analysis into a separate framework)
        """

        if self.win1.isVisible():
            self.win1.setVisible(False)
            self.butgen2.setText("Show")
        else:

            if (self.ivm.get_current_roi() is None) or (self.ivm.get_current_overlay() is None):
                m1 = QtGui.QMessageBox()
                m1.setWindowTitle("Histogram")
                m1.setText("Histogram requires a ROI and overlay to be loaded")
                m1.exec_()
                return

            self.win1.setVisible(True)
            self.butgen2.setText("Hide")

            # get analysis from analysis object
            bins = self.nbinsSpin.value()
            hist_range = (self.minSpin.value(), self.maxSpin.value())
            stats1, roi_labels, hist1, hist1x = self.ia.get_roi_stats(hist_bins=bins, hist_range=hist_range)

            self.win1.removeItem(self.plt1)
            self.plt1 = self.win1.addPlot(title="")

            for ii in range(len(stats1['mean'])):
                # FIXME This is basically duplicated from ImageView - not ideal
                val = roi_labels[ii]
                lutval = (255 * float(val)) / max(roi_labels)
                pencol = self.ivm.roi_cmap[lutval]
                pencol[3] = 150
                curve = pg.PlotCurveItem(hist1x[ii], hist1[ii], stepMode=True, brush=pg.mkBrush(pencol),
                                         fillLevel=0, pen=pg.mkPen((255, 255, 255)))
                self.plt1.addItem(curve)

    def __plot(self, values1):
        self.curve.setData(values1)

    @QtCore.Slot(np.ndarray)
    def sig_mouse(self, values1):
        self.__plot(values1)

    @QtCore.Slot(str)
    def emit_cmap(self, text):
        self.sig_choose_cmap.emit(text)

    @QtCore.Slot(int)
    def emit_alpha(self, val1):
        self.sig_set_alpha.emit(val1)

    @QtCore.Slot(int)
    def emit_ov_range_change(self, val1):
        self.ivm.ov_range = [self.ov_min.value(), self.ov_max.value()]
        self.sig_range_change.emit(val1)

