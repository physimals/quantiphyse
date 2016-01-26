from PySide import QtGui, QtCore


class HelpButton(QtGui.QPushButton):
    """
    A button for online help
    """

    def __init__(self, parent, lfp,
                 link='https://github.com/benjaminirving/PkView_help_files/blob/master/README.md#pkview-'):

        super(HelpButton, self).__init__(parent)

        self.link = link
        self.local_file_path = lfp
        self.setToolTip("Online Help")

        b1icon = QtGui.QIcon(self.local_file_path + '/icons/question-mark.svg')
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