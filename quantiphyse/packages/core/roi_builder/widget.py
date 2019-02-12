"""
Quantiphyse - Widgets allowing the user to build simple ROIs

A new ROI is based on the grid of an existing data set - chosen by the user.

Copyright (c) 2013-2018 University of Oxford
"""

from __future__ import division, unicode_literals, absolute_import, print_function

import collections

import numpy as np

from PySide import QtGui

from quantiphyse.data import NumpyData
from quantiphyse.gui.options import OptionBox, DataOption, NumericOption, TextOption
from quantiphyse.gui.widgets import QpWidget, TitleWidget
from quantiphyse.gui.pickers import PickMode
from quantiphyse.utils import get_icon

from .tools import CrosshairsTool, PenTool, WalkerTool, PainterTool, EraserTool, RectTool, EllipseTool, PolygonTool, PickTool, BucketTool

DESC = """
Widget for creating test ROIs and basic manual segmentation
"""

TOOLS = [CrosshairsTool(), PenTool(), PainterTool(), EraserTool(), RectTool(), EllipseTool(), PolygonTool(), PickTool(), WalkerTool(), BucketTool()]

class RoiBuilderWidget(QpWidget):
    """
    Widget for building ROIs
    """
    ADD = 1
    ERASE = 2
    MASK = 3

    def __init__(self, **kwargs):
        super(RoiBuilderWidget, self).__init__(name="ROI Builder", icon="roi_builder", desc=DESC,  
                                               group="ROIs", **kwargs)
        self._history = collections.deque(maxlen=10)
        self._tool = None
        self.grid = None

    def init_ui(self):
        layout = QtGui.QVBoxLayout()
        
        title = TitleWidget(self, help="roibuilder", batch_btn=False)
        layout.addWidget(title)

        self.options = OptionBox("Options")
        btn = QtGui.QPushButton("New")
        btn.clicked.connect(self._new_roi)
        self.options.add("ROI", DataOption(self.ivm, rois=True, data=False), btn, key="roi")
        self.options.add("Current label", NumericOption(minval=1, slider=False, intonly=True), key="label")
        self.options.add("Label description", TextOption(), key="label_text")
        self.options.option("roi").sig_changed.connect(self._roi_changed)
        self.options.option("label").sig_changed.connect(self._label_changed)
        self.options.option("label_text").sig_changed.connect(self._label_text_changed)
        layout.addWidget(self.options)
        
        # Add toolbox buttons in a grid
        hbox = QtGui.QHBoxLayout()
        self._toolbox = QtGui.QGroupBox()
        self._toolbox.setTitle("Toolbox")
        self.tools_grid = QtGui.QGridLayout()
        self._toolbox.setLayout(self.tools_grid)

        x, y, cols = 0, 0, 4
        for tool in TOOLS:
            self._add_tool(tool, y, x)
            x += 1
            if x == cols:
                y += 1
                x = 0

        self._undo_btn = QtGui.QPushButton()
        self._undo_btn.clicked.connect(self.undo)
        self._undo_btn.setEnabled(False)
        undo_icon = QtGui.QIcon.fromTheme("edit-undo")
        self._undo_btn.setIcon(undo_icon)
        self._undo_btn.setToolTip("Undo last action")
        self._undo_btn.setFixedSize(32, 32)
        self.tools_grid.addWidget(self._undo_btn, y, x)

        hbox.addWidget(self._toolbox)
        self._toolbox.setEnabled(False)
        hbox.addStretch(1)
        layout.addLayout(hbox)

        # Tool options box - initially invisible
        hbox = QtGui.QHBoxLayout()
        self._tool_options = QtGui.QGroupBox()
        self._tool_options.setVisible(False)

        hbox.addWidget(self._tool_options)
        hbox.addStretch(1)
        layout.addLayout(hbox)

        layout.addStretch(1)
        self.setLayout(layout)

    def activate(self):
        self._roi_changed()
        self.ivl.set_picker(PickMode.SINGLE)
        if self._tool is not None:
            self._tool.selected()

    def deactivate(self):
        self.ivl.set_picker(PickMode.SINGLE)
        if self._tool is not None:
            self._tool.deselected()

    def modify(self, vol=None, slice2d=None, points=None, mode=None):
        """
        Make a change to the ROI we are building

        :param roi_new: Numpy array containing the updated ROI data on the current base grid
        :param vol: 3D 3D selection specified as binary Numpy array same shape as ROI
        :param slice2d: 2D slice selection specified as tuple of (2D binary Numpy array, axis index, position)
        :param points: Selection specified as list of 3D co-ordinates
        :param mode: ``ADD`` to add selection to the ROI (using current label), ``ERASE`` to erase
                     selection from the ROI (set to 0), ``MASK`` to preserve ROI labels in
                     selection but zero everything outside selection
        """
        label = self.options.option("label").value
        self.debug("label=%i", label)

        # For undo functionality: selection is an object specifying which
        # points or ROI region were selected, data_orig is a corresponding
        # object which contains the data before the operation occurred.
        selection, data_orig = None, None

        if points is not None:
            selection = points
            data_orig = [self.roidata[point[0], point[1], point[2]] for point in points]
            for point in points:
                if mode == self.ADD:
                    self.roidata[point[0], point[1], point[2]] = label
                elif mode == self.ERASE:
                    self.roidata[point[0], point[1], point[2]] = 0
                else:
                    raise ValueError("Invalid mode: %i" % mode)
        else:
            # change_subset is a Numpy selection of the points to be
            # affected, data_new is a corresponding binary array identifying
            # the selected points in this subset to modify.
            if vol is not None:
                # Selection left as None to indicate whole volume
                selected_points = vol
                change_subset = self.roidata
            elif slice2d is not None:
                selected_points, axis, pos = slice2d
                slices = [slice(None)] * 3
                slices[axis] = pos
                change_subset = self.roidata[slices]
                # Selection is the axis index and position
                selection = (axis, pos)
            else:
                raise ValueError("Neither volume nor slice nor points provided")

            data_orig = np.copy(change_subset)
            if mode == self.ADD:
                self.debug("Adding: %i", np.count_nonzero(selected_points))
                change_subset[selected_points > 0] = label
            elif mode == self.ERASE:
                self.debug("Erasing: %i", np.count_nonzero(selected_points))
                change_subset[selected_points > 0] = 0
            elif mode == self.MASK:
                self.debug("Masking: %i", np.count_nonzero(selected_points))
                change_subset[selected_points == 0] = 0
            else:
                raise ValueError("Invalid mode: %i" % mode)
        
        # Save the previous state of the data in the history list
        self._history.append((selection, data_orig))
        self._undo_btn.setEnabled(True)
        
        # Update the ROI - note that the regions may have been affected so make
        # sure they are regenerated
        self._update_regions()
        self.ivl.redraw()
        self.debug("Now have %i nonzero", np.count_nonzero(self.roidata))

    def _update_regions(self):
        """
        ROI regions may have been created or added so regenerate them but put 
        back existing label names
        """
        current_regions = self.ivm.data[self.roiname].metadata.pop("roi_regions", {})
        new_regions = self.ivm.data[self.roiname].regions
        for label, desc in current_regions.items():
            if label in new_regions:
                new_regions[label] = desc
        
    def undo(self):
        """
        Undo the last change
        """
        self.debug("ROI undo: %i", len(self._history))
        if not self._history: 
            return

        selection, data_orig = self._history.pop()

        # For selection, None indicates whole volume, tuple indicates
        # an (axis, pos) slice, otherwise we have a sequence of points
        if selection is None:
            self.roidata[:] = data_orig
        elif isinstance(selection, tuple):
            axis, pos = selection
            slices = [slice(None)] * 3
            slices[axis] = pos
            self.roidata[slices] = data_orig
        else:
            for point, orig_value in zip(selection, data_orig):
                self.roidata[point[0], point[1], point[2]] = orig_value

        self._update_regions()
        self.ivl.redraw()
        self.debug("Now have %i nonzero", np.count_nonzero(self.roidata))
        self._undo_btn.setEnabled(len(self._history) > 0)
      
    def _label_changed(self):
        self.debug("Label changed")
        roi = self.ivm.data.get(self.options.option("roi").value, None)
        if roi is not None:
            label = self.options.option("label").value
            self.debug(label)
            regions = roi.regions
            if label in regions:
                self.options.option("label_text").value = regions[label]
            else:
                self.options.option("label_text").value = "Region %i" % label
        
    def _label_text_changed(self):
        self.debug("Label text changed")
        roi = self.ivm.data.get(self.options.option("roi").value, None)
        if roi is not None:
            label = self.options.option("label").value
            label_text = self.options.option("label_text").value
            self.debug(label)
            self.debug(label_text)
            regions = roi.regions
            regions[label] = label_text

    def _roi_changed(self):
        roi = self.ivm.data.get(self.options.option("roi").value, None)
        self._toolbox.setEnabled(roi is not None)
        if roi is not None:
            # FIXME this will only work if ROI is NumpyData. Otherwise we are
            # manipulating a numpy array which may just be a proxy for the file
            # storage.
            self.roiname = roi.name
            self.grid = roi.grid
            self.roidata = roi.raw()
            regions = roi.regions
            self.options.option("label").value = min(list(regions.keys()) + [1, ])

    def _new_roi(self):
        dialog = QtGui.QDialog(self)
        dialog.setWindowTitle("New ROI")
        vbox = QtGui.QVBoxLayout()
        dialog.setLayout(vbox)

        optbox = OptionBox()
        optbox.add("ROI name", TextOption(), key="name")
        optbox.add("Data space from", DataOption(self.ivm), key="grid")
        vbox.addWidget(optbox)

        buttons = QtGui.QDialogButtonBox(QtGui.QDialogButtonBox.Ok | QtGui.QDialogButtonBox.Cancel)
        buttons.accepted.connect(dialog.accept)
        buttons.rejected.connect(dialog.reject)
        vbox.addWidget(buttons)
        
        ok = dialog.exec_()
        if ok:
            roiname = optbox.option("name").value
            grid = self.ivm.data[optbox.option("grid").value].grid
            roidata = np.zeros(grid.shape, dtype=np.int)
            self.ivm.add(NumpyData(roidata, grid=grid, roi=True, name=roiname), make_current=True)

            # Throw away old history. FIXME is this right, should we keep existing data and history?
            # Also should we cache old history in case we go back to this ROI?
            self._history = []
            self._undo_btn.setEnabled(False)
            self.options.option("roi").value = roiname

    def _tool_selected(self, tool):
        def _select():
            if self._tool is not None:
                self._tool.btn.setStyleSheet("")
                self._tool.deselected()
            
            self._tool = tool
            self._tool.btn.setStyleSheet("border: 2px solid QLinearGradient( x1: 0, y1: 0, x2: 0, y2: 1, stop: 0 #ffa02f, stop: 1 #d7801a);")
            # Replace the old tool options with the new one. Need to reparent the
            # existing layout to a temporary widget which will then get deleted 
            QtGui.QWidget().setLayout(self._tool_options.layout())
            self._tool_options.setLayout(self._tool.interface())
            self._tool_options.setTitle(tool.name)
            self._tool_options.setVisible(True)
            self._tool.selected()

        return _select
    
    def _add_tool(self, tool, x, y):
        tool.ivm = self.ivm
        tool.ivl = self.ivl
        tool.builder = self
        btn = QtGui.QPushButton()
        btn.setIcon(QtGui.QIcon(get_icon(tool.name.lower())))
        btn.setToolTip(tool.tooltip)
        btn.setFixedSize(32, 32)
        btn.clicked.connect(self._tool_selected(tool))
        tool.btn = btn
        self.tools_grid.addWidget(btn, x, y)
