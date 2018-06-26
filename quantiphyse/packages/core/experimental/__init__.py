"""
Quantiphyse - Experimental widgets (not currently in GUI)

Copyright (c) 2013-2018 University of Oxford
"""

from __future__ import print_function, division

from PySide import QtCore, QtGui

from quantiphyse.gui.widgets import QpWidget, HelpButton

class ImageExportWidget(QpWidget):

    def __init__(self, **kwargs):
        super(ImageExportWidget, self).__init__(name="Image Export", desc="Export images and animations", icon="image_export", **kwargs)

    def init_ui(self):
        main_vbox = QtGui.QVBoxLayout()
        
        hbox = QtGui.QHBoxLayout()
        hbox.addWidget(QtGui.QLabel('<font size="5">Export animation</font>'))
        hbox.addStretch(1)
        hbox.addWidget(HelpButton(self))
        main_vbox.addLayout(hbox)

        hbox = QtGui.QHBoxLayout()
        b1 = QtGui.QPushButton('Generate', self)
        b1.clicked.connect(self.run_time_window_capture)
        hbox.addWidget(b1)
        hbox.addStretch(1)
        main_vbox.addLayout(hbox)

        main_vbox.addStretch(1)
        self.setLayout(main_vbox)

    @QtCore.Slot()
    def run_time_window_capture(self):
        """
        Capture 4D changes over time
        """
        if self.ivm.vol is None:
            error_dialog("No data loaded")
            return

        shape = self.ivm.vol.shape

        # Choose a folder to save images
        fname = QtGui.QFileDialog.getExistingDirectory(self, 'Choose folder to save images')
        if fname == '':
            return

        for ii in range(shape[-1]):
            self.debug("Frame number:", ii)
            self.ivl.set_time_pos(ii)
            output_name = fname + '/' + str(ii).zfill(3) + '.png'
            self.ivl.capture_view_as_image(1, output_name)

QP_WIDGETS = []





