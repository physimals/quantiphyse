import os.path

from PySide import QtGui
import nibabel as nib

class T10Widget(QtGui.QWidget):
    """
    Run T10 analysis on 3 input volumes
    """
    def __init__(self):
        super(T10Widget, self).__init__()
        self.dir = ""
        self.trval = 4.108

        layout = QtGui.QVBoxLayout()

        fabox = QtGui.QGroupBox()
        fabox.setTitle("Flip angle images")

        favbox = QtGui.QVBoxLayout()
        fabox.setLayout(favbox)

        self.l1 = QtGui.QTableWidget(self)
        self.l1.setColumnCount(2)
        self.l1.setSelectionBehavior(QtGui.QAbstractItemView.SelectRows)
        self.l1.setHorizontalHeaderLabels(["Filename", "Flip angle"])
        header = self.l1.horizontalHeader()
        header.setResizeMode(0, QtGui.QHeaderView.Stretch)

        bbox = QtGui.QHBoxLayout()
        b1 = QtGui.QPushButton('Add', self)
        b1.clicked.connect(self.add_fa)
        bbox.addWidget(b1)
        b2 = QtGui.QPushButton('Remove', self)
        b2.clicked.connect(self.remove_fa)
        bbox.addWidget(b2)

        favbox.addWidget(self.l1)
        favbox.addLayout(bbox)

        hb1 = QtGui.QHBoxLayout()
        hb1.addWidget(fabox)

        trbox = QtGui.QGroupBox()
        trbox.setTitle("Options")

        trgrid = QtGui.QGridLayout()
        trbox.setLayout(trgrid)

        trl = QtGui.QLabel("TR (ms)", self)
        trgrid.addWidget(trl, 0, 0)
        self.tre = QtGui.QLineEdit(str(self.trval), self)
        self.tre.editingFinished.connect(self.tr_changed)

        trgrid.addWidget(self.tre, 0, 1)

        hb2 = QtGui.QHBoxLayout()
        hb2.addWidget(trbox)
        hb2.addStretch(1)

        self.gen = QtGui.QPushButton('Generate T1 map', self)
        self.gen.clicked.connect(self.generate)

        hb3 = QtGui.QHBoxLayout()
        hb3.addWidget(self.gen)
        hb3.addStretch(2)

        layout.addLayout(hb1)
        layout.addLayout(hb2)
        layout.addLayout(hb3)

        self.setLayout(layout)

    def add_image_management(self, image_vol_management):
        """
        Adding image management
        """
        self.ivm = image_vol_management

    def tr_changed(self):
        try:
            self.trval = float(self.tre.text())
            print("TR=", self.trval)
        except:
            self.gen.setEnabled(False)
            QtGui.QMessageBox.warning(self, "Invalid TR", "TR must be a number", QtGui.QMessageBox.Close)

    def add_fa(self):
        filename = QtGui.QFileDialog.getOpenFileName(self, "Open FA image", dir=self.dir)
        if filename[0] is not None:
            self.dir = os.path.dirname(filename[0])
            while 1:
                text, result = QtGui.QInputDialog.getText(self, "Enter FA", "Enter flip angle")
                if result:
                    try:
                        fa = float(text)
                        self.l1.insertRow(0)
                        self.l1.setItem(0, 0, QtGui.QTableWidgetItem(filename[0]))
                        self.l1.setItem(0, 1, QtGui.QTableWidgetItem(text))
                        break
                    except:
                        QtGui.QMessageBox.warning(self, "Invalid FA", "Flip angle must be a number", QtGui.QMessageBox.Close)
                else:
                    break

    def remove_fa(self):
        row = self.l1.currentRow()
        print("Current row: ", row)
        self.l1.removeRow(row)

    def generate(self):
        fa_vols = []
        fa_angles = []
        print("TR=", self.trval)

        for i in range(self.l1.rowCount()):
            filename = self.l1.item(i, 0).text()
            fa = float(self.l1.item(i, 1).text())
            print(filename, fa)

            # FIXME need to check dimensions against volume
            img = nib.load(filename)
            fa_vols.append(img.get_data())
            fa_angles.append(fa)

#        T10 = t10_map(fa_vols, fa_angles, TR=self.trval)
