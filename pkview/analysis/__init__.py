"""

Author: Benjamin Irving (benjamin.irv@gmail.com)
Copyright (c) 2013-2015 University of Oxford, Benjamin Irving

"""
import numpy as np
import multiprocessing
import multiprocessing.pool

from PySide import QtCore

_pool = None

# Number of workers in pool. Best if equal to number of cores (or less if you want to do other things
# at the same time!)
NUM_WORKERS = 8

# Axis to split along. Could be 0, 1 or 2, but 0 is probably optimal for Numpy arrays which are column-major
# by default
SPLIT_AXIS = 0

def _init_pool():
    global _pool
    if _pool is None: _pool = multiprocessing.Pool(NUM_WORKERS)

class MultiProcess(QtCore.QObject):
    """
    Enables a parallelisable analysis task to be carried out by multiple processes by
    splitting the Numpy arrays
    """

    """ Signal emitted when process finished"""
    sig_finished = QtCore.Signal(bool, list)

    def __init__(self, n, fn, args):
        super(MultiProcess, self).__init__()
        _init_pool()
        self.n = n
        self.fn = fn
        self.queue =  multiprocessing.Manager().Queue()
        self.timer = QtCore.QTimer()
        self.timer.timeout.connect(self.progress)

        split_args = [range(n), [self.queue,] * n]
        for arg in args:
            if isinstance(arg, (np.ndarray, np.generic)):
                split_args.append(np.array_split(arg, n, 0))
            else:
                split_args.append([arg,] * n)

        # Transpose list of lists so first element is all the arguments for process 0, etc
        self.split_args = map(list, zip(*split_args))

        self.failed = False
        self.output = [None, ] * n

    def run(self, sync=False):
        processes = []
        for i in range(self.n):
            processes.append(_pool.apply_async(self.fn, self.split_args[i], callback=self.cb))
        self.timer.start(1000)
        if sync:
            for i in range(self.n):
                processes[i].get()

    def progress(self):
        """
        Override to monitor progress of job via the queue
        """
        pass

    def cb(self, result):
        id, success, output = result
        #print("Finished: id=", id)
        done = False

        if self.failed:
            # If one process fails, ignore results
            pass
        elif success:
            self.output[id] = output
            done = None not in self.output
        else:
            # If one process fails, they all fail. Output is just the first exception to be caught
            # FIXME need to cancel other processes?
            self.failed = True
            self.output = output
            done = True

        if done:
            self.timer.stop()
            self.progress()
            self.sig_finished.emit(not self.failed, self.output)
