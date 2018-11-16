"""
Quantiphyse - Histogram widget

Copyright (c) 2013-2018 University of Oxford
"""
from .widget import HistogramWidget
from .process import HistogramProcess
from .process_tests import HistogramProcessTest

QP_MANIFEST = {
    "widgets" : [HistogramWidget],
    "processes" : [HistogramProcess],
    "process-tests" : [HistogramProcessTest],
}
