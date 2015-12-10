from PySide import QtGui, QtCore
from FingerTabs import FingerTabWidget, FingerTabBarWidget

import sys

app = QtGui.QApplication(sys.argv)
tabs = QtGui.QTabWidget()
tabs.setTabBar(FingerTabBarWidget(width=100,height=25))
digits = ['Thumb','Pointer','Rude','Ring','Pinky']
for i,d in enumerate(digits):
    widget =  QtGui.QLabel("Area #%s <br> %s Finger"% (i,d))
    tabs.addTab(widget, d)
tabs.setTabPosition(QtGui.QTabWidget.West)
tabs.show()
sys.exit(app.exec_())
