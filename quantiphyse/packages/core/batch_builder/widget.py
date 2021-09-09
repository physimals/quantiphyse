"""
Quantiphyse - Widgets which supports the writing of batch files

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

import os

from PySide2 import QtGui, QtCore, QtWidgets

from quantiphyse.gui.widgets import QpWidget, TitleWidget, RunBox
from quantiphyse.utils.batch import BatchScript

class BatchBuilderWidget(QpWidget):
    """
    Simple widget for building and running batch files
    """
    def __init__(self, **kwargs):
        super(BatchBuilderWidget, self).__init__(name="Batch Builder", icon="batch", 
                                                 desc="Simple helper for building and running batch files", 
                                                 group="Utilities", **kwargs)
        self.process = BatchScript(self.ivm, stdout=open(os.devnull, "w"), quit_on_exit=False)

    def init_ui(self):
        vbox = QtWidgets.QVBoxLayout()
        self.setLayout(vbox)

        title = TitleWidget(self, title="Batch Builder", subtitle=self.description, batch_btn=False)
        vbox.addWidget(title)

        self.proc_edit = QtWidgets.QPlainTextEdit()
        self.proc_edit.textChanged.connect(self._validate)
        vbox.addWidget(self.proc_edit, stretch=2)

        hbox = QtWidgets.QHBoxLayout()
        #self.new_case_btn = QtWidgets.QPushButton("New Case")
        #hbox.addWidget(self.new_case_btn)
        #hbox.setAlignment(self.new_case_btn, QtCore.Qt.AlignTop)

        self.reset_btn = QtWidgets.QPushButton("Reset")
        self.reset_btn.clicked.connect(self._reset)
        hbox.addWidget(self.reset_btn)
        hbox.addStretch(1)

        self.save_btn = QtWidgets.QPushButton("Save")
        self.save_btn.clicked.connect(self._save)
        hbox.addWidget(self.save_btn)
        vbox.addLayout(hbox)

        self.run_box = RunBox(self._get_process, self._get_options)
        vbox.addWidget(self.run_box)

        self.proc_warn = QtWidgets.QLabel("")
        self.proc_warn.setStyleSheet("QLabel { color : red; }")
        vbox.addWidget(self.proc_warn)

        self.default_dir = os.getcwd()
        self.changed = False
        self._reset()

    def activate(self):
        self.ivm.sig_main_data.connect(self._update)
        self.ivm.sig_all_data.connect(self._update)
        self._update()

    def deactivate(self):
        self.ivm.sig_main_data.disconnect(self._update)
        self.ivm.sig_all_data.disconnect(self._update)

    def _update(self):
        if not self.changed:
            self._reset()

    def _reset(self):
        if self.changed and self.proc_edit.toPlainText().strip() != "":
            btn = QtWidgets.QMessageBox.warning(self, "Reset to current data",
                                            "Changes to batch file will be lost",
                                            QtWidgets.QMessageBox.Ok | QtWidgets.QMessageBox.Cancel)
            if btn != QtWidgets.QMessageBox.Ok:
                return
        
        t = ""
        if self.ivm.main is not None:
            filedata = [d for d in self.ivm.data.values() if hasattr(d, "fname") and d.fname is not None]
            filerois = [d for d in self.ivm.rois.values() if hasattr(d, "fname") and d.fname is not None]
            
            casedir = os.getcwd()
            if hasattr(self.ivm.main, "fname") and self.ivm.main.fname is not None:
                casedir = os.path.dirname(self.ivm.main.fname)

            t += "OutputFolder: qp_out\n"
            t += "Debug: False\n"
            t += "\n"
            t += "Processing:\n"
            t += "  - Load:\n"
            if filedata:
                t += "      data:\n"
                for qpd in filedata:
                    d, f = os.path.split(qpd.fname)
                    if d == casedir:
                        path = f
                    else:
                        path = qpd.fname
                    t += "        %s: %s\n" % (path, qpd.name)
            if filerois:
                t += "      rois:\n"
                for qpd in filerois:
                    d, f = os.path.split(qpd.fname)
                    if d == casedir:
                        path = f
                    else:
                        path = qpd.fname
                    t += "        %s: %s\n" % (path, qpd.name)
            t += "\n"
            t += "  # Additional processing steps go here\n"
            t += "\n"
            t += "  - SaveAllExcept:\n"
            for d in filedata:
                t += "      %s:\n" % d.name
            for d in filerois:
                t += "      %s:\n" % d.name
            t += "\n"

            t += "Cases:\n"
            t += "  Case1:\n"
            t += "    Folder: %s\n" % casedir
            t += "\n"

        self.proc_edit.setPlainText(t)
        self.changed = False
        self.reset_btn.setEnabled(False)

    def _validate(self):
        self.changed = True
        self.reset_btn.setEnabled(True)
        t = self.proc_edit.toPlainText()
        self.proc_warn.setText("")
        if '\t' in self.proc_edit.toPlainText():
            self.proc_warn.setText("Tabs detected")
        else:
            try:
                self.process.run({"yaml" : t, "mode" : "check"})
            except Exception as e:
                self.proc_warn.setText("Invalid script: %s" % str(e))

    def _get_process(self):
        return self.process

    def _get_options(self):
        return {"yaml" : self.proc_edit.toPlainText()}

    def _save(self):
        fname, _ = QtWidgets.QFileDialog.getSaveFileName(self, 'Save batch file', 
                                                     dir=self.default_dir, 
                                                     filter="YAML files (*.yaml)")
        if fname != '':
            f = open(fname, "w")
            try:
                f.write(self.proc_edit.toPlainText())
            finally:
                f.close()
        else: # Cancelled
            pass
