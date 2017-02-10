from PySide import QtGui, QtCore
from pkview.utils import get_icon

class HelpButton(QtGui.QPushButton):
    """
    A button for online help
    """

    def __init__(self, parent, link='http://pkview.readthedocs.io/en/latest/'):

        super(HelpButton, self).__init__(parent)

        self.link = link
        self.setToolTip("Online Help")

        b1icon = QtGui.QIcon(get_icon("question-mark"))
        self.setIcon(b1icon)
        self.setIconSize(QtCore.QSize(14, 14))

        self.clicked.connect(self.click_link)

    @QtCore.Slot()
    def click_link(self):
        """
        Provide a clickable link to help files

        :return:
        """
        QtGui.QDesktopServices.openUrl(QtCore.QUrl(self.link, QtCore.QUrl.TolerantMode))
