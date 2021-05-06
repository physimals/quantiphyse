"""
Quantiphyse - Utility functions for handling colormaps

Copyright (c) 2013-2020 University of Oxford

Licensed under the Apache License, Version 2.0 (the "License");
you may not use this file except in compliance with the License.
You may obtain a copy of the License at

    http://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and
limitations under the License.
"""
import logging

import numpy as np

from matplotlib import cm

import pyqtgraph as pg

LOG = logging.getLogger(__name__)

# Standard colour maps. Note that ROI uses jet because it gives more contrast between different indices
CMAPS = ["viridis", "magma", "inferno", "plasma", "cividis", "seismic", "jet", "hot", "gist_heat", "flame", "bipolar", "spectrum", "custom"]
DEFAULT_CMAP = "hot"
DEFAULT_CMAP_ROI = "plasma"

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
        cmap_name = DEFAULT_CMAP

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

def get_col(lut, idx, range):
    """
    Get RGB color for an index within a range, using a lookup table
    """
    lower, upper = range[0], range[1]
    if lower == upper:
        pos = 0
    else:
        pos = (idx - range[0]) / (range[1] - range[0])
    return lut[int(pos*(len(lut)-1))]

def get_roi_col(roi, region_idx):
    """
    Get RGB color for an ROI region
    """
    lut = get_lut(roi.view.cmap)
    return get_col(lut, region_idx, roi.view.cmap_range)

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
