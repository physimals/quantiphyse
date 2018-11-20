"""
Quantiphyse - Basic classes for Extras

Copyright (c) 2013-2018 University of Oxford
"""
from quantiphyse.utils import matrix_to_str

class Extra(object):
    """
    Base class for things which can be stored in the IVM apart from data sets.

    Essentially the only thing an Extra needs to be able to do is be written
    out as a string. We force subclasses to override this. 
    """
    def __init__(self, name):
        self.name = name

    def __str__(self):
        raise NotImplementedError("Subclasses of Extra must implement __str__")

class MatrixExtra(Extra):
    """
    Extra which represents a 2D matrix with optional row and column headers
    """
    def __init__(self, name, arr, row_headers=(), col_headers=()):
        Extra.__init__(self, name)
        if arr.ndim != 2:
            raise ValueError("Matrix must be 2D")
        if row_headers and len(row_headers) != arr.shape[0]:
            raise ValueError("Incorrect number of row headers given")
        if col_headers and len(col_headers) != arr.shape[1]:
            raise ValueError("Incorrect number of column headers given")

        self.arr = arr
        self.row_headers = row_headers
        self.col_headers = col_headers

    def __str__(self):
        # FIXME row and column headers in TSV output
        return matrix_to_str(self.arr)
