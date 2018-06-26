"""
Quantiphyse - Exception subclasses

Copyright (c) 2013-2018 University of Oxford
"""

class QpException(Exception):
    """ 
    Base class for quantiphyse-specific exceptions

    These are, by definition, exceptions which are expected under certain
    input conditions. They do not immediately imply a defect in the code
    (although a defect in the code might prompt one of these exceptions
    to be thrown). For example, invalid user input, malformed input files,
    etc, might all throw a QpException. No stack trace will be displayed
    for these exceptions, and when throwing the message/detail should
    be written so it can be understood by an end-user.

    By contrast, any exception within the normal Python exception hierarchy
    implies a bug in the code (even if the bug consists of 'need to throw a
    QpException instead). A stack trace will be displayed.
    
    Currently we do not define more specific subclasses although this
    might be useful in the future
    """

    def __init__(self, msg, detail=None):
        super(QpException, self).__init__(msg)
        self.msg = msg
        self.detail = detail

    def __str__(self):
        """ 
        String representation of exception
        
        Don't want QpException: in front of message as this type of exception
        is for the user to see
        """
        return self.msg
