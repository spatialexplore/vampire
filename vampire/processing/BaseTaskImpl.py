import logging
logger = logging.getLogger(__name__)

class ConfigFileError(ValueError):
    def __init__(self, message, e, *args):
        '''Raise when the config file contains an error'''
        self.message = message
        self.error = e
        super(ConfigFileError, self).__init__(message, e, *args)

class BaseTaskImpl(object):
    """ Initialise BaseTaskImpl object.

    Abstract implementation class for processing tasks.

    """
    def __init__(self, params, vampire_defaults):
        logger.debug('Initialising Task')
        self.params = params
        self.vp = vampire_defaults
        return

