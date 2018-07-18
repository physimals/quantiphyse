"""
Quantiphyse - Package for data simulation

Copyright (c) 2013-2018 University of Oxford
"""
from .widgets import AddNoiseWidget, SimMotionWidget
from .processes import AddNoiseProcess, SimMotionProcess

QP_MANIFEST = {
    "widgets" : [AddNoiseWidget, SimMotionWidget],
    "processes" : [AddNoiseProcess, SimMotionProcess],
}
