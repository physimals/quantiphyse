"""
Quantiphyse - GUI widgets for easily defining options

The intention is that this module will supercede most of the contents
of quantiphyse.gui.widgets which mostly contains thin wrappers around
Qt widgets.

Copyright (c) 2013-2018 University of Oxford
"""

from PySide import QtGui, QtCore

from ..utils import debug, warn, QpException

class OptionBox(QtGui.QGroupBox):
    """
    A box containing structured options for a QpWidget
    """
    def __init__(self, title):
        QtGui.QGroupBox.__init__(self, title)
        self.grid = QtGui.QGridLayout()
        self.setLayout(self.grid)
        self._current_row = 0

    def add(self, label, *options):
        """
        Add labelled option widgets to the option box

        :param label: Text label for the option widgets
        :param options: Sequence of arguments, each a QtWidget
        """
        self.grid.addWidget(QtGui.QLabel(label), self._current_row, 0)
        for option in options:
            self.grid.addWidget(option, self._current_row, 1)
        self._current_row += 1

        if len(options) == 1:
            return options[0]
        return options
    
class DataOption(QtGui.QComboBox):
    """
    A combo box which gives a choice of data
    """
    sig_changed = QtCore.Signal()

    def __init__(self, ivm, parent=None, **kwargs):
        super(DataOption, self).__init__(parent)
        self.ivm = ivm

        self.static_only = kwargs.get("static_only", False)
        self.none_option = kwargs.get("none_option", False)
        self.all_option = kwargs.get("all_option", False)
        self.rois = kwargs.get("rois", False)
        self.data = kwargs.get("data", True)
        if self.rois:
            self.ivm.sig_all_rois.connect(self._data_changed)
        if self.data:
            self.ivm.sig_all_data.connect(self._data_changed)
        self._data_changed()
        self.currentIndexChanged.connect(self._changed)
    
    def value(self):
        """
        :return: Name of currently selected data
        """
        return self.currentText()

    def _changed(self):
        self.sig_changed.emit()

    def _data_changed(self):
        self.blockSignals(True)
        try:
            data = []
            if self.rois:
                data += self.ivm.rois.keys()
            if self.data:
                data += self.ivm.data.keys()

            current = self.currentText()
            self.clear()
            if self.none_option:
                self.addItem("<none>")

            for name in sorted(data):
                data = self.ivm.data.get(name, self.ivm.rois.get(name, None))
                if data.nvols == 1 or not self.static_only:
                    self.addItem(data.name)

            if self.all_option:
                self.addItem("<all>")

            # Make sure names are visible even with drop down arrow
            width = self.minimumSizeHint().width()
            self.setMinimumWidth(width+50)
        finally:
            self.blockSignals(False)
        
        idx = self.findText(current)
        if idx >= 0:
            self.setCurrentIndex(idx)
        else:
            # Make sure signal is sent when first data arrives
            self.setCurrentIndex(-1)
            self.setCurrentIndex(0)

class ChoiceOption(QtGui.QComboBox):
    """ 
    Option which is chosen from a list of possible strings 
    """
    sig_changed = QtCore.Signal()

    def __init__(self, choices=(), return_values=None):
        QtGui.QComboBox.__init__(self)
        if return_values is None:
            return_values = list(choices)

        if len(return_values) != len(choices):
            raise QpException("Number of return values must match number of choices")
        self.choice_map = dict(zip(choices, return_values))
        
        for choice in choices:
            self.addItem(choice)
        self.currentIndexChanged.connect(self._changed)

    def value(self):
        """ 
        :return: Value of currently selected option. This is either
                 the selected text, or the corresponding return value
                 if these were supplied when the object was created
        """
        return self.choice_map[self.currentText()]
    
    def _changed(self):
        self.sig_changed.emit()

class OutputNameOption(QtGui.QLineEdit):
    """ 
    Option used to specify the output data name for a process
    """
    sig_changed = QtCore.Signal()

    def __init__(self, src_data=None, suffix="_out", initial="output"):
        QtGui.QLineEdit.__init__(self)
        self.src_data = src_data
        self.initial = initial
        self.suffix = suffix
        self._reset()
        if src_data is not None:
            src_data.sig_changed.connect(self._reset)
        self.editingFinished.connect(self._changed)

    def value(self):
        """ 
        :return: Current text
        """
        return self.text()
    
    def _changed(self):
        self.sig_changed.emit()

    def _reset(self):
        if self.src_data is not None:
            self.setText(self.src_data.value() + self.suffix)
        else:
            self.setText(self.initial)

class RunButton(QtGui.QWidget):
    """
    A button which, when clicked, runs an analysis process
    """

    def __init__(self, label="Run", callback=None):
        QtGui.QWidget.__init__(self)
        hbox = QtGui.QHBoxLayout()
        self.setLayout(hbox)
        self.btn = QtGui.QPushButton(label)
        self.btn.clicked.connect(callback)
        hbox.addWidget(self.btn)
        hbox.addStretch(1)
