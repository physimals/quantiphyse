import numpy as np

from PySide import QtGui

from pkview.utils import table_to_str
from pkview.analysis import Process, BackgroundProcess

class CalcVolumesProcess(Process):
    """
    Calculate volume of ROI region or regions
    """
    def __init__(self, ivm, **kwargs):
        Process.__init__(self, ivm, **kwargs)
        self.model = QtGui.QStandardItemModel()

    def run(self, options):
        roi_name = options.pop('roi', None)
        sel_region = options.pop('region', None)

        if roi_name is None:
            roi = self.ivm.current_roi
        else:
            roi = self.ivm.rois[roi_name]

        self.model.clear()
        self.model.setVerticalHeaderItem(0, QtGui.QStandardItem("Num voxels"))
        self.model.setVerticalHeaderItem(1, QtGui.QStandardItem("Volume (mm^3)"))

        sizes = self.ivm.voxel_sizes
        if roi is not None:
            counts = np.bincount(roi.flatten())
            for idx, region in enumerate(roi.regions):
                if sel_region is None or region == sel_region:
                    nvoxels = counts[region]
                    vol = counts[region]*sizes[0]*sizes[1]*sizes[2]
                    self.model.setHorizontalHeaderItem(idx, QtGui.QStandardItem("Region %i" % region))
                    self.model.setItem(0, idx, QtGui.QStandardItem(str(nvoxels)))
                    self.model.setItem(1, idx, QtGui.QStandardItem(str(vol)))

        no_artifact = options.pop('no-artifact', False)
        if not no_artifact: 
            output_name = options.pop('output-name', "roi-vols")
            self.ivm.add_artifact(output_name, table_to_str(self.model))
        self.status = Process.SUCCEEDED

class SimpleMathsProcess(Process):
    
    def __init__(self, ivm, **kwargs):
        Process.__init__(self, ivm, **kwargs)
        self.model = QtGui.QStandardItemModel()

    def run(self, options):
        globals = {'np': np, 'ivm': self.ivm}
        for name, ovl in self.ivm.overlays.items():
            globals[name] = ovl
        for name, proc in options.items():
            result = eval(proc, globals)
            self.ivm.add_overlay(name, result)
       
        self.status = Process.SUCCEEDED
