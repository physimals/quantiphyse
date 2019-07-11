"""
Quantiphyse - Module for normalising data, e.g. prior to feature extraction

Copyright (c) 2013-2018 University of Oxford
"""

from __future__ import division, print_function

import numpy as np

def norm_percentile(data, percentile=90):
    """
    Normalise the data by dividing by a given percentile

    :param data: Numpy array whose last dimension is assumed to be
                 the volume sequence
    """
    norm = np.percentile(data, percentile)
    return data / norm

def norm_median(data, volume_idx=None):
    """
    Normalise the data by dividing by the median of a given volume

    :param data: Numpy array whose last dimension is assumed to be
                 the volume sequence
    """
    if volume_idx is None:
        volume_idx = data.shape[-1] / 2
    return data / np.median(data[:, volume_idx])

def norm_indiv(data):
    """
    Scale each volume individually so it lies between 0 and 1

    :param data: Numpy array whose last dimension is assumed to be
                 the volume sequence
    """
    data = data - np.min(data, axis=0)
    return data / (np.max(data, axis=0) + 0.001)

def norm_sigenh(data, nvols=3):
    """
    Scale each data point by dividing by a 'baseline' value and then subtracting 1

    This results in 'signal enhancement' curves, starting at 0

    :param data: Numpy array whose last dimension is assumed to be
                 the volume sequence
    """
    data_nvols = data.shape[-1]
    tile_shape = [1, ] * data.ndim
    tile_shape[-1] = nvols

    baseline = np.mean(data[..., :min(nvols, data_nvols)], axis=-1)
    baseline_expanded = np.expand_dims(baseline, axis=-1)
    return data / (baseline_expanded + 0.001) - 1

def normalise(data, method, **kwargs):
    """
    Normalise data using named method

    :param data: Numpy array containing data to be normalised
    :param method: One of ``perc``, ``median``, ``indiv``, or ``sigenh``
    :return: Normalised data as matching Numpy array
    """
    norm_methods = {
        "perc" : norm_percentile,
        "median" : norm_median,
        "indiv" : norm_indiv,
        "sigenh" : norm_sigenh,
    }
    if method in norm_methods:
        return norm_methods[method](data, **kwargs)
    else:
        raise ValueError("Unknown normalisation method: %s" % method)
