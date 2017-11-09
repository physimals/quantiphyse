import numpy as np

from . import Process, BackgroundProcess
from ..volumes.io import load

class ResampleProcess(Process):
    """
    Advanced resampling of data from file FIXME unfinished
    """
    def __init__(self, ivm, **kwargs):
        Process.__init__(self, ivm, **kwargs)

    def run(self, options):
        fname = options.pop('file-name', None)
        output_name = options.pop('output-name', None)
        use_origin = options.pop('use-origin', True)
        use_orientation = options.pop('use-orientation', True)
        use_scaling = options.pop('use-scaling', True)

        data = load(os.path.join(self.folder, fname))
        if not use_origin:
            affine = data.rawgrid.affine
            
        self.ivm.add_data(ov_data, name=output_name, make_current=True)
        self.status = Process.SUCCEEDED
