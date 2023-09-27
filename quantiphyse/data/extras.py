"""
Quantiphyse - Basic classes for Extras

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
import csv
import six

class Extra(object):
    """
    Base class for things which can be stored in the IVM apart from data sets.

    Essentially the only thing an Extra needs to be able to do is be written
    out as a string by implementing __str__

    Alternatively an Extra can override the serialize() method which allows
    formatting options to be taken account of.

    We also provide a metadata dictionary - ideally extras should write their
    metadata in __str__ but in practice this may not be possible when we want
    the output to be compatible with external programs (e.g. writing out a
    matrix as TSV)

    In the future we might expand the Extra base class to define other behaviours,
    e.g. flexible saving to an output file, alternative capabilities... But we
    want to keep things simple for now while we figure out what use can
    be made of them.

    Currently the main uses for Extras are:

      - Tabular output, e.g. data statistics which we might want to write out to a file
      - Matrix outputs, e.g. affine transformations which are the output of a registration
    """
    def __init__(self, name):
        self.name = name
        self.metadata = {}

    def serialize(self, f, **format):
        text = str(self)
        f.write(text)

class NumberListExtra(Extra):
    """
    Extra which represents a list of numbers
    """
    def __init__(self, name, values):
        """
        :param name: Extra name
        :param values: Sequence of numeric values
        """
        Extra.__init__(self, name)

        # Check all values are numeric
        [float(v) for v in values]
        self.values = values

    def serialize(self, f, **format):
        sep = format.get("sep", " ")
        f.write(sep.join([str(v) for v in self.values]))

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

    This is useful for representing general tabular data.
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
