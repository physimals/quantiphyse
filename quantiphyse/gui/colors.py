"""
Quantiphyse - Utility functions for handling colormaps

Copyright (c) 2013-2018 University of Oxford
"""
import logging

import numpy as np

from matplotlib import cm

import pyqtgraph as pg

LOG = logging.getLogger(__name__)

def get_lut(cmap_name, alpha=255):
    """
    Get the colour lookup table by name.

    Handles Matplotlib as well as pyqtgraph built in colormaps
    """
    gradient = pg.GradientEditorItem()
    try:
        gradient.loadPreset(cmap_name)
        LOG.debug("Loaded standard LUT: %s", cmap_name)
    except KeyError:
        gradient.restoreState(get_lut_from_matplotlib(cmap_name))
        LOG.debug("Loaded Matplotlib LUT: %s", cmap_name)

    lut = gradient.getLookupTable(nPts=512, alpha=True)
    LOG.debug("LUT: %s", lut)
    for entry in lut:
        entry[3] = alpha
    return lut

def get_lut_from_matplotlib(cmap_name):
    """
    Slightly hacky method to copy MatPlotLib gradients to pyqtgraph.

    Is not perfect because Matplotlib specifies gradients in a different way to pyqtgraph
    (specifically there is a separate list of ticks for R, G and B). So we just sample
    the colormap at 10 points which is OK for most slowly varying gradients.
    """
    cmap = getattr(cm, cmap_name)
    ticks = [(pos, [255 * v for v in cmap(pos)]) for pos in np.linspace(0, 1, 10)]
    return {'ticks': ticks, 'mode': 'rgb'}
