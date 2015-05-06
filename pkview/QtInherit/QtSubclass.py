"""

Author: Benjamin Irving (benjamin.irv@gmail.com)
Copyright (c) 2013-2015 University of Oxford, Benjamin Irving

"""

from PySide import QtGui


class QGroupBoxB(QtGui.QGroupBox):
    """
    Subclassing QGroupBox for a nice border
    """

    def __init__(self):
        super(QGroupBoxB, self).__init__()

        self.setStyleSheet("QGroupBox{border:2px solid gray;border-radius:5px;margin-top: 1ex;} "
                           "QGroupBox::title{subcontrol-origin: margin;subcontrol-position:top center;padding:0 3px;}")