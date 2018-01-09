import logging

import yaml

import DatabaseManager
import GISServerInterface
import processing.TaskProcessor

logger = logging.getLogger(__name__)

class ConfigFileError(ValueError):
    def __init__(self, message, e, *args):
        '''Raise when the config file contains an error'''
        self.message = message
        self.error = e
        super(ConfigFileError, self).__init__(message, e, *args)

class ConfigProcessor():


    def process_config(self, config):

        global options, args
        try:
            if config:
                # parse config file
                with open(config, 'r') as ymlfile:
                    cfg = yaml.load(ymlfile)
            else:
                print "no config"
                logger.error("A config file is required. Please specify a config file on the command line.")
                return -1
        except Exception, e:
            logger.error("Cannot load config file.")
            raise ConfigFileError('no run in cfg',e)

        if not 'run' in cfg:
            print "Error in cfg!!"
        _process_list = cfg['run']
        logger.debug(_process_list)

        for i,p in enumerate(_process_list):
            _task = processing.TaskProcessor.TaskProcessor.create(p['process'].lower(), p)
            _task.process()

        return None