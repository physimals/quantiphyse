"""
Author: Martin Craig
Copyright (c) 2017 University of Oxford
"""

from __future__ import division, unicode_literals, absolute_import, print_function

import numpy as np
from PySide import QtCore, QtGui

from pkview.QtInherit.dialogs import error_dialog
from pkview.QtInherit import HelpButton
from pkview.widgets import PkWidget
from pkview.ImageView import PickMode
from pkview.utils import get_icon

DESC = """
Toolbox for building regions of interest
"""

class RoiBuilderWidget(PkWidget):
    """
    Widget for building ROIs
    """

    def __init__(self, **kwargs):
        super(RoiBuilderWidget, self).__init__(name="ROI Builder", icon="roi_builder", desc="Build ROIs", **kwargs)

    def init_ui(self):
        layout = QtGui.QVBoxLayout()
        
        hbox = QtGui.QHBoxLayout()
        title = QtGui.QLabel("<font size=5>ROI Builder</font>")
        hbox.addWidget(title)
        hbox.addStretch(1)
        help_btn = HelpButton(self, "roi_builder")
        hbox.addWidget(help_btn)
        layout.addLayout(hbox)
        
        desc = QtGui.QLabel(DESC)
        desc.setWordWrap(True)
        layout.addWidget(desc)
        layout.addWidget(QtGui.QLabel(""))

        # Toolbox buttons
        hbox = QtGui.QHBoxLayout()
        toolbox = QtGui.QGroupBox()
        toolbox.setTitle("Toolbox")
        grid = QtGui.QGridLayout()
        toolbox.setLayout(grid)

        self.eraser_btn = QtGui.QPushButton()
        self.eraser_btn.setIcon(QtGui.QIcon(get_icon("eraser")))
        self.eraser_btn.setFixedSize(32, 32)
        self.eraser_btn.clicked.connect(self.eraser)
        grid.addWidget(self.eraser_btn, 0, 0)

        self.poly_btn = QtGui.QPushButton()
        self.poly_btn.setIcon(QtGui.QIcon(get_icon("polygon")))
        self.poly_btn.setFixedSize(32, 32)
        self.poly_btn.clicked.connect(self.polygon)
        grid.addWidget(self.poly_btn, 0, 1)
        
        self.pen_btn = QtGui.QPushButton()
        self.pen_btn.setIcon(QtGui.QIcon(get_icon("pen")))
        self.pen_btn.setFixedSize(32, 32)
        self.pen_btn.clicked.connect(self.polygon)
        grid.addWidget(self.pen_btn, 1, 0)
        
        self.pick_btn = QtGui.QPushButton()
        self.pick_btn.setIcon(QtGui.QIcon(get_icon("pick")))
        self.pick_btn.setFixedSize(32, 32)
        self.pick_btn.clicked.connect(self.polygon)
        grid.addWidget(self.pick_btn, 1, 1)
        
        hbox.addWidget(toolbox)
        hbox.addStretch(1)
        layout.addLayout(hbox)

        hbox = QtGui.QHBoxLayout()
        btn = QtGui.QPushButton("Done")
        btn.clicked.connect(self.done_btn_clicked)
        hbox.addWidget(btn)
        hbox.addStretch(1)

        layout.addLayout(hbox)
        layout.addStretch(1)
        self.setLayout(layout)

    def activate(self):
        self.ivl.set_picker(PickMode.LASSO)

    def deactivate(self):
        self.ivl.set_picker(PickMode.SINGLE)

    def eraser(self):
        print("Eraser")
    
    def polygon(self):
        print("Polygon")

    def done_btn_clicked(self):
        roi = self.ivl.picker.get_roi()
        self.ivm.add_roi("ROI_BUILDER", roi)
