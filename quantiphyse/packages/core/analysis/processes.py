import numpy as np
import scipy
import sys

from PySide import QtGui

from quantiphyse.volumes.io import NumpyData
from quantiphyse.utils import table_to_str, debug
from quantiphyse.utils.exceptions import QpException

from quantiphyse.analysis import Process

class CalcVolumesProcess(Process):
    """
    Calculate volume of ROI region or regions
    """

    PROCESS_NAME = "CalcVolumes"

    def __init__(self, ivm, **kwargs):
        Process.__init__(self, ivm, **kwargs)
        self.model = QtGui.QStandardItemModel()

    def run(self, options):
        self.model.clear()
        self.model.setVerticalHeaderItem(0, QtGui.QStandardItem("Num voxels"))
        self.model.setVerticalHeaderItem(1, QtGui.QStandardItem("Volume (mm^3)"))

        if self.ivm.main is not None:
            roi_name = options.pop('roi', None)
            sel_region = options.pop('region', None)

            if roi_name is None:
                roi = self.ivm.current_roi
            else:
                roi = self.ivm.rois[roi_name]

            sizes = self.ivm.grid.spacing
            if roi is not None:
                counts = np.bincount(roi.std().flatten())
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

class HistogramProcess(Process):
    """
    Calculate histogram for a data set 
    """
    
    PROCESS_NAME = "Histogram"
    
    def __init__(self, ivm, **kwargs):
        Process.__init__(self, ivm, **kwargs)
        self.model = QtGui.QStandardItemModel()

    def run(self, options):
        ov_name = options.pop('data', None)
        roi_name = options.pop('roi', None)
        sel_region = options.pop('region', None)
        dmin = options.pop('min', None)
        dmax = options.pop('max', None)
        bins = options.pop('bins', 20)
        output_name = options.pop('output-name', "histogram")
        no_artifact = options.pop('no-artifact', False)

        if roi_name is None and self.ivm.current_roi is None:
            roi = np.ones(self.ivm.grid.shape[:3])
            roi_labels = [1,]
        elif roi_name is None:
            roi = self.ivm.current_roi.std()
            roi_labels = self.ivm.current_roi.regions
        else:
            roi = self.ivm.rois[roi_name].std()
            roi_labels = self.ivm.rois[roi_name].regions

        if ov_name is None:
            ovs = self.ivm.data.values()
        else:
            ovs = [self.ivm.data[ov_name]]

        self.model.setHorizontalHeaderItem(0, QtGui.QStandardItem("x0"))
        self.model.setHorizontalHeaderItem(1, QtGui.QStandardItem("x1"))  
        self.xvals, self.edges, self.hist = None, None, {}
        col = 2
        
        for ov in ovs:
            hrange = [dmin, dmax]
            if dmin is None: hrange[0] = ov.std().min()
            if dmax is None: hrange[1] = ov.std().max()
            for region in roi_labels:
                debug("Doing %s region %i" % (ov.name, region))
                if sel_region is not None and region != sel_region:
                    debug("Ignoring this region")
                    continue
                region_data = ov.std()[roi == region]
                yvals, edges = np.histogram(region_data, bins=bins, range=hrange)
                if self.xvals is None:
                    self.edges = edges
                    self.xvals = [(edges[i] + edges[i+1])/2 for i in range(len(edges)-1)]
                    for idx in range(len(edges)-1):
                        self.model.setVerticalHeaderItem(idx, QtGui.QStandardItem(""))
                        self.model.setItem(idx, 0, QtGui.QStandardItem(str(self.edges[idx])))
                        self.model.setItem(idx, 1, QtGui.QStandardItem(str(self.edges[idx+1])))
                self.model.setHorizontalHeaderItem(col, QtGui.QStandardItem("%s\nRegion %i" % (ov.name, region)))
                for idx, v in enumerate(yvals):
                    self.model.setItem(idx, col, QtGui.QStandardItem(str(v)))
                if ov.name not in self.hist: self.hist[ov.name] = {}
                self.hist[ov.name][region] = yvals
                col += 1

        if not no_artifact: 
            debug("Adding %s" % output_name)
            self.ivm.add_artifact(output_name, table_to_str(self.model))
        self.status = Process.SUCCEEDED

class RadialProfileProcess(Process):
    """
    Calculate radial profile for a data set
    """
    
    PROCESS_NAME = "RadialProfile"
    
    def __init__(self, ivm, **kwargs):
        Process.__init__(self, ivm, **kwargs)
        self.model = QtGui.QStandardItemModel()

    def run(self, options):
        ov_name = options.pop('data', None)
        roi_name = options.pop('roi', None)
        #roi_region = options.pop('region', None)
        centre = options.pop('centre', None)
        output_name = options.pop('output-name', "radial-profile")
        no_artifact = options.pop('no-artifact', False)
        bins = options.pop('bins', 20)

        if roi_name is None:
            if self.ivm.current_roi is not None:
                roi = self.ivm.current_roi.std()
            else:
                roi = np.ones(self.ivm.grid.shape)
        else:
            roi = self.ivm.rois[roi_name].std()

        if ov_name is None:
            ovs = self.ivm.data.values()
        else:
            ovs = [self.ivm.data[ov_name]]

        voxel_sizes = self.ivm.grid.spacing

        if centre is not None:
            centre = [int(v) for v in centre.split(",")]
        else:
            centre = self.ivm.cim_pos

        self.model.clear()
        self.rp = {}
        
        # Generate an array whose entries are integer values of the distance
        # from the centre. Set masked values to distance of -1
        x, y, z = np.indices((self.ivm.grid.shape))
        r = np.sqrt((voxel_sizes[0]*(x - centre[0]))**2 + (voxel_sizes[1]*(y - centre[1]))**2 + (voxel_sizes[2]*(z - centre[2]))**2)
        if roi is not None: 
            r[roi==0] = -1
            rmin = r[roi>0].min()   
        else: rmin = r.min()

        # Generate histogram of number of voxels in each bin
        # Use the range parameter to ignore masked values with negative distances
        voxels_per_bin, self.edges = np.histogram(r, bins=bins, range=(rmin, r.max()))

        # Prevent divide by zero, if there are no voxels in a bin, this is OK because
        # there will be no data either
        voxels_per_bin[voxels_per_bin==0] = 1
        self.xvals = [(self.edges[i] + self.edges[i+1])/2 for i in range(len(self.edges)-1)]

        for idx, xval in enumerate(self.xvals):
            self.model.setVerticalHeaderItem(idx, QtGui.QStandardItem(str(xval)))

        for col, data in enumerate(ovs):
            self.model.setHorizontalHeaderItem(col, QtGui.QStandardItem("%s" % data.name))
                
            # If data is 4d, get current 3d volume
            if data.ndim == 4:
                weights = data.std()[:, :, :, centre[3]]
            else:
                weights = data.std()

            # Generate histogram by distance, weighted by data
            rpd, junk = np.histogram(r, weights=weights, bins=bins, range=(rmin, r.max()))

            # Divide by number of voxels in each bin to get average value by distance.
            rp = rpd / voxels_per_bin
            for idx, v in enumerate(rp):
                self.model.setItem(idx, col, QtGui.QStandardItem(str(v)))
            self.rp[data.name] = rp

        if not no_artifact: 
            self.ivm.add_artifact(output_name, table_to_str(self.model))
        self.status = Process.SUCCEEDED

class DataStatisticsProcess(Process):
    """
    Calculate summary statistics on data
    """
    
    PROCESS_NAME = "OverlayStats"
    
    def __init__(self, ivm, **kwargs):
        Process.__init__(self, ivm, **kwargs)
        self.model = QtGui.QStandardItemModel()

    def run(self, options):
        roi_name = options.pop('roi', None)
        ov_name = options.pop('data', None)
        no_artifact = options.pop('no-artifact', False)
        if ov_name is None:
            ovs = self.ivm.data.values()
            output_name = options.pop('output-name', "stats")
        else:
            ovs = [self.ivm.data[ov_name]]
            output_name = options.pop('output-name', "%s_stats" % ov_name)
            
        if roi_name is None:
            roi = self.ivm.current_roi
            debug("Current=", roi)
        else:
            roi = self.ivm.rois[roi_name]
            debug("Specified=", roi)

        self.model.clear()
        self.model.setVerticalHeaderItem(0, QtGui.QStandardItem("Mean"))
        self.model.setVerticalHeaderItem(1, QtGui.QStandardItem("Median"))
        self.model.setVerticalHeaderItem(2, QtGui.QStandardItem("Variance"))
        self.model.setVerticalHeaderItem(3, QtGui.QStandardItem("Min"))
        self.model.setVerticalHeaderItem(4, QtGui.QStandardItem("Max"))

        col = 0
        for ov in ovs:
            stats1, roi_labels, hist1, hist1x = self.get_summary_stats(ov, roi, **options)
            for ii in range(len(stats1['mean'])):
                self.model.setHorizontalHeaderItem(col, QtGui.QStandardItem("%s\nRegion %i" % (ov.name, roi_labels[ii])))
                self.model.setItem(0, col, QtGui.QStandardItem(str(np.around(stats1['mean'][ii], ov.dps))))
                self.model.setItem(1, col, QtGui.QStandardItem(str(np.around(stats1['median'][ii], ov.dps))))
                self.model.setItem(2, col, QtGui.QStandardItem(str(np.around(stats1['std'][ii], ov.dps))))
                self.model.setItem(3, col, QtGui.QStandardItem(str(np.around(stats1['min'][ii], ov.dps))))
                self.model.setItem(4, col, QtGui.QStandardItem(str(np.around(stats1['max'][ii], ov.dps))))
                col += 1

        if not no_artifact: 
            self.ivm.add_artifact(output_name, table_to_str(self.model))
        self.status = Process.SUCCEEDED

    def get_summary_stats(self, ovl, roi=None, hist_bins=20, hist_range=None, slice=None):
        """
        Return:
        @m1 mean for each ROI
        @m2 median for each ROI
        @m3 standard deviation for each ROI
        @roi_labels label of each ROI
        """
        # Checks if either ROI or data is None
        if roi is not None:
            roi_labels = roi.regions
        else:
            roi = NumpyData(np.ones(ovl.stdgrid.shape[:3]), ovl.stdgrid, "temp", roi=True)
            roi_labels = [1,]

        if (ovl is None):
            stat1 = {'mean': [0], 'median': [0], 'std': [0], 'max': [0], 'min': [0]}
            return stat1, roi_labels, np.array([0, 0]), np.array([0, 1])

        stat1 = {'mean': [], 'median': [], 'std': [], 'max': [], 'min': []}
        hist1 = []
        hist1x = []

        if slice is None:
            ovldata = ovl.std()
            roidata = roi.std()
        elif slice in (0, 1, 2):
            axis = 2-slice
            slicepos = self.ivm.cim_pos[axis]
            ovldata = ovl.get_slice([(axis, slicepos)])
            roidata = roi.get_slice([(axis, slicepos)])
        else:
            raise RuntimeError("Invalid slice: " % slice)

        for ii in roi_labels:
            # get data for a single label of the roi
            vroi1 = ovldata[roidata == ii]

            stat1['mean'].append(np.mean(vroi1))
            stat1['median'].append(np.median(vroi1))
            stat1['std'].append(np.std(vroi1))
            stat1['max'].append(np.max(vroi1))
            stat1['min'].append(np.min(vroi1))
            y, x = np.histogram(vroi1, bins=hist_bins, range=hist_range)
            hist1.append(y)
            hist1x.append(x)

        return stat1, roi_labels, hist1, hist1x

class ExecProcess(Process):
    
    PROCESS_NAME = "Exec"
    
    def __init__(self, ivm, **kwargs):
        Process.__init__(self, ivm, **kwargs)
        self.model = QtGui.QStandardItemModel()

    def run(self, options):
        globals = {'np': np, 'scipy' : scipy, 'ivm': self.ivm}
        for name, ovl in self.ivm.data.items():
            globals[name] = ovl.std()
        for name, roi in self.ivm.rois.items():
            globals[name] = roi.std()
        for name in options.keys():
            proc = options.pop(name)
            if name == "exec":
                for code in proc:
                    try:
                        exec(code, globals)
                    except:
                        raise QpException("'%s' is not valid Python code (Reason: %s)" % (code, sys.exc_info()[1]))
            else:
                try:
                    result = eval(proc, globals)
                    self.ivm.add_data(result, name=name)
                except:
                    raise QpException("'%s' did not return valid data (Reason: %s)" % (proc, sys.exc_info()[1]))
       
        self.status = Process.SUCCEEDED
