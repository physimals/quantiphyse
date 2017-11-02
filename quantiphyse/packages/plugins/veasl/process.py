import sys
import os
import warnings
import traceback
import time

import numpy as np

from quantiphyse.analysis import Process, BackgroundProcess
from quantiphyse.utils.exceptions import QpException

def _run_veasl(id, queue, rundata, main_data, roi):
    # Placeholder
    for i in range(10):
        queue.put((0, (i+1)*10, 100))
        time.sleep(1)
    return 0, True, {}

class VeaslProcess(BackgroundProcess):
    """
    Asynchronous background process to run Veasl
    """

    PROCESS_NAME = "Veasl"

    def __init__(self, ivm, **kwargs):
        BackgroundProcess.__init__(self, ivm, _run_veasl, **kwargs)

    def run(self, options):
        data_name = options.pop("data", None)
        if data_name is None and self.ivm.main is not None:
            data = self.ivm.main.std()
        elif data_name is not None:
            data = self.ivm.data[data_name].std()
        else:
            raise QpException("No data loaded")

        roi_name = options.pop("roi", None)
        if roi_name is None and self.ivm.current_roi is not None:
            roidata = self.ivm.current_roi.std()
        elif roi_name is not None:
            roidata = self.ivm.rois[roi_name].std()
        else:
            roidata = np.ones(data.shape[:3])

        # Pass in input data. To enable the multiprocessing module to split our volumes
        # up automatically we have to pass the arguments as a single list. This consists of
        # options, main data, roi
        input_args = [options, data, roidata]

        #if roidata is not None: self.voxels_todo = np.count_nonzero(roidata)
        #else: self.voxels_todo = self.ivm.main.grid.nvoxels
        self.voxels_todo = 100

        # Serial processing only for now
        n = 1

        self.voxels_done = [0, ] * n
        self.start(n, input_args)

    def timeout(self):
        if self.queue.empty(): return
        while not self.queue.empty():
            id, v, nv = self.queue.get()
            self.voxels_done[id] = v
        cv = sum(self.voxels_done)
        if self.voxels_todo > 0: complete = float(cv)/self.voxels_todo
        else: complete = 1
        self.sig_progress.emit(complete)

    def finished(self):
        """ Add output data to the IVM and set the combined log """
        if self.status == Process.SUCCEEDED:
            pass
            #self.log = "\n\n".join([o.log for o in self.output])
            #first = True
            #for key in self.output[0].data:
            #    recombined_item = np.concatenate([o.data[key] for o in self.output], 0)
            #    self.ivm.add_data(recombined_item, name=key, make_current=first)
            #    first = False
        elif hasattr(self.output, "log"):
            self.log = self.output.log
        else:
            self.log = ""
