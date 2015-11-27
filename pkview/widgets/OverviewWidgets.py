from __future__ import print_function, division
from PySide import QtGui, QtCore


class OverviewWidget(QtGui.QWidget):
    #
    sig_show_se = QtCore.Signal()

    def __init__(self, local_file_path):
        super(OverviewWidget, self).__init__()

        self.local_file_path = local_file_path

        layout = QtGui.QVBoxLayout()

        t0 = QtGui.QLabel("Analysis Options")

        # Option 1
        w1 = QtGui.QPushButton(QtGui.QIcon(self.local_file_path + '/icons/voxel.svg'),
                               "Voxel analysis \n ...", self)
        w1.setStyleSheet('QPushButton {icon-size: 20px; background-color: #323232}')
        w1.setToolTip("Voxel analysis\n test")
        # w1.clicked.connect()


        # Option 2
        w2 = QtGui.QPushButton(QtGui.QIcon(self.local_file_path + '/icons/voxel.svg'),
                           "Overlay Options \n ...", self)
        w2.setStyleSheet('QPushButton {icon-size: 20px; background-color: #323232}')
        w2.setToolTip("Voxel analysis\n test")
        # w1.clicked.connect()

        # Option 3
        w3 = QtGui.QPushButton(QtGui.QIcon(self.local_file_path + '/icons/voxel.svg'),
                               "Curve Clustering \n ...", self)
        w3.setStyleSheet('QPushButton {icon-size: 20px; background-color: #323232}')
        w3.setToolTip("Voxel analysis\n test")
        # w1.clicked.connect()

        # Option 4
        w4a = QtGui.QPushButton(QtGui.QIcon(self.local_file_path + '/icons/voxel.svg'),
                               "T10 \n ...", self)
        w4a.setStyleSheet('QPushButton {icon-size: 20px; background-color: #323232}')
        w4a.setToolTip("Voxel analysis\n test")
        # w1.clicked.connect()


        # Option 4
        w4 = QtGui.QPushButton(QtGui.QIcon(self.local_file_path + '/icons/voxel.svg'),
                               "Pharmacokinetics \n ...", self)
        w4.setStyleSheet('QPushButton {icon-size: 20px; background-color: #323232}')
        w4.setToolTip("Voxel analysis\n test")
        # w1.clicked.connect()

        # Option 5
        w5 = QtGui.QPushButton(QtGui.QIcon(self.local_file_path + '/icons/voxel.svg'),
                               "Supervoxel clustering and analysis \n ...", self)
        w5.setStyleSheet('QPushButton {icon-size: 20px; background-color: #323232}')
        w5.setToolTip("Voxel analysis\n test")
        # w1.clicked.connect()

        # Option 6
        w6 = QtGui.QPushButton(QtGui.QIcon(self.local_file_path + '/icons/voxel.svg'),
                               "Clustering \n ...", self)
        w6.setStyleSheet('QPushButton {icon-size: 20px; background-color: #323232}')
        w6.setToolTip("Voxel analysis\n test")
        # w1.clicked.connect()


        # List for volume management
        t1 = QtGui.QLabel("Current overlays")
        self.l1 = CaseWidget()

        layout.addWidget(t0)
        layout.addWidget(w1)
        layout.addWidget(w2)
        layout.addWidget(w3)
        layout.addWidget(w4a)
        layout.addWidget(w4)
        layout.addWidget(w5)
        layout.addWidget(w6)

        layout.addWidget(t1)
        layout.addWidget(self.l1)

        self.setLayout(layout)

    def add_image_management(self, image_vol_management):
        """
        Adding image management
        """
        self.ivm = image_vol_management

        #listen to volume management changes
        self.ivm.sig_current_overlay.connect(self.update_current_overlay)
        self.ivm.sig_all_overlays.connect(self.update_overlays)

        self.l1.add_image_management(self.ivm)


    @QtCore.Slot(list)
    def update_overlays(self, list1):
        self.l1.update_list(list1)

    @QtCore.Slot(str)
    def update_current_overlay(self, str1):
        self.l1.update_current_overlay(str1)


class CaseWidget(QtGui.QListWidget):
    """
    Class to handle the organisation of the loaded volumes
    """

    # emit reset command
    sig_emit_reset = QtCore.Signal(bool)

    def __init__(self):
        super(CaseWidget, self).__init__()

        self.list_current = []

        self.ivm = None

        self.currentItemChanged.connect(self.emit_volume)

    def add_image_management(self, image_volume_management):

        self.ivm = image_volume_management

    def update_list(self, list1):
        """

        Args:
            list1:

        Returns:

        """
        for ii in list1:
            if ii not in self.list_current:
                self.list_current.append(ii)
                self.addItem(ii)

    def update_current_overlay(self, str1):
        """
        Get the current item
        Args:
            str1:

        Returns:

        """
        if str1 in self.list_current:
            ind1 = self.list_current.index(str1)
            self.setCurrentItem(self.item(ind1))

        else:
            print("Warning: This option does not exist")

    @QtCore.Slot()
    def emit_volume(self, choice1, choice1_prev):

        self.ivm.set_current_overlay(choice1.text(), broadcast_change=False)
        self.sig_emit_reset.emit(1)



