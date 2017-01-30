from PySide import QtGui
import numpy as np
import skimage.segmentation as seg
from pkview.volumes.volume_management import Overlay, Roi

from pkview.analysis.perfusionslic import PerfSLIC
from pkview.analysis.overlay_analysis import OverlayAnalyis


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
        self.picking_roi = False
        self.freehand_roi = False

        layout = QtGui.QVBoxLayout()
        self.setLayout(layout)

        layout.addWidget(QtGui.QLabel("<font size=5>Supervoxel Generation</font> \n"))

        hbox = QtGui.QHBoxLayout()
        optbox = QtGui.QGroupBox()
        optbox.setTitle("Supervoxel Generation")
        grid = QtGui.QGridLayout()
        optbox.setLayout(grid)
        self.n_comp = NumericOption("Number of components", grid, 0, minval=1, maxval=3, default=3, intonly=True)
        self.compactness = NumericOption("Compactness", grid, 1, minval=0, maxval=1, default=0.1, intonly=False)
        # self.segment_size = NumericOption("Segment size", grid, 2, minval=1, maxval=10000, default=1000, intonly=True)
        self.segment_number = NumericOption("Segment size", grid, 2, minval=2, maxval=10000, default=30, intonly=True)

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
        grid.addWidget(QtGui.QLabel("Rubber band tool"), 1, 0)
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

        # Disable supervoxel picking for now
        #layout.addLayout(hbox)
        layout.addStretch(1)

        self.roibox.setEnabled(False)

    def add_image_management(self, image_vol_management):
        self.ivm = image_vol_management

    def add_image_view(self, ivl):
        self.ivl = ivl

    def generate(self):
        if self.ivm.vol is None:
            QtGui.QMessageBox.warning(self, "No volume loaded", "Load a volume before generating supervoxels", QtGui.QMessageBox.Close)
            return
        img = self.ivm.vol.data

        if self.ivm.current_roi is None:
            QtGui.QMessageBox.warning(self, "No ROI loaded", "Load an ROI before generating supervoxels", QtGui.QMessageBox.Close)
            return

        ncomp = self.n_comp.spin.value()
        comp = self.compactness.spin.value()
        # ss = self.segment_size.spin.value()
        sn = self.segment_number.spin.value()


        vox_size = np.ones(3) # FIXME

        print("Initialise the perf slic class")
        ps1 = PerfSLIC(img, vox_size, mask=self.ivm.current_roi.data)
        print("Normalising image...")
        ps1.normalise_curves()
        print("Extracting features...")
        ps1.feature_extraction(n_components=ncomp)
        print("Extracting supervoxels...")
        segments = ps1.supervoxel_extraction(compactness=comp, seed_type='nrandom',
                                             recompute_seeds=True, segment_size=sn)
        # Add 1 to the supervoxel IDs as 0 is used as 'empty' value
        svdata = np.array(segments, dtype=np.int) + 1

        #self.ivm.add_overlay(Overlay(name="supervoxels", data=svdata), make_current=True)
        #self.roibox.setEnabled(True)
        #self.roi_reset()

        self.ivm.add_roi(Roi(name="supervoxels", data=svdata), make_current=True)

        #bound = seg.find_boundaries(ovl, mode='inner')
        #self.ivm.set_overlay(name="supervoxels", data=bound, force=True)
        #self.ivm.set_current_overlay("supervoxels")

    def pick_clicked(self):
        if self.pick_btn.text() == "Start":
            self.pick_btn.setText("Stop")
            self.picking_roi = True
            if self.freehand_roi:
                self.freehand_btn.setText("Start")
                self.freehand_roi = False
                self.ivl.stop_roi_lasso("supervoxels")
        elif self.pick_btn.text() == "Stop":
            self.picking_roi = False
            self.pick_btn.setText("Start")

    def closest(self, num, collection):
        return min(collection, key=lambda x: abs(x - num))

    def freehand_clicked(self):
        if self.freehand_btn.text() == "Start":
            self.freehand_btn.setText("Stop")
            self.freehand_roi = True
            self.ivl.start_roi_lasso()
            if self.picking_roi:
                self.pick_btn.setText("Start")
                self.picking_roi = False
        elif self.freehand_btn.text() == "Stop":
            self.freehand_roi = False
            self.freehand_btn.setText("Start")
            # PyQtGraph's ROI selection tool does interpolation
            # so we get slightly odd results when applied to
            # and integer overlay like 'supervoxels'
            #
            # This code first figures out what integer svoxels
            # were in the selection, then replaces non-integer
            # values in the selection with the closest supervoxel
            # integer (note that this is NOT the closest integer!
            sel = self.ivl.stop_roi_lasso("supervoxels")
            svoxels = [v for v in np.unique(sel) if v == int(v)]
            f = np.vectorize(lambda x: self.closest(x, svoxels))
            sel = f(sel)
            print(sel)
            ovl = self.ivm.overlays["supervoxels"].data
            for val in svoxels:
                self.roi = self.roi | np.where(ovl == val, 1, 0)
                self.roi_regions.add(val)
            self.roi_hist.append(svoxels)
            self.ivm.add_roi(Roi(name="sv_roi", data=self.roi), make_current=True)

    def roi_reset(self):
        self.roi = np.zeros(self.ivm.vol.shape[:3], dtype=np.int8)
        self.roi_hist = []
        self.roi_regions = set()
        self.picking_roi = False
        self.freehand_roi = False
        self.pick_btn.setText("Start")
        self.freehand_btn.setText("Start")

    def roi_undo(self):
        last_change = self.roi_hist[-1]
        ovl = self.ivm.overlays["supervoxels"].data
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
        self.ivm.add_roi(Roi(name="sv_roi", data=self.roi), make_current=True)

    def sig_mouse_click(self, values):
        pos = self.ivm.cim_pos[:3]
        if self.picking_roi:
            ovl = self.ivm.overlays["supervoxels"].data
            val = ovl[pos[0], pos[1], pos[2]]

            if val in self.roi_regions:
                self.roi = self.roi & np.where(ovl == val, 0, 1)
                self.roi_hist.append([-val])
                self.roi_regions.remove(val)
            else:
                self.roi = self.roi | np.where(ovl == val, 1, 0)
                self.roi_hist.append([val])
                self.roi_regions.add(val)
            self.ivm.add_roi(Roi(name="sv_roi", data=self.roi), make_current=True)


class MeanValuesWidget(QtGui.QWidget):
    """
    Convert an overlay + multi-level ROI into mean values overlay
    """
    def __init__(self):
        super(MeanValuesWidget, self).__init__()

        layout = QtGui.QVBoxLayout()
        layout.addWidget(QtGui.QLabel("<font size=50>Generate Mean Values Overlay</font> \n"))
        desc = QtGui.QLabel("This widget will convert the current overlay into a "
                            "new overlay in which each ROI region contains the mean "
                            "value for that region.\n\nThis is generally only useful for "
                            "multi-level ROIs such as clusters or supervoxels")
        desc.setWordWrap(True)
        layout.addWidget(desc)

        gbox = QtGui.QGroupBox()
        gbox.setTitle("Generate mean values overlay")

        vbox = QtGui.QVBoxLayout()
        gbox.setLayout(vbox)

        hbox = QtGui.QHBoxLayout()
        b = QtGui.QPushButton('Generate', self)
        b.clicked.connect(self.generate)
        hbox.addWidget(b)
        hbox.addStretch(1)
        vbox.addLayout(hbox)
        gbox.setLayout(vbox)

        layout.addWidget(gbox)
        layout.addStretch(1)
        self.setLayout(layout)

    def add_image_management(self, image_vol_management):
        self.ivm = image_vol_management

    def generate(self):
        roi = self.ivm.current_roi
        if roi is None:
            QtGui.QMessageBox.warning(self, "No ROI loaded", "Load an ROI before generating a mean values overlay",
                                      QtGui.QMessageBox.Close)
            return

        if self.ivm.current_overlay is None:
            QtGui.QMessageBox.warning(self, "No current overlay", "Load an overlay before generating a mean values overlay",
                                      QtGui.QMessageBox.Close)
            return

        oa = OverlayAnalyis()
        oa.add_image_management(self.ivm)
        stat1, roi_labels, hist1, hist1x = oa.get_roi_stats()

        #ov_name = "%s_in_%s" % (self.ivm.current_overlay.name, self.ivm.current_roi.name)
        ov_name = self.ivm.current_overlay.name + "_means"
        ov_data = np.copy(self.ivm.current_overlay.data)
        for region, mean in zip(roi_labels, stat1["mean"]):
            ov_data[roi.data == region] = mean

        ovl = Overlay(ov_name, data=ov_data)
        self.ivm.add_overlay(ovl)


