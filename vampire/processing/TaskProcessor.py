import vampire.VampireDefaults as VampireDefaults
import MODISTasksImpl
import CHIRPSTasksImpl
import IMERGTasksImpl
import GFSTasksImpl
import RasterTasksImpl
import ClimateAnalysisTasksImpl
import ImpactTasksImpl
import PublishTasksImpl
import logging
logger = logging.getLogger(__name__)

class TaskProcessor():
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

@TaskProcessor.register_subclass('modis')
class MODISTaskProcessor(TaskProcessor):
    # ...
    def __init__(self, params, vampire_defaults):
        self.impl = MODISTasksImpl.MODISTasksImpl.create(params['type'].lower(), params, vampire_defaults)
        return

    def process(self):
        return self.impl.process()

@TaskProcessor.register_subclass('chirps')
class CHIRPSTaskProcessor(TaskProcessor):
    # ...
    def __init__(self, params, vampire_defaults):
        self.impl = CHIRPSTasksImpl.CHIRPSTasksImpl.create(params['type'].lower(), params, vampire_defaults)
        return

    def process(self):
        return self.impl.process()

@TaskProcessor.register_subclass('imerg')
class IMERGTaskProcessor(TaskProcessor):
    # ...
    def __init__(self, params, vampire_defaults):
        self.impl = IMERGTasksImpl.IMERGTasksImpl.create(params['type'].lower(), params, vampire_defaults)
        return

    def process(self):
        return self.impl.process()

@TaskProcessor.register_subclass('gfs')
class GFSTaskProcessor(TaskProcessor):
    # ...
    def __init__(self, params, vampire_defaults):
        self.impl = GFSTasksImpl.GFSTasksImpl.create(params['type'].lower(), params, vampire_defaults)
        return

    def process(self):
        return self.impl.process()

@TaskProcessor.register_subclass('raster')
class RasterTaskProcessor(TaskProcessor):
    # ...
    def __init__(self, params, vampire_defaults):
        self.impl = RasterTasksImpl.RasterTasksImpl.create(params['type'].lower(), params, vampire_defaults)
        return

    def process(self):
        return self.impl.process()

@TaskProcessor.register_subclass('analysis')
class ClimateAnalysisTaskProcessor(TaskProcessor):
    # ...
    def __init__(self, params, vampire_defaults):
        self.impl = ClimateAnalysisTasksImpl.ClimateAnalysisTasksImpl.create(params['type'].lower(), params, vampire_defaults)
        return

    def process(self):
        return self.impl.process()

@TaskProcessor.register_subclass('impact')
class ImpactTaskProcessor(TaskProcessor):
    # ...
    def __init__(self, params, vampire_defaults):
        self.impl = ImpactTasksImpl.ImpactTasksImpl.create(params['type'].lower(), params, vampire_defaults)
        return

    def process(self):
        return self.impl.process()

@TaskProcessor.register_subclass('publish')
class PublishTaskProcessor(TaskProcessor):
    # ...
    def __init__(self, params, vampire_defaults):
        self.impl = PublishTasksImpl.PublishTasksImpl.create(params['type'].lower(), params, vampire_defaults)
        return

    def process(self):
        return self.impl.process()
