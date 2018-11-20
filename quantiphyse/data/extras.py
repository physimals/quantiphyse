"""
Quantiphyse - Basic classes for Extras

Copyright (c) 2013-2018 University of Oxford
"""
import csv
import six

import numpy as np

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
        if len(arr) == 0:
            raise ValueError("No matrix data given")
        if row_headers and len(row_headers) != len(arr):
            raise ValueError("Incorrect number of row headers given")
        if col_headers and len(col_headers) != len(arr[0]):
            raise ValueError("Incorrect number of column headers given")

        self.arr = arr
        self.row_headers = list(row_headers)
        self.col_headers = list(col_headers)

    def __str__(self):
        stream = six.StringIO()
        writer = csv.writer(stream, delimiter='\t', lineterminator='\n')
        if self.col_headers:
            if self.row_headers:
                writer.writerow([" "] + self.col_headers)
            else:
                writer.writerow(self.col_headers)

        for row in self.arr:
            if self.row_headers:
                writer.writerow([" "] + list(row))
            else:
                writer.writerow(list(row))

        return stream.getvalue()
