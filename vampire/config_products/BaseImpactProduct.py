""" Impact of Data Products module.

    Provides classes for each the impact of data products supported within Vampire. New product impacts should be added here.
"""
import VampireDefaults
import VHIPopnImpactProductImpl
import VHIAreaImpactProductImpl
import FloodAreaImpactProductImpl
import FloodPopnImpactProductImpl
import DSLRAreaImpactProductImpl
import DSLRPopnImpactProductImpl
import logging
logger = logging.getLogger(__name__)

class BaseImpactProduct(object):
    """ Base class for data product impact configuration objects.

    Manages registration of data product impact configurations and creation of data product impact configuration objects.
    Data product impact configurations provide the ability to generate config file sections related to impact of the
    data product.

    """

    subclasses = {}

    @classmethod
    def register_subclass(cls, impact_type):
        """ Register product impact with the productimpact  manager.

        Registers the data product impact identified by impact_type with the product impact manager.
        This allows the appropriate product impact to be created automatically when requested.

        :param impact_type: Product name.
        :type impact_type: string
        """
        def decorator(subclass):
            cls.subclasses[impact_type] = subclass
            return subclass
        return decorator

    @classmethod
    def create(cls, impact_type, country, valid_from_date, valid_to_date, vampire_defaults=None):
        """ Create impact of the specified type.

        Creates the product impact identified by impact_type and sets initialization values.

        :param impact_type: Impact name.
        :type impact_type: string
        :param country: Country data product impact will be created for.
        :type country: string
        :param valid_from_date: Date product impact is valid from.
        :type valid_from_date: datetime
        :param valid_to_date: Date product impact is valid until.
        :type valid_to_date: string
        :param vampire_defaults:
        :type vampire_defaults: VampireDefaults
        :return: Product impact object of type specified (a registered subclass of BaseImpactProduct).
        """
        if impact_type not in cls.subclasses:
            raise ValueError('Bad impact type {}'.format(impact_type))
        if vampire_defaults is None:
            vp = VampireDefaults.VampireDefaults()
        else:
            vp = vampire_defaults

        return cls.subclasses[impact_type](country, valid_from_date, valid_to_date, vp)

@BaseImpactProduct.register_subclass('vhi_impact_popn')
class VHIPopnImpactProduct(BaseImpactProduct):
    """ Vegetation Health Index product impact configuration.

    Manages generation of configuration file sections for calculating impact of Vegetation Health Index on population.

    """

    def __init__(self, country, valid_from_date, valid_to_date, vampire_defaults):
        """ Initialisation of VHI population impact.

        Initialises the VHI population impact. Creates the implementation object which does the actual work of
        generating config file sections.

        :param country: Country data product will be created for. This is used for downloading data and identifying appropriate resources and default values during processing.
        :type country: string
        :param valid_from_date: Date product impact is valid from.
        :type valid_from_date: datetime
        :param valid_to_date: Date product impact is valid until.
        :type valid_to_date: string
        :param vampire_defaults:
        :type vampire_defaults: VampireDefaults
        """
        self.impl = VHIPopnImpactProductImpl.VHIPopnImpactProductImpl(country, valid_from_date, valid_to_date, vampire_defaults)
        return

    @property
    def valid_from_date(self):
        """ Get date the output impact file is valid from. """
        return self.impl.valid_from_date()
    @property
    def valid_to_date(self):
        """ Get date the output impact file is valid until. """
        return self.impl.valid_to_date()

    def generate_config(self, hazard_file=None, hazard_dir=None, hazard_pattern=None,
                        boundary_file=None, boundary_dir=None, boundary_pattern=None, boundary_field=None,
                        population_file=None, output_file=None, output_dir=None, output_pattern=None, masked=False):
        """ Generate config file section for generating VCI.

        Generate config file entries required to create VCI for the specified country, date and interval.

        :param hazard_file: File name of hazard image file.
        :type hazard_file: string
        :param hazard_dir: Directory where the hazard file is located.
        :type hazard_dir: string
        :param hazard_pattern: Regular expression pattern to used to find the hazard file for the product date.
        :type hazard_pattern: string
        :param boundary_file: Full path to the boundary file to use to calculate impact.
        :type boundary_file: string
        :param boundary_dir: Directory where the boundary file is located.
        :type boundary_dir: string
        :param boundary_pattern: Regular expression pattern to used to find the boundary file.
        :type boundary_pattern: string
        :param boundary_field: Field within the boundary file to use to identify areas.
        :type boundary_field: string
        :param population_file: Full path to the file containing population data.
        :type population_file: string
        :param output_filename: Filename for VHI population impact output file.
        :type output_filename: string
        :param output_dir: Directory to save the VHI population impact output file.
        :type output_dir: string
        :param output_pattern: Pattern to be used to generate the VHI population impact output file name. May refer to elements within the hazard_pattern.
        :type output_pattern: string
        :param masked: Flag indicating whether the impact should be masked by a boundary or not.
        :type masked: bool
        :return: Config file sections required for generating VHI population impact.
        :rtype: string
        """
        return self.impl.generate_config(hazard_file, hazard_dir, hazard_pattern,
                        boundary_file, boundary_dir, boundary_pattern, boundary_field,
                        population_file, output_file, output_dir, output_pattern)

    def generate_publish_config(self):
        """ Generate config section to publish Flood population impact.

        Generates configuration file section to publish the Flood population impact output file to a database.

        :return: Config file sections required for publishing Flood population impact.
        :rtype: string
        """
        return self.impl.generate_publish_config()


@BaseImpactProduct.register_subclass('vhi_impact_area')
class VHIAreaImpactProduct(BaseImpactProduct):
    # ...
    def __init__(self, country, product_date, interval, vampire_defaults):
        """ Initialisation of VHI area impact.

        Initialises the VHI area impact. Creates the implementation object which does the actual work of
        generating config file sections.

        :param country: Country data product will be created for.
        :type country: string
        :param product_date: Date for impact product being generated.
        :type product_date: datetime
        :param interval: Interval for product impact generation - daily, weekly, monthly, seasonal.
        :type interval: string
        :param vampire_defaults:
        :type vampire_defaults: VampireDefaults
        """
        self.impl = VHIAreaImpactProductImpl.VHIAreaImpactProductImpl(country, product_date, interval, vampire_defaults)
        return

    @property
    def valid_from_date(self):
        """ Get date the output impact file is valid from. """
        return self.impl.valid_from_date
    @property
    def valid_to_date(self):
        """ Get date the output impact file is valid until. """
        return self.impl.valid_to_date


    def generate_header(self):
        """ Generate details related to VHI area impact that go in the config file header. """
        return self.impl.generate_header()

    def generate_config(self, hazard_file, hazard_dir, hazard_pattern,
                        boundary_file=None, boundary_dir=None, boundary_pattern=None, boundary_field=None,
                        output_file=None, output_dir=None, output_pattern=None, masked=False):
        """ Generate config file section for generating VCI.

        Generate config file entries required to create VHI area impact for the specified country, date and interval.

        :param hazard_file: File name of hazard image file.
        :type hazard_file: string
        :param hazard_dir: Directory where the hazard file is located.
        :type hazard_dir: string
        :param hazard_pattern: Regular expression pattern to used to find the hazard file for the product date.
        :type hazard_pattern: string
        :param boundary_file: Full path to the boundary file to use to calculate impact.
        :type boundary_file: string
        :param boundary_dir: Directory where the boundary file is located.
        :type boundary_dir: string
        :param boundary_pattern: Regular expression pattern to used to find the boundary file.
        :type boundary_pattern: string
        :param boundary_field: Field within the boundary file to use to identify areas.
        :type boundary_field: string
        :param output_filename: Filename for VHI area impact output file.
        :type output_filename: string
        :param output_dir: Directory to save the VHI area impact output file.
        :type output_dir: string
        :param output_pattern: Pattern to be used to generate the VHI area impact output file name. May refer to elements within the hazard_pattern.
        :type output_pattern: string
        :param masked: Flag indicating whether the impact should be masked by a boundary or not.
        :type masked: bool
        :return: Config file sections required for generating VHI area impact.
        :rtype: string
        """
        return self.impl.generate_config(hazard_file, hazard_dir, hazard_pattern,
                        boundary_file, boundary_dir, boundary_pattern, boundary_field,
                        output_file, output_dir, output_pattern)

    def generate_publish_config(self):
        """ Generate config section to publish Flood population impact.

        Generates configuration file section to publish the Flood population impact output file to a database.

        :return: Config file sections required for publishing Flood population impact.
        :rtype: string
        """
        return self.impl.generate_publish_config()

@BaseImpactProduct.register_subclass('flood_forecast_impact_area')
class FloodAreaImpactProduct(BaseImpactProduct):
    # ...
    def __init__(self, country, product_date, interval, vampire_defaults):
        """ Initialisation of Flood area impact.

        Initialises the Flood area impact. Creates the implementation object which does the actual work of
        generating config file sections.

        :param country: Country data product will be created for. This is used for downloading data and identifying appropriate resources and default values during processing.
        :type country: string
        :param product_date: Date for impact product being generated.
        :type product_date: datetime
        :param interval: Interval for product impact generation - daily, weekly, monthly, seasonal.
        :type interval: string
        :param vampire_defaults:
        :type vampire_defaults: VampireDefaults
        """
        self.impl = FloodAreaImpactProductImpl.FloodAreaImpactProductImpl(country, product_date, interval, vampire_defaults)
        return

    def generate_header(self):
        """ Generate details related to Flood area impact that go in the config file header. """
        return self.impl.generate_header()

    def generate_config(self, hazard_file, hazard_dir, hazard_pattern,
                        boundary_file=None, boundary_dir=None, boundary_pattern=None, boundary_field=None,
                        output_file=None, output_dir=None, output_pattern=None, masked=False):
        """ Generate config file section for generating Flood area impact.

        Generate config file entries required to create Flood area impact for the specified country, date and interval.

        :param hazard_file: File name of hazard image file.
        :type hazard_file: string
        :param hazard_dir: Directory where the hazard file is located.
        :type hazard_dir: string
        :param hazard_pattern: Regular expression pattern to used to find the hazard file for the product date.
        :type hazard_pattern: string
        :param boundary_file: Full path to the boundary file to use to calculate impact.
        :type boundary_file: string
        :param boundary_dir: Directory where the boundary file is located.
        :type boundary_dir: string
        :param boundary_pattern: Regular expression pattern to used to find the boundary file.
        :type boundary_pattern: string
        :param boundary_field: Field within the boundary file to use to identify areas.
        :type boundary_field: string
        :param output_filename: Filename for Flood area impact output file.
        :type output_filename: string
        :param output_dir: Directory to save the Flood area impact output file.
        :type output_dir: string
        :param output_pattern: Pattern to be used to generate the Flood area impact output file name. May refer to elements within the hazard_pattern.
        :type output_pattern: string
        :param masked: Flag indicating whether the impact should be masked by a boundary or not.
        :type masked: bool
        :return: Config file sections required for generating Flood area impact.
        :rtype: string
        """
        return self.impl.generate_config(hazard_file, hazard_dir, hazard_pattern,
                        boundary_file, boundary_dir, boundary_pattern, boundary_field,
                        output_file, output_dir, output_pattern)

    def generate_publish_config(self):
        """ Generate config section to publish Flood population impact.

        Generates configuration file section to publish the Flood population impact output file to a database.

        :return: Config file sections required for publishing Flood population impact.
        :rtype: string
        """
        return self.impl.generate_publish_config()

@BaseImpactProduct.register_subclass('flood_forecast_impact_popn')
class FloodPopnImpactProduct(BaseImpactProduct):
    # ...
    def __init__(self, country, valid_from_date, valid_to_date, vampire_defaults):
        """ Initialisation of Flood population impact.

        Initialises the Flood population impact. Creates the implementation object which does the actual work of
        generating config file sections.

        :param country: Country data product will be created for. This is used for downloading data and identifying appropriate resources and default values during processing.
        :type country: string
        :param valid_from_date: Date product impact is valid from.
        :type valid_from_date: datetime
        :param valid_to_date: Date product impact is valid until.
        :type valid_to_date: string
        :param vampire_defaults:
        :type vampire_defaults: VampireDefaults
        """
        self.impl = FloodPopnImpactProductImpl.FloodPopnImpactProductImpl(country, valid_from_date, valid_to_date, vampire_defaults)
        return

    @property
    def valid_from_date(self):
        """ Get date the output impact file is valid from. """
        return self.impl.valid_from_date()
    @property
    def valid_to_date(self):
        """ Get date the output impact file is valid until. """
        return self.impl.valid_to_date()

    def generate_config(self, hazard_file=None, hazard_dir=None, hazard_pattern=None,
                        boundary_file=None, boundary_dir=None, boundary_pattern=None, boundary_field=None,
                        population_file=None, output_file=None, output_dir=None, output_pattern=None, masked=False):
        """ Generate config file section for generating Flood population impact.

        Generate config file entries required to create Flood population impact for the specified country, date and interval.

        :param hazard_file: File name of hazard image file.
        :type hazard_file: string
        :param hazard_dir: Directory where the hazard file is located.
        :type hazard_dir: string
        :param hazard_pattern: Regular expression pattern to used to find the hazard file for the product date.
        :type hazard_pattern: string
        :param boundary_file: Full path to the boundary file to use to calculate impact.
        :type boundary_file: string
        :param boundary_dir: Directory where the boundary file is located.
        :type boundary_dir: string
        :param boundary_pattern: Regular expression pattern to used to find the boundary file.
        :type boundary_pattern: string
        :param boundary_field: Field within the boundary file to use to identify areas.
        :type boundary_field: string
        :param population_file: Full path to the file containing population data.
        :type population_file: string
        :param output_filename: Filename for Flood population impact output file.
        :type output_filename: string
        :param output_dir: Directory to save the Flood population impact output file.
        :type output_dir: string
        :param output_pattern: Pattern to be used to generate the Flood population impact output file name. May refer to elements within the hazard_pattern.
        :type output_pattern: string
        :param masked: Flag indicating whether the impact should be masked by a boundary or not.
        :type masked: bool
        :return: Config file sections required for generating Flood population impact.
        :rtype: string
        """
        return self.impl.generate_config(hazard_file, hazard_dir, hazard_pattern,
                        boundary_file, boundary_dir, boundary_pattern, boundary_field,
                        population_file, output_file, output_dir, output_pattern)

    def generate_publish_config(self):
        """ Generate config section to publish Flood population impact.

        Generates configuration file section to publish the Flood population impact output file to a database.

        :return: Config file sections required for publishing Flood population impact.
        :rtype: string
        """
        return self.impl.generate_publish_config()

@BaseImpactProduct.register_subclass('days_since_last_rain_impact_popn')
class DaysSinceLastRainPopnImpactProduct(BaseImpactProduct):
    """ Days Since Last Rain product impact configuration.

    Manages generation of configuration file sections for calculating impact of Days Since Last Rain on population.

    """

    def __init__(self, country, valid_from_date, valid_to_date, vampire_defaults):
        """ Initialisation of DSLR population impact.

        Initialises the DSLR population impact. Creates the implementation object which does the actual work of
        generating config file sections.

        :param country: Country data product will be created for. This is used for downloading data and identifying appropriate resources and default values during processing.
        :type country: string
        :param valid_from_date: Date product impact is valid from.
        :type valid_from_date: datetime
        :param valid_to_date: Date product impact is valid until.
        :type valid_to_date: string
        :param vampire_defaults:
        :type vampire_defaults: VampireDefaults
        """
        self.impl = DSLRPopnImpactProductImpl.DSLRPopnImpactProductImpl(country, valid_from_date, valid_to_date, vampire_defaults)
        return

    @property
    def valid_from_date(self):
        """ Get date the output impact file is valid from. """
        return self.impl.valid_from_date()
    @property
    def valid_to_date(self):
        """ Get date the output impact file is valid until. """
        return self.impl.valid_to_date()

    def generate_config(self, hazard_file=None, hazard_dir=None, hazard_pattern=None,
                        boundary_file=None, boundary_dir=None, boundary_pattern=None, boundary_field=None,
                        population_file=None, output_file=None, output_dir=None, output_pattern=None, masked=False):
        """ Generate config file section for generating VCI.

        Generate config file entries required to create VCI for the specified country, date and interval.

        :param hazard_file: File name of hazard image file.
        :type hazard_file: string
        :param hazard_dir: Directory where the hazard file is located.
        :type hazard_dir: string
        :param hazard_pattern: Regular expression pattern to used to find the hazard file for the product date.
        :type hazard_pattern: string
        :param boundary_file: Full path to the boundary file to use to calculate impact.
        :type boundary_file: string
        :param boundary_dir: Directory where the boundary file is located.
        :type boundary_dir: string
        :param boundary_pattern: Regular expression pattern to used to find the boundary file.
        :type boundary_pattern: string
        :param boundary_field: Field within the boundary file to use to identify areas.
        :type boundary_field: string
        :param population_file: Full path to the file containing population data.
        :type population_file: string
        :param output_filename: Filename for VHI population impact output file.
        :type output_filename: string
        :param output_dir: Directory to save the VHI population impact output file.
        :type output_dir: string
        :param output_pattern: Pattern to be used to generate the VHI population impact output file name. May refer to elements within the hazard_pattern.
        :type output_pattern: string
        :param masked: Flag indicating whether the impact should be masked by a boundary or not.
        :type masked: bool
        :return: Config file sections required for generating VHI population impact.
        :rtype: string
        """
        return self.impl.generate_config(hazard_file, hazard_dir, hazard_pattern,
                        boundary_file, boundary_dir, boundary_pattern, boundary_field,
                        population_file, output_file, output_dir, output_pattern)

    def generate_publish_config(self):
        """ Generate config section to publish Flood population impact.

        Generates configuration file section to publish the Flood population impact output file to a database.

        :return: Config file sections required for publishing Flood population impact.
        :rtype: string
        """
        return self.impl.generate_publish_config()


@BaseImpactProduct.register_subclass('days_since_last_rain_impact_area')
class DaysSinceLastRainAreaImpactProduct(BaseImpactProduct):
    # ...
    def __init__(self, country, product_date, interval, vampire_defaults):
        """ Initialisation of DSLR area impact.

        Initialises the DSLR area impact. Creates the implementation object which does the actual work of
        generating config file sections.

        :param country: Country data product will be created for.
        :type country: string
        :param product_date: Date for impact product being generated.
        :type product_date: datetime
        :param interval: Interval for product impact generation - daily, weekly, monthly, seasonal.
        :type interval: string
        :param vampire_defaults:
        :type vampire_defaults: VampireDefaults
        """
        self.impl = DSLRAreaImpactProductImpl.DSLRAreaImpactProductImpl(country, product_date, interval, vampire_defaults)
        return

    @property
    def valid_from_date(self):
        """ Get date the output impact file is valid from. """
        return self.impl.valid_from_date
    @property
    def valid_to_date(self):
        """ Get date the output impact file is valid until. """
        return self.impl.valid_to_date


    def generate_header(self):
        """ Generate details related to VHI area impact that go in the config file header. """
        return self.impl.generate_header()

    def generate_config(self, hazard_file, hazard_dir, hazard_pattern,
                        boundary_file=None, boundary_dir=None, boundary_pattern=None, boundary_field=None,
                        output_file=None, output_dir=None, output_pattern=None, masked=False):
        """ Generate config file section for generating VCI.

        Generate config file entries required to create VHI area impact for the specified country, date and interval.

        :param hazard_file: File name of hazard image file.
        :type hazard_file: string
        :param hazard_dir: Directory where the hazard file is located.
        :type hazard_dir: string
        :param hazard_pattern: Regular expression pattern to used to find the hazard file for the product date.
        :type hazard_pattern: string
        :param boundary_file: Full path to the boundary file to use to calculate impact.
        :type boundary_file: string
        :param boundary_dir: Directory where the boundary file is located.
        :type boundary_dir: string
        :param boundary_pattern: Regular expression pattern to used to find the boundary file.
        :type boundary_pattern: string
        :param boundary_field: Field within the boundary file to use to identify areas.
        :type boundary_field: string
        :param output_filename: Filename for VHI area impact output file.
        :type output_filename: string
        :param output_dir: Directory to save the VHI area impact output file.
        :type output_dir: string
        :param output_pattern: Pattern to be used to generate the VHI area impact output file name. May refer to elements within the hazard_pattern.
        :type output_pattern: string
        :param masked: Flag indicating whether the impact should be masked by a boundary or not.
        :type masked: bool
        :return: Config file sections required for generating VHI area impact.
        :rtype: string
        """
        return self.impl.generate_config(hazard_file, hazard_dir, hazard_pattern,
                        boundary_file, boundary_dir, boundary_pattern, boundary_field,
                        output_file, output_dir, output_pattern)

    def generate_publish_config(self):
        """ Generate config section to publish Flood population impact.

        Generates configuration file section to publish the Flood population impact output file to a database.

        :return: Config file sections required for publishing Flood population impact.
        :rtype: string
        """
        return self.impl.generate_publish_config()

