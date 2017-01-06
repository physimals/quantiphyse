from PySide import QtGui
import numpy as np
import skimage.segmentation as seg

from pkview.analysis.perfusionslic import PerfSLIC

class NumericOption:
    def __init__(self, text, grid, ypos, minval=0, maxval=100, default=0, intonly=False):
        self.label = QtGui.QLabel(text)
        if intonly:
            self.spin = QtGui.QSpinBox()
        else:
            self.spin = QtGui.QDoubleSpinBox()

        self.spin.setMinimum(minval)
        self.spin.setMaximum(maxval)
        self.spin.setValue(default)
        grid.addWidget(self.label, ypos, 0)
        grid.addWidget(self.spin, ypos, 1)

class PerfSlicWidget(QtGui.QWidget):
    """
    Generates supervoxels using SLIC method
    """
    def __init__(self):
        super(PerfSlicWidget, self).__init__()

        layout = QtGui.QVBoxLayout()
        self.setLayout(layout)

        layout.addWidget(QtGui.QLabel("<font size=50>Supervoxel Generation</font> \n"))

        hbox = QtGui.QHBoxLayout()
        optbox = QtGui.QGroupBox()
        optbox.setTitle("Options")
        grid = QtGui.QGridLayout()
        optbox.setLayout(grid)
        self.n_comp = NumericOption("Number of components", grid, 0, minval=1, maxval=3, default=3, intonly=True)
        self.compactness = NumericOption("Compactness", grid, 1, minval=0, maxval=1, default=0.02, intonly=False)
        self.segment_size = NumericOption("Segment size", grid, 2, minval=1, maxval=10000, default=1000, intonly=True)
        hbox.addWidget(optbox)
        hbox.addStretch(1)
        layout.addLayout(hbox)

        hbox = QtGui.QHBoxLayout()
        btn = QtGui.QPushButton('Generate supervoxels', self)
        btn.clicked.connect(self.generate)
        hbox.addWidget(btn)
        hbox.addStretch(1)
        layout.addLayout(hbox)

        layout.addStretch(1)

    def add_image_management(self, image_vol_management):
        """
        Adding image management
        """
        self.ivm = image_vol_management

    def generate(self):
        img = self.ivm.get_image()
        if img is None:
            QtGui.QMessageBox.warning(self, "No volume loaded", "Load a volume before generating supervoxels", QtGui.QMessageBox.Close)
            return

        ncomp = self.n_comp.spin.value()
        comp = self.compactness.spin.value()
        ss = self.segment_size.spin.value()

        vox_size = np.ones(3) # FIXME

        print("Initialise the perf slic class")
        ps1 = PerfSLIC(img, vox_size)
        print("Normalising image...")
        ps1.normalise_curves()
        print("Extracting features...")
        ps1.feature_extraction(n_components=ncomp)
        print("Extracting supervoxels...")
        segments = ps1.supervoxel_extraction(compactness=comp, segment_size=ss)
        ovl = np.array(segments, dtype=np.int)

        #self.ivm.set_overlay(name="supervoxels", data=ovl, force=True)
        #self.ivm.set_current_overlay("supervoxels")
        self.ivm.add_roi(name="supervoxels", img=ovl, make_current=True)

        bound = seg.find_boundaries(ovl, mode='inner')
        self.ivm.set_overlay(name="supervoxels", data=bound, force=True)
        self.ivm.set_current_overlay("supervoxels")
