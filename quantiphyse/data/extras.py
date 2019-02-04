"""
Quantiphyse - Basic classes for Extras

Copyright (c) 2013-2018 University of Oxford
"""
import csv
import six

class Extra(object):
    """
    Base class for things which can be stored in the IVM apart from data sets.

    Essentially the only thing an Extra needs to be able to do is be written
    out as a string. We force subclasses to override this. 

    We also provide a metadata dictionary - ideally extras should write their
    metadata in __str__ but in practice this may not be possible when we want
    the output to be compatible with external programs (e.g. writing out a 
    matrix as TSV)
    """
    def __init__(self, name):
        self.name = name
        self.metadata = {}

    def __str__(self):
        raise NotImplementedError("Subclasses of Extra must implement __str__")

class MatrixExtra(Extra):
    """
    Extra which represents a 2D matrix with optional row and column headers
    """
    def __init__(self, name, arr, row_headers=(), col_headers=()):
        """
        :param name: Extra name
        :param arr: List-of-lists or 2D Numpy array containing matrix data
        :param row_headers: Optional sequence of row headers
        :param col_headers: Optional sequence of column headers
        """
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
        """
        Convert matrix to a string in TSV format
        """
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

class DataFrameExtra(Extra):
    """
    Extra which represents a Pandas data frame
    """
    def __init__(self, name, df):
        """
        :param name: Extra name
        :param arr: List-of-lists or 2D Numpy array containing matrix data
        :param row_headers: Optional sequence of row headers
        :param col_headers: Optional sequence of column headers
        """
        Extra.__init__(self, name)
        self.df = df

    def __str__(self):
        stream = six.StringIO()
        self.df.to_csv(stream, sep='\t')
        return stream.getvalue()
