"""
Quantiphyse - Package for data registration and motion correction

Copyright (c) 2013-2018 University of Oxford
"""
from .widget import RegWidget
from .process import RegProcess
from .reg_method import RegMethod

QP_MANIFEST = {
    "widgets" : [RegWidget,],
    "processes" : [RegProcess,],
    "base-classes" : [RegMethod,],
}
