"""
Quantiphyse - Dialog box for editing view options

Copyright (c) 2013-2018 University of Oxford
"""

from __future__ import division, unicode_literals, print_function, absolute_import

from PySide import QtCore, QtGui

from quantiphyse.gui.widgets import NumberVList

class ScaleEditDialog(QtGui.QDialog):
    """
    Dialog used by the view options to allow the user to edit the 
    scale of the 4th volume dimension
    """
    def __init__(self, parent=None, scale=[]):
        QtGui.QDialog.__init__(self, parent)
        
        vbox = QtGui.QVBoxLayout()
        label = QtGui.QLabel('<font size="5">Edit Scale</font>')
        vbox.addWidget(label)

        self.table = NumberVList(scale, expandable=False)
        self.table.sig_changed.connect(self.changed)
        vbox.addWidget(self.table)

        self.buttonBox = QtGui.QDialogButtonBox(QtGui.QDialogButtonBox.Ok|QtGui.QDialogButtonBox.Cancel)
        self.buttonBox.accepted.connect(self.accept)
        self.buttonBox.rejected.connect(self.reject)
        vbox.addWidget(self.buttonBox)

        self.setLayout(vbox)

        shortcut = QtGui.QShortcut(QtGui.QKeySequence.Paste, self.table)
        shortcut.activated.connect(self.paste)

    def paste(self):
        clipboard = QtGui.QApplication.clipboard()
        text = clipboard.text()
        scale = text.strip().split(",")
        if len(scale) != self.table.rowCount():
            scale = text.strip().split()
        if len(scale) != self.table.rowCount():
            scale = text.strip().split("\t")
        if len(scale) == self.table.rowCount():
            try:
                self.table.setValues([float(v) for v in scale])
            except:
                pass

    def changed(self):
        self.buttonBox.button(QtGui.QDialogButtonBox.Ok).setEnabled(self.table.valid())

class ViewOptions(QtGui.QDialog):
    """
    This class is both a dialog to edit viewing options, but also
    the storage for the option values. For now this is convenient,
    however it will probably be necessary to separate the two 
    as the options become more extensive
    """
    RADIOLOGICAL = 0
    NEUROLOGICAL = 1
    
    DATA_ON_TOP = 0
    ROI_ON_TOP = 1

    SHOW = 0
    HIDE = 1

    sig_options_changed = QtCore.Signal(object)

    def __init__(self, parent, ivm):
        super(ViewOptions, self).__init__(parent)
        self.setWindowTitle("View Options")
        #self.setFixedSize(300, 300)

        self.ivm = ivm
        self.ivm.sig_main_data.connect(self.vol_changed)

        # Options
        self.orientation = self.RADIOLOGICAL
        self.crosshairs = self.SHOW
        self.t_type = "Volume"
        self.t_unit = ""
        self.t_scale_type = 0
        self.t_res = 1.0
        self.t_scale = [0, ]
        self.display_order = self.ROI_ON_TOP
        self.interp_order = 0

        grid = QtGui.QGridLayout()
        label = QtGui.QLabel('<font size="5">View Options</font>')
        grid.addWidget(label, 0, 0)

        grid.addWidget(QtGui.QLabel("Orientation"), 2, 0)
        c = QtGui.QComboBox()
        c.addItem("Radiological (Right is Left)")
        c.addItem("Neurological (Left is Left)")
        c.setCurrentIndex(self.orientation)
        c.currentIndexChanged.connect(self.orientation_changed)
        grid.addWidget(c, 2, 1)

        grid.addWidget(QtGui.QLabel("Crosshairs"), 3, 0)
        c = QtGui.QComboBox()
        c.addItem("Show")
        c.addItem("Hide")
        c.setCurrentIndex(self.crosshairs)
        c.currentIndexChanged.connect(self.crosshairs_changed)
        grid.addWidget(c, 3, 1)

        grid.addWidget(QtGui.QLabel("4D Type"), 4, 0)
        self.t_type_edit = QtGui.QLineEdit(self.t_type)
        self.t_type_edit.editingFinished.connect(self.t_type_changed)
        grid.addWidget(self.t_type_edit, 4, 1)
        
        grid.addWidget(QtGui.QLabel("4D Unit"), 5, 0)
        self.t_unit_edit = QtGui.QLineEdit(self.t_unit)
        self.t_unit_edit.editingFinished.connect(self.t_unit_changed)
        grid.addWidget(self.t_unit_edit, 5, 1)
        
        grid.addWidget(QtGui.QLabel("4D Scale"), 6, 0)
        hbox = QtGui.QHBoxLayout()
        self.t_combo = QtGui.QComboBox()
        self.t_combo.addItem("Fixed resolution")
        self.t_combo.addItem("Labelled")
        self.t_combo.setCurrentIndex(self.t_scale_type)
        self.t_combo.currentIndexChanged.connect(self.t_combo_changed)
        hbox.addWidget(self.t_combo)

        self.t_res_edit = QtGui.QLineEdit(str(self.t_res))
        self.t_res_edit.editingFinished.connect(self.t_res_changed)
        hbox.addWidget(self.t_res_edit)

        self.t_btn = QtGui.QPushButton("Edit")
        self.t_btn.setVisible(False)
        self.t_btn.clicked.connect(self.edit_scale)
        hbox.addWidget(self.t_btn)
        grid.addLayout(hbox, 6, 1)

        grid.addWidget(QtGui.QLabel("Display order"), 7, 0)
        c = QtGui.QComboBox()
        c.addItem("Data on top")
        c.addItem("ROI on top")
        c.setCurrentIndex(self.display_order)
        c.currentIndexChanged.connect(self.zorder_changed)
        grid.addWidget(c, 7, 1)

        grid.addWidget(QtGui.QLabel("View interpolation"), 8, 0)
        c = QtGui.QComboBox()
        c.setToolTip("How data is interpolated for display on non-orthogonal grids")
        c.addItem("Nearest neighbour (fast)", 0)
        c.addItem("Linear", 1)
        c.addItem("Cubic spline (slow)", 3)
        c.setCurrentIndex(self.interp_order)
        c.currentIndexChanged.connect(self.interp_changed)
        grid.addWidget(c, 8, 1)

        grid.setRowStretch(9, 1)
        self.setLayout(grid)

    def vol_changed(self, vol):
        """ 
        Do not signal 'options changed', even thought scale points may be updated. 
        The user has not changed any options, and widgets should update themselves 
        to the new volume by connecting to the volume changed signal
        """
        self.update_scale()

    def update_scale(self):
        """
        Update the list of scale points if we have a 4D volume. Always do this if
        we have a uniform scale, if not only do it if the number of points has
        changed (as a starting point for customisation)
        """
        if self.ivm.main is not None and \
           (self.t_scale_type == 0 or self.ivm.main.nvols != len(self.t_scale)):
            self.t_scale = [i*self.t_res for i in range(self.ivm.main.nvols)]

    def orientation_changed(self, idx):
        self.orientation = idx
        self.sig_options_changed.emit(self)

    def crosshairs_changed(self, idx):
        self.crosshairs = idx
        self.sig_options_changed.emit(self)

    def zorder_changed(self, idx):
        self.display_order = idx
        self.sig_options_changed.emit(self)

    def edit_scale(self):
        dlg = ScaleEditDialog(self, self.t_scale)
        if dlg.exec_():
            self.t_scale = dlg.table.values()
        self.sig_options_changed.emit(self)

    def t_unit_changed(self):
        self.t_unit = self.t_unit_edit.text()
        self.sig_options_changed.emit(self)

    def t_type_changed(self):
        self.t_type = self.t_type_edit.text()
        self.sig_options_changed.emit(self)

    def t_res_changed(self):
        self.t_res = float(self.t_res_edit.text())
        self.update_scale()
        self.sig_options_changed.emit(self)
            
    def t_combo_changed(self, idx):
        self.t_scale_type = idx
        self.t_btn.setVisible(idx == 1)
        self.t_res_edit.setVisible(idx == 0)
        self.update_scale()
        self.sig_options_changed.emit(self)

    def interp_changed(self, idx):
        if idx in (0, 1):
            self.interp_order = idx
        else:
            self.interp_order = 3
        self.sig_options_changed.emit(self)
