import numpy as np

from PySide import QtGui

from quantiphyse.volumes import DataGrid
from quantiphyse.gui.widgets import QpWidget, TitleWidget, OverlayCombo, NumericOption, NumberGrid
from quantiphyse.utils import debug
from quantiphyse.utils.exceptions import QpException

class GridView(QtGui.QWidget):

    COORD_LABELS = {
        0 : "unknown",
        1 : "scanner",
        2 : "aligned",
        3 : "Talairach",
        4 : "MNI",
    }

    def __init__(self, ivl, readonly=False):
        self.ivl = ivl
        self.data = None

        QtGui.QWidget.__init__(self)
        grid = QtGui.QGridLayout()
        self.setLayout(grid)

        grid.addWidget(QtGui.QLabel("Grid->World Transform"), 1, 0)
        self.transform = NumberGrid(initial=np.identity(3), expandable=(False, False), fix_height=True, fix_width=True, readonly=readonly)
        self.transform.itemChanged.connect(self._changed)
        grid.addWidget(self.transform, 2, 0)
        grid.addWidget(QtGui.QLabel("Origin"), 1, 1)
        self.origin = NumberGrid(initial=[[0],]*3, expandable=(False, False), fix_height=True, fix_width=True, readonly=readonly)
        self.origin.itemChanged.connect(self._changed)
        grid.addWidget(self.origin, 2, 1)

        grid.addWidget(QtGui.QLabel("Co-ordinate system: "), 3, 0)
        self.coord_label = QtGui.QLabel("unknown")
        grid.addWidget(self.coord_label, 3, 1)

        grid.setColumnStretch(3, 1)
    
    def set_data(self, data):
        self.data = data
        if data is not None:
            if hasattr(data, "nifti_header"):
                self.coord_label.setText(self.COORD_LABELS[int(data.nifti_header['sform_code'])])
            self.transform.setValues(data.rawgrid.transform)
            print(data.rawgrid.origin)
            self.origin.setValues([[x,] for x in data.rawgrid.origin])
        else:
            self.coord_label.setText("unknown")
            self.transform.setValues(np.identity(3))
            self.origin.setValues([[0],]*3)

    def _changed(self):
        if self.data is not None:
            affine = self.data.rawgrid.affine
            if self.transform.valid():
                affine[:3,:3] = self.transform.values()
            if self.origin.valid():
                affine[:3,3] = [x[0] for x in self.origin.values()]
            newgrid = DataGrid(self.data.rawgrid.shape, affine)
            self.data.rawgrid = newgrid
            self.data.stddata = None
            self.ivl.update_ortho_views()
            print("data updated")

class DataInspectorWidget(QpWidget):
    """
    Widget that lets you tweak the orientation of data
    """
    def __init__(self, **kwargs):
        super(DataInspectorWidget, self).__init__(name="Data Inspector", icon="inspect.png", 
                                                  desc="Manipulate data orientation", 
                                                  group="Utilities", **kwargs)
        
    def init_ui(self):
        vbox = QtGui.QVBoxLayout()
        self.setLayout(vbox)

        title = TitleWidget(self)
        vbox.addWidget(title)

        vbox.addWidget(QtGui.QLabel())
        vbox.addWidget(QtGui.QLabel('<font size="4">Main data grid</font>'))
        self.maingrid = GridView(self.ivl, readonly=True)
        vbox.addWidget(self.maingrid)

        vbox.addWidget(QtGui.QLabel())
        vbox.addWidget(QtGui.QLabel('<font size="4">Modify data orientation</font>'))

        hbox = QtGui.QHBoxLayout()
        hbox.addWidget(QtGui.QLabel("Select data item"))
        self.data_combo = OverlayCombo(self.ivm, data=True, rois=True)
        self.data_combo.currentIndexChanged.connect(self.sel_data_changed)
        hbox.addWidget(self.data_combo)
        hbox.addStretch(1)
        vbox.addLayout(hbox)

        self.selgrid = GridView(self.ivl)
        vbox.addWidget(self.selgrid)
        
        vbox.addStretch(1) 

    def activate(self):
        self.ivm.sig_main_data.connect(self.main_data_changed)
        self.main_data_changed(self.ivm.main)
        self.sel_data_changed()

    def deactivate(self):
        self.ivm.sig_main_data.disconnect(self.main_data_changed)

    def main_data_changed(self, data):
        self.maingrid.set_data(data)

    def sel_data_changed(self):
        name = self.data_combo.currentText()
        d = self.ivm.data.get(name, self.ivm.rois.get(name, None))
        self.selgrid.set_data(d)



