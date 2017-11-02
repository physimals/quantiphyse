"""
VEASL Quantiphyse plugin

VEASL = Vessel Encoded ASL

Author: Martin Craig <martin.craig@eng.ox.ac.uk>
Copyright (c) 2016-2017 University of Oxford, Martin Craig
"""

from .widget import VeaslWidget
from .process import VeaslProcess

QP_WIDGETS = [VeaslWidget]
QP_PROCESSES = [VeaslProcess]
