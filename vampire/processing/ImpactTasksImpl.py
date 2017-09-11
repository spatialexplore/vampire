import vampire.VampireDefaults as VampireDefaults
import BaseTaskImpl
import AreaImpactTaskImpl
import PopulationImpactTaskImpl
import PovertyImpactTaskImpl
import logging
logger = logging.getLogger(__name__)

class ImpactTasksImpl():
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

@ImpactTasksImpl.register_subclass('area')
class AreaImpactTask(object):
    """ Initialise MODISDownloadTask object.

    Implementation class for downloading MODIS products.

    """
    def __init__(self, params, vampire_defaults):
        logger.debug('Initialising MODIS download task')
        self.impl = AreaImpactTaskImpl.AreaImpactTaskImpl(params, vampire_defaults)
        return

    def process(self):
        self.impl.process()
        return

@ImpactTasksImpl.register_subclass('population')
class PopulationImpactTask(object):
    """ Initialise MODISDownloadTask object.

    Implementation class for downloading MODIS products.

    """
    def __init__(self, params, vampire_defaults):
        logger.debug('Initialising population impact task')
        self.impl = PopulationImpactTaskImpl.PopulationImpactTaskImpl(params, vampire_defaults)
        return

    def process(self):
        self.impl.process()
        return

@ImpactTasksImpl.register_subclass('poverty')
class PovertyImpactTask(object):
    """ Initialise MODISDownloadTask object.

    Implementation class for downloading MODIS products.

    """
    def __init__(self, params, vampire_defaults):
        logger.debug('Initialising poverty impact task')
        self.impl = PovertyImpactTaskImpl.PovertyImpactTaskImpl(params, vampire_defaults)
        return

    def process(self):
        self.impl.process()
        return

