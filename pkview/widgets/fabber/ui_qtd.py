# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'C:/Users/ctsu0221/build/fabber_core/pyfab/pyfab_mainwin.ui'
#
# Created: Thu Apr 27 10:29:36 2017
#      by: pyside-uic 0.2.15 running on PySide 1.2.1
#
# WARNING! All changes made in this file will be lost!

from PySide import QtCore, QtGui

class Ui_ModelOptionsDialog(object):
    def setupUi(self, ModelOptionsDialog):
        ModelOptionsDialog.setObjectName("ModelOptionsDialog")
        ModelOptionsDialog.resize(600, 500)
        sizePolicy = QtGui.QSizePolicy(QtGui.QSizePolicy.Minimum, QtGui.QSizePolicy.Minimum)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(ModelOptionsDialog.sizePolicy().hasHeightForWidth())
        ModelOptionsDialog.setSizePolicy(sizePolicy)
        ModelOptionsDialog.setMinimumSize(QtCore.QSize(600, 500))
        ModelOptionsDialog.setSizeGripEnabled(False)
        self.verticalLayout = QtGui.QVBoxLayout(ModelOptionsDialog)
        self.verticalLayout.setObjectName("verticalLayout")
        self.modelLabel = QtGui.QLabel(ModelOptionsDialog)
        sizePolicy = QtGui.QSizePolicy(QtGui.QSizePolicy.Preferred, QtGui.QSizePolicy.Fixed)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.modelLabel.sizePolicy().hasHeightForWidth())
        self.modelLabel.setSizePolicy(sizePolicy)
        font = QtGui.QFont()
        font.setPointSize(20)
        font.setWeight(50)
        font.setItalic(False)
        font.setBold(False)
        self.modelLabel.setFont(font)
        self.modelLabel.setObjectName("modelLabel")
        self.verticalLayout.addWidget(self.modelLabel)
        self.descLabel = QtGui.QLabel(ModelOptionsDialog)
        sizePolicy = QtGui.QSizePolicy(QtGui.QSizePolicy.Preferred, QtGui.QSizePolicy.Fixed)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.descLabel.sizePolicy().hasHeightForWidth())
        self.descLabel.setSizePolicy(sizePolicy)
        font = QtGui.QFont()
        font.setPointSize(10)
        font.setWeight(75)
        font.setItalic(True)
        font.setBold(True)
        self.descLabel.setFont(font)
        self.descLabel.setObjectName("descLabel")
        self.verticalLayout.addWidget(self.descLabel)
        self.scrollArea = QtGui.QScrollArea(ModelOptionsDialog)
        self.scrollArea.setHorizontalScrollBarPolicy(QtCore.Qt.ScrollBarAlwaysOff)
        self.scrollArea.setWidgetResizable(True)
        self.scrollArea.setObjectName("scrollArea")
        self.scrollAreaWidgetContents = QtGui.QWidget()
        self.scrollAreaWidgetContents.setGeometry(QtCore.QRect(0, 0, 580, 391))
        self.scrollAreaWidgetContents.setObjectName("scrollAreaWidgetContents")
        self.gridLayout = QtGui.QGridLayout(self.scrollAreaWidgetContents)
        self.gridLayout.setObjectName("gridLayout")
        self.grid = QtGui.QGridLayout()
        self.grid.setObjectName("grid")
        self.gridLayout.addLayout(self.grid, 0, 0, 1, 1)
        self.scrollArea.setWidget(self.scrollAreaWidgetContents)
        self.verticalLayout.addWidget(self.scrollArea)
        self.buttonBox = QtGui.QDialogButtonBox(ModelOptionsDialog)
        self.buttonBox.setOrientation(QtCore.Qt.Horizontal)
        self.buttonBox.setStandardButtons(QtGui.QDialogButtonBox.Close)
        self.buttonBox.setObjectName("buttonBox")
        self.verticalLayout.addWidget(self.buttonBox)

        self.retranslateUi(ModelOptionsDialog)
        QtCore.QObject.connect(self.buttonBox, QtCore.SIGNAL("accepted()"), ModelOptionsDialog.accept)
        QtCore.QObject.connect(self.buttonBox, QtCore.SIGNAL("rejected()"), ModelOptionsDialog.reject)
        QtCore.QMetaObject.connectSlotsByName(ModelOptionsDialog)

    def retranslateUi(self, ModelOptionsDialog):
        ModelOptionsDialog.setWindowTitle(QtGui.QApplication.translate("ModelOptionsDialog", "Options", None, QtGui.QApplication.UnicodeUTF8))
        self.modelLabel.setText(QtGui.QApplication.translate("ModelOptionsDialog", "Model", None, QtGui.QApplication.UnicodeUTF8))
        self.descLabel.setText(QtGui.QApplication.translate("ModelOptionsDialog", "Description", None, QtGui.QApplication.UnicodeUTF8))

# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'C:/Users/ctsu0221/build/fabber_core/pyfab/pyfab_matrix.ui'
#
# Created: Thu Apr 27 10:29:36 2017
#      by: pyside-uic 0.2.15 running on PySide 1.2.1
#
# WARNING! All changes made in this file will be lost!

from PySide import QtCore, QtGui

class Ui_VestDialog(object):
    def setupUi(self, VestDialog):
        VestDialog.setObjectName("VestDialog")
        VestDialog.resize(668, 365)
        self.verticalLayout = QtGui.QVBoxLayout(VestDialog)
        self.verticalLayout.setObjectName("verticalLayout")
        self.verticalLayout_4 = QtGui.QVBoxLayout()
        self.verticalLayout_4.setObjectName("verticalLayout_4")
        self.label_3 = QtGui.QLabel(VestDialog)
        font = QtGui.QFont()
        font.setPointSize(18)
        self.label_3.setFont(font)
        self.label_3.setObjectName("label_3")
        self.verticalLayout_4.addWidget(self.label_3)
        self.horizontalLayout = QtGui.QHBoxLayout()
        self.horizontalLayout.setObjectName("horizontalLayout")
        self.verticalLayout_3 = QtGui.QVBoxLayout()
        self.verticalLayout_3.setObjectName("verticalLayout_3")
        self.label = QtGui.QLabel(VestDialog)
        self.label.setObjectName("label")
        self.verticalLayout_3.addWidget(self.label)
        self.descEdit = QtGui.QPlainTextEdit(VestDialog)
        sizePolicy = QtGui.QSizePolicy(QtGui.QSizePolicy.Expanding, QtGui.QSizePolicy.Fixed)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.descEdit.sizePolicy().hasHeightForWidth())
        self.descEdit.setSizePolicy(sizePolicy)
        self.descEdit.setMaximumSize(QtCore.QSize(16777215, 60))
        self.descEdit.setObjectName("descEdit")
        self.verticalLayout_3.addWidget(self.descEdit)
        self.label_2 = QtGui.QLabel(VestDialog)
        self.label_2.setObjectName("label_2")
        self.verticalLayout_3.addWidget(self.label_2)
        self.table = QtGui.QTableWidget(VestDialog)
        self.table.setRowCount(2)
        self.table.setColumnCount(2)
        self.table.setObjectName("table")
        self.table.setColumnCount(2)
        self.table.setRowCount(2)
        self.verticalLayout_3.addWidget(self.table)
        self.horizontalLayout.addLayout(self.verticalLayout_3)
        self.verticalLayout_2 = QtGui.QVBoxLayout()
        self.verticalLayout_2.setObjectName("verticalLayout_2")
        self.AddColBtn = QtGui.QPushButton(VestDialog)
        self.AddColBtn.setObjectName("AddColBtn")
        self.verticalLayout_2.addWidget(self.AddColBtn)
        self.DelColBtn = QtGui.QPushButton(VestDialog)
        self.DelColBtn.setObjectName("DelColBtn")
        self.verticalLayout_2.addWidget(self.DelColBtn)
        self.AddRowBtn = QtGui.QPushButton(VestDialog)
        self.AddRowBtn.setObjectName("AddRowBtn")
        self.verticalLayout_2.addWidget(self.AddRowBtn)
        self.DelRowBtn = QtGui.QPushButton(VestDialog)
        self.DelRowBtn.setObjectName("DelRowBtn")
        self.verticalLayout_2.addWidget(self.DelRowBtn)
        spacerItem = QtGui.QSpacerItem(20, 40, QtGui.QSizePolicy.Minimum, QtGui.QSizePolicy.Expanding)
        self.verticalLayout_2.addItem(spacerItem)
        self.horizontalLayout.addLayout(self.verticalLayout_2)
        self.verticalLayout_4.addLayout(self.horizontalLayout)
        self.verticalLayout.addLayout(self.verticalLayout_4)
        self.buttonBox = QtGui.QDialogButtonBox(VestDialog)
        self.buttonBox.setOrientation(QtCore.Qt.Horizontal)
        self.buttonBox.setStandardButtons(QtGui.QDialogButtonBox.Cancel|QtGui.QDialogButtonBox.Ok)
        self.buttonBox.setObjectName("buttonBox")
        self.verticalLayout.addWidget(self.buttonBox)

        self.retranslateUi(VestDialog)
        QtCore.QObject.connect(self.buttonBox, QtCore.SIGNAL("accepted()"), VestDialog.accept)
        QtCore.QObject.connect(self.buttonBox, QtCore.SIGNAL("rejected()"), VestDialog.reject)
        QtCore.QMetaObject.connectSlotsByName(VestDialog)

    def retranslateUi(self, VestDialog):
        VestDialog.setWindowTitle(QtGui.QApplication.translate("VestDialog", "Matrix File Editor", None, QtGui.QApplication.UnicodeUTF8))
        self.label_3.setText(QtGui.QApplication.translate("VestDialog", "Matrix Editor", None, QtGui.QApplication.UnicodeUTF8))
        self.label.setText(QtGui.QApplication.translate("VestDialog", "Description", None, QtGui.QApplication.UnicodeUTF8))
        self.label_2.setText(QtGui.QApplication.translate("VestDialog", "Data", None, QtGui.QApplication.UnicodeUTF8))
        self.AddColBtn.setText(QtGui.QApplication.translate("VestDialog", "Add Column", None, QtGui.QApplication.UnicodeUTF8))
        self.DelColBtn.setText(QtGui.QApplication.translate("VestDialog", "Remove Column", None, QtGui.QApplication.UnicodeUTF8))
        self.AddRowBtn.setText(QtGui.QApplication.translate("VestDialog", "Add Row", None, QtGui.QApplication.UnicodeUTF8))
        self.DelRowBtn.setText(QtGui.QApplication.translate("VestDialog", "Remove Row", None, QtGui.QApplication.UnicodeUTF8))

