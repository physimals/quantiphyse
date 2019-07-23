"""
Quantiphyse - Plotting widgets

Copyright (c) 2013-2018 University of Oxford
"""

from __future__ import division, unicode_literals, absolute_import

import numpy as np
import pyqtgraph as pg
try:
    from PySide import QtGui, QtCore, QtGui as QtWidgets
except ImportError:
    from PySide2 import QtGui, QtCore, QtWidgets

from scipy.interpolate import UnivariateSpline

from quantiphyse.gui.widgets import OptionsButton
from quantiphyse.utils import LogSource, get_kelly_col, get_icon, norecurse

class PlotOptions(QtGui.QDialog):
    """
    Options dialog for a line plot
    """

    sig_options_changed = QtCore.Signal(object)

    def __init__(self, graph=None, **kwargs):
        QtGui.QDialog.__init__(self, graph)
        self.graph = graph
        self.sig_enh = False
        self.smooth = False

        self.setWindowTitle('Plot options')
        grid = QtGui.QGridLayout()
        self.setLayout(grid)

        row = 0
        # Display mode
        if kwargs.get("display_mode", True):
            grid.addWidget(QtGui.QLabel("Display mode"), row, 0)
            mode_combo = QtGui.QComboBox()
            mode_combo.addItem("Signal")
            mode_combo.addItem("Signal Enhancement")
            mode_combo.currentIndexChanged.connect(self._mode_changed)
            grid.addWidget(mode_combo, row, 1)
            row += 1

            # Signal enhancement baseline
            self.se_lbl = QtGui.QLabel('Signal enhancement: Use first')
            self.se_lbl.setEnabled(False)
            grid.addWidget(self.se_lbl, row, 0)

            hbox = QtGui.QHBoxLayout()
            self._norm_frames_spin = QtGui.QSpinBox()
            self._norm_frames_spin.setValue(3)
            self._norm_frames_spin.setMinimum(1)
            self._norm_frames_spin.setMaximum(100)
            self._norm_frames_spin.valueChanged.connect(self._changed)
            self._norm_frames_spin.setEnabled(False)
            hbox.addWidget(self._norm_frames_spin)
            self.se_lbl2 = QtGui.QLabel('frames as baseline')
            self.se_lbl2.setEnabled(False)
            hbox.addWidget(self.se_lbl2)
            hbox.addStretch(1)
            grid.addLayout(hbox, row, 1)
            row += 1

        # Y-axis scale
        if kwargs.get("y_scale", True):
            hbox = QtGui.QHBoxLayout()
            self.auto_y_cb = QtGui.QCheckBox('Automatic Y axis scale', self)
            self.auto_y_cb.setChecked(True)
            self.auto_y_cb.stateChanged.connect(self._auto_y_changed)
            grid.addWidget(self.auto_y_cb, row, 0)

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
            grid.addLayout(hbox, row, 1)
            row += 1

        # Smoothing
        if kwargs.get("smoothing", True):
            smooth_cb = QtGui.QCheckBox('Smooth curves', self)
            smooth_cb.setChecked(self.smooth)
            smooth_cb.stateChanged.connect(self._smooth_changed)
            grid.addWidget(smooth_cb, row, 0)
            row += 1

    @property
    def yrange(self):
        return self.min_spin.value(), self.max_spin.value()

    @yrange.setter
    def yrange(self, yrange):
        try:
            self.min_spin.blockSignals(True)
            self.max_spin.blockSignals(True)
            self.min_spin.setValue(yrange[0])
            self.max_spin.setValue(yrange[1])
            self.sig_options_changed.emit(self)
        finally:
            self.min_spin.blockSignals(False)
            self.max_spin.blockSignals(False)

    @property
    def autorange(self):
        return self.auto_y_cb.isChecked()

    @autorange.setter
    def autorange(self, autorange):
        self.auto_y_cb.setChecked(autorange)

    @property
    def norm_frames(self):
        return self._norm_frames_spin.value()

    def _mode_changed(self, idx):
        self.sig_enh = (idx == 1)
        self.se_lbl.setEnabled(self.sig_enh)
        self._norm_frames_spin.setEnabled(self.sig_enh)
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

class LinePlot(LogSource):
    """
    A 1-D array of data to be plotted as a line
    """
    def __init__(self, graph, yvalues, xvalues=None, axes=None, name=None, **kwargs):
        LogSource.__init__(self)
        if axes is None:
            self.axes = graph.axes
        if xvalues is None:
            xvalues = range(len(yvalues))

        self.name = name
        self.graph = graph
        self.axes = axes
        
        self.graph.options.sig_options_changed.connect(self._options_changed)

        self.yvalues = np.copy(np.array(yvalues, dtype=np.double))
        self.xvalues = np.copy(np.array(xvalues, dtype=np.double))
        self.line_col = kwargs.get("line_col", (255, 255, 255))
        self.line_width = kwargs.get("line_width", 1.0)
        self.line_style = kwargs.get("line_style", QtCore.Qt.SolidLine)
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
        if self.graph.options.sig_enh:
            norm_frames = min(len(self.yvalues), self.graph.options.norm_frames)
            mean = np.mean(self.yvalues[:norm_frames])
            plot_values = self.yvalues / mean - 1
        else:
            plot_values = self.yvalues

        if self.graph.options.smooth:
            indexes = range(len(plot_values))
            # Tolerance does not scale by data value to scale input
            spline = UnivariateSpline(indexes, plot_values/plot_values.max(), s=0.1, k=4)
            self.debug("Number of knots in B-spline smoothing: %i", len(spline.get_knots()))
            line_values = spline(indexes)*plot_values.max()
        else:
            line_values = plot_values

        self.hide()
        # Plot line and points separately as line may be smoothed
        line = self.axes.plot(self.xvalues, line_values, 
                              pen=pg.mkPen(color=self.line_col, width=self.line_width, style=self.line_style))

        pts = self.axes.plot(self.xvalues, plot_values, 
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
        items = self.graphics_items
        self.graphics_items = ()
        self.legend_item = None

        for item in items:
            self.axes.removeItem(item)

    def _options_changed(self):
        if self.graphics_items:
            self.show()

class Plot(QtGui.QWidget):
    """
    Widget for plotting graphs
    """
    def __init__(self, parent=None, title="", **kwargs):
        """
        Create a plot widget

        :param qpo: Global options
        """
        QtGui.QWidget.__init__(self, parent)
        self.items = []
        self.updating = False
        self.legend_pos = (30, 30)

        vbox = QtGui.QVBoxLayout()
        self.setLayout(vbox)

        hbox = QtGui.QHBoxLayout()
        hbox.addStretch(1)

        if kwargs.get("opts_btn", True):
            self.opts_btn = OptionsButton()
            self.opts_btn.clicked.connect(self._show_options)
            hbox.addWidget(self.opts_btn)


        if kwargs.get("clear_btn", False):
            clear_icon = QtGui.QIcon(get_icon("clear"))
            self.clear_btn = QtGui.QPushButton(self)
            self.clear_btn.setIcon(clear_icon)
            self.clear_btn.setIconSize(QtCore.QSize(14, 14))
            self.clear_btn.setToolTip("Clear curves")
            self.clear_btn.clicked.connect(self.clear)
            hbox.addWidget(self.clear_btn)

        vbox.addLayout(hbox)

        self.graphics_layout = pg.GraphicsLayoutWidget()
        self.graphics_layout.setBackground(background=None)
        vbox.addWidget(self.graphics_layout, 10)

        self.axes = self.graphics_layout.addPlot()
        self.axes.setTitle(title)
        self.axes.sigRangeChanged.connect(self._range_changed)
        self.axes.vb.sigRangeChangedManually.connect(self._range_changed_manually)

        if kwargs.get("twoaxis", False):
            # For a second y-axis, create a new ViewBox, link the right axis to its coordinate system
            self.axes_alt = pg.ViewBox()
            self.axes.scene().addItem(self.axes_alt)
            self.axes.getAxis('right').linkToView(self.axes_alt)
            self.axes_alt.setXLink(self.axes)
            self.axes.vb.sigResized.connect(self._update_plot_viewbox)
        else:
            self.axes_alt = None

        self.options = PlotOptions(self, **kwargs)
        self._options_changed()
        self.options.sig_options_changed.connect(self._options_changed)
        self._regenerate_legend()

    def set_xlabel(self, name):
        """
        Set the label for the X axis
        """
        self.axes.setLabel('bottom', name)

    def set_ylabel(self, name):
        """
        Set the label for the Y axis
        """
        self.axes.setLabel('left', name)

    def add_line(self, yvalues, name=None, xvalues=None, **kwargs):
        """
        Add a line to the plot

        :param values: 1-D Array of data values
        """
        if "line_col" not in kwargs:
            kwargs["line_col"] = get_kelly_col(len(self.items))

        axes = kwargs.get("axes", "main") 
        if axes.lower() == "main":
            axes = self.axes
        elif axes.lower() == "alt":
            axes = self.axes_alt
        else:
            raise ValueError("Unknown axes: %s" % axes)

        line = LinePlot(self, yvalues, xvalues=xvalues, name=name, axes=axes, **kwargs)
        self.items.append(line)
        self._contents_changed()
        return line

    def remove(self, item):
        """
        Remove an item from the plot
        """
        item.hide()
        self.items.remove(item)
        self._contents_changed()

    def clear(self):
        """
        Clear the plot
        """
        for item in self.items:
            item.hide()
        self.items = []
        self._contents_changed()

    def _show_options(self):
        """
        Show the options dialog box
        """
        self.options.show()
        self.options.raise_()

    def _update_plot_viewbox(self):
        # Required to keep the right and left axis plots in sync with each other
        self.axes_alt.setGeometry(self.axes.vb.sceneBoundingRect())
        
        # Need to re-update linked axes since this was called
        # incorrectly while views had different shapes.
        # (probably this should be handled in ViewBox.resizeEvent)
        self.axes_alt.linkedViewChanged(self.axes.vb, self.axes_alt.XAxis)

    @norecurse
    def _range_changed(self, *args):
        self.options.yrange = self.axes.viewRange()[1]

    @norecurse
    def _range_changed_manually(self, *args):
        self.options.yrange = self.axes.viewRange()[1]
        self.options.autorange = False

    def _contents_changed(self):
        self._regenerate_legend()

    @norecurse
    def _options_changed(self, *args):
        if self.axes_alt is not None:
            self.axes_alt.enableAutoRange() # FIXME
        if self.options.autorange:
            self.axes.enableAutoRange()
        else: 
            self.axes.disableAutoRange()
            self.axes.setYRange(*self.options.yrange)

    def _regenerate_legend(self):
        # Replaces any existing legend but keep position the same in case user moved it
        # This is necessary because of what seems to be a bug in pyqtgraph which prevents
        # legend items from being removed
        if self.axes.legend:
            self.legend_pos = self.axes.legend.pos()
            if self.axes.legend.scene(): 
                self.axes.legend.scene().removeItem(self.axes.legend)
            self.axes.legend = None
    
        for item in self.items:
            if item.name:
                if not self.axes.legend:
                    self.axes.addLegend(offset=self.legend_pos)
                self.axes.legend.addItem(item.legend_item, item.name)
