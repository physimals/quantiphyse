# -*- coding: utf-8 -*-
"""
functions.py -  Miscellaneous functions with no other home
Copyright 2010  Luke Campagnola
Distributed under MIT/X11 license. See license.txt for more infomation.
"""

from __future__ import division
import numpy as np

# THIS CODE IS COPIED DIRECTLY FROM PYQTGRAPH 0.11.1. THE RELATIVE
# IMPORTS BELOW HAVE BEEN CHANGED TO POINT TO THE INSTALLED PYQTGRAPH AND
# A MINOR FIX HAS BEEN APPLIED TO affineSlice / interpolateArray TO USE THE
# cval ARGUMENT. THE PYTHON2-3 COMPATIBILITY FUNCTIONS BELOW HAVE ALSO BEEN 
# REMOVED AS THEY DO NOT EXIST IN PYQTGRAPH 0.12
from pyqtgraph import debug

def affineSliceCoords(shape, origin, vectors, axes):
    """Return the array of coordinates used to sample data arrays in affineSlice().
    """
    # sanity check
    if len(shape) != len(vectors):
        raise Exception("shape and vectors must have same length.")
    if len(origin) != len(axes):
        raise Exception("origin and axes must have same length.")
    for v in vectors:
        if len(v) != len(axes):
            raise Exception("each vector must be same length as axes.")
        
    shape = list(map(np.ceil, shape))

    ## make sure vectors are arrays
    if not isinstance(vectors, np.ndarray):
        vectors = np.array(vectors)
    if not isinstance(origin, np.ndarray):
        origin = np.array(origin)
    origin.shape = (len(axes),) + (1,)*len(shape)

    ## Build array of sample locations. 
    grid = np.mgrid[tuple([slice(0,x) for x in shape])]  ## mesh grid of indexes
    x = (grid[np.newaxis,...] * vectors.transpose()[(Ellipsis,) + (np.newaxis,)*len(shape)]).sum(axis=1)  ## magic
    x += origin

    return x

    
def affineSlice(data, shape, origin, vectors, axes, order=1, returnCoords=False, **kargs):
    """
    Take a slice of any orientation through an array. This is useful for extracting sections of multi-dimensional arrays
    such as MRI images for viewing as 1D or 2D data.
    
    The slicing axes are aribtrary; they do not need to be orthogonal to the original data or even to each other. It is
    possible to use this function to extract arbitrary linear, rectangular, or parallelepiped shapes from within larger
    datasets. The original data is interpolated onto a new array of coordinates using either interpolateArray if order<2
    or scipy.ndimage.map_coordinates otherwise.
    
    For a graphical interface to this function, see :func:`ROI.getArrayRegion <pyqtgraph.ROI.getArrayRegion>`
    
    ==============  ====================================================================================================
    **Arguments:**
    *data*          (ndarray) the original dataset
    *shape*         the shape of the slice to take (Note the return value may have more dimensions than len(shape))
    *origin*        the location in the original dataset that will become the origin of the sliced data.
    *vectors*       list of unit vectors which point in the direction of the slice axes. Each vector must have the same 
                    length as *axes*. If the vectors are not unit length, the result will be scaled relative to the 
                    original data. If the vectors are not orthogonal, the result will be sheared relative to the 
                    original data.
    *axes*          The axes in the original dataset which correspond to the slice *vectors*
    *order*         The order of spline interpolation. Default is 1 (linear). See scipy.ndimage.map_coordinates
                    for more information.
    *returnCoords*  If True, return a tuple (result, coords) where coords is the array of coordinates used to select
                    values from the original dataset.
    *All extra keyword arguments are passed to scipy.ndimage.map_coordinates.*
    --------------------------------------------------------------------------------------------------------------------
    ==============  ====================================================================================================
    
    Note the following must be true: 
        
        | len(shape) == len(vectors) 
        | len(origin) == len(axes) == len(vectors[i])
        
    Example: start with a 4D fMRI data set, take a diagonal-planar slice out of the last 3 axes
        
        * data = array with dims (time, x, y, z) = (100, 40, 40, 40)
        * The plane to pull out is perpendicular to the vector (x,y,z) = (1,1,1) 
        * The origin of the slice will be at (x,y,z) = (40, 0, 0)
        * We will slice a 20x20 plane from each timepoint, giving a final shape (100, 20, 20)
        
    The call for this example would look like::
        
        affineSlice(data, shape=(20,20), origin=(40,0,0), vectors=((-1, 1, 0), (-1, 0, 1)), axes=(1,2,3))
    
    """
    x = affineSliceCoords(shape, origin, vectors, axes)

    ## transpose data so slice axes come first
    trAx = list(range(data.ndim))
    for ax in axes:
        trAx.remove(ax)
    tr1 = tuple(axes) + tuple(trAx)
    data = data.transpose(tr1)
    #print "tr1:", tr1
    ## dims are now [(slice axes), (other axes)]

    if order > 1:
        try:
            import scipy.ndimage
        except ImportError:
            raise ImportError("Interpolating with order > 1 requires the scipy.ndimage module, but it could not be imported.")

        # iterate manually over unused axes since map_coordinates won't do it for us
        extraShape = data.shape[len(axes):]
        output = np.empty(tuple(shape) + extraShape, dtype=data.dtype)
        for inds in np.ndindex(*extraShape):
            ind = (Ellipsis,) + inds
            output[ind] = scipy.ndimage.map_coordinates(data[ind], x, order=order, **kargs)
    else:
        # map_coordinates expects the indexes as the first axis, whereas
        # interpolateArray expects indexes at the last axis. 
        tr = tuple(range(1, x.ndim)) + (0,)
        output = interpolateArray(data, x.transpose(tr), order=order, **kargs)
    
    tr = list(range(output.ndim))
    trb = []
    for i in range(min(axes)):
        ind = tr1.index(i) + (len(shape)-len(axes))
        tr.remove(ind)
        trb.append(ind)
    tr2 = tuple(trb+tr)

    ## Untranspose array before returning
    output = output.transpose(tr2)
    if returnCoords:
        return (output, x)
    else:
        return output


def interpolateArray(data, x, default=0.0, order=1, **kargs):
    """
    N-dimensional interpolation similar to scipy.ndimage.map_coordinates.
    
    This function returns linearly-interpolated values sampled from a regular
    grid of data. It differs from `ndimage.map_coordinates` by allowing broadcasting
    within the input array.
    
    ==============  ===========================================================================================
    **Arguments:**
    *data*          Array of any shape containing the values to be interpolated.
    *x*             Array with (shape[-1] <= data.ndim) containing the locations within *data* to interpolate.
                    (note: the axes for this argument are transposed relative to the same argument for
                    `ndimage.map_coordinates`).
    *default*       Value to return for locations in *x* that are outside the bounds of *data*.
    *order*         Order of interpolation: 0=nearest, 1=linear.
    ==============  ===========================================================================================
    
    Returns array of shape (x.shape[:-1] + data.shape[x.shape[-1]:])
    
    For example, assume we have the following 2D image data::
    
        >>> data = np.array([[1,   2,   4  ],
                             [10,  20,  40 ],
                             [100, 200, 400]])
        
    To compute a single interpolated point from this data::
        
        >>> x = np.array([(0.5, 0.5)])
        >>> interpolateArray(data, x)
        array([ 8.25])
        
    To compute a 1D list of interpolated locations:: 
        
        >>> x = np.array([(0.5, 0.5),
                          (1.0, 1.0),
                          (1.0, 2.0),
                          (1.5, 0.0)])
        >>> interpolateArray(data, x)
        array([  8.25,  20.  ,  40.  ,  55.  ])
        
    To compute a 2D array of interpolated locations::
    
        >>> x = np.array([[(0.5, 0.5), (1.0, 2.0)],
                          [(1.0, 1.0), (1.5, 0.0)]])
        >>> interpolateArray(data, x)
        array([[  8.25,  40.  ],
               [ 20.  ,  55.  ]])
               
    ..and so on. The *x* argument may have any shape as long as 
    ```x.shape[-1] <= data.ndim```. In the case that 
    ```x.shape[-1] < data.ndim```, then the remaining axes are simply 
    broadcasted as usual. For example, we can interpolate one location
    from an entire row of the data::
    
        >>> x = np.array([[0.5]])
        >>> interpolateArray(data, x)
        array([[  5.5,  11. ,  22. ]])

    This is useful for interpolating from arrays of colors, vertexes, etc.
    """
    if order not in (0, 1):
        raise ValueError("interpolateArray requires order=0 or 1 (got %s)" % order)

    default = kargs.get("cval", default)
    prof = debug.Profiler()

    nd = data.ndim
    md = x.shape[-1]
    if md > nd:
        raise TypeError("x.shape[-1] must be less than or equal to data.ndim")

    totalMask = np.ones(x.shape[:-1], dtype=bool) # keep track of out-of-bound indexes
    if order == 0:
        xinds = np.round(x).astype(int)  # NOTE: for 0.5 this rounds to the nearest *even* number
        for ax in range(md):
            mask = (xinds[...,ax] >= 0) & (xinds[...,ax] <= data.shape[ax]-1) 
            xinds[...,ax][~mask] = 0
            # keep track of points that need to be set to default
            totalMask &= mask
        result = data[tuple([xinds[...,i] for i in range(xinds.shape[-1])])]
        
    elif order == 1:
        # First we generate arrays of indexes that are needed to 
        # extract the data surrounding each point
        fields = np.mgrid[(slice(0,order+1),) * md]
        xmin = np.floor(x).astype(int)
        xmax = xmin + 1
        indexes = np.concatenate([xmin[np.newaxis, ...], xmax[np.newaxis, ...]])
        fieldInds = []
        for ax in range(md):
            mask = (xmin[...,ax] >= 0) & (x[...,ax] <= data.shape[ax]-1) 
            # keep track of points that need to be set to default
            totalMask &= mask
            
            # ..and keep track of indexes that are out of bounds 
            # (note that when x[...,ax] == data.shape[ax], then xmax[...,ax] will be out
            #  of bounds, but the interpolation will work anyway)
            mask &= (xmax[...,ax] < data.shape[ax])
            axisIndex = indexes[...,ax][fields[ax]]
            axisIndex[axisIndex < 0] = 0
            axisIndex[axisIndex >= data.shape[ax]] = 0
            fieldInds.append(axisIndex)
        prof()

        # Get data values surrounding each requested point
        fieldData = data[tuple(fieldInds)]
        prof()
    
        ## Interpolate
        s = np.empty((md,) + fieldData.shape, dtype=float)
        dx = x - xmin
        # reshape fields for arithmetic against dx
        for ax in range(md):
            f1 = fields[ax].reshape(fields[ax].shape + (1,)*(dx.ndim-1))
            sax = f1 * dx[...,ax] + (1-f1) * (1-dx[...,ax])
            sax = sax.reshape(sax.shape + (1,) * (s.ndim-1-sax.ndim))
            s[ax] = sax
        s = np.product(s, axis=0)
        result = fieldData * s
        for i in range(md):
            result = result.sum(axis=0)

    prof()

    if totalMask.ndim > 0:
        result[~totalMask] = default
    else:
        if totalMask is False:
            result[:] = default

    prof()
    return result

