
from PySide import QtGui, QtCore


class OverviewWidget(QtGui.QWidget):

    def __init__(self, local_file_path):
        super(OverviewWidget, self).__init__()

        self.local_file_path = local_file_path

        layout = QtGui.QVBoxLayout()

        w1 = QtGui.QPushButton(QtGui.QIcon(self.local_file_path + '/icons/voxel.svg'), "", self)

        w1.setStyleSheet('QPushButton {icon-size: 80px; background-color: #323232}')
        w1.setToolTip("Voxel analysis\n test")
        # w1.clicked.connect()

        # List for volume management
        t1 = QtGui.QLabel("Volume management")
        self.l1 = QtGui.QListWidget()

        layout.addWidget(w1)
        layout.addWidget(t1)
        layout.addWidget(self.l1)

        self.setLayout(layout)

        self.list_current = []

    def add_image_management(self, image_vol_management):
        """
        Adding image management
        """
        self.ivm = image_vol_management

        #listen to volume management changes
        self.ivm.sig_current_overlay.connect(self.update_current_overlay)
        self.ivm.sig_all_overlays.connect(self.update_overlays)

    # TODO need to make this previous code work for the list view
    @QtCore.Slot(list)
    def update_overlays(self, list1):

        """
        Adds additional overlay volumes to the list
        """

        for ii in list1:
            if ii not in self.list_current:
                self.list_current.append(ii)
                self.l1.addItem(ii)

    @QtCore.Slot(str)
    def update_current_overlay(self, str1):

        if str1 in self.list_current:
            ind1 = self.list_current.index(str1)
            self.l1.setCurrentIndex(ind1)

        else:
            print("Warning: This option does not exist")


