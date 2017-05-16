import os

import numpy as np

from scipy.ndimage.filters import gaussian_filter

from pkview.volumes.io import load
from pkview.analysis import Process
from pkview.analysis.t1_model import t10_map

def _get_filepath(fname, folder):
    if os.path.isabs(fname):
        return fname
    else:
        return os.path.abspath(os.path.join(folder, fname))

class T10Process(Process):

    def __init__(self, ivm, **kwargs):
        Process.__init__(self, ivm, **kwargs)

    def run(self, options):
        fa_vols, fas = [], []
        for fname, fa in options["vfa"].items():
            vol =load(_get_filepath(fname, self.workdir))
            if isinstance(fa, list):
                for i, a in enumerate(fa):
                    fas.append(a)
                    fa_vols.append(vol[:,:,:,i])
            else:
                fas.append(fa)
                fa_vols.append(vol)

        if "afi" in options:
            # We are doing a B0 correction (preclinical)
            afi_vols, trs = [], []
            for fname, tr in options["afi"].items():
                vol = load(_get_filepath(fname, self.workdir))
                if isinstance(tr, list):
                    for i, a in enumerate(tr):
                        trs.append(a)
                        afi_vols.append(vol[:,:,:,i])
                else:
                    trs.append(tr)
                    afi_vols.append(vol)

            fa_afi = options["fa-afi"]
            T10 = t10_map(fa_vols, fas, TR=options["tr"], afi_vols=afi_vols, fa_afi=fa_afi, TR_afi=trs)
            if "smooth" in options:
                T10 = gaussian_filter(T10, sigma=options["smooth"].get("sigma", 0.5), 
                                    truncate=options["smooth"].get("truncate", 3))
        else:
            T10 = t10_map(fa_vols, fas, options["tr"])

        if "clamp" in options:
            np.clip(T10, options["clamp"]["min"], options["clamp"]["max"], out=T10)
        self.ivm.add_overlay("T10", T10)
        self.status = Process.SUCCEEDED
