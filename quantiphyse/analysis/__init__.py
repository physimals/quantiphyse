"""

Author: Benjamin Irving (benjamin.irv@gmail.com)
Copyright (c) 2013-2015 University of Oxford, Benjamin Irving

"""
import numpy as np
import multiprocessing
import multiprocessing.pool
import threading

from PySide import QtCore

_pool = None

# Axis to split along. Could be 0, 1 or 2, but 0 is probably optimal for Numpy arrays which are column-major
# by default
SPLIT_AXIS = 0

def _init_pool():
    global _pool
    if _pool is None: 
        n_workers = multiprocessing.cpu_count()
        #print("Initializing multiprocessing using %i workers" % n_workers)
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
    sig_finished = QtCore.Signal(int, list, str)

    NOTSTARTED = 0
    RUNNING = 1
    FAILED = 2
    SUCCEEDED = 3

    def __init__(self, ivm, **kwargs):
        super(Process, self).__init__()
        self.ivm = ivm
        self.log = ""
        self.status = Process.NOTSTARTED
        self.debug = kwargs.get("debug", False)
        self.folder = kwargs.get("indir", "")
        self.outdir = kwargs.get("outdir", "")

    def run(self, options):
        """ Override to run the process """
        pass

class BackgroundProcess(Process):
    """
    A serial (non parallelized) asynchronous process
    """

    def __init__(self, ivm, fn, sync=False, **kwargs):
        super(BackgroundProcess, self).__init__(ivm)
        _init_pool()
        self.fn = fn
        self.queue =  multiprocessing.Manager().Queue()
        self.sync = sync
        self._timer = None

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
        Start worker processes. Should be called by run()

        n = number of workers
        args = list of run arguments - will be split up amongst workers by split_args()
        """
        worker_args = self.split_args(n, args)
        self.output = [None, ] * n
        self.status = Process.RUNNING
        processes = []
        for i in range(n):
            print("start: ", np.max(worker_args[i][4]), np.max(worker_args[i][5]), np.max(worker_args[i][6]))
            proc = _pool.apply_async(self.fn, worker_args[i], callback=self._process_cb)
            processes.append(proc)
        
        if self.sync:
            for i in range(n):
                processes[i].get()
        else:
            self._restart_timer()
    
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
                split_args.append(np.array_split(arg, n, 0))
                print("Splitting numpy array shape ", arg.shape, np.max(arg))
            else:
                split_args.append([arg,] * n)

        # Transpose list of lists so first element is all the arguments for process 0, etc
        return map(list, zip(*split_args))

    def _restart_timer(self):
        self._timer = threading.Timer(1, self._timer_cb)
        self._timer.daemon = True
        self._timer.start()

    def _timer_cb(self):
        if self.status == Process.RUNNING:
            self.timeout()
            self._restart_timer()

    def _process_cb(self, result):
        worker_id, success, output = result
        #print("Finished: id=", worker_id, success, str(output))
        
        if self.status == Process.FAILED:
            # If one process has already failed, ignore results of others
            return
        elif success:
            self.output[worker_id] = output
            if None not in self.output:
                self.status = Process.SUCCEEDED
        else:
            # If one process fails, they all fail. Output is just the first exception to be caught
            # FIXME cancel other processes?
            self.status = Process.FAILED
            self.output = output

        if self.status != Process.RUNNING:
            self.timeout()
            self.finished()
            self.sig_finished.emit(self.status, self.output, self.log)
