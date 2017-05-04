from PySide.QtGui import QDialog, QTableWidgetItem

from .ui_qtd import Ui_ModelOptionsDialog, Ui_VestDialog

class ModelOptionsDialog(QDialog, Ui_ModelOptionsDialog):
    def __init__(self, parent=None):
        super(ModelOptionsDialog, self).__init__(parent)
        self.setupUi(self)

class MatrixEditDialog(QDialog, Ui_VestDialog):
    def __init__(self, parent=None):
        QDialog.__init__(self, parent)
        self.setupUi(self)
        self.table.setRowCount(1)
        self.table.setColumnCount(1)
        self.AddColBtn.clicked.connect(self.add_col)
        self.DelColBtn.clicked.connect(self.del_col)
        self.AddRowBtn.clicked.connect(self.add_row)
        self.DelRowBtn.clicked.connect(self.del_row)

    def add_col(self):
        self.table.insertColumn(self.table.currentColumn())

    def del_col(self):
        if self.table.columnCount() > 1:
            self.table.removeColumn(self.table.currentColumn())

    def add_row(self):
        self.table.insertRow(self.table.currentRow())

    def del_row(self):
        if self.table.rowCount() > 1:
            self.table.removeRow(self.table.currentRow())

    def set_matrix(self, m, desc=""):
        self.descEdit.clear()
        self.descEdit.insertPlainText(desc)
        self.table.setRowCount(max(1, len(m)))
        self.table.setCurrentCell(0, 0);
        if len(m) > 0: self.table.setColumnCount(max(1, len(m[0])))
        for x, row in enumerate(m):
            for y, d in enumerate(row):
                self.table.setItem(x, y, QTableWidgetItem(str(d)))

    def get_matrix(self):
        m = []
        for r in range(self.table.rowCount()):
            row = []
            for c in range(self.table.columnCount()):
                try:
                    data = self.table.item(r, c).text()
                    row.append(float(data))
                except:
                    row.append(0)
                    print("WARNING: non-numeric data, converting to zero")
            m.append(row)
        return m, self.descEdit.toPlainText()
