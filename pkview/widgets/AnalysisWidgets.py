"""

Author: Benjamin Irving (benjamin.irv@gmail.com)
Copyright (c) 2013-2015 University of Oxford, Benjamin Irving

"""

from __future__ import division, unicode_literals, print_function, absolute_import

import sys
import warnings

import numpy as np
import pyqtgraph as pg
from PySide import QtCore, QtGui
from scipy.interpolate import UnivariateSpline

from . import PkWidget
from ..ImageView import PickMode
from ..utils import get_icon, copy_table
from ..QtInherit import HelpButton
from ..analysis.misc import CalcVolumesProcess, SimpleMathsProcess, OverlayStatisticsProcess, RadialProfileProcess, HistogramProcess

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

class SECurve(PkWidget):
    """
    Plots SE curve for current main data
    """
    sig_add_pnt = QtCore.Signal(tuple)
    sig_clear_pnt = QtCore.Signal(bool)

    def __init__(self, **kwargs):
        super(SECurve, self).__init__(name="Voxel Analysis", icon="voxel", desc="Display signal enhancement curves", **kwargs)

        self.colors = {'grey':(200, 200, 200), 'red':(255, 0, 0), 'green':(0, 255, 0), 'blue':(0, 0, 255),
                       'orange':(255, 140, 0), 'cyan':(0, 255, 255), 'brown':(139, 69, 19)}

        self.setStatusTip("Click points on the 4D volume to see data curve")

        title = QtGui.QLabel("<font size=5> Voxelwise analysis </font>")
        bhelp = HelpButton(self, "curve_compare")
        lhelp = QtGui.QHBoxLayout()
        lhelp.addWidget(title)
        lhelp.addStretch(1)
        lhelp.addWidget(bhelp)

        self.win1 = pg.GraphicsLayoutWidget()
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
        b1icon = QtGui.QIcon(get_icon("clear"))
        b1 = QtGui.QPushButton(self)
        b1.setIcon(b1icon)
        b1.setIconSize(QtCore.QSize(14, 14))
        b1.setToolTip("Clear curves")
        b1.clicked.connect(self.clear_all)

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

        l04 = QtGui.QVBoxLayout()
        l04.addLayout(l01)
        l04.addWidget(self.cb1)
        l04.addWidget(self.cb2)
        l04.addWidget(self.cb3)
        l04.addWidget(self.cb4)

        g01 = QtGui.QGroupBox()
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

        self.plot_col_changed("grey")
        self.multi = False
        self.clear_all()

    def activate(self):
        self.ivl.sig_sel_changed.connect(self.sel_changed)
        self.clear_all()

    def deactivate(self):
        self.ivl.sig_sel_changed.disconnect(self.sel_changed)

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
                plt.plot(self.p1, self.cb3.isChecked(), self.cb1.isChecked(), self.opts.t_res)
                self.mean_plots[col] = plt

    def clear_graph(self):
        """
        Clear the graph but don't delete data
        """
        self.win1.setVisible(True)
        if self.p1 is not None: self.win1.removeItem(self.p1)
        self.p1 = self.win1.addPlot(title="Signal enhancement curve")
        if self.ivm.vol is not None:
            if self.cb3.isChecked():
                self.p1.setLabel('left', "%s (Signal Enhancement)" % self.ivm.vol.name)
            else:
                self.p1.setLabel('left', self.ivm.vol.name)
            
        self.p1.setLabel('bottom', self.opts.t_type, units=self.opts.t_unit)

    def options_changed(self, opts):
        self.replot_graph()

    @QtCore.Slot()
    def replot_graph(self):
        self.clear_graph()
        for plt in self.plots.values():
            plt.plot(self.p1, self.cb3.isChecked(), self.cb1.isChecked(), self.opts.t_res)
        if self.cb4.isChecked():
            self.update_mean()

    @QtCore.Slot()
    def clear_all(self):
        """
        Clear the graph and all data
        """
        self.clear_graph()
        self.plots = {}
        self.mean_plots = {}
        # Reset the list of picked points
        if self.multi:
            self.ivl.set_picker(PickMode.MULTIPLE)
            self.ivl.picker.col = self.col
        else:
            self.ivl.set_picker(PickMode.SINGLE)
            self.ivl.picker.col = self.col

    @QtCore.Slot()
    def multi_curves(self, state):
        self.multi = state
        self.clear_all()

    @QtCore.Slot(np.ndarray)
    def sel_changed(self, picker):
        """
        Get signal from mouse click
        """
        allpoints = []
        for col, points in picker.points.items():
            allpoints += points
            for point in points:
                if point not in self.plots:
                    if self.ivm.vol.ndim == 3:
                        # FIXME this should take into account which window the picked point was from
                        warnings.warn("3D image so just calculating cross image profile")
                        sig = self.ivm.vol[point[0], :, point[2]]
                    elif self.ivm.vol.ndim == 4:
                        sig = self.ivm.vol[point[0], point[1], point[2], :]
                    else:
                        warnings.warn("Image is not 3D or 4D")
                        continue
                    plt = SEPlot(sig, pen=col)
                    plt.plot(self.p1, self.cb3.isChecked(), self.cb1.isChecked(), self.opts.t_res)
                    self.plots[point] = plt

        for point in self.plots.keys():
            if point not in allpoints:
                self.plots[point].remove(self.p1)
                del self.plots[point]

        if self.cb4.isChecked(): self.update_mean()

    @QtCore.Slot(str)
    def plot_col_changed(self, text):
        self.col = self.colors.get(text, (255, 255, 255))
        self.ivl.picker.col = self.col

class OverlayStatistics(PkWidget):

    """
    Color overlay interaction
    """
    CURRENT_OVERLAY = 0
    ALL_OVERLAYS = 1

    # Signals
    # emit colormap choice
    sig_choose_cmap = QtCore.Signal(str)
    # emit alpha value
    sig_set_alpha = QtCore.Signal(int)
    # emit reset command
    sig_emit_reset = QtCore.Signal(bool)
    # emit a change in range
    sig_range_change = QtCore.Signal(int)

    def __init__(self, **kwargs):
        super(OverlayStatistics, self).__init__(name="Overlay Statistics", desc="Display statistics about the current overlay", icon="edit", **kwargs)

    def init_ui(self):
        """ Set up UI controls here so as not to delay startup"""
        self.setStatusTip("Load a ROI and overlay to analyse statistics")

        self.process = OverlayStatisticsProcess(self.ivm)
        self.process_ss = OverlayStatisticsProcess(self.ivm)
        self.process_rp = RadialProfileProcess(self.ivm)
        self.process_hist = HistogramProcess(self.ivm)
        
        l1 = QtGui.QVBoxLayout()

        hbox = QtGui.QHBoxLayout()
        title1 = QtGui.QLabel("<font size=5>Overlay statistics: </font>")
        hbox.addWidget(title1)
        self.mode_combo = QtGui.QComboBox()
        self.mode_combo.addItem("Current overlay")
        self.mode_combo.addItem("All overlays")
        self.mode_combo.currentIndexChanged.connect(self.mode_changed)
        hbox.addWidget(self.mode_combo)
        self.ovl_selection = self.CURRENT_OVERLAY
        hbox.addStretch(1)
        bhelp = HelpButton(self, "overlay_stats")
        hbox.addWidget(bhelp)
        l1.addLayout(hbox)

        self.win1 = pg.GraphicsLayoutWidget()
        self.win1.setVisible(False)
        self.plt1 = self.win1.addPlot(title="Overlay histogram")

        self.tab1 = QtGui.QTableView()
        self.tab1.resizeColumnsToContents()
        self.tab1.setModel(self.process.model)
        self.tab1.setVisible(False)

        self.tab1ss = QtGui.QTableView()
        self.tab1ss.resizeColumnsToContents()
        self.tab1ss.setModel(self.process_ss.model)
        self.tab1ss.setVisible(False)

        l02 = QtGui.QHBoxLayout()
        self.butgen = QtGui.QPushButton("Show")
        self.butgen.setToolTip("Show standard statistics for the overlay values in each ROI")
        self.butgen.clicked.connect(self.show_overlay_stats)
        l02.addWidget(self.butgen)
        self.copy_btn = QtGui.QPushButton("Copy")
        self.copy_btn.clicked.connect(self.copy_stats)
        self.copy_btn.setVisible(False)
        l02.addWidget(self.copy_btn)
        l02.addStretch(1)

        l02ss = QtGui.QHBoxLayout()
        self.butgenss = QtGui.QPushButton("Show")
        self.butgenss.setToolTip("Show standard statistics for the current slice")
        self.butgenss.clicked.connect(self.show_overlay_stats_current_slice)
        l02ss.addWidget(self.butgenss)
        self.slice_dir_label = QtGui.QLabel("Slice direction:")
        self.slice_dir_label.setVisible(False)
        l02ss.addWidget(self.slice_dir_label)
        self.sscombo = QtGui.QComboBox()
        self.sscombo.addItem("Axial")
        self.sscombo.addItem("Saggital")
        self.sscombo.addItem("Coronal")
        self.sscombo.setSizeAdjustPolicy(QtGui.QComboBox.AdjustToContents)
        self.sscombo.currentIndexChanged.connect(self.update)
        self.sscombo.setVisible(False)
        l02ss.addWidget(self.sscombo)
        self.copy_btn_ss = QtGui.QPushButton("Copy")
        self.copy_btn_ss.clicked.connect(self.copy_stats_ss)
        self.copy_btn_ss.setVisible(False)
        l02ss.addWidget(self.copy_btn_ss)
        l02ss.addStretch(1)

        l03 = QtGui.QHBoxLayout()

        self.butgen2 = QtGui.QPushButton("Show")
        self.butgen2.setToolTip("Show a histogram of the overlay values in each ROI")
        self.butgen2.clicked.connect(self.show_histogram)

        regenHbox = QtGui.QHBoxLayout()
        self.regenBtn = QtGui.QPushButton("Recalculate")
        self.regenBtn.clicked.connect(self.update_histogram)
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

        self.minSpin = QtGui.QDoubleSpinBox()
        # Silly numbers for max and min because seems to be no way to have
        # a spin box without a range
        self.minSpin.setMaximum(100000000)
        self.minSpin.setMinimum(-100000000)
        l03.addWidget(self.minSpin)

        maxLabel = QtGui.QLabel("Max value")
        l03.addWidget(maxLabel)

        self.maxSpin = QtGui.QDoubleSpinBox()
        self.maxSpin.setMaximum(100000000)
        self.maxSpin.setMinimum(-100000000)
        l03.addWidget(self.maxSpin)

        l07 = QtGui.QVBoxLayout()
        l07.addLayout(l03)
        l07.addWidget(self.win1)
        l07.addLayout(regenHbox)
        l07.addStretch(1)

        # Hide histogram for the meanwhile
        f02 = QtGui.QGroupBox()
        f02.setTitle('Histogram')
        f02.setLayout(l07)

        l08 = QtGui.QVBoxLayout()
        l08.addLayout(l02)
        l08.addWidget(self.tab1)
        l08.addStretch(1)

        f03 = QtGui.QGroupBox()
        f03.setTitle('Summary Statistics')
        f03.setLayout(l08)

        l08ss = QtGui.QVBoxLayout()
        l08ss.addLayout(l02ss)
        l08ss.addWidget(self.tab1ss)
        l08ss.addStretch(1)

        f03ss = QtGui.QGroupBox()
        f03ss.setTitle('Summary Statistics - Slice')
        f03ss.setLayout(l08ss)

        l1.addWidget(f03)
        l1.addWidget(f03ss)

        l1.addWidget(f02)

        # Radial profile widgets
        box = QtGui.QGroupBox()
        box.setTitle("Radial Profile")
        vbox = QtGui.QVBoxLayout()
        box.setLayout(vbox)

        hbox = QtGui.QHBoxLayout()
        self.rp_btn = QtGui.QPushButton("Show")
        self.rp_btn.clicked.connect(self.show_radial_profile)
        hbox.addWidget(self.rp_btn)

        hbox.addWidget(QtGui.QLabel("Number of distance bins"))
        self.rp_nbins = QtGui.QSpinBox()
        self.rp_nbins.setMaximum(100)
        self.rp_nbins.setMinimum(5)
        self.rp_nbins.setValue(30)
        self.rp_nbins.valueChanged.connect(self.update_radial_profile)
        hbox.addWidget(self.rp_nbins)
       
        hbox.addStretch()
        vbox.addLayout(hbox)

        self.rp_win = pg.GraphicsLayoutWidget()
        self.rp_win.setVisible(False)
        self.rp_plt = self.rp_win.addPlot(title="Radial Profile", labels={'left' : 'Mean data value', 'bottom' : 'Distance (mm)'})
        self.rp_curve = pg.PlotCurveItem(pen=pg.mkPen(color=[192, 192, 192], width=2))
        self.rp_plt.addItem(self.rp_curve)
        vbox.addWidget(self.rp_win)
        l1.addWidget(box)

        l1.addStretch(1)
        self.setLayout(l1)

    def activate(self):
        self.ivm.sig_current_roi.connect(self.update_all)
        self.ivm.sig_all_overlays.connect(self.update_all)
        self.ivm.sig_current_overlay.connect(self.update_all)
        self.ivl.sig_focus_changed.connect(self.focus_changed)

    def deactivate(self):
        self.ivm.sig_current_roi.disconnect(self.update_all)
        self.ivm.sig_all_overlays.disconnect(self.update_all)
        self.ivm.sig_current_overlay.connect(self.update_all)
        self.ivl.sig_focus_changed.disconnect(self.focus_changed)

    def mode_changed(self, idx):
        self.ovl_selection = idx
        self.update_all()

    def focus_changed(self, pos):
        if self.rp_win.isVisible():
            self.update_radial_profile()
        if self.tab1ss.isVisible():
            self.update_overlay_stats_current_slice()

    def update_all(self):
        if self.ivm.current_overlay is None:
            self.mode_combo.setItemText(0, "Current overlay")
        else:
            self.mode_combo.setItemText(0, self.ivm.current_overlay.name)
            self.rp_plt.setLabel('left', self.ivm.current_overlay.name)

        self.update_histogram_spins()

        if self.rp_win.isVisible():
            self.update_radial_profile()
        if self.tab1.isVisible():
            self.update_overlay_stats()
        if self.tab1ss.isVisible():
            self.update_overlay_stats_current_slice()
        if self.win1.isVisible():
            self.update_histogram()

    def update_histogram_spins(self):
        # Min and max set for overlay choice
        ov = self.ivm.current_overlay
        if ov is not None:
            self.minSpin.setValue(ov.range[0])
            self.maxSpin.setValue(ov.range[1])
            self.minSpin.setDecimals(ov.dps)
            self.maxSpin.setDecimals(ov.dps)
            self.minSpin.setSingleStep(10**(1-ov.dps))
            self.maxSpin.setSingleStep(10**(1-ov.dps))

    def copy_stats(self):
        copy_table(self.process.model)

    def copy_stats_ss(self):
        copy_table(self.process_ss.model)
        
    def show_overlay_stats(self):
        if self.tab1.isVisible():
            self.tab1.setVisible(False)
            self.copy_btn.setVisible(False)
            self.butgen.setText("Show")
        else:
            self.update_overlay_stats()
            self.tab1.setVisible(True)
            self.copy_btn.setVisible(True)
            self.butgen.setText("Hide")

    def show_overlay_stats_current_slice(self):
        if self.tab1ss.isVisible():
            self.tab1ss.setVisible(False)
            self.slice_dir_label.setVisible(False)
            self.sscombo.setVisible(False)
            self.copy_btn_ss.setVisible(False)
            self.butgenss.setText("Show")
        else:
            self.update_overlay_stats_current_slice()
            self.tab1ss.setVisible(True)
            self.slice_dir_label.setVisible(True)
            self.sscombo.setVisible(True)
            self.copy_btn_ss.setVisible(True)
            self.butgenss.setText("Hide")

    def show_histogram(self):
        if self.win1.isVisible():
            self.win1.setVisible(False)
            self.regenBtn.setVisible(False)
            self.butgen2.setText("Show")
        else:
            self.update_histogram()
            self.win1.setVisible(True)
            self.regenBtn.setVisible(True)
            self.butgen2.setText("Hide")

    def show_radial_profile(self):
        if self.rp_win.isVisible():
            self.rp_win.setVisible(False)
            self.rp_btn.setText("Show")
        else:
            self.update_radial_profile()
            self.rp_win.setVisible(True)
            self.rp_btn.setText("Hide")

    def update_radial_profile(self):
        options = {"overlay" : self.ivm.current_overlay.name, 
                   "no-artifact" : True, "bins" : self.rp_nbins.value()}
        self.process_rp.run(options)
        self.rp_curve.setData(x=self.process_rp.xvals, y=self.process_rp.rp[self.ivm.current_overlay.name])

    def update_overlay_stats(self):
        self.populate_stats_table(self.process)

    def update_overlay_stats_current_slice(self):
        selected_slice = self.sscombo.currentIndex()
        self.populate_stats_table(self.process_ss, slice=selected_slice)

    def update_histogram(self):
        if self.ivm.current_overlay is None:
            error_dialog("No current overlay")
            return

        options = {"overlay" : self.ivm.current_overlay.name, 
                   "no-artifact" : True, "bins" : self.nbinsSpin.value(),
                   "min" : self.minSpin.value(), "max" : self.maxSpin.value()}
        self.process_hist.run(options)

        self.win1.removeItem(self.plt1)
        self.plt1 = self.win1.addPlot(title="")

        for ov_name in self.process_hist.hist:
            for region, yvals in self.process_hist.hist[ov_name].items():
                pencol = self.ivm.current_roi.get_pencol(region)
                curve = pg.PlotCurveItem(self.process_hist.edges, yvals, stepMode=True, pen=pg.mkPen(pencol, width=2))
            self.plt1.addItem(curve)

    def populate_stats_table(self, process, **options):
        if self.ivm.current_overlay is not None and self.ovl_selection == self.CURRENT_OVERLAY:
            options["overlay"] = self.ivm.current_overlay.name
        process.run(options)

class RoiAnalysisWidget(PkWidget):
    """
    Analysis of ROIs
    """
    def __init__(self, **kwargs):
        super(RoiAnalysisWidget, self).__init__(name="ROI Analysis", icon="roi", desc="Analysis of ROIs", **kwargs)
        
    def init_ui(self):
        self.process = CalcVolumesProcess(self.ivm)

        layout = QtGui.QVBoxLayout()
        self.setLayout(layout)

        hbox = QtGui.QHBoxLayout()
        hbox.addWidget(QtGui.QLabel('<font size="5">Roi Analysis</font>'))
        hbox.addStretch(1)
        hbox.addWidget(HelpButton(self))
        layout.addLayout(hbox)

        info = QtGui.QLabel("<i><br>Calculate size and volume of the current ROI<br></i>")
        info.setWordWrap(True)
        layout.addWidget(info)

        self.table = QtGui.QTableView()
        self.table.resizeColumnsToContents()
        self.table.setModel(self.process.model)
        layout.addWidget(self.table)

        hbox = QtGui.QHBoxLayout()
        self.copy_btn = QtGui.QPushButton("Copy")
        self.copy_btn.clicked.connect(self.copy_stats)
        hbox.addWidget(self.copy_btn)
        hbox.addStretch(1)
        layout.addLayout(hbox)
        layout.addStretch(1)

    def activate(self):
        self.ivm.sig_current_roi.connect(self.update)
        self.ivm.sig_all_rois.connect(self.update)
        self.update()

    def deactivate(self):
        self.ivm.sig_current_roi.disconnect(self.update)
        self.ivm.sig_all_rois.disconnect(self.update)

    def update(self):
        self.process.run({"no-artifact" : True})
        
    def copy_stats(self):
        copy_table(self.process.model)

MATHS_INFO = """
<i>Create data using simple mathematical operations on existing data
<br><br>
For example, if you have loaded data called 'mydata' and run modelling
to produce a model prediction 'modelfit', you could calculate the residuals
using:</i>
<br><br>
resids = mydata - modelfit
<br>
"""

class SimpleMathsWidget(PkWidget):
    def __init__(self, **kwargs):
        super(SimpleMathsWidget, self).__init__(name="Simple Maths", icon="maths", desc="Simple mathematical operations on data", **kwargs)

    def init_ui(self):
        layout = QtGui.QVBoxLayout()
        self.setLayout(layout)

        hbox = QtGui.QHBoxLayout()
        hbox.addWidget(QtGui.QLabel('<font size="5">Simple Maths</font>'))
        hbox.addStretch(1)
        hbox.addWidget(HelpButton(self))
        layout.addLayout(hbox)
        
        info = QtGui.QLabel(MATHS_INFO)
        info.setWordWrap(True)
        layout.addWidget(info)

        self.process = SimpleMathsProcess(self.ivm)

        hbox = QtGui.QHBoxLayout()
        hbox.addWidget(QtGui.QLabel("Set"))
        self.output_name_edit = QtGui.QLineEdit("newdata")
        self.output_name_edit.setFixedWidth(100)
        hbox.addWidget(self.output_name_edit)
        hbox.addWidget(QtGui.QLabel("="))
        self.proc_edit = QtGui.QLineEdit()
        hbox.addWidget(self.proc_edit)
        layout.addLayout(hbox)
        
        hbox = QtGui.QHBoxLayout()
        self.go_btn = QtGui.QPushButton("Go")
        self.go_btn.setFixedWidth(50)
        self.go_btn.clicked.connect(self.go)
        hbox.addWidget(self.go_btn)
        hbox.addStretch(1)
        layout.addLayout(hbox)

        layout.addStretch(1)

    def go(self):
        options = {self.output_name_edit.text() : self.proc_edit.text()}
        self.process.run(options)
