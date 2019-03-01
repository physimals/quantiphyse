"""
Quantiphyse - GUI widgets for easily defining options

The intention is that this module will supercede most of the contents
of quantiphyse.gui.widgets which mostly contains thin wrappers around
Qt widgets.

The idea is that you create an OptionBox and then use ``add()`` to
add any of the option widgets to it, providing a label and generally 
a key. The ``values()`` method then returns a dictionary of option
values suitable to feeding in to a ``Process``. 

Alternatively options can be used directly. All have a ``value``
property which returns an appropriate value, and a ``sig_changed`` signal
which is emitted whenever this value changes

Copyright (c) 2013-2018 University of Oxford
"""
import os
import logging
import collections

import six
import numpy as np

from PySide import QtGui, QtCore

from quantiphyse.utils import QpException, sf, load_matrix, local_file_from_drop_url
from quantiphyse.gui.dialogs import MatrixViewerDialog
from quantiphyse.gui.pickers import PickMode

LOG = logging.getLogger(__name__)

class OptionBox(QtGui.QGroupBox):
    """
    A box containing structured options for a QpWidget
    """
    sig_changed = QtCore.Signal()

    def __init__(self, title=""):
        QtGui.QGroupBox.__init__(self, title)
        if not title:
            self.setStyleSheet("border: none")
        self.grid = QtGui.QGridLayout()
        self.setLayout(self.grid)
        self._current_row = 0
        self._options = {}
        self._rows = {}

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
        checked = kwargs.get("checked", False)
        enabled = kwargs.get("enabled", False)
        key = kwargs.get("key", label)
        keys = kwargs.get("keys", [key,])
        
        real_options = [opt for opt in options if isinstance(opt, Option)]
        extra_widgets = [opt for opt in options if opt not in real_options]

        if not real_options:
            # Allow no options for just a label
            real_options = []
            keys = []

        if len(keys) != len(real_options):
            raise ValueError("keys must be sequence which is the same length as the number of options")

        self.grid.addWidget(QtGui.QLabel(label), self._current_row, 0, 1, 1 if real_options else 3)
        opt_col = 1
        if checked:
            cb = QtGui.QCheckBox()
            cb.setChecked(enabled)
            self.grid.addWidget(cb, self._current_row, 1)
            opt_col += 1

        for idx, keyopt in enumerate(zip(keys, real_options)):
            key, option = keyopt
            if option is None: continue
            LOG.debug("Adding option: %s (key=%s)", option, key)
            self.grid.addWidget(option, self._current_row, idx+opt_col, 1, 1 if checked else 2)
            if checked:
                option.setEnabled(enabled)
                cb.stateChanged.connect(self._cb_toggled(option))
            self._options[key] = option
            option.sig_changed.connect(self.sig_changed.emit)

        for extra_idx, widget in enumerate(extra_widgets):
            self.grid.addWidget(widget, self._current_row, len(real_options)+extra_idx+2)

        self._rows[key] = self._current_row
        self._current_row += 1

        if len(real_options) == 1:
            return real_options[0]
        else:
            return real_options
    
    def set_visible(self, key, visible=True):
        """
        Show or hide an option. 
        
        FIXME this only works for simple key/single option rows at the moment
        """
        row = self._rows[key]
        col = 0
        checked = True
        while 1:
            item = self.grid.itemAtPosition(row, col)
            if item is None:
                break
            item.widget().setVisible(visible)
            if col == 1 and isinstance(item.widget(), QtGui.QCheckBox) and not isinstance(item.widget(), Option):
                checked = item.widget().isChecked()
                item.widget().setEnabled(visible)
            else:
                item.widget().setEnabled(visible and checked)
            col += 1

    def set_checked(self, key, checked):
        """
        Set whether an option with a checkbox is checked or not
        """
        row = self._rows[key]
        cb = self.grid.itemAtPosition(row, 1)
        if isinstance(cb.widget(), QtGui.QCheckBox) and not isinstance(cb.widget(), Option):
            cb.widget().setChecked(checked)
        else:
            raise ValueError("set_checked called on option '%s' which is not a checked option" % key)

    def clear(self):
        """
        Clear all widgets out of the options box
        """
        while self.grid.count():
            child = self.grid.takeAt(0)
            if child.widget():
                child.widget().deleteLater()
        self._current_row = 0
        self._options = {}

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
        ret = collections.OrderedDict()
        for key, option in self._options.items():
            if option.isEnabled() and option.value is not None:
                ret[key] = option.value
        return ret

    def _cb_toggled(self, option):
        def _toggled(state):
            option.setEnabled(state)
            option.sig_changed.emit()
        return _toggled

class Option(object):
    """
    Base class for  an option

    We have a base class mainly so we can use ``isinstance`` to detect option
    widgets.
    
    All option widgets *must* define a ``value`` property method which returns the
    current value of the option in whatever type makes sense to the particular
    option type. Options must also define a Qt signal ``sig_changed`` which takes
    no parameters and is emitted whenever the option value changes.

    We would like to define sig_changed in the base class but this requires
    the class to be a QObject and we would end up with 
    multiple inheritance from QObject, QWidget which is probably
    very bad if it gets into the C++
    
    Options should probably make the ``value`` property settable so the option
    UI can be updated programatically.
    
    Options may support other properties, e.g. ``choices`` to set the current set
    of options in a ChoiceOption.
    """
    pass

class DataOption(Option, QtGui.QComboBox):
    """
    A combo box which gives a choice of data

    There is quite a lot of ugliness here because the box can be put into two modes - 
    single and multi-select. In multi-select mode we subvert the QComboBox to provide
    essentially a dropdown list of checkboxes. In single select mode things can be 
    complicated by providing 'all' and 'none' option.

    Probably this class should be split into two for each use case.
    """
    sig_changed = QtCore.Signal()

    def __init__(self, ivm, parent=None, **kwargs):
        super(DataOption, self).__init__(parent)
        self.ivm = ivm
        self._changed = False

        self._include_3d = kwargs.get("include_3d", True)
        self._include_4d = kwargs.get("include_4d", not kwargs.get("static_only", False))
        self._include_rois = kwargs.get("rois", False)
        self._include_nonrois = kwargs.get("data", True)
        
        self._none_option = kwargs.get("none_option", False)
        self._all_option = kwargs.get("all_option", False)
        self._multi = kwargs.get("multi", False)
        self._explicit = kwargs.get("explicit", False)
        self._data_changed()

        self.currentIndexChanged.connect(self._index_changed)
        self.ivm.sig_all_data.connect(self._data_changed)
        if self._multi:
            self.view().pressed.connect(self._item_pressed)
    
    @property
    def value(self):
        """ 
        Get the names of the selected data item(s)
        
        If neither all option nor multi options are specified, returns
        name of currently selected data item. Otherwise returns list of
        all selected data items.
        
        Also returns None if the none option is active and selected.
        """
        if self._multi:
            ret = []
            for idx in range(1, self.count()):
                item = self.model().item(idx, 0)
                if item.checkState() == QtCore.Qt.Checked:
                    ret.append(self.itemText(idx))
        else:
            current = self.currentText()        
            if self._none_option and current == "<none>":
                ret = None
            elif self._explicit and current == "":
                ret = None
            elif self._all_option and current == "<all>":
                ret = list(self.ivm.data.keys())
            elif self._all_option:
                ret = [current,]
            else:
                ret = current
        return ret
        
    @value.setter
    def value(self, val):
        """ 
        Set the selected data name(s)

        In multi-select mode val should be a sequence of data item names.
        In single-select mode val should be a data item name, or None
        or '<all>' (valid if the none/all options are enabled)
        """ 
        if self._multi:
            for name in val:
                idx = self.findText(name)
                item = self.model().item(idx, 0)
                item.setCheckState(QtCore.Qt.Checked)
        else:
            if val is None and self._none_option:
                val = "<none>"
                
            if self._explicit and val is None:
                self.setCurrentIndex(-1)
            elif isinstance(val, six.string_types):
                idx = self.findText(val)
                if idx >= 0:
                    self.setCurrentIndex(idx)
                else:
                    raise ValueError("Data item %s is not a valid choice for this option")
            else:
                raise ValueError("Can't specify multiple data items when DataOption is not in multi select mode")

    def _item_pressed(self, idx):
        item = self.model().itemFromIndex(idx)
        if item.checkState() == QtCore.Qt.Checked:
            item.setCheckState(QtCore.Qt.Unchecked)
        else:
            item.setCheckState(QtCore.Qt.Checked)
        self.setItemText(0, self._visible_text(self.value))
        self.sig_changed.emit()
        self._changed = True

    def hidePopup(self):
        """
        Overridden from QtGui.QComboBox

        To allow multi-select, don't hide the popup when it's clicked on to
        select/deselect data sets, so we can check and uncheck
        them in one go. However if nothing has changed as
        a result of the click (e.g. we click outside the popup
        window), this will close the popup
        """
        if not self._changed:
            QtGui.QComboBox.hidePopup(self)
        self._changed = False

    def _visible_text(self, selected_items):
        if selected_items:
            return ", ".join(selected_items)
        else:
            return "<Select data items>"

    def _index_changed(self):
        if self._multi:
            self.setCurrentIndex(0)
        self._update_highlight()
        self.sig_changed.emit()

    def _data_changed(self):
        self.blockSignals(True)
        try:
            data = []
            for name, qpd in self.ivm.data.items():
                if self._include_nonrois or (qpd.roi and self._include_rois):
                    data.append(name)

            current = self.value
            self.clear()
            
            if self._none_option and not self._multi:
                self.addItem("<none>")
            elif self._multi:
                self.addItem(self._visible_text(current))

            idx = 1
            for name in sorted(data):
                data = self.ivm.data.get(name, None)
                if data.nvols == 1 and self._include_3d:
                    self.addItem(data.name)
                    added = True
                elif data.nvols > 1 and self._include_4d:
                    self.addItem(data.name)
                    added = True
                else:
                    added = False

                if added:
                    if self._multi:
                        item = self.model().item(idx, 0)
                        if data.name in current:
                            item.setCheckState(QtCore.Qt.Checked)
                        else:
                            item.setCheckState(QtCore.Qt.Unchecked)
                    idx += 1

            if self._all_option and not self._multi:
                self.addItem("<all>")

            # Make sure names are visible even with drop down arrow
            width = self.minimumSizeHint().width()
            self.setMinimumWidth(width+50)
        finally:
            self.blockSignals(False)
        
        if self._multi:
            self.setCurrentIndex(0)
        elif isinstance(current, six.string_types):
            idx = self.findText(current)
            if idx >= 0:
                self.setCurrentIndex(idx)
            elif not self._explicit:
                # Default to first item, but do a quick switch to 
                # make sure signal is sent when first data arrives
                self.setCurrentIndex(-1)
                self.setCurrentIndex(0)
            else:
                self.setCurrentIndex(-1)
        elif self._explicit:
            self.setCurrentIndex(-1)
        else:
            # Must be <all> option
            self.setCurrentIndex(0)
        self._update_highlight()

    def setEnabled(self, enable):
        """
        Overridden from QtGui.QWidget

        Only highlight selector in red when widget is enabled
        """
        QtGui.QWidget.setEnabled(self, enable)
        self._update_highlight()

    def _update_highlight(self):
        if self._explicit and self.isEnabled() and self.currentIndex() == -1:
            self.setStyleSheet("QComboBox {background-color: #d05050}")
        else:
            self.setStyleSheet("")

class ChoiceOption(Option, QtGui.QComboBox):
    """ 
    Option which is chosen from a list of possible strings 
    """
    sig_changed = QtCore.Signal()

    def __init__(self, choices=(), return_values=None, default=None):
        QtGui.QComboBox.__init__(self)
        self.setChoices(choices, return_values)
        # Bizarre hack to make the dropdown height adjust to the items added
        self.setView(QtGui.QListView())
        if default:
            self.value = default
        self.currentIndexChanged.connect(self._changed)

    def setChoices(self, choices, return_values=None):
        """
        Set the list of options to be chosen from

        :param choices: Sequence of strings
        :param return_values: Optional matching sequence of strings to be returned 
                              as the ``value`` for each choice
        """
        if return_values is None:
            return_values = list(choices)

        if len(return_values) != len(choices):
            raise QpException("Number of return values must match number of choices")
        self.return_values = return_values
        self.choice_map = dict(zip([str(choice) for choice in choices], return_values))
        
        try:
            self.blockSignals(True)
            self.clear()
            for choice in choices:
                self.addItem(str(choice))
            self.setCurrentIndex(0)
        finally:
            self.blockSignals(False)
        self._changed()

    @property
    def value(self):
        """ 
        Value of currently selected option. 
        
        This is either the selected text, or the corresponding return value
        if these were supplied when the object was created
        """
        return self.choice_map.get(self.currentText(), None)
    
    @value.setter
    def value(self, choice):
        idx = self.findText(str(choice))
        if idx < 0:
            for ret_idx, ret in enumerate(self.return_values):
                if ret == choice:
                    idx = ret_idx
                    break
            
        if idx >= 0:
            self.setCurrentIndex(idx)
        else:
            raise ValueError("Value %s is not a valid choice for this option" % choice)

    def _changed(self):
        self.sig_changed.emit()

class TextOption(Option, QtGui.QLineEdit):
    """ 
    Option which contains arbitrary text
    """
    sig_changed = QtCore.Signal()

    def __init__(self, initial=""):
        QtGui.QLineEdit.__init__(self, initial)
        self.editingFinished.connect(self._changed)

    @property
    def value(self):
        """ Current text """
        return self.text()
    
    @value.setter
    def value(self, name):
        self.setText(name)

    def _changed(self):
        self.sig_changed.emit()
     
class OutputNameOption(TextOption):
    """ 
    Option used to specify the output data name for a process
    """
    
    def __init__(self, src_data=None, suffix="_out", initial="output"):
        TextOption.__init__(self)
        self.src_data = src_data
        self.initial = initial
        self.suffix = suffix
        self._reset()
        if src_data is not None:
            src_data.sig_changed.connect(self._reset)

    def _reset(self):
        if self.src_data is not None:
            self.setText(self.src_data.value + self.suffix)
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
        hbox.setContentsMargins(0, 0, 0, 0)
        self.setLayout(hbox)

        #self.min_edit = QtGui.QLineEdit(str(minval))
        #self.min_edit.editingFinished.connect(self_min_changed)
        #hbox.addWidget(self.min_edit)

        self.slider = QtGui.QSlider(QtCore.Qt.Horizontal)
        self.slider.setMaximum(100)
        self.slider.setMinimum(0)
        self.slider.setSliderPosition(int(100 * (default - minval) / (maxval - minval)))
        self.slider.valueChanged.connect(self._slider_changed)
        if kwargs.get("slider", True):
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

            val = self.value
            pos = 100 * (val - self.minval) / (self.maxval - self.minval)
            try:
                self.slider.blockSignals(True)
                self.slider.setSliderPosition(int(pos))
            finally:
                self.slider.blockSignals(False)

        except ValueError:
            self.val_edit.setStyleSheet("QLineEdit {background-color: #d05050}")
            self.valid = False

        self._changed()

    def _slider_changed(self, value):
        val = self.rtype(self.minval + (self.maxval - self.minval) * float(value) / 100)
        try:
            self.val_edit.blockSignals(True)
            self._update_edit(val)
        finally:
            self.val_edit.blockSignals(False)
        self._changed()

    @property
    def value(self):
        """ The numeric value selected """
        if self.valid:
            return self.rtype(self.val_edit.text())
        else:
            raise QpException("'%s' is not a valid number")

    @value.setter
    def value(self, value):
        self._update_edit(value)
        self._edit_changed()
    
    def _update_edit(self, value):
        if self.rtype == int:
            self.val_edit.setText(str(value))
        else:
            self.val_edit.setText(sf(value, sig_fig=self.decimals))

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

    def __init__(self, default=False, invert=False):
        """
        :param default: Initial value of ``value`` property
        :param invert: If True, ``value`` property is the opposite of the check state
        """ 
        QtGui.QCheckBox.__init__(self)
        if invert: default = not default
        self.setChecked(default)
        self.invert = invert
        self.stateChanged.connect(self._changed)

    @property
    def value(self):
        """ True or False according to whether the option is selected """
        if self.invert:
            return not self.isChecked()
        else:
            return self.isChecked()
    
    @value.setter
    def value(self, checked):
        if self.invert:
            checked = not checked
        self.setChecked(checked)

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
        """
        :return: True if matrix contains valid numeric values
        """
        try:
            self.values()
            return True
        except ValueError:
            return False

    @property
    def value(self):
        """ Matrix of numbers as a sequence of sequences """
        rows = []
        try:
            for r in range(self._model.rowCount()-int(self.expandable[1])):
                row = [float(self._model.item(r, c).text()) for c in range(self._model.columnCount()-int(self.expandable[0]))]
                rows.append(row)
        except:
            raise ValueError("Non-numeric data in list")
        return np.array(rows)

    @value.setter
    def value(self, mat):
        self.setMatrix(mat)

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
        """
        Set the values in the matrix
        """
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
                    item.setBackground(QtGui.QColor('#d05050'))

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
        """ Called when item is dragged into the matrix grid"""
        if event.mimeData().hasUrls:
            event.accept()
        else:
            event.ignore()

    def dragMoveEvent(self, event):
        """ Called when item is dragged over the matrix grid"""
        if event.mimeData().hasUrls:
            event.setDropAction(QtCore.Qt.CopyAction)
            event.accept()
        else:
            event.ignore()

    def dropEvent(self, event):
        """ 
        Called when item is dropped onto the matrix grid
        
        If it's a filename-like item, try to load a matrix
        from the file. Otherwise ignore it
        """
        if event.mimeData().hasUrls:
            event.setDropAction(QtCore.Qt.CopyAction)
            event.accept()
            for url in event.mimeData().urls():
                self._load_file(local_file_from_drop_url(url))
        else:
            event.ignore()
            
    def _load_file(self, filename):
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

    @property
    def value(self):
        """ Sequence of numbers """
        return self._from_matrix(MatrixOption.value.fget(self))

    def setList(self, values, **kwargs):
        """
        Set the matrix values as a 1D list
        """
        MatrixOption.setMatrix(self, self._to_matrix(values), **kwargs)

    def _load_file(self, filename):
        fvals, nrows, ncols = load_matrix(filename)

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
  
class NumberListOption(Option, QtGui.QLineEdit):
    """ 
    A list of numbers which may be entered space or comma separated
    """
    sig_changed = QtCore.Signal()

    def __init__(self, initial=(), intonly=False):
        QtGui.QLineEdit.__init__(self)
        if intonly:
            self._type = int
        else:
            self._type = float
        self.value = initial
        self.editingFinished.connect(self._edit_changed)

    @property
    def value(self):
        """ List of numbers or empty list if invalid data entered """
        try:
            text = self.text().replace(",", " ")
            return [self._type(v) for v in text.split()] 
        except ValueError:
            return []

    @value.setter
    def value(self, vals):
        self.setText(" ".join([str(v) for v in vals]))
        self._edit_changed()

    def _edit_changed(self):
        try:
            text = self.text().replace(",", " ")
            numbers = [self._type(v) for v in text.split()]
            self.setText(" ".join([str(v) for v in numbers]))
            self.setStyleSheet("")
        except ValueError:
            # Colour edit red but don't change anything
            self.setStyleSheet("QLineEdit {background-color: #d05050}")
        self.sig_changed.emit()

class PickPointOption(Option, QtGui.QWidget):
    """ 
    Option used to specify a single point in a data set
    """
    sig_changed = QtCore.Signal()

    def __init__(self, ivl, grid=None, intonly=True):
        """
        :param grid: DataGrid instance - output position will be reported relative to this grid
        :param intonly: If True, positions will be rounded to nearest integer
        """
        QtGui.QWidget.__init__(self)
        self._ivl = ivl
        self._grid = grid
        if intonly:
            self._rtype = int
            self._offset = 0.5
        else:
            self._rtype = float
            self._offset = 0

        hbox = QtGui.QHBoxLayout()
        hbox.setContentsMargins(0, 0, 0, 0)
        self.setLayout(hbox)

        self._edit = QtGui.QLineEdit()
        self._edit.editingFinished.connect(self._edit_changed)
        hbox.addWidget(self._edit)
        self._btn = QtGui.QPushButton("Pick point")
        self._btn.clicked.connect(self._pick_point)
        hbox.addWidget(self._btn)

        self._point = None
        
    @property
    def value(self):
        """ 3D position as float sequence relative to the grid specified in ``setGrid`` """
        return self._point
    
    def setGrid(self, grid):
        """
        Set the grid to be used when reporting the output point
        
        :param grid: DataGrid instance
        """
        if self._point:
            self._set_point(grid.grid_to_grid(self._point, from_grid=self._grid))
        self._grid = grid

    def _edit_changed(self):
        self._point = None
        try:
            point = [self._rtype(float(v)) for v in self._edit.text().split()]
            if len(point) == 3:
                self._point = point
        except ValueError:
            # Leave point as None if text is not valid
            pass

        self.sig_changed.emit()
      
    def _pick_point(self):
        self._ivl.set_picker(PickMode.SINGLE)
        self._ivl.sig_selection_changed.connect(self._point_picked)
        self._btn.setEnabled(False)

    def _point_picked(self, picker):
        self._set_point(picker.selection(self._grid))
        self._btn.setEnabled(True)
        self._ivl.sig_selection_changed.disconnect(self._point_picked)

    def _set_point(self, point):
        self._edit.setText(" ".join([str(self._rtype(v+self._offset)) for v in point[:3]]))
        self._edit_changed()

class FileOption(Option, QtGui.QWidget):
    """ 
    Option used to specify a file or directory
    """
    sig_changed = QtCore.Signal()

    def __init__(self, dirs=False, initial=""):
        """
        :param dirs: If True, allow only directories to be selected
        """
        QtGui.QWidget.__init__(self)
        self._dirs = dirs
        
        hbox = QtGui.QHBoxLayout()
        self.setLayout(hbox)
        self._edit = QtGui.QLineEdit(initial)
        hbox.addWidget(self._edit)
        self._btn = QtGui.QPushButton("Choose")
        self._btn.clicked.connect(self._clicked)
        hbox.addWidget(self._btn)
        
    @property
    def value(self):
        """ Return path of selected file """
        return self._edit.text()

    def _clicked(self):
        if self._dirs:
            path = QtGui.QFileDialog.getExistingDirectory(dir=self.value)
        else:
            path = QtGui.QFileDialog.getOpenFileName(dir=os.path.dirname(self.value))
        self._edit.setText(path)
        self.sig_changed.emit()

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
