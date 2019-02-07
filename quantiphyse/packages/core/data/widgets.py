"""
Quantiphyse - Widgets for viewing and modifying data orientation and grids

Copyright (c) 2013-2018 University of Oxford
"""

import math

import numpy as np

from PySide import QtGui

from quantiphyse.gui.widgets import QpWidget, TitleWidget, NumberGrid
from quantiphyse.gui.options import OptionBox, DataOption, ChoiceOption, OutputNameOption, RunButton, NumericOption

from .processes import ResampleProcess

class ResampleDataWidget(QpWidget):
    """
    Widget that lets you resample data onto a different grid
    """
    def __init__(self, **kwargs):
        super(ResampleDataWidget, self).__init__(name="Resample Data", icon="resample.png", 
                                                 desc="Resample data onto the same grid as another data item",
                                                 group="Utilities", **kwargs)
        
    def init_ui(self):
        vbox = QtGui.QVBoxLayout()
        self.setLayout(vbox)

        vbox.addWidget(TitleWidget(self))

        optbox = OptionBox("Resampling options")
        self.data = optbox.add("Data to resample", DataOption(self.ivm))
        self.grid_data = optbox.add("Resample onto grid from", DataOption(self.ivm))
        self.order = optbox.add("Interpolation", ChoiceOption(["Nearest neighbour", "Linear", "Quadratic", "Cubic"], [0, 1, 2, 3]))
        self.output_name = optbox.add("Output name", OutputNameOption(src_data=self.data, suffix="_res"))
        vbox.addWidget(optbox)

        self.run = RunButton("Resample", self._run)
        vbox.addWidget(self.run)

        vbox.addStretch(1)
    
    def batch_options(self):
        options = {
            "data" : self.data.value,
            "grid" : self.grid_data.value,
            "output-name" : self.output_name.value,
            "order" : self.order.value,
        }

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
        vbox = QtGui.QVBoxLayout()
        self.setLayout(vbox)

        title = TitleWidget(self)
        vbox.addWidget(title)

        hbox = QtGui.QHBoxLayout()
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

        hbox = QtGui.QHBoxLayout()
        reset_btn = QtGui.QPushButton("Reset to original")
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
        for axis in range(3):
            angle = rotations[axis]
            rot3d = self._rotmtx_3d(axis, angle)
            affine[:3, :3] = np.dot(rot3d, affine[:3, :3])
            origin_offset = world_centre - np.dot(rot3d, world_centre)
            #origin_offset[axis] = 0
            self.debug("Origin offset\n%s", origin_offset)
            translation += origin_offset

        affine[:3, 3] += translation
        self.debug("Final affine\n%s", affine)
        self.gridview.data.grid.affine = affine
        self.gridview.update()
        # HACK
        if self.gridview.data == self.ivm.current_data:
            self.ivm.sig_current_data.emit(self.ivm.current_data)
        elif self.gridview.data == self.ivm.main:
            self.ivm.sig_main_data.emit(self.ivm.main)

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

class GridView(QtGui.QWidget):

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

        QtGui.QWidget.__init__(self)
        grid = QtGui.QGridLayout()
        self.setLayout(grid)

        grid.addWidget(QtGui.QLabel("Grid->World Transform"), 1, 0)
        self.transform = NumberGrid(initial=np.identity(3), expandable=(False, False), fix_height=True, fix_width=True, readonly=readonly)
        self.transform.sig_changed.connect(self._changed)
        grid.addWidget(self.transform, 2, 0)

        grid.addWidget(QtGui.QLabel("Origin"), 1, 1)
        self.origin = NumberGrid(initial=[[0],]*3, expandable=(False, False), fix_height=True, fix_width=True, readonly=readonly)
        self.origin.sig_changed.connect(self._changed)
        grid.addWidget(self.origin, 2, 1)

        grid.addWidget(QtGui.QLabel("Co-ordinate system: "), 3, 0)
        self.coord_label = QtGui.QLabel("unknown")
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
                