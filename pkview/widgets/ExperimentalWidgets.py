"""

Author: Benjamin Irving (benjamin.irv@gmail.com)
Copyright (c) 2013-2015 University of Oxford, Benjamin Irving

"""

from __future__ import print_function, division

import warnings

from PySide import QtCore, QtGui


class ImageExportWidget(QtGui.QWidget):

    sig_set_temp = QtCore.Signal(int)
    sig_cap_image = QtCore.Signal(int, str)

    def __init__(self):
        super(ImageExportWidget, self).__init__()

        #Clear curves button
        b1 = QtGui.QPushButton('Generate temporal animation', self)
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
        if self.ivm.vol is None:
            QtGui.QMessageBox.warning(self, "No volume", "Can't generate animation without main volume loaded",
                                      QtGui.QMessageBox.Close)
            return

        imshape = self.ivm.vol.shape

        # Choose a folder to save images
        fname = QtGui.QFileDialog.getExistingDirectory(self, 'Choose folder to save images')
        if fname == '':
            return

        for ii in range(imshape[-1]):
            print("Frame number:", ii)
            self.sig_set_temp.emit(ii)
            output_name = fname + '/' + str(ii).zfill(3) + '.png'
            self.sig_cap_image.emit(1, output_name)






