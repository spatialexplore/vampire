import logging

import VampireDefaults as VampireDefaults

import DaysSinceLastRainTaskImpl
import FloodAlertTaskImpl
import RainfallAnomalyTaskImpl
import SPITaskImpl
import TCITaskImpl
import VCITaskImpl
import VHITaskImpl

logger = logging.getLogger(__name__)

class ConfigFileError(ValueError):
    def __init__(self, message, e, *args):
        '''Raise when the config file contains an error'''
        self.message = message
        self.error = e
        super(ConfigFileError, self).__init__(message, e, *args)

class ClimateAnalysisTasksImpl():
    subclasses = {}

    @classmethod
    def register_subclass(cls, product_type):
        def decorator(subclass):
            cls.subclasses[product_type] = subclass
            return subclass
        return decorator

    @classmethod
    def create(cls, process_type, params, vampire_defaults=None):
        if process_type not in cls.subclasses:
            raise ValueError('Bad process type {}'.format(process_type))
        if vampire_defaults is None:
            vp = VampireDefaults.VampireDefaults()
        else:
            vp = vampire_defaults

        return cls.subclasses[process_type](params, vp)

@ClimateAnalysisTasksImpl.register_subclass('rainfall_anomaly')
class RainfallAnomalyTask(object):
    """ Initialise MODISDownloadTask object.

    Implementation class for downloading MODIS products.

    """
    def __init__(self, params, vampire_defaults):
        logger.debug('Initialising MODIS download task')
        self.impl = RainfallAnomalyTaskImpl.RainfallAnomalyTaskImpl(params, vampire_defaults)
        return

    def process(self):
        return self.impl.process()


@ClimateAnalysisTasksImpl.register_subclass('spi')
class SPITask(object):
    """ Initialise MODISDownloadTask object.

    Implementation class for downloading MODIS products.

    """
    def __init__(self, params, vampire_defaults):
        logger.debug('Initialising MODIS download task')
        self.impl = SPITaskImpl.SPITaskImpl(params, vampire_defaults)
        return

    def process(self):
        return self.impl.process()


@ClimateAnalysisTasksImpl.register_subclass('days_since_last_rain')
class DaysSinceLastRainTask(object):
    """ Initialise MODISDownloadTask object.

    Implementation class for downloading MODIS products.

    """
    def __init__(self, params, vampire_defaults):
        logger.debug('Initialising MODIS download task')
        self.impl = DaysSinceLastRainTaskImpl.DaysSinceLastRainTaskImpl(params, vampire_defaults)
        return

    def process(self):
        self.impl.process()
        return



@ClimateAnalysisTasksImpl.register_subclass('vci')
class VCITask(object):
    """ Initialise MODISDownloadTask object.

    Implementation class for downloading MODIS products.

    """
    def __init__(self, params, vampire_defaults):
        logger.debug('Initialising MODIS download task')
        self.impl = VCITaskImpl.VCITaskImpl(params, vampire_defaults)
        return

    def process(self):
        self.impl.process()
        return

@ClimateAnalysisTasksImpl.register_subclass('tci')
class VCITask(object):
    """ Initialise MODISDownloadTask object.

    Implementation class for downloading MODIS products.

    """
    def __init__(self, params, vampire_defaults):
        logger.debug('Initialising MODIS download task')
        self.impl = TCITaskImpl.TCITaskImpl(params, vampire_defaults)
        return

    def process(self):
        self.impl.process()
        return


@ClimateAnalysisTasksImpl.register_subclass('vhi')
class VHITask(object):
    """ Initialise MODISDownloadTask object.

    Implementation class for downloading MODIS products.

    """
    def __init__(self, params, vampire_defaults):
        logger.debug('Initialising MODIS download task')
        self.impl = VHITaskImpl.VHITaskImpl(params, vampire_defaults)
        return

    def process(self):
        self.impl.process()
        return None

@ClimateAnalysisTasksImpl.register_subclass('flood_alert')
class FloodAlertTask(object):
    """ Initialise FloodAlertTask object.

    Implementation class for predicting flood products.

    """
    def __init__(self, params, vampire_defaults):
        logger.debug('Initialising Flood Alert task')
        self.impl = FloodAlertTaskImpl.FloodAlertTaskImpl(params, vampire_defaults)
        return

    def process(self):
        self.impl.process()
        return None
