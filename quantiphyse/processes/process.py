"""
Quantiphyse - Generic analysis processes

Copyright (c) 2013-2018 University of Oxford
"""

import multiprocessing
import multiprocessing.pool
import threading
import traceback

import numpy as np
from PySide import QtCore, QtGui

from quantiphyse.data import NumpyData
from quantiphyse.utils import debug, warn, QpException

""" 
Multiprocessing pool 
"""
_POOL = None

""" 
Axis to split along. Could be 0, 1 or 2, but 0 is probably optimal for Numpy arrays which are 
column-major by default
"""
SPLIT_AXIS = 0

"""
Whether to use multiprocessing - can be disabled for debugging
"""
MULTIPROC = True

def _init_pool():
    global _POOL
    if _POOL is None: 
        n_workers = multiprocessing.cpu_count()
        debug("Initializing multiprocessing using %i workers" % n_workers)
        _POOL = multiprocessing.Pool(n_workers)

class Process(QtCore.QObject):
    """
    A data processing task
    
    The purpose of this class and it subclasses is to expose processing tasks to the batch system, 
    and also allow them to be used from the GUI

    Processes take options in the form of a key/value dictionary derived from the YAML batch file.
    Certain option names are standardized:

      name - Optional name given to the process. Will be used to name the log file output. 
             This is set in the constructor by the batch code but is taken from the process
             options list if present. If not given as an option, the process generic name
             (e.g. MoCo) is used.
      data - The name of the main input data set
      roi - The name of the main input ROI if applicable
      output-name - The name of the output data set or ROI 

    Simple 'fast' processes such as loading/saving data and very simple image processing tasks
    should be implemented by subclassing Process and overriding ``run``. Processes which may
    take time should subclass BackgroundProcess or ParallelProcess.

    Attributes:

      indir - Input data folder if process needs to load data
      outdir - Output data folder if process needs to save data
    """

    NOTSTARTED = 0
    RUNNING = 1
    FAILED = 2
    SUCCEEDED = 3
    CANCELLED = 4

    def __init__(self, ivm, **kwargs):
        """
        :param ivm: ImageVolumeManagement object
        
        Keyword arguments:

        :param proc_id: ID string for this process
        :param indir: Input data folder
        :param outdir: Output data folder
        """
        super(Process, self).__init__()
        self.ivm = ivm
        self.proc_id = kwargs.pop("proc_id", None)
        self.indir = kwargs.pop("indir", "")
        self.outdir = kwargs.pop("outdir", "")

        self.log = ""
        self.status = Process.NOTSTARTED

    def get_data(self, options, multi=False):
        """ 
        Standard method to get the data object the process is to operate on 
        
        If no 'data' option is specified, go with main data if it exists
        If 'multi' then allow data to be a list of items

        :param options: Dictionary of options - ``data`` will be consumed if present
        :return: QpData instance
        """
        data_name = options.pop("data", None)
        if data_name is None:
            if self.ivm.main is None:
                raise QpException("No data loaded")
            data = self.ivm.main
        elif multi and isinstance(data_name, list):
            # Allow specifying a list of data volumes which are concatenated
            if not data_name:
                raise QpException("Empty list given for data")
            for name in data_name:
                if name not in self.ivm.data:
                    raise QpException("Data not found: %s" % name)

            multi_data = [self.ivm.data[name] for name in data_name]
            nvols = sum([d.nvols for d in multi_data])
            debug("Multivol: nvols=", nvols)
            grid = None
            v = 0
            for d in multi_data:
                if grid is None:
                    grid = d.grid
                d = d.resample(grid)
                if d.nvols == 1:
                    rawdata = np.expand_dims(d.raw(), 3)
                else:
                    rawdata = d.raw()
                data[..., v:v+d.nvols] = rawdata
                v += d.nvols
            data = NumpyData(data, grid=grid, name="multi_data")
        else:
            if data_name in self.ivm.data:
                data = self.ivm.data[data_name]
            else:
                raise QpException("Data not found: %s" % data_name)
        return data

    def get_roi(self, options, grid=None):
        """
        Standard method to get the ROI the process is to operate on

        If no 'roi' option is specified, go with currently selected ROI, 
        if it exists.

        :param options: Dictionary of options - ``roi`` will be consumed if present
        :param grid:    If specified, return ROI on this grid
        :return:        QpData instance. If no ROI can be found and ``grid`` is specified, will
                        return an ROI where all voxels are unmasked.
        """
        roi_name = options.pop("roi", None)
        if roi_name is None or roi_name.strip() == "":
            if self.ivm.current_roi is not None:
                roidata = self.ivm.current_roi
            elif grid is not None:
                roidata = NumpyData(np.ones(grid.shape[:3]), grid=grid, name="dummy_roi", roi=True)
            else:
                raise QpException("No default ROI could be constructed")
        else:
            if roi_name in self.ivm.rois:
                roidata = self.ivm.rois[roi_name]
            else:
                raise QpException("ROI not found: %s" % roi_name)

        if grid is not None:
            roidata = roidata.resample(grid)
        return roidata

    def run(self, options):
        """ 
        Override to run the process 

        :param options: Dictionary of string : value for process options
        """
        pass

    def output_data_items(self):
        """
        Optional method allowing a Process to indicate what data items it produced after completion

        :return: a sequence of data item names that were output
        """
        return []

class BackgroundProcess(Process):
    """
    An asynchronous background process
    """

    """ 
    Signal which may be emitted to track progress 

    Argument should be between 0 and 1 and indicate degree of completion
    """
    sig_progress = QtCore.Signal(float)

    """ 
    Signal which will be emitted when process finishes
    
    Arguments: (status, log, if status not SUCCEEDED or CANCELLED, exception, otherwise object())
    """
    sig_finished = QtCore.Signal(int, str, object)

    """ 
    Signal which may be emitted when the process starts a new step
    
    Arguments is text description
    """
    sig_step = QtCore.Signal(str)

    def __init__(self, ivm, worker_fn, **kwargs):
        """
        :param ivm: ImageVolumeManagement object
        :param worker_fn: Function which will be called to do the processing. This should
                          take a sequence of arguments which are all pickleable objects. The
                          first two arguments are the worker ID and the Queue object for
                          passing results back. Remaining arguments are defined by the 
                          implementation and should be passed to ``start``
        """
        super(BackgroundProcess, self).__init__(ivm, **kwargs)
        _init_pool()
        self._worker_fn = worker_fn
        self._sync = kwargs.get("sync", False)
        self._multiproc = MULTIPROC and kwargs.get("multiproc", True)
        self._timer = None

        self.queue = multiprocessing.Manager().Queue()
        self.workers = []
        self.output = []
        # We seem to get a segfault when emitting a signal with a None object
        self.exception = object()

    def start(self, args):
        """
        Start background worker
        
        This would normally called by ``run()`` after setting up the arguments to pass to the 
        worker run function.

        :param args: Sequence of arguments to the worker run function. All must be pickleable objects
        """
        worker_args = [0, self.queue, ] + [a for a in args]
        self.output = [None, ]
        self.status = Process.RUNNING
        if self._multiproc:
            self.workers = [_POOL.apply_async(self._worker_fn, worker_args, callback=self._worker_finished_cb)]
            if self._sync:
                self.workers[0].get()
            else:
                self._restart_timer()
        else:
            result = self._worker_fn(*worker_args)
            self.timeout()
            if QtGui.qApp is not None: 
                QtGui.qApp.processEvents()
            self._worker_finished_cb(result)

    def cancel(self):
        """
        Cancel all workers. The status will be CANCELLED unless it is already complete
        """
        if self.status == Process.RUNNING:
            self.status = Process.CANCELLED
            if self._multiproc:
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
            except Exception as e:
                traceback.print_exc(e)
                warn("Error executing finished methods for process")

            self.sig_finished.emit(self.status, self.log, self.exception)

    def timeout(self):
        """
        Called every 1s while the process is running. 
        
        Override to monitor progress of job via the queue and emit 
        sig_progress / sig_step as required
        """
        pass

    def finished(self):
        """
        Called when process completes, successful or not, before sig_finished is emitted.

        Should combine output data and add to the ivm and set self.log 
        """
        pass
    
    def _restart_timer(self):
        self._timer = threading.Timer(1, self._timer_cb)
        self._timer.daemon = True
        self._timer.start()

    def _timer_cb(self):
        if self.status == Process.RUNNING:
            self.timeout()
            self._restart_timer()

    def _worker_finished_cb(self, result):
        worker_id, success, output = result
        debug("Finished: id=", worker_id, success, output)
        
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
            except Exception as e:
                traceback.print_exc(e)
                warn("Error executing finished methods for process")
            self.sig_finished.emit(self.status, self.log, self.exception)

class ParallelProcess(BackgroundProcess):
    """
    An background process which runs multiple workers in parallel
    """

    def start_parallel(self, args, n_workers):
        """
        Split input arguments into chunks and run in parallel. 
        
        This would normally called by run() after setting up the arguments to pass to the 
        worker run function.

        :param n_workers: Number of parallel worker processes to use
        :param args: Sequence of arguments to the worker run function. All must be pickleable objects.
                     By default Numpy arrays will be split along SPLIT_AXIS and a chunk passed to each
                     worker.
        """
        worker_args = self.split_args(n_workers, args)
        self.output = [None, ] * n_workers
        self.status = Process.RUNNING
        if self._multiproc:
            self.workers = []
            for i in range(n_workers):
                debug("starting task %i..." % n_workers)
                proc = _POOL.apply_async(self._worker_fn, worker_args[i], callback=self._worker_finished_cb)
                self.workers.append(proc)
            
            if self._sync:
                debug("synchronous")
                for i in range(n_workers):
                    self.workers[i].get()
            else:
                debug("async - restarting timer")
                self._restart_timer()
        else:
            for i in range(n_workers):
                if self.status != Process.RUNNING:
                    break
                result = self._worker_fn(*worker_args[i])
                self.timeout()
                if QtGui.qApp is not None: QtGui.qApp.processEvents()
                self._worker_finished_cb(result)
                if self.status != Process.RUNNING: break
        debug("done start")

    def split_args(self, n_workers, args):
        """
        Split function arguments up across workers. 

        Numpy arrays are split along SPLIT_AXIS, other types of argument
        are simply copied
        
        Note that this can be overridden to customize splitting behaviour
        """
        # First argument is worker ID, second is queue
        split_args = [range(n_workers), [self.queue,] * n_workers]

        for arg in args:
            if isinstance(arg, (np.ndarray, np.generic)):
                split_args.append(np.array_split(arg, n_workers, SPLIT_AXIS))
            else:
                split_args.append([arg,] * n_workers)

        # Transpose list of lists so first element is all the arguments for process 0, etc
        return map(list, zip(*split_args))

    def recombine_data(self, data):
        """
        Recombine a sequence of data items into a single data item

        This implementation assumes data contains Numpy arrays and returns
        a new Numpy array concatenated along SPLIT_AXIS. However this method
        could be overridden, especially if split_data has been overridden.
        """
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

def _run_macro(worker_id, queue, script):
    pass
