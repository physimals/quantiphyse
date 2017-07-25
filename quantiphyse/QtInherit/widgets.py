from PySide import QtGui, QtCore

from ..utils import get_icon
from .dialogs import error_dialog, TextViewerDialog, MatrixViewerDialog

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
    A button for online help
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
            proc_name, opts = self.widget.batch_options()
            text = "  - %s:\n" % proc_name
            text += "\n".join(["      %s: %s" % (str(k), str(v)) for k, v in opts.items()])
            TextViewerDialog(self.widget, title="Batch options for %s" % self.widget.name, text=text).show()
        else:
            error_dialog("This widget does not provide a list of batch options")

class OverlayCombo(QtGui.QComboBox):
    """
    A combo box which gives a choice of overlays
    """
    def __init__(self, ivm, parent=None, static_only=False):
        super(OverlayCombo, self).__init__(parent)
        self.ivm = ivm
        self.static_only=static_only
        self.ivm.sig_all_overlays.connect(self.overlays_changed)
        self.overlays_changed()
    
    def overlays_changed(self):
        current = self.currentText()
        self.clear()
            
        for ovl in self.ivm.overlays.values():
            if (ovl.ndim == 3 or not self.static_only):
                self.addItem(ovl.name)

        idx = self.findText(current)
        self.setCurrentIndex(max(0, idx))
        # Make sure names are visible even with drop down arrow
        width = self.minimumSizeHint().width()
        self.setMinimumWidth(width+50)
        
class RoiCombo(QtGui.QComboBox):
    """
    A combo box which gives a choice of ROIs
    """
    def __init__(self, ivm, parent=None):
        super(RoiCombo, self).__init__(parent)
        self.ivm = ivm
        self.ivm.sig_all_rois.connect(self.rois_changed)
        self.rois_changed()
    
    def rois_changed(self):
        current = self.currentText()
        self.clear()
            
        for roi in self.ivm.rois.values():
            self.addItem(roi.name)

        idx = self.findText(current)
        self.setCurrentIndex(max(0, idx))
        # Make sure names are visible even with drop down arrow
        width = self.minimumSizeHint().width()
        self.setMinimumWidth(width+50)
        
class NumericOption(QtGui.QWidget):
    def __init__(self, text, grid, ypos, xpos=0, minval=0, maxval=100, default=0, step=1, decimals=2, intonly=False):
        QtGui.QWidget.__init__(self)
        self.label = QtGui.QLabel(text)
        if intonly:
            self.spin = QtGui.QSpinBox()
        else:
            self.spin = QtGui.QDoubleSpinBox()
            self.spin.setDecimals(decimals)

        self.spin.setMinimum(minval)
        self.spin.setMaximum(maxval)
        self.spin.setValue(default)
        self.spin.setSingleStep(step)

        grid.addWidget(self.label, ypos, xpos)
        grid.addWidget(self.spin, ypos, xpos+1)

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
        try:
            self.values()
            return True
        except:
            return False

    def values(self):
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
            self.setItem(0, col,  QtGui.QTableWidgetItem("%g" % val))
            self.resizeRowsToContents()
        finally:
            self.blockSignals(False)

    def _item_changed(self, item):
        c = item.column()
        try:
            val = float(item.text())
            item.setBackground(self.default_bg)
        except:
            item.setBackground(QtGui.QColor('red'))

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
            links = []
            for url in event.mimeData().urls():
                self.loadFromFile(str(url.toLocalFile()))
        else:
            event.ignore()

    def loadFromFile(self, filename):
        f = open(filename)
        fvals = []
        ncols = -1
        try:
            lines = f.readlines()
            for line in lines:
                # Discard comments
                line = line.split("#", 1)[0].strip()
                # Split by commas or spaces
                vals = line.replace(",", " ").split()
                if ncols < 0: ncols = len(vals)
                elif len(vals) != ncols:
                    raise RuntimeError("File must contain a matrix of numbers with fixed size (rows/columns)")

                for val in vals:
                    try:
                        fval = float(val)
                    except:
                        raise RuntimeError("Non-numeric value '%s' found in file %s" % (val, filename))
                fvals.append([float(v) for v in vals])     
        finally:
            f.close()

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

class NumberGrid(QtGui.QTableWidget):
    """
    Table of numeric values
    """
    def __init__(self, initial, col_headers=None, row_headers=None, expandable=True):
        QtGui.QTableWidget.__init__(self, 1, 1)
        
        self.expandable=expandable
        self.setValues(initial)

        if col_headers:
            self.setHorizontalHeaderLabels(col_headers)
        else:
            self.horizontalHeader().hide()
        if row_headers:
            self.setVerticalHeaderLabels(row_headers)
        else:
            self.verticalHeader().hide()

        self.default_bg = self.item(0, 0).background()
        self.itemChanged.connect(self._item_changed)

    def valid(self):
        try:
            self.values()
            return True
        except:
            return False

    def values(self):
        rows = []
        try:
            for r in range(self.rowCount()-int(self.expandable)):
                row = [float(self.item(r, c).text()) for c in range(self.columnCount()-int(self.expandable))]
                rows.append(row)
        except:
            raise RuntimeError("Non-numeric data in list")
        return rows

    def setValues(self, vals):
        if len(vals) == 0: raise RuntimeError("No values provided")
        
        self.blockSignals(True)
        try:
            self.setRowCount(len(vals)+int(self.expandable))
            self.setColumnCount(len(vals[0])+int(self.expandable))
            for r, rvals in enumerate(vals):
                for c, v in enumerate(rvals):
                    self.setItem(r, c, QtGui.QTableWidgetItem("%g" % v))

            if self.expandable:
                for r in range(len(vals)):
                    self.setItem(r, self.columnCount()-1, QtGui.QTableWidgetItem(""))
                for c in range(len(vals[0])):
                    self.setItem(self.rowCount()-1, c, QtGui.QTableWidgetItem(""))

            self.resizeColumnsToContents()
            self.resizeRowsToContents()
        finally:
            self.blockSignals(False)

    def _item_changed(self, item):
        c = item.column()
        try:
            val = float(item.text())
            item.setBackground(self.default_bg)
        except:
            item.setBackground(QtGui.QColor('red'))

        if self.expandable:
            self.blockSignals(True)
            try:
                if c == self.columnCount() - 1:
                    self.setColumnCount(self.columnCount()+1)
                if r == self.rowCount() - 1:
                    self.setRowCount(self.rowCount()+1)
            finally:
                self.blockSignals(False)

        self.resizeColumnsToContents()
        self.resizeRowsToContents()

class OrderList(QtGui.QListWidget):
    """
    Vertical list of items which can be re-ordered but not changed directly
    """
    def __init__(self, initial):
        QtGui.QListWidget.__init__(self)
        self.setItems(initial)
        #self.setFixedHeight(self.rowHeight(0)+5)
        self.setSelectionMode(QtGui.QAbstractItemView.SingleSelection)
        self.setDropIndicatorShown(True)
        self.setDragDropMode(QtGui.QAbstractItemView.InternalMove)

    def setItems(self, items):
        self.blockSignals(True)
        try:
            self.clear()
            for r, item in enumerate(items):
                self.addItem(item)
        finally:
            self.blockSignals(False)

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
        self.up_btn = QtGui.QPushButton("Up")
        self.up_btn.clicked.connect(self.list.currentUp)
        self.addWidget(self.up_btn)
        self.down_btn = QtGui.QPushButton("Down")
        self.down_btn.clicked.connect(self.list.currentDown)
        self.addWidget(self.down_btn)
        self.addStretch(1)
        