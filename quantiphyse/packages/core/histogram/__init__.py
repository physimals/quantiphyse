"""
Quantiphyse - Histogram widget

Copyright (c) 2013-2018 University of Oxford
"""
from .widget import HistogramWidget
from .process import HistogramProcess

QP_MANIFEST = {
    "widgets" : [HistogramWidget],
    "processes" : [HistogramProcess],
}
