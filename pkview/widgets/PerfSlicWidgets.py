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
        optbox.setTitle("Supervoxel Generation")
        grid = QtGui.QGridLayout()
        optbox.setLayout(grid)
        self.n_comp = NumericOption("Number of components", grid, 0, minval=1, maxval=3, default=3, intonly=True)
        self.compactness = NumericOption("Compactness", grid, 1, minval=0, maxval=1, default=0.02, intonly=False)
        self.segment_size = NumericOption("Segment size", grid, 2, minval=1, maxval=10000, default=1000, intonly=True)
        btn = QtGui.QPushButton('Generate supervoxels', self)
        btn.clicked.connect(self.generate)
        grid.addWidget(btn, 3, 0)
        hbox.addWidget(optbox)
        hbox.addStretch(1)
        layout.addLayout(hbox)

        hbox = QtGui.QHBoxLayout()
        self.roibox = QtGui.QGroupBox()
        self.roibox.setTitle("ROI from Supervoxels")
        grid = QtGui.QGridLayout()
        self.roibox.setLayout(grid)
        grid.addWidget(QtGui.QLabel("Supervoxel Picking"), 0, 0)
        self.pick_btn = QtGui.QPushButton("Start");
        self.pick_btn.clicked.connect(self.pick_clicked)
        grid.addWidget(self.pick_btn, 0, 1)
        grid.addWidget(QtGui.QLabel("Freehand tool"), 1, 0)
        self.freehand_btn = QtGui.QPushButton("Start");
        self.freehand_btn.clicked.connect(self.freehand_clicked)
        grid.addWidget(self.freehand_btn, 1, 1)
        btn = QtGui.QPushButton("Undo");
        btn.clicked.connect(self.roi_undo)
        grid.addWidget(btn, 2, 0)
        btn = QtGui.QPushButton("Reset");
        btn.clicked.connect(self.roi_reset)
        grid.addWidget(btn, 2, 1)
        hbox.addWidget(self.roibox)
        hbox.addStretch(1)
        layout.addLayout(hbox)
        layout.addStretch(1)

        self.roibox.setEnabled(False)

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

        self.ivm.set_overlay(name="supervoxels", data=ovl, force=True)
        self.ivm.set_current_overlay("supervoxels")
        self.roibox.setEnabled(True)
        self.roi_reset()

        #self.ivm.add_roi(name="supervoxels", img=ovl, make_current=True)

        #bound = seg.find_boundaries(ovl, mode='inner')
        #self.ivm.set_overlay(name="supervoxels", data=bound, force=True)
        #self.ivm.set_current_overlay("supervoxels")

    def pick_clicked(self):
        if self.pick_btn.text() == "Start":
            self.pick_btn.setText("Stop")
            self.picking_roi = True
        elif self.pick_btn.text() == "Stop":
            self.picking_roi = False
            self.pick_btn.setText("Start")

    def freehand_clicked(self):
        if self.freehand_btn.text() == "Start":
            self.freehand_btn.setText("Stop")
            self.freehand_roi = True
        elif self.freehand_btn.text() == "Stop":
            self.freehand_roi = False
            self.freehand_btn.setText("Start")

    def roi_reset(self):
        self.roi = np.zeros(self.ivm.img_dims[:3], dtype=np.int8)
        self.roi_hist = []
        self.roi_regions = set()
        self.picking_roi = False
        self.freehand_roi = False
        self.pick_btn.setText("Start")
        self.freehand_btn.setText("Start")

    def roi_undo(self):
        last_change = self.roi_hist[-1]
        ovl = self.ivm.overlay_all["supervoxels"]
        for val in last_change:
            if val < 0:
                # Undo region removal, i.e. add it back
                self.roi = self.roi | np.where(ovl == val, 1, 0)
                self.roi_regions.add(val)
            else:
                # Undo region addition, i.e. remove it
                self.roi = self.roi & np.where(ovl == val, 0, 1)
                self.roi_regions.remove(val)
        self.roi_hist = self.roi_hist[:-1]
        self.ivm.add_roi(name="sv_roi", img=self.roi, make_current=True)

    def sig_mouse_click(self, values):
        if self.picking_roi:
            pos = self.ivm.cim_pos[:3]
            ovl = self.ivm.overlay_all["supervoxels"]
            val = ovl[pos[0], pos[1], pos[2]]
            if val in self.roi_regions:
                self.roi = self.roi & np.where(ovl == val, 0, 1)
                self.roi_hist.append([-val])
                self.roi_regions.remove(val)
            else:
                self.roi = self.roi | np.where(ovl == val, 1, 0)
                self.roi_hist.append([val])
                self.roi_regions.add(val)
            self.ivm.add_roi(name="sv_roi", img=self.roi, make_current=True)


