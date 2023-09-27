"""
Quantiphyse - PCA reduction process

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
from quantiphyse.data.extras import NumberListExtra
from quantiphyse.utils import QpException
from quantiphyse.processes import Process

import numpy as np

class AifProcess(Process):
    """
    Calculate AIF from an ROI 
    """

    PROCESS_NAME = "Aif"

    def __init__(self, ivm, **kwargs):
        Process.__init__(self, ivm, **kwargs)

    def run(self, options):
        qpdata = self.get_data(options, multi=False)
        roi = self.get_roi(options, use_current=False)
        name = options.pop('output-name', 'aif')
        
        aif_samples = qpdata.raw()[roi.raw() > 0]
        if len(aif_samples) == 0:
            raise QpException("ROI is empty - cannot define AIF")

        aif = np.zeros([qpdata.nvols], dtype=np.float32)
        for sig in aif_samples:
            aif += sig
        aif = aif / len(aif_samples)

        extra = NumberListExtra(name, aif)
        self.ivm.add_extra(name, extra)
