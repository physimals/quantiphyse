from PySide import QtGui, QtCore

from ..utils import get_icon
from .dialogs import error_dialog, TextViewerDialog

class HelpButton(QtGui.QPushButton):
    """
    A button for online help
    """

    def __init__(self, parent, section="", base='http://quantiphyse.readthedocs.io/en/latest/'):

        super(HelpButton, self).__init__(parent)

        if section != "" and not section.endswith(".html"): section += ".html"
        self.link = base + section
        self.setToolTip("Online Help")

        icon = QtGui.QIcon(get_icon("question-mark"))
        self.setIcon(icon)
        self.setIconSize(QtCore.QSize(14, 14))

        self.clicked.connect(self.click_link)

    def click_link(self):
        """
        Provide a clickable link to help files

        :return:
        """
        QtGui.QDesktopServices.openUrl(QtCore.QUrl(self.link, QtCore.QUrl.TolerantMode))

class BatchButton(QtGui.QPushButton):
    """
    A button for online help
    """

    def __init__(self, widget):
        super(BatchButton, self).__init__(widget)
        self.widget = widget
        
        icon = QtGui.QIcon(get_icon("batch"))
        self.setIcon(icon)
        self.setIconSize(QtCore.QSize(14, 14))

        self.setToolTip("Show batch mode options for this widget")

        self.clicked.connect(self.show_batch_options)
        
    def show_batch_options(self):
        """
        Show a dialog box containing the batch options supplied by the parent
        """
        if hasattr(self.widget, "batch_options"):
            proc_name, opts = self.widget.batch_options()
            text = "  - %s:\n" % proc_name
            text += "\n".join(["      %s: %s" % (str(k), str(v)) for k, v in opts.items()])
            TextViewerDialog(self.widget, title="Batch options for %s" % self.widget.name, text=text).show()
        else:
            error_dialog("This widget does not provide a list of batch options")

class OverlayCombo(QtGui.QComboBox):
    """
    A combo box which gives a choice of overlays
    """
    
    def __init__(self, ivm, parent=None):
        super(OverlayCombo, self).__init__(parent)
        self.ivm = ivm
        self.ivm.sig_all_overlays.connect(self.overlays_changed)
        self.overlays_changed()
    
    def overlays_changed(self):
        current = self.currentText()
        self.clear()
            
        for ovl in self.ivm.overlays.values():
            self.addItem(ovl.name)

        idx = self.findText(current)
        self.setCurrentIndex(max(0, idx))
        
class RoiCombo(QtGui.QComboBox):
    """
    A combo box which gives a choice of ROIs
    """
    
    def __init__(self, ivm, parent=None):
        super(RoiCombo, self).__init__(parent)
        self.ivm = ivm
        self.ivm.sig_all_rois.connect(self.rois_changed)
        self.rois_changed()
    
    def rois_changed(self):
        current = self.currentText()
        self.clear()
            
        for roi in self.ivm.rois.values():
            self.addItem(roi.name)

        idx = self.findText(current)
        self.setCurrentIndex(max(0, idx))
        