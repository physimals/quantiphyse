"""
Quantiphyse - Generic analysis widgets

Copyright (c) 2013-2018 University of Oxford
"""

from __future__ import division, unicode_literals, print_function, absolute_import

import math

import numpy as np
try:
    from PySide import QtGui, QtCore, QtGui as QtWidgets
except ImportError:
    from PySide2 import QtGui, QtCore, QtWidgets

from quantiphyse.gui.plot import Plot
from quantiphyse.gui.viewer.pickers import PickMode
from quantiphyse.gui.widgets import QpWidget, RoiCombo, TitleWidget, RunButton
from quantiphyse.gui.options import OptionBox, DataOption, ChoiceOption, BoolOption, TextOption, OutputNameOption
from quantiphyse.utils import copy_table, get_kelly_col, sf

from .processes import CalcVolumesProcess, DataStatisticsProcess

class MultiVoxelAnalysis(QpWidget):
    """
    Plots timeseries for multiple selected points
    """
    
    def __init__(self, **kwargs):
        super(MultiVoxelAnalysis, self).__init__(name="Multi-Voxel", icon="voxel", desc="Compare signal curves at different voxels", group="Visualisation", position=2, **kwargs)

        self.activated = False
        self.colors = {'grey':(200, 200, 200), 'red':(255, 0, 0), 'green':(0, 255, 0), 'blue':(0, 0, 255),
                       'orange':(255, 140, 0), 'cyan':(0, 255, 255), 'brown':(139, 69, 19)}
        self.col = self.colors["red"]
        self.plots = {}
        self.mean_plots = {}

    def init_ui(self):
        self.setStatusTip("Click points on the 4D volume to see data curve")

        vbox = QtGui.QVBoxLayout()
        self.setLayout(vbox)

        title = TitleWidget(self, "Multi-Voxel Visualisation", help="curve_compare", batch_btn=False)
        vbox.addWidget(title)

        self.plot = Plot(clear_btn=True)
        self.plot.clear_btn.clicked.connect(self._clear)
        self.plot.options.sig_options_changed.connect(self._options_changed)
        vbox.addWidget(self.plot)

        self.options = OptionBox("Options")
        self.options.add("Data set", DataOption(self.ivm, include_3d=False), key="data")
        col_names = [text for text in self.colors]
        cols = [col for text, col in self.colors.items()]
        self.options.add("Plot colour", ChoiceOption(col_names, cols, default="red"), key="col")
        self.options.add("Show individual curves", BoolOption(default=True), key="indiv")
        self.options.add("Show mean curve", BoolOption(), key="mean")

        self.options.option("data").sig_changed.connect(self._data_changed)
        self.options.option("indiv").sig_changed.connect(self._indiv_changed)
        self.options.option("mean").sig_changed.connect(self._mean_changed)
        self.options.option("col").sig_changed.connect(self._col_changed)

        hbox = QtGui.QHBoxLayout()
        hbox.addWidget(self.options)
        hbox.addStretch()
        vbox.addLayout(hbox)

        vbox.addStretch(1)    
        self._options_changed()

    def activate(self):
        self.ivl.sig_selection_changed.connect(self._selection_changed)
        self.ivl.set_picker(PickMode.MULTIPLE)
        self.activated = True

    def deactivate(self):
        self.ivl.sig_selection_changed.disconnect(self._selection_changed)
        self.ivl.set_picker(PickMode.SINGLE)

    def _options_changed(self):
        if self.plot.options.sig_enh:
            self.plot.set_ylabel("Signal enhancement")
        else:
            self.plot.set_ylabel("Signal")

    def _data_changed(self):
        self._clear()
        data_name = self.options.option("data").value
        if data_name in self.ivm.data:
            # FIXME not clear whether to use metadata
            #data = self.ivm.data[data_name]
            #xlabel = data.metadata.get("vol_scale", "Volume")
            #xunits = data.metadata.get("vol_units", "")
            #if xunits:
            #    xlabel = "%s (%s)" % (xlabel, xunits)
            self.plot.set_xlabel("Volume")

    def _indiv_changed(self):
        show_indiv = self.options.option("indiv").value
        for plt in self.plots.values():
            if show_indiv:
                plt.show()
            else:
                plt.hide()

    def _mean_changed(self):
        show_mean = self.options.option("mean").value
        if show_mean:
            self._update_means()
            for plt in self.mean_plots.values():
                plt.show()
        else:
            for plt in self.mean_plots.values():
                plt.hide()

    def _clear(self):
        """
        Clear point data
        """
        self.plot.clear()
        self.plots, self.mean_plots = {}, {}
        # Reset the list of picked points
        self.ivl.set_picker(PickMode.MULTIPLE)
        self.ivl.picker.col = self.col

    def _add_point(self, point, col):
        """
        Add a selected point of the specified colour
        """
        data_name = self.options.option("data").value
        if data_name in self.ivm.data:
            data = self.ivm.data[data_name]
            sig = data.timeseries(point, grid=self.ivl.grid)
            if point in self.plots:
                self.plot.remove(self.plots[point])

            self.plots[point] = self.plot.add_line(sig, line_col=col)
            if not self.options.option("indiv").value:
                self.plots[point].hide()
            self._update_means()

    def _update_means(self):
        for col in self.colors.values():
            if col in self.mean_plots:
                self.plot.remove(self.mean_plots[col])
                del self.mean_plots[col]
            all_plts = [plt for plt in self.plots.values() if plt.line_col == col]
            if all_plts:
                mean_values = np.stack([plt.yvalues for plt in all_plts], axis=1)
                mean_values = np.squeeze(np.mean(mean_values, axis=1))
                self.mean_plots[col] = self.plot.add_line(mean_values, line_col=col, line_style=QtCore.Qt.DashLine, point_brush=col, point_col='k', point_size=10)
                if not self.options.option("mean").value:
                    self.mean_plots[col].hide()

    def _selection_changed(self, picker):
        """
        Point selection changed
        """
        # Add plots for points in the selection which we haven't plotted (or which have changed colour)
        allpoints = []
        for col, points in picker.selection().items():
            points = [tuple([int(p+0.5) for p in pos]) for pos in points]
            allpoints += points
            for point in points:
                if point not in self.plots or self.plots[point].line_col != col:
                    self._add_point(point, col)

        # Remove plots for points no longer in the selection
        for point in list(self.plots.keys()):
            if point not in allpoints:
                self.plots[point].hide()
                del self.plots[point]

    def _col_changed(self):
        self.col = self.options.option("col").value
        self.ivl.picker.col = self.col

class DataStatistics(QpWidget):

    def __init__(self, **kwargs):
        super(DataStatistics, self).__init__(name="Data Statistics", desc="Display statistics about data sets", icon="edit", group="DEFAULT", position=1, **kwargs)
        
    def init_ui(self):
        """ Set up UI controls here so as not to delay startup"""
        self.process = DataStatisticsProcess(self.ivm)
        self.process_ss = DataStatisticsProcess(self.ivm)
        
        main_vbox = QtGui.QVBoxLayout()

        title = TitleWidget(self, help="overlay_stats", batch_btn=False)
        main_vbox.addWidget(title)

        hbox = QtGui.QHBoxLayout()
        hbox.addWidget(QtGui.QLabel("Data selection"))
        self.data = DataOption(self.ivm, multi=True)
        self.data.sig_changed.connect(self.update_all)
        hbox.addWidget(self.data)
        hbox.addWidget(QtGui.QLabel("ROI"))
        self.roi = DataOption(self.ivm, data=False, rois=True, none_option=True)
        self.roi.sig_changed.connect(self.update_all)
        hbox.addWidget(self.roi)
        hbox.setStretch(1, 1)
        hbox.setStretch(3, 1)
        main_vbox.addLayout(hbox)

        hbox = QtGui.QHBoxLayout()
        self.current_vol = QtGui.QCheckBox("Current volume only")
        hbox.addWidget(self.current_vol)
        self.exact_median = QtGui.QCheckBox("Exact median")
        self.exact_median.setToolTip("Computing an exact median can fail on extremely large data sets")
        hbox.addWidget(self.exact_median)
        hbox.addStretch(1)
        main_vbox.addLayout(hbox)
        self.current_vol.stateChanged.connect(self.update_all)

        # Summary stats
        stats_box = QtGui.QGroupBox()
        stats_box.setTitle('Summary Statistics')
        vbox = QtGui.QVBoxLayout()
        stats_box.setLayout(vbox)

        hbox = QtGui.QHBoxLayout()
        self.butgen = QtGui.QPushButton("Show")
        self.butgen.setToolTip("Show standard statistics for the data in each ROI")
        self.butgen.clicked.connect(self.show_stats)
        hbox.addWidget(self.butgen)
        self.copy_btn = QtGui.QPushButton("Copy")
        self.copy_btn.clicked.connect(self.copy_stats)
        self.copy_btn.setVisible(False)
        hbox.addWidget(self.copy_btn)
        hbox.addStretch(1)
        vbox.addLayout(hbox)

        self.stats_table = QtGui.QTableView()
        self.stats_table.resizeColumnsToContents()
        self.stats_table.setModel(self.process.model)
        self.stats_table.setVisible(False)
        vbox.addWidget(self.stats_table)

        main_vbox.addWidget(stats_box)

        # Summary stats (single slice)

        stats_box_ss = QtGui.QGroupBox()
        stats_box_ss.setTitle('Summary Statistics - Slice')
        vbox = QtGui.QVBoxLayout()
        stats_box_ss.setLayout(vbox)

        hbox = QtGui.QHBoxLayout()
        self.butgenss = QtGui.QPushButton("Show")
        self.butgenss.setToolTip("Show standard statistics for the current slice")
        self.butgenss.clicked.connect(self.show_stats_current_slice)
        hbox.addWidget(self.butgenss)
        self.slice_dir_label = QtGui.QLabel("Slice direction:")
        self.slice_dir_label.setVisible(False)
        hbox.addWidget(self.slice_dir_label)
        self.sscombo = QtGui.QComboBox()
        self.sscombo.addItem("Axial")
        self.sscombo.addItem("Coronal")
        self.sscombo.addItem("Sagittal")
        self.sscombo.setSizeAdjustPolicy(QtGui.QComboBox.AdjustToContents)
        self.sscombo.currentIndexChanged.connect(self.focus_changed)
        self.sscombo.setVisible(False)
        hbox.addWidget(self.sscombo)
        self.copy_btn_ss = QtGui.QPushButton("Copy")
        self.copy_btn_ss.clicked.connect(self.copy_stats_ss)
        self.copy_btn_ss.setVisible(False)
        hbox.addWidget(self.copy_btn_ss)
        hbox.addStretch(1)
        vbox.addLayout(hbox)

        self.stats_table_ss = QtGui.QTableView()
        self.stats_table_ss.resizeColumnsToContents()
        self.stats_table_ss.setModel(self.process_ss.model)
        self.stats_table_ss.setVisible(False)
        vbox.addWidget(self.stats_table_ss)

        main_vbox.addWidget(stats_box_ss)

        main_vbox.addStretch(1)
        self.setLayout(main_vbox)

    def activate(self):
        self.ivm.sig_current_roi.connect(self.update_all)
        self.ivm.sig_all_data.connect(self.update_all)
        self.ivm.sig_current_data.connect(self.update_all)
        self.ivl.sig_focus_changed.connect(self.focus_changed)
        self.update_all()

    def deactivate(self):
        self.ivm.sig_current_roi.disconnect(self.update_all)
        self.ivm.sig_all_data.disconnect(self.update_all)
        self.ivm.sig_current_data.disconnect(self.update_all)
        self.ivl.sig_focus_changed.disconnect(self.focus_changed)

    def mode_changed(self, idx):
        self.ovl_selection = idx
        self.update_all()

    def focus_changed(self, _):
        if self.stats_table_ss.isVisible():
            self.update_stats_current_slice()
        if self.stats_table.isVisible() and self.current_vol.isChecked():
            self.update_stats()

    def update_all(self):
        if self.stats_table.isVisible():
            self.update_stats()
        if self.stats_table_ss.isVisible():
            self.update_stats_current_slice()

    def copy_stats(self):
        copy_table(self.process.model)

    def copy_stats_ss(self):
        copy_table(self.process_ss.model)
        
    def show_stats(self):
        if self.stats_table.isVisible():
            self.stats_table.setVisible(False)
            self.copy_btn.setVisible(False)
            self.butgen.setText("Show")
        else:
            self.update_stats()
            self.stats_table.setVisible(True)
            self.copy_btn.setVisible(True)
            self.butgen.setText("Hide")

    def show_stats_current_slice(self):
        if self.stats_table_ss.isVisible():
            self.stats_table_ss.setVisible(False)
            self.slice_dir_label.setVisible(False)
            self.sscombo.setVisible(False)
            self.copy_btn_ss.setVisible(False)
            self.butgenss.setText("Show")
        else:
            self.update_stats_current_slice()
            self.stats_table_ss.setVisible(True)
            self.slice_dir_label.setVisible(True)
            self.sscombo.setVisible(True)
            self.copy_btn_ss.setVisible(True)
            self.butgenss.setText("Hide")

    def update_stats(self):
        self.populate_stats_table(self.process, {})

    def update_stats_current_slice(self):
        if self.ivm.main is not None:
            slice_dir = 2-self.sscombo.currentIndex()
            options = {
                "slice-dir" : slice_dir,
                "slice-pos" : self.ivl.focus(self.ivm.main.grid)[slice_dir],
            }
            self.populate_stats_table(self.process_ss, options)

    def populate_stats_table(self, process, options):
        options["data"] = self.data.value
        options["roi"] = self.roi.value
        if self.current_vol.isChecked():
            options["vol"] = self.ivl.focus()[3]
        options["exact-median"] = self.exact_median.isChecked()
        process.run(options)

class RoiAnalysisWidget(QpWidget):
    """
    Analysis of ROIs
    """
    def __init__(self, **kwargs):
        super(RoiAnalysisWidget, self).__init__(name="ROI Analysis", icon="roi", desc="Analysis of ROIs", 
                                                group="ROIs", **kwargs)
        
    def init_ui(self):
        self.process = CalcVolumesProcess(self.ivm)

        layout = QtGui.QVBoxLayout()
        self.setLayout(layout)

        title = TitleWidget(self, help="roi_analysis")
        layout.addWidget(title)

        info = QtGui.QLabel("<i><br>Calculate size and volume of an ROI<br></i>")
        info.setWordWrap(True)
        layout.addWidget(info)

        hbox = QtGui.QHBoxLayout()
        hbox.addWidget(QtGui.QLabel('ROI: '))
        self.combo = RoiCombo(self.ivm)
        self.combo.currentIndexChanged.connect(self.update)
        hbox.addWidget(self.combo)
        hbox.addStretch(1)
        layout.addLayout(hbox)

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
        self.ivm.sig_current_roi.connect(self.current_roi_changed)
        self.ivm.sig_all_data.connect(self.update)
        self.update()

    def deactivate(self):
        self.ivm.sig_current_roi.disconnect(self.current_roi_changed)
        self.ivm.sig_all_data.disconnect(self.update)

    def batch_options(self):
        return "CalcVolumes", {"roi" : self.combo.currentText()}

    def current_roi_changed(self, roi):
        self.combo.setCurrentIndex(self.combo.findText(roi.name))

    def update(self):
        roi = self.combo.currentText()
        if roi in self.ivm.rois:
            self.process.run({"roi" : roi, "no-extras" : True})
        
    def copy_stats(self):
        copy_table(self.process.model)

MATHS_INFO = """
<i>Create data using simple mathematical operations on existing data
<br><br>
For example, if you have loaded data called 'mydata' and run modelling
to produce a model prediction 'modelfit', you could calculate the residuals
using:</i>
<br><br>
mydata - modelfit
<br><br>
<i>The output will be interpreted as being defined in the same data space as the
'data space' option - if this is incorrect the output will probably be 
misaligned!</i>
"""

class SimpleMathsWidget(QpWidget):
    """
    Widget which lets you run arbitrary Python/Numpy code on the data in the IVM
    """
    def __init__(self, **kwargs):
        super(SimpleMathsWidget, self).__init__(name="Simple Maths", icon="maths", 
                                                desc="Simple mathematical operations on data", 
                                                group="Processing", **kwargs)

    def init_ui(self):
        layout = QtGui.QVBoxLayout()
        self.setLayout(layout)

        title = TitleWidget(self, help="simple_maths")
        layout.addWidget(title)

        info = QtGui.QLabel(MATHS_INFO)
        info.setWordWrap(True)
        layout.addWidget(info)

        self.optbox = OptionBox()
        self.optbox.add("Data space from", DataOption(self.ivm), key="grid")
        self.optbox.add("Command", TextOption(), key="cmd")
        self.optbox.add("Output name", OutputNameOption(src_data=self.optbox.option("grid")), key="output-name")
        self.optbox.add("Output is an ROI", BoolOption(), key="output-is-roi")
        layout.addWidget(self.optbox)
        
        hbox = QtGui.QHBoxLayout()
        self.go_btn = RunButton(self)
        hbox.addWidget(self.go_btn)
        hbox.addStretch(1)
        layout.addLayout(hbox)

        layout.addStretch(1)

    def processes(self):
        return {
            "Exec" : {
                "grid" : self.optbox.option("grid").value,
                "output-is-roi" : self.optbox.option("output-is-roi").value,
                self.optbox.option("output-name").value : self.optbox.option("cmd").value,
            }
        }

class VoxelAnalysis(QpWidget):
    """
    View original data and generated signal curves side by side
    """

    def __init__(self, **kwargs):
        super(VoxelAnalysis, self).__init__(name="Voxel analysis", desc="Display data at a voxel", 
                                            icon="curve_view", group="DEFAULT", **kwargs)
        self.data_enabled = {}
        self.updating = False

    def init_ui(self):
        main_vbox = QtGui.QVBoxLayout()
        self.setLayout(main_vbox)

        title = TitleWidget(self, title="Voxel analysis", help="modelfit", batch_btn=False)
        main_vbox.addWidget(title)

        self.plot = Plot(twoaxis=True)
        main_vbox.addWidget(self.plot)

        tabs = QtGui.QTabWidget()
        main_vbox.addWidget(tabs)

        # Table showing RMS deviation
        self.rms_table = QtGui.QStandardItemModel()
        self.rms_table.itemChanged.connect(self._data_table_changed)
        tview = QtGui.QTableView()
        tview.setModel(self.rms_table)
        tview.horizontalHeader().setResizeMode(QtGui.QHeaderView.ResizeToContents)
        tabs.addTab(tview, "Timeseries data")

        # Table showing value of model parameters
        self.values_table = QtGui.QStandardItemModel()
        tview = QtGui.QTableView()
        tview.setModel(self.values_table)
        tview.horizontalHeader().setResizeMode(QtGui.QHeaderView.ResizeToContents)
        tabs.addTab(tview, 'Non-timeseries data')

    def activate(self):
        self.ivm.sig_all_data.connect(self._update)
        self.ivl.sig_focus_changed.connect(self._update)
        self._update()

    def deactivate(self):
        self.ivm.sig_all_data.disconnect(self._update)
        self.ivl.sig_focus_changed.disconnect(self._update)

    def _update(self, pos=None):
        self._update_table()
        self._update_rms_table()
        self._plot()

    def _update_table(self):
        """
        Set the data parameter values in the table based on the current point clicked
        """
        self.values_table.clear()
        self.values_table.setHorizontalHeaderItem(0, QtGui.QStandardItem("Value"))
        data_vals = self.ivm.values(self.ivl.focus(), self.ivl.grid)
        for ii, ovl in enumerate(sorted(data_vals.keys())):
            if self.ivm.data[ovl].ndim == 3:
                self.values_table.setVerticalHeaderItem(ii, QtGui.QStandardItem(ovl))
                self.values_table.setItem(ii, 0, QtGui.QStandardItem(sf(data_vals[ovl])))

    def _update_rms_table(self):
        try:
            self.updating = True # Hack to prevent plot being refreshed during table update
            self.rms_table.clear()
            self.rms_table.setHorizontalHeaderItem(0, QtGui.QStandardItem("Name"))
            self.rms_table.setHorizontalHeaderItem(1, QtGui.QStandardItem("RMS (Position)"))

            pos = self.ivl.focus()
            sigs = self.ivm.timeseries(pos, self.ivl.grid)
            max_length = max([0,] + [len(sig) for sig in sigs.values()])
            if self.ivm.main is not None:
                main_curve = self.ivm.main.timeseries(pos, grid=self.ivl.grid)
                main_curve.extend([0] * max_length)
                main_curve = main_curve[:max_length]

            for idx, name in enumerate(sorted(sigs.keys())):
                # Make sure data curve is correct length
                data_curve = sigs[name]
                data_curve.extend([0] * max_length)
                data_curve = data_curve[:max_length]

                if self.ivm.main is not None:
                    data_rms = np.sqrt(np.mean(np.square([v1-v2 for v1, v2 in zip(main_curve, data_curve)])))
                else:
                    data_rms = 0

                name_item = QtGui.QStandardItem(name)
                name_item.setCheckable(True)
                name_item.setEditable(False)
                if name not in self.data_enabled:
                    self.data_enabled[name] = QtCore.Qt.Checked
                name_item.setCheckState(self.data_enabled[name])
                self.rms_table.setItem(idx, 0, name_item)

                item = QtGui.QStandardItem(sf(data_rms))
                item.setEditable(False)
                self.rms_table.setItem(idx, 1, item)
        finally:
            self.updating = False

    def _data_table_changed(self, item):
        if not self.updating:
            # A checkbox has been toggled
            self.data_enabled[item.text()] = item.checkState()
            self._plot()

    def _plot(self):
        """
        Regenerate the plot
        """
        self.plot.clear() 

        # Get all timeseries signals
        pos = self.ivl.focus()
        sigs = self.ivm.timeseries(pos, self.ivl.grid)
        if not sigs:
            return
            
        # Get x scale
        self.plot.set_xlabel("Volume")
        
        # Set y labels
        #axis_labels = {0 : "Signal", 1 : "Signal enhancement", 2 : "Signal"}
        #self.plot.setLabel('left', axis_labels[self.plot_opts.mode])
        #if self.plot_opts.mode == 2:
        #    self.plot.showAxis('right')
        #    self.plot.getAxis('right').setLabel('Residual')
        #else:
        #    self.plot.hideAxis('right')

        #if not self.ivm.main:
        #    return
        #main_curve = self.ivm.main.timeseries(pos, grid=self.ivl.grid)

        idx, _ = 0, len(sigs)
        for ovl, sig_values in sigs.items():
            if self.data_enabled[ovl] == QtCore.Qt.Checked:
                col = get_kelly_col(idx)

                #if self.plot_opts.mode == 2 and ovl != self.ivm.main.name:
                #    # Show residuals on the right hand axis
                #    resid_values = [v1 - v2 for v1, v2 in zip(sig_values, main_curve)]
                #    self.plot_rightaxis.addItem(pg.PlotCurveItem(resid_values, pen=pg.mkPen(pen, style=QtCore.Qt.DashLine)))
                    
                self.plot.add_line(sig_values, name=ovl, line_col=col, point_brush=(200, 200, 200), point_col='k', point_size=5.0)
                idx += 1

class MeasureWidget(QpWidget):
    """
    Widget which lets you measure physical distances and angles
    """
    ANGLE = "angle"
    DISTANCE = "distance"

    def __init__(self, **kwargs):
        super(MeasureWidget, self).__init__(name="Measurements", icon="measure", 
                                                desc="Measure distances and angles", 
                                                group="Visualisation", **kwargs)
        self._points = None
        self._mode = None

    def init_ui(self):
        layout = QtGui.QVBoxLayout()
        self.setLayout(layout)

        title = TitleWidget(self)
        layout.addWidget(title)

        box = QtGui.QGroupBox("Measurements")
        vbox = QtGui.QVBoxLayout()
        box.setLayout(vbox)
        
        self._dist_btn = QtGui.QPushButton("Measure distance")
        self._dist_btn.clicked.connect(self._measure_dist)
        vbox.addWidget(self._dist_btn)

        self._angle_btn = QtGui.QPushButton("Measure angle")
        self._angle_btn.clicked.connect(self._measure_angle)
        vbox.addWidget(self._angle_btn)

        self._label = QtGui.QLabel()
        vbox.addWidget(self._label)

        layout.addWidget(box)
        layout.addStretch(1)

    def activate(self):
        self.ivl.set_picker(PickMode.SINGLE)
        self.ivl.sig_selection_changed.connect(self._sel_changed)

    def deactivate(self):
        self.ivl.set_picker(PickMode.SINGLE)
        self.ivl.sig_selection_changed.disconnect(self._sel_changed)

    def _sel_changed(self):
        if self._mode is None:
            return

        selection = self.ivl.picker.selection()
        if len(selection) != 1:
            raise ValueError("Expected single colour")

        points = list(selection.values())[0]
        if len(points) == 1:
            self._label.setText("Select the second point")
        elif self._mode == self.DISTANCE and len(points) == 2:
            self._calc_distance(points)
        elif self._mode == self.ANGLE and len(points) == 2:
            self._label.setText("Select the final point")
        elif self._mode == self.ANGLE and len(points) == 3:
            self._calc_angle(points)
        else:
            raise ValueError("Incorrect number of points: %i (%s)" % (len(points), self._mode))

    def _calc_distance(self, points):
        v = [p1 - p2 for p1, p2 in zip(points[0], points[1])]
        v_world = self.ivl.grid.grid_to_world(v, direction=True)
        distance = np.linalg.norm(v_world)
        self._label.setText("Distance: %.3g %s" % (distance, self.ivl.grid.units))
        self.ivl.set_picker(PickMode.SINGLE)
        self._mode = None

    def _calc_angle(self, points):
        u = [p1 - p2 for p1, p2 in zip(points[0], points[1])]
        v = [p1 - p2 for p1, p2 in zip(points[2], points[1])]
        u_world = self.ivl.grid.grid_to_world(u, direction=True)
        v_world = self.ivl.grid.grid_to_world(v, direction=True)
        cos = np.dot(u_world, v_world) / np.linalg.norm(u_world) / np.linalg.norm(v_world)
        angle = math.degrees(math.acos(cos))
        self._label.setText("Angle: %.3g \N{DEGREE SIGN}" % angle)
        self.ivl.set_picker(PickMode.SINGLE)
        self._mode = None

    def _measure_dist(self):
        self._mode = self.DISTANCE
        self.ivl.set_picker(PickMode.MULTIPLE)
        self._label.setText("Select the first point")
        self._points = []

    def _measure_angle(self):
        self._mode = self.ANGLE
        self.ivl.set_picker(PickMode.MULTIPLE)
        self._label.setText("Select the first point")
        self._points = []
