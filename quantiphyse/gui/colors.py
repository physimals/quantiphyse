"""
Quantiphyse - Utility functions for handling colormaps

Copyright (c) 2013-2018 University of Oxford
"""
import logging

import numpy as np

from matplotlib import cm

import pyqtgraph as pg

LOG = logging.getLogger(__name__)

def initial_cmap_range(qpdata, percentile=100):
    """
    Get an initial colourmap range for a data item.

    This is taken by ignoring NaN and infinity and returning
    a percentile of the data range. By default returns
    the full min to max range.

    :return: Sequence of (min, max)
    """
    cmin, cmax = qpdata.range(vol=int(qpdata.nvols/2), percentile=percentile)
    # Issue #101: if min is exactly zero, make it slightly more
    # as a heuristic for data sets where zero=background
    if cmin == 0:
        cmin = 1e-7*cmax

    return cmin, cmax

def get_lut(cmap_name, alpha=255):
    """
    Get the colour lookup table by name.

    Handles Matplotlib as well as pyqtgraph built in colormaps.
    Pyqtgraph is a bit rubbish here - to load a predefined color
    map and extract the lookup table we need to create a
    GradientEditorItem even though we're not doing anything involving
    the GUI.
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
