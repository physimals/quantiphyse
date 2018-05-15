"""
Quantiphyse - Example process definition

Copyright (c) 2013-2018 University of Oxford
"""
import sys
import os
import warnings
import traceback

import numpy as np

from quantiphyse.analysis import Process

class ExamplePluginProcess(Process):

    PROCESS_NAME = "ExamplePluginProcess"

    def __init__(self, ivm, **kwargs):
        ExamplePluginProcess.__init__(self, ivm, **kwargs)

    def run(self, options):
        pass
