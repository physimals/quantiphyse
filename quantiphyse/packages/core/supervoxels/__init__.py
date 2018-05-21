"""
Quantiphyse - supervoxel clustering package

Copyright (c) 2013-2018 University of Oxford
"""

from .widgets import MeanValuesWidget, PerfSlicWidget
from .process import SupervoxelsProcess, MeanValuesProcess
from .tests import PerfSlicWidgetTest, MeanValuesProcessTest, SupervoxelsProcessTest

QP_MANIFEST = {
    "widgets" : [MeanValuesWidget, PerfSlicWidget],
    "widget-tests" : [PerfSlicWidgetTest,],
    "process-tests" : [MeanValuesProcessTest, SupervoxelsProcessTest,],
    "processes" : [SupervoxelsProcess, MeanValuesProcess],
}
