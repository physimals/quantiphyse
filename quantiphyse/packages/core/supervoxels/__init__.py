"""
Quantiphyse - supervoxel clustering package

Copyright (c) 2013-2018 University of Oxford
"""

from .widgets import MeanValuesWidget, PerfSlicWidget
from .process import SupervoxelsProcess, MeanValuesProcess
from .tests import PerfSlicWidgetTest

QP_MANIFEST = {
    "widgets" : [MeanValuesWidget, PerfSlicWidget],
    "widget-tests" : [PerfSlicWidgetTest,],
    "processes" : [SupervoxelsProcess, MeanValuesProcess],
}
