"""

Author: Benjamin Irving (benjamin.irv@gmail.com)
Copyright (c) 2013-2015 University of Oxford, Benjamin Irving

"""

from PySide import QtGui

from pkview.utils import get_icon

class PkWidget(QtGui.QWidget):
    """
    Base class for a PkView widget

    The following properties are set automatically:
      self.ivm - Image Volume Management instance
      self.ivl - ImageView instance
      self.icon
      self.name
      self.description
    """
    def __init__(self, **kwargs):
        super(PkWidget, self).__init__()
        self.name = kwargs.get("name", "")
        self.description = kwargs.get("desc", self.name)
        self.icon = QtGui.QIcon(get_icon(kwargs.get("icon", "")))
        self.ivm = kwargs.get("ivm", None)
        self.ivl = kwargs.get("ivl", None)
        self.default = kwargs.get("default", False)
	self.visible = False
        self.tabname = kwargs.get("tabname", self.name.replace(" ", "\n"))
