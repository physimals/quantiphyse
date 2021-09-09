"""
Quantiphyse - Experimental widgets (not currently in GUI)

Copyright (c) 2013-2020 University of Oxford

Licensed under the Apache License, Version 2.0 (the "License");
you may not use this file except in compliance with the License.
You may obtain a copy of the License at

    http://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and
limitations under the License.
"""

from __future__ import print_function, division

from PySide2 import QtGui, QtCore, QtWidgets

from quantiphyse.gui.widgets import QpWidget, HelpButton

class ImageExportWidget(QpWidget):

    def __init__(self, **kwargs):
        super(ImageExportWidget, self).__init__(name="Image Export", desc="Export images and animations", icon="image_export", **kwargs)

    def init_ui(self):
        main_vbox = QtWidgets.QVBoxLayout()
        
        hbox = QtWidgets.QHBoxLayout()
        hbox.addWidget(QtWidgets.QLabel('<font size="5">Export animation</font>'))
        hbox.addStretch(1)
        hbox.addWidget(HelpButton(self))
        main_vbox.addLayout(hbox)

        hbox = QtWidgets.QHBoxLayout()
        b1 = QtWidgets.QPushButton('Generate', self)
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
        fname = QtWidgets.QFileDialog.getExistingDirectory(self, 'Choose folder to save images')
        if fname == '':
            return

        for ii in range(shape[-1]):
            self.debug("Frame number:", ii)
            self.ivl.set_time_pos(ii)
            output_name = fname + '/' + str(ii).zfill(3) + '.png'
            self.ivl.capture_view_as_image(1, output_name)

QP_WIDGETS = []





