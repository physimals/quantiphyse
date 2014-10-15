from __future__ import print_function, division

from PySide import QtCore, QtGui
from QtInherit.QtSubclass import QGroupBoxB


class ImageExportWidget(QtGui.QWidget):

    sig_set_temp = QtCore.Signal(int)
    sig_cap_image = QtCore.Signal(int, str)

    def __init__(self):
        super(ImageExportWidget, self).__init__()

        #Clear curves button
        b1 = QtGui.QPushButton('Generate images', self)
        b1.clicked.connect(self.run_time_window_capture)

        l1 = QtGui.QVBoxLayout()
        l1.addWidget(b1)
        self.setLayout(l1)

        # Volume management
        self.ivm = None

    def add_image_management(self, image_vol_management):
        """
        Adding image management
        """
        self.ivm = image_vol_management

    @QtCore.Slot()
    def run_time_window_capture(self):
        """
        Capture 4D changes over time
        """
        imshape = self.ivm.get_image_shape()

        for ii in range(imshape[-1]):
            print(ii)

            self.sig_set_temp.emit(ii)

            #TODO Allow manual choice of a save directory
            output_name = '/local/engs1170/Test_image/' + str(ii).zfill(3) + '.png'
            print('Warning: Currently exporting to a preset directory in the code.')
            self.sig_cap_image.emit(1, output_name)






