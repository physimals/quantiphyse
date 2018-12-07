"""
Quantiphyse - Base class for logging

Copyright (c) 2013-2018 University of Oxford
"""

import logging
logging.basicConfig(format='%(asctime)s %(levelname)s %(name)s %(message)s', datefmt='%H:%M:%S')

# This is a generic logger for the application. Intention is to move to
# per-widget loggers but in the interim this is what we use for calls to debug() etc
BASE_LOG = logging.getLogger("quantiphyse")
DEBUG = False

def set_debug(enable_debug):
    """
    Set the generic debug level

    .. deprecated:: 0.8
    """
    if enable_debug:
        BASE_LOG.setLevel(logging.DEBUG)
    else:
        BASE_LOG.setLevel(logging.WARN)

def get_debug():
    """
    Get the generic debug level

    .. deprecated:: 0.8
    """
    return BASE_LOG.getEffectiveLevel() <= logging.DEBUG

class LogSource(object):
    """
    Base class for anything which wants to log messages
    """
    def __init__(self):
        logname = "%s.%s" % (self.__module__, self.__class__.__name__)
        if not logname.startswith("quantiphyse"):
            # Plugins do not come under the quantiphyse namespace but we want them
            # to be ancestors of the generic logger
            logname = "quantiphyse." + logname
        self.logger = logging.getLogger(logname)

    def debug(self, *args, **kwargs):
        """
        Log a debug level message
        """
        self.logger.debug(*args, **kwargs)

    def warn(self, *args, **kwargs):
        """
        Log a warning
        """
        self.logger.warn(*args, **kwargs)
        