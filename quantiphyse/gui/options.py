"""
Quantiphyse - GUI widgets for easily defining options

The intention is that this module will supercede most of the contents
of quantiphyse.gui.widgets which mostly contains thin wrappers around
Qt widgets.

The idea is that you create an OptionBox and then use ``add()`` to
add any of the option widgets to it, providing a label and generally 
a key. The ``values()`` method then returns a dictionary of option
values suitable to feeding in to a ``Process``. 

Alternatively options can be used directly. All have a ``value()``
method which returns an appropriate value, and a ``sig_changed`` signal
which is emitted whenever this value changes

Copyright (c) 2013-2018 University of Oxford
"""
import logging

import numpy as np

from PySide import QtGui, QtCore

from quantiphyse.utils import QpException, sf, load_matrix, local_file_from_drop_url
from quantiphyse.gui.dialogs import MatrixViewerDialog

LOG = logging.getLogger(__name__)

class OptionBox(QtGui.QGroupBox):
    """
    A box containing structured options for a QpWidget
    """
    def __init__(self, title):
        QtGui.QGroupBox.__init__(self, title)
        self.grid = QtGui.QGridLayout()
        self.setLayout(self.grid)
        self._current_row = 0
        self._options = {}

    def add(self, label, *options, **kwargs):
        """
        Add labelled option widgets to the option box

        :param label: Text label for the option widgets
        :param options: Sequence of arguments, each a QtWidget
        :param key: Optional keyword argument specifying the key to use when 
                    returning the option value in ``values()``. Only valid
                    when a single option is given. If not specified, the 
                    label is used.
        :param keys: Optional keyword argument specifying a sequence of keys
                     to use when returning the option values in ``values()``.
                     Must be specified when there are multiple options, and
                     must have the same length as the number of options.
        """
        key = kwargs.get("key", label)
        keys = kwargs.get("keys", [key,])
        
        if len(keys) != len(options):
            raise ValueError("keys must be sequence which is the same length as the number of options")

        self.grid.addWidget(QtGui.QLabel(label), self._current_row, 0)
        for idx, keyopt in enumerate(zip(keys, options)):
            key, option = keyopt
            LOG.debug("Adding option: %s (key=%s)", option, key)
            self.grid.addWidget(option, self._current_row, idx+1)
            self._options[key] = option

        self._current_row += 1

        if len(options) == 1:
            return options[0]
        return options
    
    def option(self, key):
        """
        :return: The option widget having key=``key``
        """
        return self._options[key]

    def values(self):
        """
        Get the values of all options as a dict

        :return: dict of key:option value for all options
        """
        ret = {}
        for key, option in self._options.items():
            ret[key] = option.value()
        return ret

class Option(object):
    """
    Base class for  an option

    This is simply so we can detect instances of option widgets.
    We would like to define sig_changed here but this requires
    the class to be a QObject and we would end up with 
    multiple inheritance from QObject, QWidget which is probably
    very bad if it gets into the C++
    """
    pass

class DataOption(Option, QtGui.QComboBox):
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

class ChoiceOption(Option, QtGui.QComboBox):
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

class OutputNameOption(Option, QtGui.QLineEdit):
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
      
class NumericOption(Option, QtGui.QWidget):
    """
    Numeric option chooser which uses a slider and two spin boxes
    """
    sig_changed = QtCore.Signal()

    def __init__(self, minval=0, maxval=100, default=0, intonly=False, decimals=2, **kwargs):
        QtGui.QWidget.__init__(self)
        self.minval = minval
        self.maxval = maxval
        self.hardmin = kwargs.get("hardmin", False)
        self.hardmax = kwargs.get("hardmax", False)
        self.valid = True

        if intonly:
            self.rtype = int
            self.decimals = 0
        else:
            self.rtype = float
            self.decimals = decimals
            
        hbox = QtGui.QHBoxLayout()
        self.setLayout(hbox)

        #self.min_edit = QtGui.QLineEdit(str(minval))
        #self.min_edit.editingFinished.connect(self_min_changed)
        #hbox.addWidget(self.min_edit)

        self.slider = QtGui.QSlider(QtCore.Qt.Horizontal)
        self.slider.setMaximum(100)
        self.slider.setMinimum(0)
        self.slider.setSliderPosition(int(100 * (default - minval) / (maxval - minval)))
        self.slider.valueChanged.connect(self._slider_changed)
        hbox.addWidget(self.slider)

        self.val_edit = QtGui.QLineEdit(str(default))
        self.val_edit.editingFinished.connect(self._edit_changed)
        hbox.addWidget(self.val_edit)

    def _changed(self):
        self.sig_changed.emit()

    def _edit_changed(self):
        try:
            val = self.rtype(self.val_edit.text())
            self.valid = True
            self.val_edit.setStyleSheet("")

            if val > self.maxval and not self.hardmax:
                self.maxval = val
            if val < self.minval and not self.hardmin:
                self.minval = val

            val = self.value()
            pos = 100 * (val - self.minval) / (self.maxval - self.minval)
            try:
                self.slider.blockSignals(True)
                self.slider.setSliderPosition(int(pos))
            finally:
                self.slider.blockSignals(False)

        except ValueError:
            self.val_edit.setStyleSheet("QLineEdit {background-color: red}")
            self.valid = False

        self._changed()

    def _slider_changed(self, value):
        val = self.minval + (self.maxval - self.minval) * float(value) / 100
        try:
            self.val_edit.blockSignals(True)
            self.val_edit.setText(sf(val, sig_fig=self.decimals))
        finally:
            self.val_edit.blockSignals(False)
        self._changed()

    def value(self):
        """ Get the numeric value selected """
        if self.valid:
            return self.rtype(self.val_edit.text())
        else:
            raise QpException("'%s' is not a valid number")

    def setLimits(self, minval=None, maxval=None):
        """
        Set the minimum and maximum slider values
        """
        if minval:
            self.minval = minval
        if maxval:
            self.maxval = maxval

        try:
            self.blockSignals(True)
            if self.valid:
                self._edit_changed()
        finally:
            self.blockSignals(False)

class BoolOption(Option, QtGui.QCheckBox):
    """ 
    Option used to specify a true or false value
    """
    sig_changed = QtCore.Signal()

    def __init__(self, default=False):
        QtGui.QCheckBox.__init__(self)
        self.setChecked(default)
        self.stateChanged.connect(self._changed)

    def value(self):
        """ 
        :return: True or False according to whether the option is selected
        """
        return self.isChecked()
    
    def _changed(self):
        self.sig_changed.emit()
      
class MatrixOption(Option, QtGui.QTableView):
    """
    Option which returns a 2D matrix of numbers
    """

    sig_changed = QtCore.Signal()

    def __init__(self, initial, col_headers=None, row_headers=None, expandable=(True, True),
                 fix_height=False, fix_width=False, readonly=False):
        QtGui.QTableView.__init__(self)
        
        self._model = QtGui.QStandardItemModel()
        self.setModel(self._model)
        self.updating = False
        self.expandable = expandable
        self.row_headers = row_headers
        self.col_headers = col_headers
        self.fix_height = fix_height
        self.fix_width = fix_width
        self.default_bg = None
        self.horizontalHeader().hide()
        self.verticalHeader().hide()

        self.setMatrix(initial, False, col_headers=col_headers, row_headers=row_headers)
        
        if readonly:
            self.setEditTriggers(QtGui.QAbstractItemView.NoEditTriggers)
        else:
            self.model().itemChanged.connect(self._item_changed)
        
        self.setSizePolicy(QtGui.QSizePolicy.Expanding, QtGui.QSizePolicy.Expanding)
        #self.horizontalHeader().setResizeMode(QtGui.QHeaderView.ResizeToContents)
        self.itemDelegate().closeEditor.connect(self._expand_if_required, QtCore.Qt.QueuedConnection)
        self.setAcceptDrops(True)
        
    def valid(self):
        try:
            self.values()
            return True
        except ValueError:
            return False

    def value(self):
        """
        :return: Matrix of numbers as a sequence of sequences
        """
        rows = []
        try:
            for r in range(self._model.rowCount()-int(self.expandable[1])):
                row = [float(self._model.item(r, c).text()) for c in range(self._model.columnCount()-int(self.expandable[0]))]
                rows.append(row)
        except:
            raise ValueError("Non-numeric data in list")
        return np.array(rows)

    def _set_size(self):
        # QTableWidget is completely incapable of choosing a sensible size. We do our best
        # here but have to allow a bit of random 'padding' in case scrollbars are necessary
        tx, ty = self.horizontalHeader().length()+15, self.verticalHeader().length()+15
        if self.row_headers is not None: tx += self.verticalHeader().width()
        if self.col_headers is not None: ty += self.horizontalHeader().height()
        #sh = self.sizeHint()
        #tx = min(tx, sh.width())
        #ty = min(ty, sh.height())
        if self.fix_height: self.setFixedHeight(ty)
        if self.fix_width: self.setFixedWidth(tx)

    def setMatrix(self, matrix, validate=True, col_headers=None, row_headers=None):
        if validate:
            if not matrix:
                raise ValueError("No values provided")
            elif len(matrix[0]) != self._model.columnCount() and not self.expandable[0]:
                raise ValueError("Incorrect number of columns - expected %i" % self._model.columnCount())
            elif len(matrix) != self._model.rowCount() and not self.expandable[1]:
                raise ValueError("Incorrect number of rows - expected %i" % self._model.rowCount())

        if (col_headers and self.expandable[0]) or (row_headers and self.expandable[1]):
            raise RuntimeError("Can't specify headers for auto-expandable dimensions")

        self._model.setRowCount(len(matrix)+int(self.expandable[1]))
        self._model.setColumnCount(len(matrix[0])+int(self.expandable[0]))

        if col_headers:
            self._model.setHorizontalHeaderLabels(col_headers)
            self.horizontalHeader().show()

        if row_headers:
            self._model.setVerticalHeaderLabels(row_headers)
            self.verticalHeader().show()
        
        self._model.blockSignals(True)
        try:
            for r, rvals in enumerate(matrix):
                for c, v in enumerate(rvals):
                    item = QtGui.QStandardItem("%g" % v)
                    self._model.setItem(r, c, item)
            
            if self.expandable[0]:
                for r in range(len(matrix)):
                    item = QtGui.QStandardItem("")
                    self._model.setItem(r, self._model.columnCount()-1, item)
        
            if self.expandable[1]:
                for c in range(len(matrix[0])):
                    item = QtGui.QStandardItem("")
                    self._model.setItem(self._model.rowCount()-1, c, item)
        
            self.resizeColumnsToContents()
            self.resizeRowsToContents()
        finally:
            self._model.blockSignals(False)
            
        self._set_size()
        self.sig_changed.emit()

    def _range_empty(self, cs, rs):
        empty = True
        for r in rs:
            for c in cs:
                # Check if r or c is negative and do not consider empty
                # so last row/column will not be deleted
                if r < 0 or c < 0 or (self._model.item(r, c) is not None and self._model.item(r, c).text() != ""):
                    empty = False
                    break
        return empty

    def _item_changed(self, item):
        if self.updating: return
        self.updating = True
        try:
            if self.default_bg is None:
                self.default_bg = item.background()

            try:
                float(item.text())
                item.setBackground(self.default_bg)
            except ValueError:
                if item.text() != "": 
                    item.setBackground(QtGui.QColor('red'))

            self.resizeColumnsToContents()
            self.resizeRowsToContents()
        finally:
            self.updating = False

    def _expand_if_required(self):
        last_col = self._model.columnCount()-1
        last_row = self._model.rowCount()-1
        if self.expandable[0]:
            if not self._range_empty([last_col], range(self._model.rowCount())):
                # Last column is not empty - add a new empty column
                self._model.setColumnCount(self._model.columnCount()+1)
                # Set rest of new column to prevent it from immediately being invalid
                for row in range(self._model.rowCount()-int(self.expandable[1])):
                    item = self._model.item(row, last_col)
                    if item is None or item.text() == "":
                        item = QtGui.QStandardItem(self._model.item(row, last_col-1).text())
                        self._model.setItem(row, last_col, item)
                    
            elif self._range_empty([self._model.columnCount()-2], range(self._model.rowCount())):
                # Last two columns are empty, so remove last column
                self._model.setColumnCount(self._model.columnCount()-1)

        if self.expandable[1]:
            if not self._range_empty(range(self._model.columnCount()), [last_row]):
               # Last row is not empty - add a new empty row
                self._model.setRowCount(self._model.rowCount()+1)
                # Set rest of new row to prevent it from immediately being invalid
                for col in range(self._model.columnCount()-int(self.expandable[0])):
                    item = self._model.item(last_row, col)
                    if item is None or item.text() == "":
                        self._model.setItem(last_row, col, QtGui.QStandardItem(self._model.item(last_row-1, col).text()))
            
            elif self._range_empty(range(self._model.columnCount()), [self._model.rowCount()-2]):
                # Last-but-one row is empty, so remove last row (which is always empty)
                self._model.setColumnCount(self._model.columnCount()-1)
        self.sig_changed.emit()

    def dragEnterEvent(self, event):
        if event.mimeData().hasUrls:
            event.accept()
        else:
            event.ignore()

    def dragMoveEvent(self, event):
        if event.mimeData().hasUrls:
            event.setDropAction(QtCore.Qt.CopyAction)
            event.accept()
        else:
            event.ignore()

    def dropEvent(self, event):
        if event.mimeData().hasUrls:
            event.setDropAction(QtCore.Qt.CopyAction)
            event.accept()
            for url in event.mimeData().urls():
                self.loadFromFile(local_file_from_drop_url(url))
        else:
            event.ignore()
            
    def loadFromFile(self, filename):
        fvals, _, ncols = load_matrix(filename)
        if ncols <= 0:
            raise RuntimeError("No numeric data found in file")
        else:
            self.setMatrix(fvals)

class VectorOption(MatrixOption):
    """
    Option which returns a list of numbers
    """
    def __init__(self, initial, row=True, headers=None, expandable=True, fix_size=True):
        self._row = row
        initial = self._to_matrix(initial)
        if row:
            row_headers, col_headers = None, headers
            expandable = (expandable, False)
            fix_height, fix_width = fix_size, False
        else:
            row_headers, col_headers = headers, None
            expandable = (False, expandable)
            fix_height, fix_width = False, fix_size

        MatrixOption.__init__(self, initial, 
                              row_headers=row_headers, col_headers=col_headers, 
                              expandable=expandable, 
                              fix_height=fix_height, fix_width=fix_width)

    def _to_matrix(self, vals):
        if self._row:
            return [vals,]
        else:
            return [v[0] for v in vals]

    def _from_matrix(self, matrix):
        if self._row:
            return matrix[0]
        else:
            return np.array([row[0] for row in matrix])

    def value(self):
        return self._from_matrix(MatrixOption.value(self))

    def setList(self, values, **kwargs):
        MatrixOption.setMatrix(self, self._to_matrix(values), **kwargs)

    def loadFromFile(self, filename):
        fvals, nrows, ncols = load_matrix(filename)
        print(fvals, nrows, ncols)

        if ncols <= 0:
            raise RuntimeError("No numeric data found in file")
        elif ncols == 1:
            self.setList([row[0] for row in fvals])
        elif nrows == 1:
            self.setList(fvals[0])
        else:
            # Choose row or column you want
            row, col = self._choose_row_col(fvals)
            if row is not None:
                self.setList(fvals[row])
            elif col is not None:
                vals = [v[col] for v in fvals]
                self.setList(vals)

    def _choose_row_col(self, vals):
        d = MatrixViewerDialog(self, vals, title="Choose a row or column", text="Select a row or column containing the data you want")
        if d.exec_():
            ranges = d.table.selectedRanges()
            if ranges:
                r = ranges[0]
                if r.topRow() == r.bottomRow():
                    # Row select
                    return r.topRow(), None
                elif r.leftColumn() == r.rightColumn():
                    # Column select
                    return None, r.leftColumn()
        return None, None    

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
