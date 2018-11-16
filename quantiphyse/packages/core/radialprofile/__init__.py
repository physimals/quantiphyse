"""
Quantiphyse - Histogram widget

Copyright (c) 2013-2018 University of Oxford
"""
from .widget import RadialProfileWidget
from .process import RadialProfileProcess
from .process_tests import RadialProfileProcessTest

QP_MANIFEST = {
    "widgets" : [RadialProfileWidget],
    "processes" : [RadialProfileProcess],
    "process-tests" : [RadialProfileProcessTest],
}
