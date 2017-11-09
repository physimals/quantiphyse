from PySide import QtGui

from quantiphyse.utils import debug
from quantiphyse.utils.exceptions import QpException

from .mcflirt_wrapper import mcflirt

class McFlirtRegMethod:
    def __init__(self):
        self.name = "mcflirt"

        self.cost_models = {"Mutual information" : "mutualinfo",
                            "Woods" : "woods",
                            "Correlation ratio" : "corratio",
                            "Normalized correlation" : "normcorr",
                            "Normalized mutual information" : "normmi",
                            "Least squares" : "leastsquares"}
                            
        grid = QtGui.QGridLayout()

        grid.addWidget(QtGui.QLabel("Cost model"), 0, 0)
        self.cost_combo = QtGui.QComboBox()
        for name, opt in self.cost_models.items():
            self.cost_combo.addItem(name, opt)
        self.cost_combo.setCurrentIndex(self.cost_combo.findData("normcorr"))
        grid.addWidget(self.cost_combo, 0, 1)

        grid.addWidget(QtGui.QLabel("Number of search stages"), 3, 0)
        self.stages = QtGui.QComboBox()
        for i in range(1, 5):
            self.stages.addItem(str(i), i)
        self.stages.setCurrentIndex(2)
        grid.addWidget(self.stages, 3, 1)

        self.final_label = QtGui.QLabel("Final stage interpolation")
        grid.addWidget(self.final_label, 4, 0)
        self.final = QtGui.QComboBox()
        self.final.addItem("None", "")
        self.final.addItem("Sinc", "sinc_final")
        self.final.addItem("Spline", "spline_final")
        self.final.addItem("Nearest neighbour", "nn_final")
        grid.addWidget(self.final, 4, 1)

        grid.addWidget(QtGui.QLabel("Field of view (mm)"), 5, 0)
        self.fov = QtGui.QSpinBox()
        self.fov.setValue(20)
        self.fov.setMinimum(1)
        self.fov.setMaximum(100)
        grid.addWidget(self.fov, 5, 1)

        grid.addWidget(QtGui.QLabel("Number of bins"), 6, 0)
        self.num_bins = QtGui.QSpinBox()
        self.num_bins.setMinimum(1)
        self.num_bins.setMaximum(1000)
        self.num_bins.setValue(256)
        grid.addWidget(self.num_bins, 6, 1)

        grid.addWidget(QtGui.QLabel("Number of transform degrees of freedom"), 7, 0)
        self.num_dofs = QtGui.QSpinBox()
        self.num_dofs.setMinimum(6)
        self.num_dofs.setMaximum(12)
        self.num_dofs.setValue(6)
        grid.addWidget(self.num_dofs, 7, 1)

        grid.addWidget(QtGui.QLabel("Scaling"), 8, 0)
        self.scaling = QtGui.QDoubleSpinBox()
        self.scaling.setValue(6.0)
        self.scaling.setMinimum(0.1)
        self.scaling.setMaximum(10.0)
        self.scaling.setSingleStep(0.1)
        grid.addWidget(self.scaling, 8, 1)

        grid.addWidget(QtGui.QLabel("Smoothing in cost function"), 9, 0)
        self.smoothing = QtGui.QDoubleSpinBox()
        self.smoothing.setValue(1.0)
        self.smoothing.setMinimum(0.1)
        self.smoothing.setMaximum(10.0)
        self.smoothing.setSingleStep(0.1)
        grid.addWidget(self.smoothing, 9, 1)

        grid.addWidget(QtGui.QLabel("Scaling factor for rotation\noptimization tolerances"), 10, 0)
        self.rotation = QtGui.QDoubleSpinBox()
        self.rotation.setValue(1.0)
        self.rotation.setMinimum(0.1)
        self.rotation.setMaximum(10.0)
        self.rotation.setSingleStep(0.1)
        grid.addWidget(self.rotation, 10, 1)

        grid.addWidget(QtGui.QLabel("Search on gradient images"), 11, 0)
        self.gdt = QtGui.QCheckBox()
        grid.addWidget(self.gdt, 11, 1)

        self.options_layout = grid

    def reg(regdata, refdata, warp_rois, options):
        if warp_rois is not None:
            raise QpException("MCFLIRT does not yet support warping ROIs")
        # MCFLIRT wants to do motion correction so we stack the reg and ref
        # data together and tell it to use the second as the reference.
        data = np.stack((regdata, refdata), -1)
        options["refvol"] = 1
        # FIXME voxel sizes?
        retdata, log = mcflirt(data, [1.0,] * data.ndim, **options)
        return retdata[:,:,:,0], None, log

    def interface(self):
        return self.options_layout

    def options(self):
        opts = {}
        opts["cost"] = self.cost_combo.itemData(self.cost_combo.currentIndex())
        opts["bins"] = self.num_bins.value()
        opts["dof"] = self.num_dofs.value()
        opts["scaling"] = self.scaling.value()
        opts["smooth"] = self.smoothing.value()
        opts["rotation"] = self.rotation.value()
        opts["stages"] = self.stages.itemData(self.stages.currentIndex())
        opts["fov"] = self.fov.value()
        if self.gdt.isChecked(): opts["gdt"] = ""

        final_interp = self.final.currentIndex()
        if final_interp != 0: opts[self.final.itemData(final_interp)] = ""

        for key, value in opts.items():
            debug(key, value)
        return opts

QP_MANIFEST = {"reg-methods" : [McFlirtRegMethod,]}