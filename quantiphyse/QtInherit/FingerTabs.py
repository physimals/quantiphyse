# Finger Tabs
#
# Based on https://gist.github.com/LegoStormtroopr/5075267 by http://www.twitter.com/legostormtroopr - thanks!

from PySide import QtGui, QtCore

from ..utils import get_icon

class FingerTabBarWidget(QtGui.QTabBar):
    
    def __init__(self, tab_widget, parent=None, *args, **kwargs):
        self.tabSize = QtCore.QSize(kwargs.pop('width', 100), kwargs.pop('height', 25))
        QtGui.QTabBar.__init__(self, parent, *args, **kwargs)
        self.close_icon = QtGui.QIcon(get_icon("close"))
        self.tab_widget = tab_widget

    def paintEvent(self, event):
        painter = QtGui.QStylePainter(self)
        option = QtGui.QStyleOptionTab()
 
        for index in range(self.count()):
            self.initStyleOption(option, index)
            tabRect = self.tabRect(index)
            tabRect.moveLeft(10)
            painter.drawControl(QtGui.QStyle.CE_TabBarTabShape, option)
            painter.drawText(tabRect, QtCore.Qt.AlignVCenter |
                             QtCore.Qt.AlignHCenter,
                             self.tabText(index))
            painter.drawItemPixmap(tabRect,  QtCore.Qt.AlignLeft | QtCore.Qt.AlignVCenter,
                                   self.tabIcon(index).pixmap(20, 20))
            w = self.tab_widget.widget(index)
            if not w.default:
                tabRect.moveLeft(-5)
                tabRect.moveTop(tabRect.top()+5)
                painter.drawItemPixmap(tabRect,  QtCore.Qt.AlignRight | QtCore.Qt.AlignTop,
                                    self.close_icon.pixmap(10, 10))
        painter.end()

    def mousePressEvent(self, evt):
        QtGui.QTabBar.mousePressEvent(self, evt)
        idx = self.tabAt(evt.pos())
        if idx >= 0 and evt.button() == QtCore.Qt.LeftButton:
             tabRect = self.tabRect(idx)
             oy = evt.pos().y() - tabRect.top() - 5
             ox = tabRect.right() - evt.pos().x() - 5
             if ox > 0 and ox < 10 and oy > 0 and oy < 10:
                 # Click was inside close button
                 w = self.tab_widget.widget(idx)
                 if not w.default:
                     w.visible = False
                     self.tab_widget.removeTab(idx)
        
    def tabSizeHint(self,index):
        return self.tabSize

class FingerTabWidget(QtGui.QTabWidget):
    """A QTabWidget equivalent which uses our FingerTabBarWidget"""
    def __init__(self, parent, *args):
        QtGui.QTabWidget.__init__(self, parent, *args)
        self.setTabBar(FingerTabBarWidget(self, width=110, height=50))
        self.setTabPosition(QtGui.QTabWidget.West)
        self.setMovable(False)
        self.setIconSize(QtCore.QSize(16, 16))
    