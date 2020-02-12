"""
Quantiphyse - Dialog box for editing view options

Copyright (c) 2013-2018 University of Oxford
"""

from __future__ import division, unicode_literals, print_function, absolute_import

try:
    from PySide import QtGui, QtCore, QtGui as QtWidgets
except ImportError:
    from PySide2 import QtGui, QtCore, QtWidgets

from quantiphyse.utils.enums import Orientation, DisplayOrder, Visibility
from quantiphyse.gui.options import OptionBox, ChoiceOption

class ViewerOptions(QtGui.QDialog):
    """
    Dialog box which controls viewer options
    """

    def __init__(self, parent, ivl):
        super(ViewerOptions, self).__init__(parent)
        self.setWindowTitle("View Options")
        self._ivl = ivl

        vbox = QtGui.QVBoxLayout()
        label = QtGui.QLabel('<font size="5">View Options</font>')
        vbox.addWidget(label)

        self._optbox = OptionBox()
        self._optbox.add("Orientation", 
                         ChoiceOption(["Radiological (Right is Left)", "Neurological (Left is Left)"],
                                      [Orientation.RADIOLOGICAL, Orientation.NEUROLOGICAL], 
                                      default=self._ivl.opts.orientation),
                         key="orient")
        self._optbox.add("Crosshairs", 
                         ChoiceOption(["Show", "Hide"], [Visibility.SHOW, Visibility.HIDE],
                                      default=self._ivl.opts.crosshairs),
                         key="crosshairs")
        self._optbox.add("Orientation labels", 
                         ChoiceOption(["Show", "Hide"], [Visibility.SHOW, Visibility.HIDE],
                                      default=self._ivl.opts.labels),
                         key="labels")
        self._optbox.add("Main data background", 
                         ChoiceOption(["Show", "Hide"], [Visibility.SHOW, Visibility.HIDE],
                                      default=self._ivl.opts.main_data),
                         key="main_data")
        self._optbox.add("Display order", 
                         ChoiceOption(["User selected", "Data always on top", "ROIs always on top"], 
                                      [DisplayOrder.USER, DisplayOrder.DATA_ON_TOP, DisplayOrder.ROI_ON_TOP],
                                      default=self._ivl.opts.display_order),
                         key="display_order")
        self._optbox.add("View interpolation", 
                         ChoiceOption(["Nearest neighbour (fast)", "Linear", "Cubic spline (slow)"], [0, 1, 3],
                                      default=self._ivl.opts.interp),
                         key="interp")
        self._optbox.option("orient").sig_changed.connect(self._orientation_changed)
        self._optbox.option("crosshairs").sig_changed.connect(self._crosshairs_changed)
        self._optbox.option("labels").sig_changed.connect(self._labels_changed)
        self._optbox.option("main_data").sig_changed.connect(self._main_data_changed)
        self._optbox.option("display_order").sig_changed.connect(self._display_order_changed)
        self._optbox.option("interp").sig_changed.connect(self._interp_changed)
        vbox.addWidget(self._optbox)

        vbox.addStretch(1)
        self.setLayout(vbox)

    def _orientation_changed(self):
        self._ivl.opts.orientation = self._optbox.option("orient").value

    def _crosshairs_changed(self):
        self._ivl.opts.crosshairs = self._optbox.option("crosshairs").value

    def _labels_changed(self):
        self._ivl.opts.labels = self._optbox.option("labels").value

    def _main_data_changed(self):
        self._ivl.opts.main_data = self._optbox.option("main_data").value

    def _display_order_changed(self):
        self._ivl.opts._display_order = self._optbox.option("display_order").value

    def _interp_changed(self):
        self._ivl.opts.interp = self._optbox.option("interp").value
