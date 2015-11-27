from __future__ import print_function, division
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
        self.l1 = CaseWidget()

        layout.addWidget(w1)
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



