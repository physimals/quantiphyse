"""
Quantiphyse - Widgets for viewing and modifying data orientation and grids

Copyright (c) 2013-2020 University of Oxford

Licensed under the Apache License, Version 2.0 (the "License");
you may not use this file except in compliance with the License.
You may obtain a copy of the License at

    http://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and
limitations under the License.
"""

import math

import numpy as np

from PySide2 import QtGui, QtCore, QtWidgets

from quantiphyse.gui.widgets import QpWidget, TitleWidget, NumberGrid
from quantiphyse.gui.options import OptionBox, DataOption, ChoiceOption, OutputNameOption, RunButton, NumericOption, NumberListOption, BoolOption
from quantiphyse.utils.enums import Visibility

from .processes import ResampleProcess

class ResampleDataWidget(QpWidget):
    """
    Widget that lets you resample data onto a different grid
    """
    def __init__(self, **kwargs):
        super(ResampleDataWidget, self).__init__(name="Resample Data", icon="resample.png", 
                                                 desc="Resample data onto a different grid",
                                                 group="Utilities", **kwargs)
        
    def init_ui(self):
        vbox = QtWidgets.QVBoxLayout()
        self.setLayout(vbox)

        vbox.addWidget(TitleWidget(self))

        self.optbox = OptionBox("Resampling options")
        self.data = self.optbox.add("Data to resample", DataOption(self.ivm), key="data")
        self.resample_type = self.optbox.add("Resampling method", ChoiceOption(["On to grid from another data set", "Upsample", "Downsample", "Specified resolution"], ["data", "up", "down", "res"]), key="type")
        self.grid_data = self.optbox.add("Use grid from", DataOption(self.ivm), key="grid")
        self.factor = self.optbox.add("Factor", NumericOption(default=2, minval=2, maxval=10, intonly=True), key="factor")
        self.voxel_sizes = self.optbox.add("Voxel sizes (mm)", NumberListOption(), key="voxel-sizes")
        self.slicewise = self.optbox.add("2D only", BoolOption(), key="2d")
        self.order = self.optbox.add("Interpolation", ChoiceOption(["Nearest neighbour", "Linear", "Quadratic", "Cubic"], [0, 1, 2, 3], default=1), key="order")
        self.output_name = self.optbox.add("Output name", OutputNameOption(src_data=self.data, suffix="_res"), key="output-name")
        vbox.addWidget(self.optbox)
        self.resample_type.sig_changed.connect(self._resample_type_changed)

        self.run = RunButton("Resample", self._run)
        vbox.addWidget(self.run)
        vbox.addStretch(1)

        self._resample_type_changed()

    def _resample_type_changed(self):
        resample_type = self.resample_type.value
        self.optbox.set_visible("grid", resample_type == "data")
        self.optbox.set_visible("factor", resample_type in ("up", "down"))
        self.optbox.set_visible("order", resample_type != "down")
        self.optbox.set_visible("2d", resample_type in ("up", "down"))
        self.optbox.set_visible("voxel-sizes", resample_type == "res")

    def batch_options(self):
        options = self.optbox.values()
        return "Resample", options

    def _run(self):
        _, options = self.batch_options()
        ResampleProcess(self.ivm).run(options)

class OrientDataWidget(QpWidget):
    """
    Widget that lets you tweak the orientation of data
    """
    def __init__(self, **kwargs):
        super(OrientDataWidget, self).__init__(name="Orient Data", icon="inspect.png", 
                                               desc="Manipulate data orientation", 
                                               group="Utilities", **kwargs)
        self._transform_cache = {}
        self.ivm.sig_all_data.connect(self._all_data_changed)

    def init_ui(self):
        vbox = QtWidgets.QVBoxLayout()
        self.setLayout(vbox)

        title = TitleWidget(self)
        vbox.addWidget(title)

        hbox = QtWidgets.QHBoxLayout()
        self.options = OptionBox("Re-orient data")
        data = self.options.add("Data item", DataOption(self.ivm), key="data")
        data.sig_changed.connect(self._data_changed)
        self.trans, self.rot = {}, {}
        self.options.add("Translation")
        for axis, label in {2 : "axial", 0 : "sagittal", 1 : "coronal"}.items():
            trans = self.options.add("  %s (mm)" % label.title(), NumericOption(minval=-100, maxval=100, default=0), key="trans-%s" % label)
            trans.sig_changed.connect(self._translate(axis, label))
            self.trans[axis] = trans
        self.options.add("Rotation")
        for axis, label in {2 : "axial", 0 : "sagittal", 1 : "coronal"}.items():
            rot = self.options.add("  %s (degrees)" % label.title(), NumericOption(minval=-180, maxval=180, default=0), key="rot-%s" % label)
            rot.sig_changed.connect(self._rotate(axis, label))
            self.rot[axis] = rot
        hbox.addWidget(self.options)
        vbox.addLayout(hbox)

        self.gridview = GridView(self.ivm, self.ivl)
        vbox.addWidget(self.gridview)

        hbox = QtWidgets.QHBoxLayout()
        reset_btn = QtWidgets.QPushButton("Reset to original")
        reset_btn.clicked.connect(self._reset)
        hbox.addWidget(reset_btn)
        hbox.addStretch(1)
        vbox.addLayout(hbox)

        vbox.addStretch(1) 

    def activate(self):
        self._data_changed()

    def _all_data_changed(self, data):
        for name in list(self._transform_cache.keys()):
            if name not in data:
                del self._transform_cache[name]

    def _data_changed(self):
        name = self.options.values()["data"]
        qpdata = self.ivm.data.get(name, self.ivm.rois.get(name, None))
        self.gridview.set_data(qpdata)
        if qpdata is not None:
            if name not in self._transform_cache:
                self._transform_cache[name] = ([0, 0, 0], [0, 0, 0])
            translation, rotations = self._transform_cache[name]
            for axis in range(3):
                self.trans[axis].value = translation[axis]
                self.rot[axis].value = rotations[axis]
            self._set()

    def _translate(self, axis, label):
        def _trans():
            name = self.gridview.data.name
            trans = self.options.values()["trans-%s" % label]
            self._transform_cache[name][0][axis] = trans
            self._set()
        return _trans

    def _rotate(self, axis, label):
        def _rot():
            name = self.gridview.data.name
            angle = self.options.values()["rot-%s" % label]
            if axis == 1: angle = -angle
            self._transform_cache[name][1][axis] = angle
            self._set()
        return _rot

    def _reset(self):
        name = self.gridview.data.name
        del self._transform_cache[name]
        self._data_changed()

    def _set(self):
        name = self.gridview.data.name
        affine = self.gridview.data.grid.affine_orig
        grid_centre = [float(dim) / 2 for dim in self.gridview.data.grid.shape]
        world_centre = np.dot(affine[:3, :3], grid_centre)
        self.debug("Initial affine\n%s", affine)
        translation, rotations = self._transform_cache[name]

        R = np.identity(3)
        for axis in range(3):
            angle = rotations[axis]
            rot3d = self._rotmtx_3d(axis, angle)
            affine[:3, :3] = np.dot(rot3d, affine[:3, :3])
            R = np.dot(rot3d, R)

        origin_offset = world_centre - np.dot(R, world_centre)
        origin_offset += translation
        self.debug("Origin offset\n%s", origin_offset)
        affine[:3, 3] += origin_offset

        self.debug("Final affine\n%s", affine)
        self.gridview.data.grid.affine = affine
        self.gridview.update()
        if self.gridview.data == self.ivm.main:
            self.ivm.sig_main_data.emit(self.ivm.main)
        if self.gridview.data.view.visible == Visibility.SHOW or self.gridview.data == self.ivm.main:
            self.ivl.redraw()

    def _rotmtx_3d(self, axis, angle):
        # FIXME this is not quite right when rotating in a plane where
        # the basis vectors have different lengths
        c, s = math.cos(math.radians(angle)), math.sin(math.radians(angle))
        rot2d = np.array([[c, -s], [s, c]])
        rot3d = np.identity(3)
        if axis == 0:
            rot3d[1:, 1:] = rot2d
        elif axis == 1:
            rot3d[0, 0] = rot2d[0, 0]
            rot3d[0, 2] = rot2d[0, 1]
            rot3d[2, 0] = rot2d[1, 0]
            rot3d[2, 2] = rot2d[1, 1]
        elif axis == 2:
            rot3d[:2, :2] = rot2d
        self.debug("3d rotation matrix: %i %f", axis, angle)
        self.debug("\n%s", rot3d)
        return rot3d

class GridView(QtWidgets.QWidget):

    COORD_LABELS = {
        0 : "unknown",
        1 : "scanner",
        2 : "aligned",
        3 : "Talairach",
        4 : "MNI",
    }

    def __init__(self, ivm, ivl, readonly=False):
        self.ivm, self.ivl = ivm, ivl
        self.data = None
        self._updating = False

        QtWidgets.QWidget.__init__(self)
        grid = QtWidgets.QGridLayout()
        self.setLayout(grid)

        grid.addWidget(QtWidgets.QLabel("Grid->World Transform"), 1, 0)
        self.transform = NumberGrid(initial=np.identity(3), expandable=(False, False), fix_height=True, fix_width=True, readonly=readonly)
        self.transform.sig_changed.connect(self._changed)
        grid.addWidget(self.transform, 2, 0)

        grid.addWidget(QtWidgets.QLabel("Origin"), 1, 1)
        self.origin = NumberGrid(initial=[[0],]*3, expandable=(False, False), fix_height=True, fix_width=True, readonly=readonly)
        self.origin.sig_changed.connect(self._changed)
        grid.addWidget(self.origin, 2, 1)

        grid.addWidget(QtWidgets.QLabel("Co-ordinate system: "), 3, 0)
        self.coord_label = QtWidgets.QLabel("unknown")
        grid.addWidget(self.coord_label, 3, 1)

        grid.setColumnStretch(3, 1)
    
    def set_data(self, data):
        if data == self.data:
            return
        self.data = data
        self.update()

    def update(self):
        self._updating = True
        try:
            if self.data is not None:
                if hasattr(self.data, "nifti_header"):
                    self.coord_label.setText(self.COORD_LABELS[int(self.data.nifti_header['sform_code'])])
                self.transform.setValues(self.data.grid.transform)
                self.origin.setValues([[x,] for x in self.data.grid.origin])
            else:
                self.coord_label.setText("unknown")
                self.transform.setValues(np.identity(3))
                self.origin.setValues([[0],]*3)
        finally:
            self._updating = False

    def _changed(self):
        if self.data is not None and not self._updating:
            affine = self.data.grid.affine
            if self.transform.valid():
                affine[:3, :3] = self.transform.values()
            if self.origin.valid():
                affine[:3, 3] = [x[0] for x in self.origin.values()]
            self.data.grid.affine = affine
            # HACK
            if self.data == self.ivm.current_data:
                self.ivm.sig_current_data.emit(self.ivm.current_data)
            elif self.data == self.ivm.main:
                self.ivm.sig_main_data.emit(self.ivm.main)
                