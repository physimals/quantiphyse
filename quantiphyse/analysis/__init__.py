"""

Author: Benjamin Irving (benjamin.irv@gmail.com)
Copyright (c) 2013-2015 University of Oxford, Benjamin Irving

"""
import numpy as np
import multiprocessing
import multiprocessing.pool
import threading

from PySide import QtCore, QtGui

from quantiphyse.utils import debug, warn
from quantiphyse.utils.exceptions import QpException

_pool = None

# Axis to split along. Could be 0, 1 or 2, but 0 is probably optimal for Numpy arrays which are column-major
# by default
SPLIT_AXIS = 0

# Whether to use multiprocessing - can be disabled for debugging
MULTIPROC = True

def _init_pool():
    global _pool
    if _pool is None: 
        n_workers = multiprocessing.cpu_count()
        debug("Initializing multiprocessing using %i workers" % n_workers)
        _pool = multiprocessing.Pool(n_workers)

class Process(QtCore.QObject):
    """
    A simple synchronous process
    
    The purpose of this class and it subclasses is to expose processing tasks to the batch system, 
    and also allow them to be used from the GUI
    """

    """ Signal may be emitted to track progress"""
    sig_progress = QtCore.Signal(float)

    """ Signal emitted when process finished"""
    sig_finished = QtCore.Signal(int, list, str, object)

    NOTSTARTED = 0
    RUNNING = 1
    FAILED = 2
    SUCCEEDED = 3
    CANCELLED = 4

    def __init__(self, ivm, **kwargs):
        super(Process, self).__init__()
        self.ivm = ivm
        self.log = ""
        self.status = Process.NOTSTARTED
        self.name = kwargs.pop("name", None)
        self.folder = kwargs.pop("indir", "")
        self.outdir = kwargs.pop("outdir", "")

    def run(self, options):
        """ Override to run the process """
        pass

class BackgroundProcess(Process):
    """
    A serial (non parallelized) asynchronous process
    """

    def __init__(self, ivm, fn, **kwargs):
        super(BackgroundProcess, self).__init__(ivm, **kwargs)
        _init_pool()
        self.fn = fn
        self.queue =  multiprocessing.Manager().Queue()
        self.sync = kwargs.get("sync", False)
        self.multiproc = MULTIPROC and kwargs.get("multiproc", True)
        self._timer = None
        self.workers = []
        self.output = []
        # We seem to get a segfault when emitting a signal with a None object
        self.exception = object()

    def timeout(self):
        """
        Called every 1s. Override to monitor progress of job via the queue
        and emit sig_progress
        """
        pass

    def finished(self):
        """
        Called when process completes, successful or not, before sig_finished is emitted.
        Should combine output data and add to the ivm and set self.log 
        """
        pass
    
    def start(self, n, args):
        """
        Start workers. Normally called by run()

        n = number of tasks
        args = list of run arguments - will be split up amongst workers by split_args()
        """
        worker_args = self.split_args(n, args)
        self.output = [None, ] * n
        self.status = Process.RUNNING
        if self.multiproc:
            self.workers = []
            for i in range(n):
                debug("starting task %i..." % n)
                proc = _pool.apply_async(self.fn, worker_args[i], callback=self._process_cb)
                self.workers.append(proc)
            
            if self.sync:
                debug("synchronous")
                for i in range(n):
                    self.workers[i].get()
            else:
                debug("async - restarting timer")
                self._restart_timer()
        else:
            for i in range(n):
                if self.status != Process.RUNNING:
                    break
                result = self.fn(*worker_args[i])
                self.timeout()
                if QtGui.qApp is not None: QtGui.qApp.processEvents()
                self._process_cb(result)
                if self.status != Process.RUNNING: break
        debug("done start")

    def cancel(self):
        """
        Cancel all workers. The status will be CANCELLED unless it
        is already complete
        """
        if self.status == Process.RUNNING:
            self.status = Process.CANCELLED
            if self.multiproc:
                # FIXME this does not work. Not incredibly harmful because
                # with status set to CANCELLED results are ignored anyway.
                # But workers will continue to work. Maybe look into
                # abortable_worker solution?
                pass
                #for p in self.workers:
                #    p.terminate()
                #    p.join(timeout=1.0)
            else:
                # Just setting the status is enough - no more workers
                # will be started
                pass

            try:
                self.timeout()
                self.finished()
            except:
                warn("Error executing finished methods for process")
            self.sig_finished.emit(self.status, self.output, self.log, self.exception)

    def split_args(self, n, args):
        """
        Split function arguments up across workers. 

        Numpy arrays are split along SPLIT_AXIS, other types of argument
        are simply copied
        
        Note that this can be overridden to customize splitting behaviour
        """
        # First argument is worker ID, second is queue
        split_args = [range(n), [self.queue,] * n]

        for arg in args:
            if isinstance(arg, (np.ndarray, np.generic)):
                split_args.append(np.array_split(arg, n, SPLIT_AXIS))
            else:
                split_args.append([arg,] * n)

        # Transpose list of lists so first element is all the arguments for process 0, etc
        return map(list, zip(*split_args))

    def recombine_data(self, data):
        shape = None
        for d in data:
            if d is not None:
                shape = d.shape
        if shape is None:
            raise RuntimeError("No data to re-combine")
        else:
            debug("Recombining data with shape", shape)
        empty = np.zeros(shape)
        real_data = []
        for d in data:
            if d is None:
                real_data.append(empty)
            else:
                real_data.append(d)
        
        return np.concatenate(real_data, SPLIT_AXIS)

    def _restart_timer(self):
        self._timer = threading.Timer(1, self._timer_cb)
        self._timer.daemon = True
        self._timer.start()

    def _timer_cb(self):
        debug("timer CB")
        if self.status == Process.RUNNING:
            self.timeout()
            self._restart_timer()

    def _process_cb(self, result):
        worker_id, success, output = result
        debug("Finished: id=", worker_id, success, str(output))
        
        if self.status in (Process.FAILED, Process.CANCELLED):
            # If one process has already failed or been cancelled, ignore results of others
            debug("Ignoring, already failed")
            return
        elif success:
            self.output[worker_id] = output
            if None not in self.output:
                self.status = Process.SUCCEEDED
        else:
            # If one process fails, they all fail. Output is just the first exception to be caught
            # FIXME cancel other workers?
            self.status = Process.FAILED
            self.exception = output

        if self.status != Process.RUNNING:
            try:
                self.timeout()
                self.finished()
            except:
                warn("Error executing finished methods for process")
            self.sig_finished.emit(self.status, self.output, self.log, self.exception)
