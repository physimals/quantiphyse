from __future__ import division, unicode_literals, absolute_import, print_function

from PySide import QtCore, QtGui

import pyqtgraph as pg
import numpy as np

#TODO create an non-model based analysis tool which ties into creating new image objects


class SECurve(QtGui.QWidget):
    """
    Side widgets for plotting SE curves
    """

    sig_add_pnt = QtCore.Signal(tuple)
    sig_clear_pnt = QtCore.Signal(bool)

    def __init__(self):
        super(SECurve, self).__init__()

        self.win1 = pg.GraphicsWindow(title="Basic plotting examples")
        self.win1.setVisible(False)
        self.p1 = self.win1.addPlot(title="Signal enhancement curve")
        self.reset_graph()

        # Take a local region mean to reduce noise
        self.cb1 = QtGui.QCheckBox('Smooth curves', self)
        self.cb1.stateChanged.connect(self.reset_graph)

        #cb1.toggle()
        self.cb2 = QtGui.QCheckBox('Multiple curves', self)
        self.cb2.stateChanged.connect(self.reset_graph)

        #Signal enhancement (normalised)
        self.cb3 = QtGui.QCheckBox('Signal enhancement', self)
        self.cb3.stateChanged.connect(self.reset_graph)

        #Show mean
        self.cb4 = QtGui.QCheckBox('Show mean', self)

        #Clear curves button
        b1 = QtGui.QPushButton('Clear curves', self)
        b1.clicked.connect(self.reset_graph)


        # input temporal resolution
        self.text1 = QtGui.QLineEdit('1.0', self)
        self.text1.returnPressed.connect(self.replot_graph)

        # Select plot color
        combo = QtGui.QComboBox(self)
        combo.addItem("red")
        combo.addItem("blue")
        combo.addItem("green")
        combo.addItem("orange")
        combo.addItem("cyan")
        combo.addItem("brown")
        combo.activated[str].connect(self.emit_cchoice)

        l1 = QtGui.QGridLayout()
        l1.setSpacing(10)
        l1.addWidget(self.win1, 0, 0, 1, 3)

        space1 = QtGui.QLabel('')
        l1.addWidget(space1, 1, 0)

        l1.addWidget(self.cb1, 2, 0)
        l1.addWidget(self.cb2, 3, 0)
        l1.addWidget(self.cb3, 4, 0)
        l1.addWidget(QtGui.QLabel('Plot color'), 5, 0)

        l1.addWidget(QtGui.QLabel("Temporal resolution (s)"), 2, 1)
        l1.addWidget(self.text1, 2, 2)
        l1.addWidget(self.cb4, 3, 1)
        l1.addWidget(b1, 4, 1)
        l1.addWidget(combo, 5, 1)



        l1.setRowStretch(0, 2)
        l1.setRowStretch(1, 1)
        l1.setRowStretch(2, 1)
        l1.setRowStretch(3, 1)
        l1.setColumnStretch(0, 1)
        l1.setColumnStretch(1, 1)
        l1.setColumnStretch(2, 1)

        self.setLayout(l1)

        self.plot_color = (200, 200, 200)

    def _plot(self, values1):

        """
        Plot the curve / curves
        """
        #Make window visible and populate
        self.win1.setVisible(True)

        values1 = np.array(values1, dtype=np.double)
        values2 = np.copy(values1)

        # Setting x-values
        xres = float(self.text1.text())
        xx = xres * np.arange(len(values1))

        if self.values2_mean is None:
            self.values2_mean = np.zeros((1, len(xx)))

        if self.cb3.isChecked() is True:
            m1 = np.mean(values1[:3])
            values1 = values1 / m1 - 1
            values2 = np.copy(values1)

        if self.cb1.isChecked() is True:
            wsize = 3
            cwin1 = np.ones(wsize)/wsize
            values2 = np.convolve(values1, cwin1)
            print(len(values1))
            print(len(values2))
            values2 = values2[1:-1]
            print(len(values2))

        # Plotting using single or multiple plots
        if self.cb2.isChecked() is False:
            if self.curve1 is None:
                self.curve1 = self.p1.plot(pen=None, symbolBrush=(255, 0, 0), symbolPen='k')
                self.curve2 = self.p1.plot(pen=self.plot_color, width=4.0)
            self.curve2.setData(xx, values2)
            self.curve1.setData(xx, values1)

        # Multiple plots
        else:
            #Signal (add point to image
            self.sig_add_pnt.emit(self.plot_color)

            self.p1.plot(xx, values2, pen=self.plot_color, width=4.0)
            self.p1.plot(xx, values1, pen=None, symbolBrush=(200, 200, 200), symbolPen='k', symbolSize=5.0)

            # Plot mean curve as well
            if self.cb4.isChecked() is True:
                if self.curve_mean is None:
                    self.curve_mean = self.p1.plot(pen=(150, 0, 0), symbolBrush=(255, 0, 0), symbolPen='k')

                self.values2_mean[self.curve_count, :] = values2
                #self.curve_count += 1
                self.values2_mean = np.append(self.values2_mean, np.expand_dims(values2, axis=0), axis=0)
                self.curve_mean.setData(xx, np.squeeze(np.mean(self.values2_mean[1:], axis=0)))

        self.p1.setLabel('left', "Signal Enhancement")
        self.p1.setLabel('bottom', "Time", units='s')
        #self.p1.setLogMode(x=False, y=False)

    @QtCore.Slot()
    def replot_graph(self):
        self.reset_graph()
        #other stuff

    @QtCore.Slot()
    def reset_graph(self):
        """
        Reset and clear the graph
        """
        self.win1.removeItem(self.p1)
        self.p1 = self.win1.addPlot(title="Signal enhancement curve")
        self.curve1 = None
        self.curve2 = None
        self.curve_mean = None
        self.curve_count = 0
        self.values2_mean = None

        # Clear points on graph
        self.sig_clear_pnt.emit(True)

    @QtCore.Slot(np.ndarray)
    def sig_mouse(self, values1):
        """
        Get signal from mouse click
        """
        self._plot(values1)

    @QtCore.Slot(str)
    def emit_cchoice(self, text):
        if text == 'red':
            cvec = (255, 0, 0)
        elif text == 'green':
            cvec = (0, 255, 0)
        elif text == 'blue':
            cvec = (0, 0, 255)
        elif text == 'orange':
            cvec = (255, 140, 0)
        elif text == 'cyan':
            cvec = (0, 255, 255)
        elif text == 'brown':
            cvec = (139, 69, 19)
        else:
            cvec = (255, 255, 255)
        self.plot_color = cvec


class ColorOverlay1(QtGui.QWidget):
    """
    Color overlay interaction
    """

    #Signals
    #emit colormap choice
    sig_choose_cmap = QtCore.Signal(str)
    #emit alpha value
    sig_set_alpha = QtCore.Signal(int)

    def __init__(self):
        super(ColorOverlay1, self).__init__()

        l1 = QtGui.QVBoxLayout()

        lab1 = QtGui.QLabel("Transparency")

        sld1 = QtGui.QSlider(QtCore.Qt.Horizontal, self)
        sld1.setFocusPolicy(QtCore.Qt.NoFocus)
        sld1.setRange(0, 255)
        sld1.setValue(255)
        sld1.valueChanged[int].connect(self.emit_alpha)

        combo = QtGui.QComboBox(self)
        combo.addItem("jet")
        combo.addItem("hot")
        combo.addItem("gist_heat")
        combo.activated[str].connect(self.emit_cmap)

        # Take a local region mean to reduce noise
        self.cb1 = QtGui.QCheckBox('Show overlay', self)
        self.cb1.toggle()

        # Take a local region mean to reduce noise
        self.cb2 = QtGui.QCheckBox('Only show overlay in ROI', self)
        self.cb2.toggle()

        l1.addWidget(lab1)
        l1.addWidget(sld1)
        l1.addWidget(self.cb1)
        l1.addWidget(self.cb2)
        l1.addWidget(combo)

        self.setLayout(l1)

    def __plot(self, values1):
        self.curve.setData(values1)

    @QtCore.Slot(np.ndarray)
    def sig_mouse(self, values1):
        self.__plot(values1)

    @QtCore.Slot(str)
    def emit_cmap(self, text):
        self.sig_choose_cmap.emit(text)

    @QtCore.Slot(int)
    def emit_alpha(self, val1):
        self.sig_set_alpha.emit(val1)


class SECurve3(QtGui.QWidget):
    """
    Side widgets for plotting SE curves
    """

    def __init__(self):
        super(SECurve3, self).__init__()

        l1 = QtGui.QVBoxLayout()
        button1 = QtGui.QPushButton("test OK 2")

        l1.addWidget(button1)
        self.setLayout(l1)

    def __plot(self, values1):
        self.curve.setData(values1)

    @QtCore.Slot(np.ndarray)
    def sig_mouse(self, values1):
        self.__plot(values1)
