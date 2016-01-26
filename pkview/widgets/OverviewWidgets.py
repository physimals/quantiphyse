from __future__ import print_function, division, absolute_import

from PySide import QtGui, QtCore
from ..QtInherit import HelpButton

class OverviewWidget(QtGui.QWidget):
    #
    sig_show_se = QtCore.Signal()

    def __init__(self, local_file_path):
        super(OverviewWidget, self).__init__()

        self.local_file_path = local_file_path

        layout = QtGui.QVBoxLayout()

        # List for volume management
        tb = QtGui.QLabel("<font size=50> PKView </font> \n")

        pixmap = QtGui.QPixmap(self.local_file_path + "/icons/main_icon.png")
        pixmap = pixmap.scaled(35, 35, QtCore.Qt.KeepAspectRatio)
        lpic = QtGui.QLabel(self)
        lpic.setPixmap(pixmap)

        b1 = HelpButton(self, self.local_file_path)
        l03 = QtGui.QHBoxLayout()
        l03.addWidget(lpic)
        l03.addWidget(tb)
        l03.addStretch(1)
        l03.addWidget(b1)

        ta = QtGui.QLabel("The GUI enables loading of an DCE-MRI \n volume, ROI and mulitiple overlays. \n"
                          "use help (?) buttons for more online information on \n each widget. \n")

        t1 = QtGui.QLabel("Current overlays")
        self.l1 = CaseWidget(self)

        self.cb1 = QtGui.QCheckBox('Show overlay', self)
        self.cb1.toggle()

        # Take a local region mean to reduce noise
        self.cb2 = QtGui.QCheckBox('Only show overlay in ROI', self)
        # self.cb2.toggle()

        layout.addLayout(l03)
        layout.addWidget(ta)
        layout.addStretch()
        layout.addWidget(t1)
        layout.addWidget(self.l1)
        layout.addWidget(self.cb1)
        layout.addWidget(self.cb2)

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

    def __init__(self, parent):
        super(CaseWidget, self).__init__(parent)

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



