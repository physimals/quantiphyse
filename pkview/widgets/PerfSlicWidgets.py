from PySide import QtGui
import numpy as np
import skimage.segmentation as seg

from ..QtInherit import HelpButton
from ..analysis.perfusionslic import PerfSLIC
from ..analysis.overlay_analysis import OverlayAnalysis
from . import PkWidget

CITE = """
<i>Irving et al (2017)
"maskSLIC: Regional Superpixel Generation with Application to Local Pathology Characterisation in Medical Images"
https://arxiv.org/abs/1606.09518v2</i>
"""

class NumericOption:
    def __init__(self, text, grid, ypos, minval=0, maxval=100, default=0, step=1, intonly=False):
        self.label = QtGui.QLabel(text)
        if intonly:
            self.spin = QtGui.QSpinBox()
        else:
            self.spin = QtGui.QDoubleSpinBox()

        self.spin.setMinimum(minval)
        self.spin.setMaximum(maxval)
        self.spin.setValue(default)
        self.spin.setSingleStep(step)
        grid.addWidget(self.label, ypos, 0)
        grid.addWidget(self.spin, ypos, 1)

class PerfSlicWidget(PkWidget):
    """
    Generates supervoxels using SLIC method
    """
    def __init__(self, **kwargs):
        super(PerfSlicWidget, self).__init__(name="Super Voxels", icon="sv", desc="Generate supervoxel clusters", **kwargs)
        
    def init_ui(self):
        self.picking_roi = False
        self.freehand_roi = False

        layout = QtGui.QVBoxLayout()
        self.setLayout(layout)

        hbox = QtGui.QHBoxLayout()
        hbox.addWidget(QtGui.QLabel('<font size="5">Supervoxel Generation</font>'))
        hbox.addStretch(1)
        hbox.addWidget(HelpButton(self, "sv"))
        layout.addLayout(hbox)
        
        cite = QtGui.QLabel(CITE)
        cite.setWordWrap(True)
        layout.addWidget(cite)
        layout.addWidget(QtGui.QLabel(""))

        hbox = QtGui.QHBoxLayout()
        optbox = QtGui.QGroupBox()
        optbox.setTitle("Options")
        grid = QtGui.QGridLayout()
        optbox.setLayout(grid)
        self.n_comp = NumericOption("Number of components", grid, 0, minval=1, maxval=3, default=3, intonly=True)
        self.compactness = NumericOption("Compactness", grid, 1, minval=0.01, maxval=1, step=0.05, default=0.1, intonly=False)
        self.segment_number = NumericOption("Number of supervoxels", grid, 2, minval=2, maxval=1000, default=20, intonly=True)

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

    def generate(self):
        if self.ivm.vol is None:
            QtGui.QMessageBox.warning(self, "No volume loaded", "Load a volume before generating supervoxels", QtGui.QMessageBox.Close)
            return
        
        if self.ivm.current_roi is None:
            QtGui.QMessageBox.warning(self, "No ROI loaded", "Load an ROI before generating supervoxels", QtGui.QMessageBox.Close)
            return
        
        options = {"n-components" : self.n_comp.spin.value(),
                   "compactness" : self.compactness.spin.value(),
                   "segment-size" :  self.segment_number.spin.value() }

        process = SupervoxelsProcess(self.ivm, sync=True)
        process.run(options)
        if process.status != Process.SUCCEEDED:
            QtGui.QMessageBox.warning(None, "Process error", "Supervoxels process failed to run:\n\n" + str(process.output),
                                      QtGui.QMessageBox.Close)

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
            ovl = self.ivm.overlays["supervoxels"]
            for val in svoxels:
                self.roi = self.roi | np.where(ovl == val, 1, 0)
                self.roi_regions.add(val)
            self.roi_hist.append(svoxels)
            self.ivm.add_roi("sv_roi", self.roi, make_current=True)

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
        ovl = self.ivm.overlays["supervoxels"]
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
        self.ivm.add_roi("sv_roi", self.roi, make_current=True)

    def sig_mouse_click(self, values):
        pos = self.ivm.cim_pos[:3]
        if self.picking_roi:
            ovl = self.ivm.overlays["supervoxels"]
            val = ovl[pos[0], pos[1], pos[2]]

            if val in self.roi_regions:
                self.roi = self.roi & np.where(ovl == val, 0, 1)
                self.roi_hist.append([-val])
                self.roi_regions.remove(val)
            else:
                self.roi = self.roi | np.where(ovl == val, 1, 0)
                self.roi_hist.append([val])
                self.roi_regions.add(val)
            self.ivm.add_roi("sv_roi", self.roi, make_current=True)


class MeanValuesWidget(PkWidget):
    """
    Convert an overlay + multi-level ROI into mean values overlay
    """
    def __init__(self, **kwargs):
        super(MeanValuesWidget, self).__init__(name="Mean Values", icon="meanvals", desc="Generate mean values overlays", **kwargs)

        layout = QtGui.QVBoxLayout()

        hbox = QtGui.QHBoxLayout()
        hbox.addWidget(QtGui.QLabel('<font size="5">Generate Mean Values Overlay</font>'))
        hbox.addStretch(1)
        hbox.addWidget(HelpButton(self, "mean_values"))
        layout.addLayout(hbox)
        
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

        oa = OverlayAnalysis(self.ivm)
        stat1, roi_labels, hist1, hist1x = oa.get_roi_stats()

        #ov_name = "%s_in_%s" % (self.ivm.current_overlay.name, self.ivm.current_roi.name)
        ov_name = self.ivm.current_overlay.name + "_means"
        ov_data = np.copy(self.ivm.current_overlay)
        for region, mean in zip(roi_labels, stat1["mean"]):
            ov_data[roi == region] = mean

        self.ivm.add_overlay(ov_name, ov_data, make_current=True)


