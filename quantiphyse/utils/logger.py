"""
Quantiphyse - Base class for logging

Copyright (c) 2013-2018 University of Oxford
"""

import logging
logging.basicConfig(format='%(asctime)s %(levelname)s %(name)s %(message)s', datefmt='%H:%M:%S')

def set_base_log_level(level):
    """
    Set the base logging level
    """
    logging.getLogger("quantiphyse").setLevel(level)

class LogSource(object):
    """
    Base class for anything which wants to log messages
    """
    def __init__(self):
        logname = "%s.%s" % (self.__module__, self.__class__.__name__)
        if not logname.startswith("quantiphyse."):
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
    
    def debug_enabled(self):
        return self.logger.getEffectiveLevel() <= logging.DEBUG