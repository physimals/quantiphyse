"""
Quantiphyse - Analysis processes for generating T1 map from VFA images

Copyright (c) 2013-2018 University of Oxford
"""

import os

import numpy as np

from scipy.ndimage.filters import gaussian_filter

from quantiphyse.data import load
from quantiphyse.processes import Process

from .t1_model import t10_map

def _get_filepath(fname, folder):
    if os.path.isabs(fname):
        return fname
    else:
        return os.path.abspath(os.path.join(folder, fname))

class T10Process(Process):
    """
    Process which calculates T1 map from VFA images
    """

    PROCESS_NAME = "T10"
    
    def __init__(self, ivm, **kwargs):
        Process.__init__(self, ivm, **kwargs)

    def run(self, options):
        # TR specified in ms but pass in s
        tr = float(options.pop("tr"))/1000
        fa_vols, fas = [], []
        grid = None
        for fname, fa in options.pop("vfa").items():
            self.debug("FA=%f: %s", fa, fname)
            if fname in self.ivm.data:
                data = self.ivm.data[fname]
            else:
                data = load(_get_filepath(fname, self.indir))
            
            if grid is None: 
                grid = data.grid
            else:
                data = data.resample(grid)
            
            arr = data.raw()
            if isinstance(fa, list):
                if len(fa) > 1:
                    for i, a in enumerate(fa):
                        fas.append(a)
                        fa_vols.append(arr[:, :, :, i])
                else:
                    fas.append(fa[0])
                    fa_vols.append(arr)
            else:
                fas.append(fa)
                fa_vols.append(arr)

        if "afi" in options:
            # We are doing a B0 correction (preclinical)
            afi_vols, trs = [], []
            for fname, t in options.pop("afi").items():
                if fname in self.ivm.data:
                    data = self.ivm.data[fname]
                else:
                    data = load(_get_filepath(fname, self.indir))
                    
                if grid is None: 
                    grid = data.grid
                else:
                    data = data.resample(grid)
            
                arr = data.raw()
                if isinstance(t, list):
                    for i, a in enumerate(t):
                        trs.append(float(a)/1000)
                        afi_vols.append(arr[:, :, :, i])
                else:
                    trs.append(t)
                    afi_vols.append(arr)

            fa_afi = options.pop("fa-afi")
            T10 = t10_map(fa_vols, fas, TR=tr, afi_vols=afi_vols, fa_afi=fa_afi, TR_afi=trs)
            smooth = options.pop("smooth", None)
            if smooth is not None:
                T10 = gaussian_filter(T10, sigma=smooth.get("sigma", 0.5), 
                                      truncate=smooth.get("truncate", 3))
        else:
            T10 = t10_map(fa_vols, fas, tr)

        clamp = options.pop("clamp", None)
        if clamp is not None:
            np.clip(T10, clamp["min"], clamp["max"], out=T10)
        self.ivm.add(T10, grid=grid, name="T10", make_current=True)
