"""
Quantiphyse - Miscellaneous custom Qt widgets

Copyright (c) 2013-2018 University of Oxford
"""

import os
import sys
import inspect
import traceback

from PySide import QtGui, QtCore

from ..analysis import Process
from ..utils import debug, warn, get_icon, load_matrix, local_file_from_drop_url
from ..utils.exceptions import QpException
from .dialogs import error_dialog, TextViewerDialog, MultiTextViewerDialog, MatrixViewerDialog
from ..volumes.io import save

class QpWidget(QtGui.QWidget):
    """
    Base class for a Quantiphyse widget

    The following properties are set automatically from keyword args or defaults:
      self.ivm - Image Volume Management instance
      self.ivl - ImageView instance
      self.icon - QIcon for the menu/tab
      self.name - Name for the menu
      self.description - Longer description (for tooltip)
      self.tabname - Name for the tab
    """

    def __init__(self, **kwargs):
        super(QpWidget, self).__init__()

        # Basic metadata
        self.name = kwargs.get("name", "")
        self.tabname = kwargs.get("tabname", self.name.replace(" ", "\n"))
        self.group = kwargs.get("group", "")
        self.position = kwargs.get("position", 999)
        self.description = kwargs.get("desc", self.name)
        self.visible = False

        # This attempts to return the directory where the derived widget is defined - 
        # so we can look there for icons as well as in the default location
        self.pkgdir = os.path.abspath(os.path.dirname(inspect.getmodule(self).__file__))
        self.icon = QtGui.QIcon(get_icon(kwargs.get("icon", ""), self.pkgdir))

        # References to core classes
        self.ivm = kwargs.get("ivm", None)
        self.ivl = kwargs.get("ivl", None)
        self.opts = kwargs.get("opts", None)
        if self.opts:
            self.opts.sig_options_changed.connect(self.options_changed)

    def get_local_file(self, name):
        """
        Get a file which is stored locally to the implementing class
        """
        return os.path.abspath(os.path.join(self.pkgdir, name))

    def init_ui(self):
        """
        Called when widget is first shown. Widgets should ideally override this to build their
        UI widgets when required, rather than in the constructor which is called at startup
        """
        pass

    def activate(self):
        """
        Called when widget is made active, so can for example connect signals to the 
        volume management or view classes, and update it's current state
        """
        pass

    def deactivate(self):
        """
        Called when widget is made inactive, so should for example disconnect signals and remove 
        any related selections from the view
        """
        pass

    def options_changed(self):
        """
        Override to respond to global option changes
        """
        pass

class FingerTabBarWidget(QtGui.QTabBar):
    """
    Vertical tab bar used for the analysis widget setSelectionMode
    """
    def __init__(self, tab_widget, parent=None, *args, **kwargs):
        self.tab_size = QtCore.QSize(kwargs.pop('width', 100), kwargs.pop('height', 25))
        QtGui.QTabBar.__init__(self, parent, *args, **kwargs)
        self.close_icon = QtGui.QIcon(get_icon("close"))
        self.tab_widget = tab_widget

    def paintEvent(self, _):
        painter = QtGui.QStylePainter(self)
        option = QtGui.QStyleOptionTab()
 
        for index in range(self.count()):
            self.initStyleOption(option, index)
            tab_rect = self.tabRect(index)
            tab_rect.moveLeft(10)
            painter.drawControl(QtGui.QStyle.CE_TabBarTabShape, option)
            painter.drawText(tab_rect, QtCore.Qt.AlignVCenter |
                             QtCore.Qt.AlignHCenter,
                             self.tabText(index))
            painter.drawItemPixmap(tab_rect, QtCore.Qt.AlignLeft | QtCore.Qt.AlignVCenter,
                                   self.tabIcon(index).pixmap(20, 20))
            w = self.tab_widget.widget(index)
            if w.group != "DEFAULT":
                tab_rect.moveLeft(-5)
                tab_rect.moveTop(tab_rect.top()+5)
                painter.drawItemPixmap(tab_rect, QtCore.Qt.AlignRight | QtCore.Qt.AlignTop,
                                       self.close_icon.pixmap(10, 10))
        painter.end()

    def mousePressEvent(self, evt):
        QtGui.QTabBar.mousePressEvent(self, evt)
        idx = self.tabAt(evt.pos())
        if idx >= 0 and evt.button() == QtCore.Qt.LeftButton:
            tab_rect = self.tabRect(idx)
            oy = evt.pos().y() - tab_rect.top() - 5
            ox = tab_rect.right() - evt.pos().x() - 5
            if ox > 0 and ox < 10 and oy > 0 and oy < 10:
                # Click was inside close button
                w = self.tab_widget.widget(idx)
                if w.group != "DEFAULT":
                    w.visible = False
                    self.tab_widget.removeTab(idx)
        
    def tabSizeHint(self, _):
        return self.tab_size

class FingerTabWidget(QtGui.QTabWidget):
    """
    A QTabWidget equivalent which uses our FingerTabBarWidget
    """
    def __init__(self, parent, *args):
        QtGui.QTabWidget.__init__(self, parent, *args)
        self.setTabBar(FingerTabBarWidget(self, width=110, height=50))
        self.setTabPosition(QtGui.QTabWidget.West)
        self.setMovable(False)
        self.setIconSize(QtCore.QSize(16, 16))
    
class HelpButton(QtGui.QPushButton):
    """
    A button for online help
    """
    def __init__(self, parent, section="", base='http://quantiphyse.readthedocs.io/en/latest/'):

        super(HelpButton, self).__init__(parent)

        if section != "" and not section.endswith(".html"): section += ".html"
        self.link = base + section
        self.setToolTip("Online Help")

        icon = QtGui.QIcon(get_icon("question-mark"))
        self.setIcon(icon)
        self.setIconSize(QtCore.QSize(14, 14))

        self.clicked.connect(self.click_link)

    def click_link(self):
        """
        Provide a clickable link to help files

        :return:
        """
        QtGui.QDesktopServices.openUrl(QtCore.QUrl(self.link, QtCore.QUrl.TolerantMode))

class BatchButton(QtGui.QPushButton):
    """
    A button which displays the batch file code for the current analysis widget
    """
    def __init__(self, widget):
        super(BatchButton, self).__init__(widget)
        self.widget = widget
        
        icon = QtGui.QIcon(get_icon("batch"))
        self.setIcon(icon)
        self.setIconSize(QtCore.QSize(14, 14))

        self.setToolTip("Show batch mode options for this widget")

        self.clicked.connect(self.show_batch_options)
        
    def show_batch_options(self):
        """
        Show a dialog box containing the batch options supplied by the parent
        """
        if hasattr(self.widget, "batch_options"):
            batchopts = self.widget.batch_options()
            if len(batchopts) == 2:
                proc_name, opts = batchopts

                text = "  - %s:\n" % proc_name
                text += "\n".join(["      %s: %s" % (str(k), str(v)) for k, v in opts.items()])
                text += "\n"
                TextViewerDialog(self.widget, title="Batch options for %s" % self.widget.name, text=text).show()
            elif len(batchopts) == 3:
                proc_name, opts, support_files = batchopts
                text = "  - %s:\n" % proc_name
                text += "\n".join(["      %s: %s" % (str(k), str(v)) for k, v in opts.items()])
                text += "\n"
                support_files.insert(0, ("Batch code", text))
                MultiTextViewerDialog(self.widget, title="Batch options for %s" % self.widget.name, 
                                      pages=support_files).show()     
        else:
            error_dialog("This widget does not provide a list of batch options")

class OverlayCombo(QtGui.QComboBox):
    """
    A combo box which gives a choice of data

    Really ugly hacks to make it work for data / rois
    """
    def __init__(self, ivm, parent=None, static_only=False, none_option=False, all_option=False, data=True, rois=False):
        super(OverlayCombo, self).__init__(parent)
        self.ivm = ivm
        self.static_only = static_only
        self.none_option = none_option
        self.all_option = all_option
        self.rois = rois
        self.data = data
        if self.rois:
            self.ivm.sig_all_rois.connect(self._data_changed)
        if self.data:
            self.ivm.sig_all_data.connect(self._data_changed)
        self._data_changed()
    
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
                d = self.ivm.data.get(name, self.ivm.rois.get(name, None))
                if d.nvols == 1 or not self.static_only:
                    self.addItem(d.name)

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

class RoiCombo(OverlayCombo):
    """
    A combo box which gives a choice of ROIs
    """
    def __init__(self, ivm, *args, **kwargs):
        kwargs["rois"] = True
        kwargs["data"] = False
        super(RoiCombo, self).__init__(ivm, *args, **kwargs)
    
class NumericOption(QtGui.QWidget):
    """ Option whose value must be a number (int or float) """

    sig_changed = QtCore.Signal()

    def __init__(self, text, grid, ypos, xpos=0, minval=0, maxval=100, default=0, step=1, decimals=2, intonly=False, spin=True):
        QtGui.QWidget.__init__(self)
        self.use_spin = spin
        self.text = text
        self.minval = minval
        self.maxval = maxval
        self.valid = True

        if intonly:
            self.rtype = int
        else:
            self.rtype = float
            
        self.label = QtGui.QLabel(text)
        grid.addWidget(self.label, ypos, xpos)

        if spin:
            if intonly:
                self.spin = QtGui.QSpinBox()
            else:
                self.spin = QtGui.QDoubleSpinBox()
                self.spin.setDecimals(decimals)
                self.spin.setMinimum(minval)
            self.spin.setMaximum(maxval)
            self.spin.setValue(default)
            self.spin.setSingleStep(step)
            self.spin.valueChanged.connect(self._changed)
            grid.addWidget(self.spin, ypos, xpos+1)
        else:
            self.edit = QtGui.QLineEdit(str(default))
            self.edit.editingFinished.connect(self._edit_changed)
            grid.addWidget(self.edit, ypos, xpos+1)

    def _changed(self):
        self.sig_changed.emit()

    def _edit_changed(self):
        try:
            val = self.rtype(self.edit.text())
            self.valid = (val >= self.minval and val <= self.maxval)
            self.edit.setStyleSheet("")
        except ValueError:
            self.edit.setStyleSheet("QLineEdit {background-color: red}")
            self.valid = False
        self._changed()

    def value(self):
        """ Get the numeric value selected """
        if self.use_spin:
            return self.spin.value()
        elif self.valid:
            return self.rtype(self.edit.text())
        else:
            raise QpException("'%s' is not a valid number")
        
class OptionalName(QtGui.QWidget):
    """ String option which can be enabled or disabled """

    sig_changed = QtCore.Signal()

    def __init__(self, text, grid, ypos, xpos=0, default_on=False, default=""):
        QtGui.QWidget.__init__(self)
            
        self.label = QtGui.QCheckBox(text)
        self.label.setChecked(default_on)
        grid.addWidget(self.label, ypos, xpos)

        self.edit = QtGui.QLineEdit(default)
        self.edit.editingFinished.connect(self._edit_changed)
        grid.addWidget(self.edit, ypos, xpos+1)

        self.label.stateChanged.connect(self.edit.setVisible)

    def _changed(self):
        self.sig_changed.emit()

    def _edit_changed(self):
        self._changed()

    def selected(self):
        """ Return True if enabled """
        return self.label.isChecked()

    def value(self):
        """ Return the current text entered """
        return self.edit.text()
        
class ChoiceOption(QtGui.QWidget):
    """ Option which is chosen from a list of possible strings """

    sig_changed = QtCore.Signal()

    def __init__(self, text, grid, ypos, xpos=0, choices=None):
        QtGui.QWidget.__init__(self)
        if choices is None:
            choices = []
        self.choices = choices
        
        self.label = QtGui.QLabel(text)
        grid.addWidget(self.label, ypos, xpos)

        self.combo = QtGui.QComboBox()
        for c in choices:
            self.combo.addItem(c)
        self.combo.currentIndexChanged.connect(self._changed)
        grid.addWidget(self.combo, ypos, xpos+1)

    def _changed(self):
        self.sig_changed.emit()

    def value(self):
        """ Get currently selected text """
        return self.combo.currentText()
        
class NumberList(QtGui.QTableWidget):
    """
    Horizontal list of numeric values
    """
    def __init__(self, initial):
        QtGui.QTableWidget.__init__(self, 1, 1)
        self.horizontalHeader().hide()
        self.verticalHeader().hide()
        self.setValues(initial)
        self.setFixedHeight(self.rowHeight(0)+5)
        self.default_bg = self.item(0, 0).background()
        self.itemChanged.connect(self._item_changed)
        self.setAcceptDrops(True)

    def valid(self):
        """ Return True if all entries are valid numbers """
        try:
            self.values()
            return True
        except ValueError:
            return False

    def values(self):
        """ Return values as a list of list of floats """
        try:
            return [float(self.item(0, c).text()) for c in range(self.columnCount()-1)]
        except:
            raise RuntimeError("Non-numeric data in list")

    def setValues(self, vals):
        self.blockSignals(True)
        try:
            self.setColumnCount(len(vals)+1)
            for c, val in enumerate(vals):
                self.setItem(0, c, QtGui.QTableWidgetItem("%g" % val))
            self.setItem(0, self.columnCount()-1, QtGui.QTableWidgetItem("..."))
            self.resizeColumnsToContents()
            self.resizeRowsToContents()
        finally:
            self.blockSignals(False)

    def contextMenuEvent(self, event):
        menu = QtGui.QMenu(self)
        insertAction = menu.addAction("Insert before")
        deleteAction = menu.addAction("Delete")
        item = self.itemAt(event.pos())

        action = menu.exec_(self.mapToGlobal(event.pos()))
        if action == insertAction:
            self.insertValue(item.column(), 0)
        elif action == deleteAction:
            self.deleteValue(item.column())
            
    def deleteValue(self, col):
        self.blockSignals(True)
        try:
            for c in range(col, self.columnCount()-1):
                item = self.item(0, c+1)
                self.setItem(0, c, QtGui.QTableWidgetItem(item.text()))
            self.setColumnCount(self.columnCount()-1)
            self.resizeRowsToContents()
        finally:
            self.blockSignals(False)

    def insertValue(self, col, val):
        self.blockSignals(True)
        try:
            self.setColumnCount(self.columnCount()+1)
            for c in range(self.columnCount()-1, col, -1):
                item = self.item(0, c-1)
                self.setItem(0, c, QtGui.QTableWidgetItem(item.text()))
            self.setItem(0, col, QtGui.QTableWidgetItem("%g" % val))
            self.resizeRowsToContents()
        finally:
            self.blockSignals(False)

    def _item_changed(self, item):
        c = item.column()
        if item.text() == "":
            self.deleteValue(c)
        else:
            # Validate new value
            try:
                float(item.text())
                item.setBackground(self.default_bg)
            except ValueError:
                item.setBackground(QtGui.QColor('red'))

            # Add a new column if we have just edited the last one
            if c == self.columnCount() - 1:
                self.blockSignals(True)
                try:
                    self.setColumnCount(self.columnCount()+1)
                    self.setItem(0, self.columnCount()-1, QtGui.QTableWidgetItem("..."))
                finally:
                    self.blockSignals(False)
            self.resizeColumnsToContents()

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
        fvals, nrows, ncols = load_matrix(filename)
        
        if ncols <= 0:
            raise RuntimeError("No numeric data found in file")
        elif ncols == 1:
            self.setValues([r[0] for r in fvals])
        elif nrows == 1:
            self.setValues(fvals[0])
        else:
            # Choose row or column you want
            row, col = self._choose_row_col(fvals)
            if row is not None:
                self.setValues(fvals[row])
            elif col is not None:
                vals = [v[col] for v in fvals]
                self.setValues(vals)

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

class LoadNumbers(QtGui.QPushButton):
    """
    PushButton which loads values into a NumberList
    """
    def __init__(self, num_list, label="Load"):
        QtGui.QPushButton.__init__(self, label)
        self.num_list = num_list
        self.clicked.connect(self._button_clicked)

    def _button_clicked(self):
        filename = QtGui.QFileDialog.getOpenFileName()[0]
        if filename:
            self.num_list.loadFromFile(filename)

class NumberGrid(QtGui.QTableView):
    """
    Table of numeric values
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

        self.setValues(initial, False, col_headers=col_headers, row_headers=row_headers)
        
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

    def values(self):
        rows = []
        try:
            for r in range(self._model.rowCount()-int(self.expandable[1])):
                row = [float(self._model.item(r, c).text()) for c in range(self._model.columnCount()-int(self.expandable[0]))]
                rows.append(row)
        except:
            raise ValueError("Non-numeric data in list")
        return rows

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

    def setValues(self, vals, validate=True, col_headers=None, row_headers=None):
        if validate:
            if not vals: 
                raise ValueError("No values provided")
            elif len(vals[0]) != self._model.columnCount() and not self.expandable[0]:
                raise ValueError("Incorrect number of columns - expected %i" % self._model.columnCount())
            elif len(vals) != self._model.rowCount() and not self.expandable[1]:
                raise ValueError("Incorrect number of rows - expected %i" % self._model.rowCount())

        if (col_headers and self.expandable[0]) or (row_headers and self.expandable[1]):
            raise RuntimeError("Can't specify headers for auto-expandable dimensions")

        self._model.setRowCount(len(vals)+int(self.expandable[1]))
        self._model.setColumnCount(len(vals[0])+int(self.expandable[0]))

        if col_headers:
            self._model.setHorizontalHeaderLabels(col_headers)
            self.horizontalHeader().show()

        if row_headers:
            self._model.setVerticalHeaderLabels(row_headers)
            self.verticalHeader().show()
        
        self._model.blockSignals(True)
        try:
            for r, rvals in enumerate(vals):
                for c, v in enumerate(rvals):
                    item = QtGui.QStandardItem("%g" % v)
                    self._model.setItem(r, c, item)
            
            if self.expandable[0]:
                for r in range(len(vals)):
                    item = QtGui.QStandardItem("")
                    self._model.setItem(r, self._model.columnCount()-1, item)
        
            if self.expandable[1]:
                for c in range(len(vals[0])):
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
            links = []
            for url in event.mimeData().urls():
                self.loadFromFile(local_file_from_drop_url(url))
        else:
            event.ignore()
            
    def loadFromFile(self, filename):
        fvals, nrows, ncols = load_matrix(filename)
        if ncols <= 0:
            raise RuntimeError("No numeric data found in file")
        else:
            self.setValues(fvals)

class NumberGrid(QtGui.QTableWidget):
    """
    Table of numeric values
    """

    sig_changed = QtCore.Signal()

    def __init__(self, initial, col_headers=None, row_headers=None, expandable=(True, True),
                 fix_height=False, fix_width=False, readonly=False):
        QtGui.QTableWidget.__init__(self, 1, 1)
        
        if (col_headers and expandable[0]) or (row_headers and expandable[1]):
            raise RuntimeError("Can't specify headers for expandable dimensions")

        self.expandable=expandable
        self.row_headers = row_headers
        self.col_headers = col_headers
        self.fix_height = fix_height
        self.fix_width = fix_width
        self.setValues(initial, False)

        if col_headers:
            self.setHorizontalHeaderLabels(col_headers)
        else:
            self.horizontalHeader().hide()

        if row_headers:
            self.setVerticalHeaderLabels(row_headers)
        else:
            self.verticalHeader().hide()

        self.default_bg = self.item(0, 0).background()
        if readonly:
            self.setEditTriggers(QtGui.QAbstractItemView.NoEditTriggers)
        else:
            self.itemChanged.connect(self._item_changed)
        self.setSizePolicy(QtGui.QSizePolicy.Expanding, QtGui.QSizePolicy.Expanding)
        self.horizontalHeader().setResizeMode(QtGui.QHeaderView.ResizeToContents)
        self.setAcceptDrops(True)

    def valid(self):
        try:
            self.values()
            return True
        except:
            return False

    def values(self):
        rows = []
        try:
            for r in range(self.rowCount()-int(self.expandable[1])):
                row = [float(self.item(r, c).text()) for c in range(self.columnCount()-int(self.expandable[0]))]
                rows.append(row)
        except:
            raise RuntimeError("Non-numeric data in list")
        return rows

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

    def setValues(self, vals, validate=True):
        if validate:
            if len(vals) == 0: 
                raise RuntimeError("No values provided")
            elif len(vals[0]) != self.columnCount() and not self.expandable[0]:
                raise RuntimeError("Incorrect number of columns - expected %i" % self.columnCount())
            elif len(vals) != self.rowCount() and not self.expandable[1]:
                raise RuntimeError("Incorrect number of rows - expected %i" % self.rowCount())
            
        self.blockSignals(True)
        try:
            self.setRowCount(len(vals)+int(self.expandable[1]))
            self.setColumnCount(len(vals[0])+int(self.expandable[0]))
            for r, rvals in enumerate(vals):
                for c, v in enumerate(rvals):
                    item = QtGui.QTableWidgetItem("%g" % v)
                    self.setItem(r, c, item)
            
            if self.expandable[0]:
                for r in range(len(vals)):
                    item = QtGui.QTableWidgetItem("")
                    self.setItem(r, self.columnCount()-1, item)

            if self.expandable[1]:
                for c in range(len(vals[0])):
                    item = QtGui.QTableWidgetItem("")
                    self.setItem(self.rowCount()-1, c, item)

            self.resizeColumnsToContents()
            self.resizeRowsToContents()
        finally:
            self.blockSignals(False)
            
        self._set_size()
        
    def _range_empty(self, cs, rs):
        empty = True
        for r in rs:
            for c in cs:
                # Check if r or c is negative and do not consider empty
                # so last row/column will not be deleted
                if r < 0 or c < 0 or (self.item(r, c) is not None and self.item(r, c).text() != ""):
                    empty = False
                    break
        return empty

    def _item_changed(self, item):
        self.blockSignals(True)
        try:
            c = item.column()
            r = item.row()
            try:
                val = float(item.text())
                item.setBackground(self.default_bg)
            except:
                if item.text != "": 
                    item.setBackground(QtGui.QColor('red'))

            if self.expandable[0]:
                if c == self.columnCount() - 1:
                    self.setColumnCount(self.columnCount()+1)
                    # Set rest of new column to prevent it from immediately being invalid
                    for row in range(self.rowCount()-int(self.expandable[1])):
                        if row != r:
                            self.setItem(row, c, QtGui.QTableWidgetItem(self.item(row, c-1).text()))
                if self._range_empty([self.columnCount()-2], range(self.rowCount())):
                    # Last-but-one column is empty, so remove last column (which is always empty)
                    self.setColumnCount(self.columnCount()-1)

            if self.expandable[1]:
                if r == self.rowCount() - 1:
                    self.setRowCount(self.rowCount()+1)
                    # Set rest of new row to prevent it from immediately being invalid
                    for col in range(self.columnCount()-int(self.expandable[0])):
                        if col != c:
                            self.setItem(r, col, QtGui.QTableWidgetItem(self.item(r-1, col).text()))
                if self._range_empty(range(self.columnCount()), [self.rowCount()-2]):
                    # Last-but-one row is empty, so remove last row (which is always empty)
                    self.setColumnCount(self.columnCount()-1)
        finally:
            self.blockSignals(False)

        self.resizeColumnsToContents()
        self.resizeRowsToContents()
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
            links = []
>>>>>>> 568cb810af640a94bf939236e6160cfbbd41a26a
            for url in event.mimeData().urls():
                self.loadFromFile(local_file_from_drop_url(url))
        else:
            event.ignore()
            
    def loadFromFile(self, filename):
        fvals, nrows, ncols = load_matrix(filename)
        if ncols <= 0:
            raise RuntimeError("No numeric data found in file")
        else:
            self.setValues(fvals)

class NumberVList(NumberGrid):
    """
    Single-column NumberGrid
    """
    def __init__(self, initial, headers=None, expandable=True, fix_height=False):
        NumberGrid.__init__(self, initial, row_headers=headers, 
                            expandable=(False, expandable), fix_height=fix_height)

    def values(self):
        return [v[0] for v in NumberGrid.values(self)]

    def setValues(self, values, validate=True):
        NumberGrid.setValues(self, [[v,] for v in values], validate)

    def loadFromFile(self, filename):
        fvals, nrows, ncols = load_matrix(filename)
        
        if ncols <= 0:
            raise RuntimeError("No numeric data found in file")
        elif ncols == 1:
            self.setValues(fvals[0])
        else:
            # Choose row or column you want
            row, col = self._choose_row_col(fvals)
            if row is not None:
                self.setValues(fvals[row])
            elif col is not None:
                vals = [v[col] for v in fvals]
                self.setValues(vals)

    def _choose_row_col(self, vals):
        d = MatrixViewerDialog(self, vals, title="Choose a row or column", text="Select a row or column containing the data you want")
        if d.exec_():
            ranges = d.table.selectedRanges()
            if len(ranges) > 0:
                r = ranges[0]
                if r.topRow() == r.bottomRow():
                    # Row select
                    return r.topRow(), None
                elif r.leftColumn() == r.rightColumn():
                    # Column select
                    return None, r.leftColumn()
        return None, None    

class NumberHList(NumberVList):
    """
    Single-row NumberGrid
    """
    def __init__(self, initial, headers=None, expandable=True, fix_width=False):
        NumberGrid.__init__(self, initial, col_headers=headers, 
                            expandable=(expandable, False), fix_width=fix_width)

    def values(self):
        return NumberGrid.values(self)[0]

    def setValues(self, values, validate=True):
        NumberGrid.setValues(self, [values,], validate)

class Citation(QtGui.QWidget):
    def __init__(self, title, author, journal):
        QtGui.QWidget.__init__(self)
        self.title, self.author, self.journal = title, author, journal
        hbox = QtGui.QHBoxLayout()
        self.setLayout(hbox)

        btn = QtGui.QPushButton()
        icon = QtGui.QIcon(get_icon("citation"))
        btn.setIcon(icon)
        btn.setSizePolicy(QtGui.QSizePolicy.Maximum, QtGui.QSizePolicy.Maximum)
        btn.clicked.connect(self.lookup)
        hbox.addWidget(btn)
        hbox.setAlignment(btn, QtCore.Qt.AlignTop)

        text = "<font size=3><i>" + title + "</i><br>" + author + "<br>" + journal + "</font>"
        label = QtGui.QLabel(text)
        label.setWordWrap(True)
        hbox.addWidget(label)
        
    def lookup(self):
        import webbrowser, urllib
        search_terms = tuple([urllib.quote(s) for s in (self.title, self.author, self.journal)])
        url = "https://www.google.com/search?q=%s+%s+%s" % search_terms
        webbrowser.open(url, new=0, autoraise=True)

class OptionsButton(QtGui.QPushButton):
    def __init__(self, widget):
        QtGui.QPushButton.__init__(self)
        self.setIcon(QtGui.QIcon(get_icon("options.png")))
        self.setIconSize(QtCore.QSize(14, 14))
        self.clicked.connect(widget.show_options)

class TitleWidget(QtGui.QWidget):
    def __init__(self, widget, title=None, subtitle=None, help="", help_btn=True, batch_btn=True, opts_btn=False):
        QtGui.QWidget.__init__(self)
        if title is None:
            title = widget.name
        vbox = QtGui.QVBoxLayout()
        self.setLayout(vbox) 
        
        hbox = QtGui.QHBoxLayout()
        hbox.addWidget(QtGui.QLabel('<font size="5">%s</font>' % title))   
        hbox.addStretch(1)
        if batch_btn: hbox.addWidget(BatchButton(widget))
        if help_btn: hbox.addWidget(HelpButton(self, help))
        if opts_btn: hbox.addWidget(OptionsButton(widget))
        vbox.addLayout(hbox)

        if subtitle is None:
            subtitle = widget.description
        vbox.addWidget(QtGui.QLabel(subtitle))     

class RunBox(QtGui.QGroupBox):

    sig_postrun = QtCore.Signal()

    """
    Box containing a 'run' button, a progress bar, a 'cancel' button and a 'view log' button 

    Designed for use with BackgroundTask
    """
    def __init__(self, get_process_fn, get_rundata_fn, title="Run", btn_label="Run", save_option=False):
        QtGui.QGroupBox.__init__(self)
        self.save_option = save_option
        
        self.setTitle(title)
        self.setSizePolicy(QtGui.QSizePolicy.MinimumExpanding, QtGui.QSizePolicy.MinimumExpanding)
        
        vbox = QtGui.QVBoxLayout()
        self.setLayout(vbox)

        hbox = QtGui.QHBoxLayout()
        self.runBtn = QtGui.QPushButton(btn_label, self)
        self.runBtn.clicked.connect(self.start)
        hbox.addWidget(self.runBtn)
        self.progress = QtGui.QProgressBar(self)
        hbox.addWidget(self.progress)
        self.cancelBtn = QtGui.QPushButton('Cancel', self)
        self.cancelBtn.clicked.connect(self.cancel)
        self.cancelBtn.setEnabled(False)
        hbox.addWidget(self.cancelBtn)
        self.logBtn = QtGui.QPushButton('View log', self)
        self.logBtn.clicked.connect(self.view_log)
        self.logBtn.setEnabled(False)
        hbox.addWidget(self.logBtn)
        vbox.addLayout(hbox)

        if self.save_option:
            hbox = QtGui.QHBoxLayout()
            self.save_cb = QtGui.QCheckBox("Save copy of output data")
            hbox.addWidget(self.save_cb)
            self.save_folder_edit = QtGui.QLineEdit()
            hbox.addWidget(self.save_folder_edit)
            btn = QtGui.QPushButton("Choose folder")
            btn.clicked.connect(self.choose_output_folder)
            hbox.addWidget(btn)
            self.save_cb.stateChanged.connect(self.save_folder_edit.setEnabled)
            self.save_cb.stateChanged.connect(btn.setEnabled)
            vbox.addLayout(hbox)

        self.get_process_fn = get_process_fn
        self.get_rundata_fn = get_rundata_fn

    def start(self):
        """
        Start running the process
        """
        self.process = self.get_process_fn()
        rundata = self.get_rundata_fn()

        self.progress.setValue(0)
        self.runBtn.setEnabled(False)
        self.cancelBtn.setEnabled(True)
        self.logBtn.setEnabled(False)

        self.process.sig_finished.connect(self.finished)
        self.process.sig_progress.connect(self.update_progress)
    
        try:
            self.process.run(rundata)
        except:
            # Process failed to start, so call finished cb manually
            debug(traceback.format_exc())
            self.finished(Process.FAILED, sys.exc_info()[1], "", sys.exc_info()[1])

    def update_progress(self, complete):
        self.progress.setValue(100*complete)

    def cancel(self):
        self.process.cancel()
        self.progress.setValue(0)
        # These should be set by the 'finished' CB but make sure in case it fails
        self.runBtn.setEnabled(True)
        self.cancelBtn.setEnabled(False)

    def finished(self, status, result, log, exception):
        debug("Finished: ", status, result, len(log), exception)
        try:
            self.log = log
            if status == Process.SUCCEEDED:
                if self.save_option and self.save_cb.isChecked():
                    save_folder = self.save_folder_edit.text()   
                    data_to_save = []
                    for o in result:
                        if len(o.data) > 0: data_to_save = o.data.keys()
                    debug("Data to save: ", data_to_save)    
                    for d in data_to_save:
                        save(self.process.ivm.data[d], os.path.join(save_folder, d + ".nii"), self.process.ivm.save_grid)
                    logfile = open(os.path.join(save_folder, "logfile"), "w")
                    logfile.write(self.log)
                    logfile.close()
            elif status == Process.CANCELLED:
                pass
            elif exception is not None:
                raise exception
        finally:
            self.process.sig_finished.disconnect(self.finished)
            self.process.sig_progress.disconnect(self.update_progress)
            self.process = None
            self.runBtn.setEnabled(True)
            self.logBtn.setEnabled(True)
            self.cancelBtn.setEnabled(False)
            self.sig_postrun.emit()
            
    def view_log(self):
        self.logview = TextViewerDialog(text=self.log, parent=self)
        self.logview.show()
        self.logview.raise_()

    def choose_output_folder(self):
        outputDir = QtGui.QFileDialog.getExistingDirectory(self, 'Choose directory to save output')
        if outputDir:
            self.save_folder_edit.setText(outputDir)

class OrderList(QtGui.QListWidget):
    """
    Vertical list of items which can be re-ordered but not changed directly
    """
    
    sig_changed = QtCore.Signal()

    def __init__(self, initial=[], col_headers=None):
        QtGui.QListWidget.__init__(self)
        self.setSelectionMode(QtGui.QAbstractItemView.SingleSelection)
        self.setDropIndicatorShown(True)
        self.setDragDropMode(QtGui.QAbstractItemView.InternalMove)
        self.setSizePolicy(QtGui.QSizePolicy.Maximum, QtGui.QSizePolicy.Preferred)
        #if col_headers:
        #    self.setVerticalHeaderLabels(col_headers)
        #else:
        #    self.horizontalHeader().hide()

        self.setItems(initial)

    def setItems(self, items):
        self.blockSignals(True)
        try:
            self.clear()
            for r, item in enumerate(items):
                self.addItem(item)
            height = 0
            for r in range(len(items)):
                height += self.rectForIndex(self.indexFromItem(self.item(r))).height()
            self.setFixedHeight(height + 2*len(items))
        finally:
            self.blockSignals(False)
            self.sig_changed.emit()

    def items(self):
        return [self.item(r).text() for r in range(self.count())]

    def currentUp(self):
        """ Move currently selected item up"""
        idx = self.currentRow()
        if idx > 0:
            items = self.items()
            temp = items[idx-1]
            items[idx-1] = items[idx]
            items[idx] = temp
            self.setItems(items)
            self.setCurrentRow(idx-1)

    def currentDown(self):
        """ Move currently selected item down"""
        idx = self.currentRow() 
        if idx < self.count() - 1:
            items = self.items()
            temp = items[idx+1]
            items[idx+1] = items[idx]
            items[idx] = temp
            self.setItems(items)
            self.setCurrentRow(idx+1)

class OrderListButtons(QtGui.QVBoxLayout):
    def __init__(self, orderlist):
        QtGui.QVBoxLayout.__init__(self)
        self.list = orderlist
        self.up_btn = QtGui.QPushButton()
        self.up_btn.setIcon(QtGui.QIcon(get_icon("up.png")))
        self.up_btn.setFixedSize(16, 16)
        self.up_btn.clicked.connect(self.list.currentUp)
        self.addWidget(self.up_btn)
        self.down_btn = QtGui.QPushButton()
        self.down_btn.setIcon(QtGui.QIcon(get_icon("down.png")))
        self.down_btn.setFixedSize(16, 16)
        self.down_btn.clicked.connect(self.list.currentDown)
        self.addWidget(self.down_btn)
        self.addStretch(1)
        
