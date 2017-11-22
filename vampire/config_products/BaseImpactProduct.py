import VampireDefaults
import VHIPopnImpactProductImpl
import VHIAreaImpactProductImpl
import FloodAreaImpactProductImpl
import logging
logger = logging.getLogger(__name__)

class BaseImpactProduct(object):
    subclasses = {}

    @classmethod
    def register_subclass(cls, impact_type):
        def decorator(subclass):
            cls.subclasses[impact_type] = subclass
            return subclass
        return decorator

    @classmethod
    def create(cls, impact_type, country, valid_from_date, valid_to_date, vampire_defaults=None):
        if impact_type not in cls.subclasses:
            raise ValueError('Bad impact type {}'.format(impact_type))
        if vampire_defaults is None:
            vp = VampireDefaults.VampireDefaults()
        else:
            vp = vampire_defaults

        return cls.subclasses[impact_type](country, valid_from_date, valid_to_date, vp)

@BaseImpactProduct.register_subclass('vhi_impact_popn')
class VHIPopnImpactProduct(BaseImpactProduct):
    # ...
    def __init__(self, country, valid_from_date, valid_to_date, vampire_defaults):
        self.impl = VHIPopnImpactProductImpl.VHIPopnImpactProductImpl(country, valid_from_date, valid_to_date, vampire_defaults)
        return

    @property
    def valid_from_date(self):
        return self.impl.valid_from_date()
    @property
    def valid_to_date(self):
        return self.impl.valid_to_date()

    def generate_config(self, hazard_file=None, hazard_dir=None, hazard_pattern=None,
                        boundary_file=None, boundary_dir=None, boundary_pattern=None, boundary_field=None,
                        population_file=None, output_file=None, output_dir=None, output_pattern=None, masked=False):
        return self.impl.generate_config(hazard_file, hazard_dir, hazard_pattern,
                        boundary_file, boundary_dir, boundary_pattern, boundary_field,
                        population_file, output_file, output_dir, output_pattern, masked)

    def generate_publish_config(self):
        return self.impl.generate_publish_config()


@BaseImpactProduct.register_subclass('vhi_impact_area')
class VHIAreaImpactProduct(BaseImpactProduct):
    # ...
    def __init__(self, country, product_date, interval, vampire_defaults):
        self.impl = VHIAreaImpactProductImpl.VHIAreaImpactProductImpl(country, product_date, interval, vampire_defaults)
        return

    @property
    def valid_from_date(self):
        return self.impl.valid_from_date
    @property
    def valid_to_date(self):
        return self.impl.valid_to_date


    def generate_header(self):
        return self.impl.generate_header()

    def generate_config(self, hazard_file, hazard_dir, hazard_pattern,
                        boundary_file=None, boundary_dir=None, boundary_pattern=None, boundary_field=None,
                        output_file=None, output_dir=None, output_pattern=None):
        return self.impl.generate_config(hazard_file, hazard_dir, hazard_pattern,
                        boundary_file, boundary_dir, boundary_pattern, boundary_field,
                        output_file, output_dir, output_pattern)

    def generate_publish_config(self):
        return self.impl.generate_publish_config()

@BaseImpactProduct.register_subclass('flood_impact_area')
class FloodAreaImpactProduct(BaseImpactProduct):
    # ...
    def __init__(self, country, product_date, interval, vampire_defaults):
        self.impl = FloodAreaImpactProductImpl.FloodAreaImpactProductImpl(country, product_date, interval, vampire_defaults)
        return

    def generate_header(self):
        return self.impl.generate_header()

    def generate_config(self, hazard_file, hazard_dir, hazard_pattern,
                        boundary_file=None, boundary_dir=None, boundary_pattern=None, boundary_field=None,
                        output_file=None, output_dir=None, output_pattern=None):
        return self.impl.generate_config(hazard_file, hazard_dir, hazard_pattern,
                        boundary_file, boundary_dir, boundary_pattern, boundary_field,
                        output_file, output_dir, output_pattern)

    def generate_publish_config(self):
        return self.impl.generate_publish_config()