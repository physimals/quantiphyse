"""
Quantiphyse - Plotting widgets

Copyright (c) 2013-2018 University of Oxford
"""

from __future__ import division, unicode_literals, print_function, absolute_import

import numpy as np
import pyqtgraph as pg
from PySide import QtCore, QtGui
from scipy.interpolate import UnivariateSpline

from quantiphyse.gui.widgets import OptionsButton
from quantiphyse.utils import debug, get_kelly_col

class PlotOptions(QtGui.QDialog):
    """
    Options dialog for a line plot
    """

    sig_options_changed = QtCore.Signal(object)

    def __init__(self, qpo, parent=None):
        QtGui.QDialog.__init__(self, parent)
        self.qpo = qpo
        self.sig_enh = False
        self.smooth = False
        self.t_scale = range(10)

        self.setWindowTitle('Plot options')
        grid = QtGui.QGridLayout()
        self.setLayout(grid)

        # Display mode
        grid.addWidget(QtGui.QLabel("Display mode"), 0, 0)
        mode_combo = QtGui.QComboBox()
        mode_combo.addItem("Signal")
        mode_combo.addItem("Signal Enhancement")
        mode_combo.currentIndexChanged.connect(self._mode_changed)
        grid.addWidget(mode_combo, 0, 1)

        # Y-axis scale
        hbox = QtGui.QHBoxLayout()

        auto_y_cb = QtGui.QCheckBox('Automatic Y axis scale', self)
        auto_y_cb.setChecked(True)
        auto_y_cb.stateChanged.connect(self._auto_y_changed)
        grid.addWidget(auto_y_cb, 1, 0)

        self.min_lbl = QtGui.QLabel("Min")
        self.min_lbl.setEnabled(False)
        hbox.addWidget(self.min_lbl)
        self.min_spin = QtGui.QDoubleSpinBox()
        self.min_spin.setMinimum(-1e20)
        self.min_spin.setMaximum(1e20)
        self.min_spin.valueChanged.connect(self._changed)
        self.min_spin.setEnabled(False)
        hbox.addWidget(self.min_spin)

        self.max_lbl = QtGui.QLabel("Max")
        self.max_lbl.setEnabled(False)
        hbox.addWidget(self.max_lbl)
        self.max_spin = QtGui.QDoubleSpinBox()
        self.max_spin.setMinimum(-1e20)
        self.max_spin.setMaximum(1e20)
        self.max_spin.valueChanged.connect(self._changed)
        self.max_spin.setEnabled(False)
        hbox.addWidget(self.max_spin)

        hbox.addStretch(1)
        grid.addLayout(hbox, 1, 1)

        # Signal enhancement baseline
        self.se_lbl = QtGui.QLabel('Signal enhancement: Use first')
        self.se_lbl.setEnabled(False)
        grid.addWidget(self.se_lbl, 2, 0)

        hbox = QtGui.QHBoxLayout()
        self.norm_frames = QtGui.QSpinBox()
        self.norm_frames.setValue(3)
        self.norm_frames.setMinimum(1)
        self.norm_frames.setMaximum(100)
        self.norm_frames.valueChanged.connect(parent.update)
        self.norm_frames.setEnabled(False)
        hbox.addWidget(self.norm_frames)
        self.se_lbl2 = QtGui.QLabel('frames as baseline')
        self.se_lbl2.setEnabled(False)
        hbox.addWidget(self.se_lbl2)
        hbox.addStretch(1)
        grid.addLayout(hbox, 2, 1)

        # Smoothing
        smooth_cb = QtGui.QCheckBox('Smooth curves', self)
        smooth_cb.setChecked(self.smooth)
        smooth_cb.stateChanged.connect(self._smooth_changed)
        grid.addWidget(smooth_cb, 3, 0)

    def _mode_changed(self, idx):
        self.sig_enh = (idx == 1)
        self.se_lbl.setEnabled(self.sig_enh)
        self.norm_frames.setEnabled(self.sig_enh)
        self.se_lbl2.setEnabled(self.sig_enh)
        self.sig_options_changed.emit(self)

    def _auto_y_changed(self, selected):
        self.min_lbl.setEnabled(not selected)
        self.min_spin.setEnabled(not selected)
        self.max_lbl.setEnabled(not selected)
        self.max_spin.setEnabled(not selected)
        self.sig_options_changed.emit(self)
        
    def _smooth_changed(self, state):
        self.smooth = state
        self.sig_options_changed.emit(self)

    def _changed(self):
        self.sig_options_changed.emit(self)

class LinePlot(object):
    """
    A 1-D array of data to be plotted as a line
    """
    def __init__(self, name, plot, values, options, **kwargs):
        self.name = name
        self.plot = plot
        self.plot_options = options
        self.plot_options.sig_options_changed.connect(self.show)

        self.values = np.copy(np.array(values, dtype=np.double))
        self.line_col = kwargs.get("line_col", (255, 255, 255))
        self.line_width = kwargs.get("line_width", 1.0)
        self.point_col = kwargs.get("point_col", "k")
        self.point_size = kwargs.get("point_size", 5.0)
        self.point_brush = kwargs.get("point_brush", (200, 200, 200))

        self.legend_item = None
        self.graphics_items = ()
        self.show()

    def show(self):
        """
        Draw the line on to the plot
        """
        if self.plot_options.sig_enh:
            mean = np.mean(self.values[:self.plot_options.norm_frames.value()])
            plot_values = self.values / mean - 1
        else:
            plot_values = self.values

        if self.plot_options.smooth:
            indexes = range(len(plot_values))
            # Tolerance does not scale by data value to scale input
            spline = UnivariateSpline(indexes, plot_values/plot_values.max(), s=0.1, k=4)
            debug("Number of knots in B-spline smoothing: ", len(spline.get_knots()))
            line_values = spline(indexes)*plot_values.max()
        else:
            line_values = plot_values

        self.hide()

        # Make sure x-scale is correct length
        t_scale = range(len(line_values))
        scale_length = min(len(line_values), len(self.plot_options.t_scale))
        t_scale[:scale_length] = self.plot_options.t_scale[:scale_length]

        # Plot line and points separately as line may be smoothed
        line = self.plot.plot(t_scale, line_values, 
                              pen=pg.mkPen(color=self.line_col, width=self.line_width))

        pts = self.plot.plot(t_scale, plot_values, 
                             pen=None, 
                             symbolBrush=self.point_brush, 
                             symbolPen=self.point_col,
                             symbolSize=self.point_size)

        self.legend_item = line
        self.graphics_items = (line, pts)

    def hide(self):
        """
        Remove the line from the plot
        """
        for item in self.graphics_items:
            self.plot.removeItem(item)
        self.graphics_items = ()
        self.legend_item = None

class Plot(QtGui.QWidget):
    """
    A line plot
    """
    def __init__(self, qpo=None, parent=None, title=""):
        """
        Create a plot widget

        :param qpo: Global options
        """
        QtGui.QWidget.__init__(self, parent)
        self.options = PlotOptions(qpo, parent)
        self.items = []

        vbox = QtGui.QVBoxLayout()
        self.setLayout(vbox)

        hbox = QtGui.QHBoxLayout()
        hbox.addStretch(1)
        opts_btn = OptionsButton()
        opts_btn.clicked.connect(self._show_options)
        hbox.addWidget(opts_btn)
        vbox.addLayout(hbox)

        self.graphics_layout = pg.GraphicsLayoutWidget()
        self.graphics_layout.setBackground(background=None)
        vbox.addWidget(self.graphics_layout, 10)

        self.plot = self.graphics_layout.addPlot()
        self.plot.setTitle(title)
        self._regenerate_legend()
        
    def add_line(self, name, values, **kwargs):
        """
        Add a line to the plot

        :param values: 1-D Array of data values
        """

        if "line_col" not in kwargs:
            kwargs["line_col"] = get_kelly_col(len(self.items))

        line = LinePlot(name, self.plot, values, self.options, **kwargs)
        self.items.append(line)
        self._regenerate_legend()
        return line

    def clear(self):
        for item in self.items:
            item.hide()
        self.items = []
        self._regenerate_legend()

    def _show_options(self):
        """
        Show the options dialog box
        """
        self.options.show()
        self.options.raise_()

    def _regenerate_legend(self):
        # Replaces any existing legend but keep position the same in case user moved it
        # This is necessary because of what seems to be a bug in pyqtgraph which prevents
        # legend items from being removed
        legend_pos = (30, 30)
        if self.plot.legend: 
            legend_pos = self.plot.legend.pos()
            self.plot.legend.scene().removeItem(self.plot.legend)

        self.plot.addLegend(offset=legend_pos)
        for item in self.items:
            self.plot.legend.addItem(item.legend_item, item.name)