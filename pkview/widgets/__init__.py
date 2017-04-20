"""

Author: Benjamin Irving (benjamin.irv@gmail.com)
Copyright (c) 2013-2015 University of Oxford, Benjamin Irving

"""

from PySide import QtGui

from pkview.utils import get_icon

class PkWidget(QtGui.QWidget):
    """
    Base class for a PkView widget

    The following properties are set automatically from keyword args or defaults:
      self.ivm - Image Volume Management instance
      self.ivl - ImageView instance
      self.icon - QIcon for the menu/tab
      self.name - Name for the menu
      self.desc - Longer description (for tooltip)
      self.tabname - Name for the tab
    """
    def __init__(self, **kwargs):
        super(PkWidget, self).__init__()
        self.name = kwargs.get("name", "")
        self.description = kwargs.get("desc", self.name)
        self.icon = QtGui.QIcon(get_icon(kwargs.get("icon", "")))
        self.opts = kwargs.get("opts", None)
        self.ivm = kwargs.get("ivm", None)
        self.ivl = kwargs.get("ivl", None)
        self.default = kwargs.get("default", False)
        self.visible = False
        self.tabname = kwargs.get("tabname", self.name.replace(" ", "\n"))
        if self.opts:
                self.opts.sig_options_changed.connect(self.options_changed)

    def init(self):
        """
        Called when widget is first shown. Widgets may choose to override this to delay
        expensive setup operations until required
        """
        pass

    def activate(self):
        """
        Called when widget is made active, so can for example connect signals to the 
        volume management or view classes, and update it's current state
        """
        pass

    def deactivate(self):
        """
        Called when widget is made inactive, so should for example disconnect signals and remove 
        any related selections from the view
        """
        pass

    def options_changed(self):
        """
        Override to respond to global option changes
        """
        pass

