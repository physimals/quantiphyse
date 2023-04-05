"""
Quantiphyse - Radial profile widget

Copyright (c) 2013-2020 University of Oxford

Licensed under the Apache License, Version 2.0 (the "License");
you may not use this file except in compliance with the License.
You may obtain a copy of the License at

    http://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and
limitations under the License.
"""
import math
import os

from PySide2 import QtGui, QtCore, QtWidgets
  
from quantiphyse.gui.widgets import QpWidget, TitleWidget
from quantiphyse.gui.plot import Plot
from quantiphyse.gui.options import OptionBox, DataOption, NumericOption, BoolOption, FileOption, ChoiceOption
from quantiphyse.data.load_save import load

class MyFileSystemModel(QtGui.QStandardItemModel):
    """
    Simple filesystem model for a tree view
    
    QFileSystemModel is not suitable here because it does not read the whole tree so we can't
    easily preserve state e.g. which files have been selected or not. This version is intended
    only for relatively small filesystem trees that do not change during use, e.g. processed
    output data
    
    This class has another useful feature in that when the root dir is change, files with 
    the same relative path in the new root dir have their check status preserved.

    A checkStateChanged signal is emitted for each change in check status. When the root
    dir is changed, this signal will be emitted for every currently selected file, and then
    again for any file that is selected automatically because it matched a previously selected
    file with the same relative path.
    """

    checkStateChanged = QtCore.Signal(str, bool)

    def __init__(self, extensions):
        """
        :param extensions: List of extensions (including .) which we should include
        """
        QtGui.QStandardItemModel.__init__(self)
        self._root = self.invisibleRootItem()
        self._subjid = ""
        self._rootdir = ""
        self._extensions = extensions
        self._checked = set()
        self.itemChanged.connect(self._item_changed)

    def _get_parent(self, parent_relpath):
        parts = os.path.normpath(parent_relpath).split(os.path.sep)
        ret = self._root
        for p in parts:
            if p == ".": continue
            found = False
            for idx in range(ret.rowCount()):
                child = ret.child(idx)
                if child.text() == p:
                    ret = child
                    found = True
                    break
            if not found:
                child = QtGui.QStandardItem(p)
                ret.appendRow(child)
                ret = child
        return ret

    def _item_changed(self, item):
        path = item.data(QtCore.Qt.UserRole)
        checked = item.checkState() == QtCore.Qt.Checked
        if checked:
            self._checked.add(path)
        else:
            self._checked.remove(path)
        self.checkStateChanged.emit(path, checked)

    @property
    def rootdir(self):
        return self._rootdir
    
    @rootdir.setter
    def rootdir(self, rootdir):
        self.clear()
        base = self.invisibleRootItem()
        self._rootdir = rootdir
        self._subjid = os.path.basename(rootdir)
        self._root = QtGui.QStandardItem(self._subjid)
        base.appendRow(self._root)

        for path in self._checked:
            self.checkStateChanged.emit(path, False)

        for path, dirs, files in os.walk(rootdir, topdown=True):
            relpath = os.path.relpath(path, self._rootdir)
            for f in files:
                for ext in self._extensions:
                    if f.endswith(ext):
                        parent = self._get_parent(relpath)
                        fpath = os.path.normpath(os.path.join(relpath, f))
                        item = QtGui.QStandardItem(f)
                        item.setData(fpath, QtCore.Qt.UserRole)
                        item.setCheckable(True)
                        if fpath in self._checked:
                            item.setCheckState(QtCore.Qt.Checked)
                            self._item_changed(item)
                        parent.appendRow(item)
                        break

class FileList(QtWidgets.QTreeView):
    """
    A tree view that displays a list of files matching a given set of extensions
    """

    sig_add = QtCore.Signal(str, str)
    sig_remove = QtCore.Signal(str, str)

    def __init__(self, extensions):
        QtWidgets.QTreeView.__init__(self)
        self._extensions = extensions
        self.model = MyFileSystemModel(extensions)
        self.model.checkStateChanged.connect(self._changed)
        self.setModel(self.model)
        self.setSortingEnabled(True)
        self.header().setSectionResizeMode(QtWidgets.QHeaderView.Stretch)

    def setDir(self, rootdir):
        self.model.rootdir = rootdir

    def _changed(self, relpath, checked):
        path = os.path.join(self.model.rootdir, relpath)
        if os.path.isfile(path):
            if checked:
                self.sig_add.emit(path, relpath) 
            else:
                self.sig_remove.emit(path, relpath)
    
class DataList(FileList):
    """
    Tree view that displays Nifti files in the viewer
    """

    def __init__(self, ivm):
        FileList.__init__(self, [".nii", ".nii.gz"])
        self.ivm = ivm
        self.sig_add.connect(self._add)
        self.sig_remove.connect(self._remove)
        
    def _get_name(self, path):
        fname = os.path.basename(path)
        for ext in self._extensions:
            if fname.endswith(ext):
                fname = fname[:fname.index(ext)]
                break
        return self.ivm.suggest_name(fname, ensure_unique=False)

    def _add(self, path, relpath):
        qpdata = load(path)
        self.ivm.add(qpdata, self._get_name(relpath), make_current=True)

    def _remove(self, path, relpath):
        name = self._get_name(relpath)
        if name in self.ivm.data:
            self.ivm.delete(name) 
    
class ImgList(QtWidgets.QWidget):
    """
    Widget containing a tree view that displays image files files and
    a Matplotlib canvas that displays selected images in a grid
    """

    def __init__(self):
        QtWidgets.QWidget.__init__(self)
        self.tree = FileList([".png", ".jpg"])
        self._grid_size = 1
        self._imgs = {}
        
        vbox = QtWidgets.QVBoxLayout()
        self.setLayout(vbox)
        vbox.addWidget(self.tree)

        from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
        from matplotlib.figure import Figure
        self.fig = Figure(figsize=(7, 5), dpi=65, facecolor=(1, 1, 1), edgecolor=(0, 0, 0))
        self.canvas = FigureCanvas(self.fig)
        vbox.addWidget(self.canvas)

        self.tree.sig_add.connect(self._add)
        self.tree.sig_remove.connect(self._remove)
    
    def setDir(self, rootdir):
        self.tree.setDir(rootdir)

    def _update_grid(self):
        num_imgs = len(self._imgs)
        gridx = max(1, int(math.ceil(math.sqrt(num_imgs))))
        gridy = int(math.ceil(num_imgs/gridx))
        self.fig.clear()

        idx = 1
        for path in self._imgs:
            img, _artist = self._imgs[path]
            ax = self.fig.add_subplot(gridy, gridx, idx)
            ax.get_xaxis().set_visible(False)
            ax.get_yaxis().set_visible(False)
            artist = ax.imshow(img)
            self._imgs[path] = (img, artist)
            idx += 1
        
        self.fig.tight_layout()
        self.canvas.draw()

    def _add(self, path, relpath):
        import matplotlib.image
        img = matplotlib.image.imread(path)
        self._imgs[relpath] = (img, None)
        self._update_grid()

    def _remove(self, path, relpath):
        self._imgs.pop(relpath, None)
        self._update_grid()

class TableList(FileList):

    def __init__(self):
        FileList.__init__(self, [".tsv", ".csv"])

class BatchExplorer(QpWidget):
    """
    Widget which allows you to explore the output of pipeline processing
    """
    def __init__(self, **kwargs):
        super(BatchExplorer, self).__init__(name="Batch Explorer", 
                                            icon="batch_explorer",
                                            desc="Explore the output of multi-subject pipelines", 
                                            group="Visualisation", **kwargs)

    def init_ui(self):
        vbox = QtWidgets.QVBoxLayout()
        self.setLayout(vbox)

        title = TitleWidget(self)
        vbox.addWidget(title)

        self.options = OptionBox("Subject selection")
        self.options.add("Root directory", FileOption(dirs=True), key="rootdir")
        self.options.add("Subject", ChoiceOption(), key="subjid")
        vbox.addWidget(self.options)

        self.tabs = QtWidgets.QTabWidget()
        self._data_tab = DataList(self.ivm)
        self.tabs.addTab(self._data_tab, "Data sets")
        self._img_tab = ImgList()
        self.tabs.addTab(self._img_tab, "Images")
        self._table_tab = TableList()
        #self.tabs.addTab(self._table_tab, "Tables")
        vbox.addWidget(self.tabs)

    def activate(self):
        self.ivm.sig_all_data.connect(self._data_changed)
        self.options.option("rootdir").sig_changed.connect(self._rootdir_changed)
        self.options.option("subjid").sig_changed.connect(self._subjid_changed)
        self._update()

    def deactivate(self):
        self.ivm.sig_all_data.disconnect(self._data_changed)
        self.options.option("rootdir").sig_changed.disconnect(self._rootdir_changed)
        self.options.option("subjid").sig_changed.disconnect(self._subjid_changed)

    def _data_changed(self):
        pass

    def _update(self):
        pass

    def _rootdir_changed(self):
        rootdir = self.options.option("rootdir").value
        subjids = [d for d in os.listdir(rootdir) if os.path.isdir(os.path.join(rootdir, d))]
        self.options.option("subjid").setChoices(subjids)

    def _subjid_changed(self):
        rootdir = self.options.option("rootdir").value
        subjid = self.options.option("subjid").value
        if subjid:
            subjdir = os.path.join(rootdir, subjid)
            self._data_tab.setDir(subjdir)
            self._img_tab.setDir(subjdir)
            self._table_tab.setDir(subjdir)
