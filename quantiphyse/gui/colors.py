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
    if not cmap_name:
        cmap_name = "jet"
        
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

def get_col(lut, idx, out_of):
    """
    Get RGB color for an index within a range, using a Matplotlib colour map
    """
    if out_of == 0 or len(lut) == 0: 
        return [255, 0, 0]
    else:
        pos = int((len(lut) - 1) * float(idx) / out_of)
        return lut[pos][:3]

# Kelly (1965) - set of 20 contrasting colours
# We alter the order a bit to prioritize those that give good contrast to our dark background
# plus we add an 'off white' at the start
KELLY_COLORS = [
    ("off_white", (230, 230, 230)),
    ("vivid_yellow", (255, 179, 0)),
    ("vivid_orange", (255, 104, 0)),
    ("very_light_blue", (166, 189, 215)),
    ("vivid_red", (193, 0, 32)),
    ("grayish_yellow", (206, 162, 98)),
    ("medium_gray", (129, 112, 102)),
    ("strong_purple", (128, 62, 117)),

    # these aren't good for people with defective color vision:
    ("vivid_green", (0, 125, 52)),
    ("strong_purplish_pink", (246, 118, 142)),
    ("strong_blue", (0, 83, 138)),
    ("strong_yellowish_pink", (255, 122, 92)),
    ("strong_violet", (83, 55, 122)),
    ("vivid_orange_yellow", (255, 142, 0)),
    ("strong_purplish_red", (179, 40, 81)),
    ("vivid_greenish_yellow", (244, 200, 0)),
    ("strong_reddish_brown", (127, 24, 13)),
    ("vivid_yellowish_green", (147, 170, 0)),
    ("deep_yellowish_brown", (89, 51, 21)),
    ("vivid_reddish_orange", (241, 58, 19)),
    ("dark_olive_green", (35, 44, 22)),
]

def get_kelly_col(idx, wrap=True):
    """
    Get the Kelly colour for a given index

    :param idx: Index
    :param wrap: If True, wrap index to number of Kelly colours
    :return: (RGB) tuple in range 0-255
    """
    baseidx = idx % len(KELLY_COLORS)
    basecol = KELLY_COLORS[baseidx][1]
    if not wrap:
        raise RuntimeError("Not implemented yet")
    return basecol
