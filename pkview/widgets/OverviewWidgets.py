
from PySide import QtGui, QtCore


class OverviewWidget(QtGui.QWidget):

    def __init__(self, local_file_path):
        super(OverviewWidget, self).__init__()

        self.local_file_path = local_file_path

        layout = QtGui.QVBoxLayout()

        w1 = QtGui.QPushButton(QtGui.QIcon(self.local_file_path + '/icons/voxel.svg'), "", self)

        w1.setStyleSheet('QPushButton {icon-size: 100px; background-color: #323232}')
        w1.setToolTip("Voxel analysis\n test")
        # w1.clicked.connect()

        t1 = QtGui.QLabel("Volume management")

        l1 = QtGui.QListWidget()

        layout.addWidget(w1)
        layout.addWidget(t1)
        layout.addWidget(l1)

        self.setLayout(layout)

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
        Adds additional overlay volumes to the combo list
        """

        for ii in list1:
            if ii not in self.combo2_all:
                self.combo2_all.append(ii)
                self.combo2.addItem(ii)

    @QtCore.Slot(str)
    def update_current_overlay(self, str1):

        if str1 in self.combo2_all:
            ind1 = self.combo2_all.index(str1)
            self.combo2.setCurrentIndex(ind1)

        else:
            print("Warning: This option does not exist")


