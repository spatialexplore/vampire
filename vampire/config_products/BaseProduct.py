""" Data Products module.

    Provides classes for each data product supported within Vampire. New products should be added here.
"""
import VampireDefaults
import RainfallAnomalyProductImpl
import SPIProductImpl
import VCIProductImpl
import TCIProductImpl
import VHIProductImpl
import MODISEVILongtermAverageProductImpl
import MODISLSTLongtermAverageProductImpl
import CHIRPSLongtermAverageProductImpl
import DaysSinceLastRainProductImpl
import FloodForecastProductImpl
import logging
logger = logging.getLogger(__name__)

class BaseProduct(object):
    """ Base class for data product configuration objects.

    Manages registration of data product configurations and creation of data product configuration objects.
    Data product configurations provide the ability to generate config file sections related to the specific
    data product (e.g. product generation, publishing of data product to database or GIS server).

    """

    subclasses = {}

    @classmethod
    def register_subclass(cls, product_type):
        """ Register product with the product manager.

        Registers the data product identified by product_type with the data product manager.
        This allows the appropriate product to be created automatically when requested.

        :param product_type: Product name.
        :type product_type: string
        """
        def decorator(subclass):
            cls.subclasses[product_type] = subclass
            return subclass
        return decorator

    @classmethod
    def create(cls, product_type, country, product_date, interval, vampire_defaults=None):
        """ Create data product of the specified type.

        Creates the data product identified by product_type and sets required values.

        :param product_type: Product name.
        :type product_type: string
        :param country: Country data product will be created for. This is used for downloading data and identifying appropriate resources and default values during processing.
        :type country: string
        :param product_date: Date for product being generated.
        :type product_date: datetime
        :param interval: Interval for product generation - daily, weekly, monthly, seasonal.
        :type interval: string
        :param vampire_defaults:
        :type vampire_defaults: VampireDefaults
        :return: Data product object of type specified (a registered subclass of BaseProduct).
        """
        if product_type not in cls.subclasses:
            raise ValueError('Bad product type {}'.format(product_type))
        if vampire_defaults is None:
            vp = VampireDefaults.VampireDefaults()
        else:
            vp = vampire_defaults

        return cls.subclasses[product_type](country, product_date, interval, vp)

@BaseProduct.register_subclass('vci')
class VCIProduct(BaseProduct):
    """ Vegetation Condition Index data product configuration.

    Manages generation of configuration file sections for Vegetation Condition Index data products including product
    generation and publishing.

    """

    def __init__(self, country, product_date, interval, vampire_defaults):
        """ Initialisation of VCI data product.

        Initialises the VCI data product. Creates the implementation object which does the actual work of
        generating config file sections.

        :param country: Country data product will be created for. This is used for downloading data and identifying appropriate resources and default values during processing.
        :type country: string
        :param product_date: Date for product being generated.
        :type product_date: datetime
        :param interval: Interval for product generation - daily, weekly, monthly, seasonal.
        :type interval: string
        :param vampire_defaults:
        :type vampire_defaults: VampireDefaults
        """
        self.impl = VCIProductImpl.VCIProductImpl(country, product_date, interval, vampire_defaults)
        return

    @property
    def product_file(self):
        """ Get full path to the output product file name. """
        return self.impl.product_file
    @property
    def product_dir(self):
        """ Get directory name for product output. """
        return self.impl.product_dir
    @property
    def product_pattern(self):
        """ Get output product file name pattern (regular expression used to search for the product file). """
        return self.impl.product_pattern
    @property
    def valid_from_date(self):
        """ Get date the output product file is valid from. """
        return self.impl.valid_from_date
    @property
    def valid_to_date(self):
        """ Get date the output product file is valid until. """
        return self.impl.valid_to_date

    def generate_header(self):
        """ Generate details related to VCI that go in the config file header. """
        return self.impl.generate_header()

    def generate_config(self, evi_cur_file=None, evi_cur_dir=None, evi_cur_pattern=None,
                        evi_max_file=None, evi_max_dir=None, evi_max_pattern=None,
                        evi_min_file=None, evi_min_dir=None, evi_min_pattern=None,
                        output_filename=None, output_dir=None, output_pattern=None):
        """ Generate config file section for generating VCI.

        Generate config file entries required to create VCI for the specified country, date and interval.

        :param evi_cur_file: Enhanced Vegetation Index (EVI) file for the product date.
        :type evi_cur_file: string
        :param evi_cur_dir: Directory where the EVI file for the product date is located.
        :type evi_cur_dir: string
        :param evi_cur_pattern: Regular expression pattern to used to find the EVI file for the product date.
        :type evi_cur_pattern: string
        :param evi_max_file: EVI long-term maximum file.
        :type evi_max_file: string
        :param evi_max_dir: Directory where the long-term maximum EVI file is located.
        :type evi_max_dir: string
        :param evi_max_pattern: Regular expression pattern to used to find the EVI long-term maximum file.
        :type evi_max_pattern: string
        :param evi_min_file: EVI long-term minimum file.
        :type evi_min_file: string
        :param evi_min_dir: Directory where the long-term maximum EVI file is located.
        :type evi_min_dir: string
        :param evi_min_pattern: Regular expression pattern to used to find the EVI long-term minimum file.
        :type evi_min_pattern: string
        :param output_filename: Filename for VCI output file.
        :type output_filename: string
        :param output_dir: Directory to save the VCI output file.
        :type output_dir: string
        :param output_pattern: Pattern to be used to generate the VCI output file name. May refer to elements within the evi_cur_pattern.
        :type output_pattern: string
        :return: Config file sections required for generating VCI.
        :rtype: string
        """
        return self.impl.generate_config(evi_cur_file, evi_cur_dir, evi_cur_pattern, evi_max_file, evi_max_dir,
                                         evi_max_pattern, evi_min_file, evi_min_dir, evi_min_pattern, output_filename,
                                         output_dir, output_pattern)

@BaseProduct.register_subclass('tci')
class TCIProduct(BaseProduct):
    """ Temperature Condition Index data product configuration.

    Manages generation of configuration file sections for Temperature Condition Index data products including product
    generation.

    """

    def __init__(self, country, product_date, interval, vampire_defaults):
        """ Initialisation of TCI data product.

        Initialises the TCI data product. Creates the implementation object which does the actual work of
        generating config file sections.

        :param country: Country data product will be created for. This is used for downloading data and identifying appropriate resources and default values during processing.
        :type country: string
        :param product_date: Date for product being generated.
        :type product_date: datetime
        :param interval: Interval for product generation - daily, weekly, monthly, seasonal.
        :type interval: string
        :param vampire_defaults:
        :type vampire_defaults: VampireDefaults
        """
        self.impl = TCIProductImpl.TCIProductImpl(country, product_date, interval, vampire_defaults)
        return

    @property
    def product_file(self):
        """ Get full path to the output product file name. """
        return self.impl.product_file
    @property
    def product_dir(self):
        """ Get directory name for product output. """
        return self.impl.product_dir
    @property
    def product_pattern(self):
        """ Get output product file name pattern (regular expression used to search for the product file). """
        return self.impl.product_pattern
    @property
    def valid_from_date(self):
        """ Get date the output product file is valid from. """
        return self.impl.valid_from_date
    @property
    def valid_to_date(self):
        """ Get date the output product file is valid until. """
        return self.impl.valid_to_date

    def generate_header(self):
        """ Generate details related to TCI that go in the config file header. """
        return self.impl.generate_header()

    def generate_config(self, lst_cur_file=None, lst_cur_dir=None, lst_cur_pattern=None,
                        lst_max_file=None, lst_max_dir=None, lst_max_pattern=None,
                        lst_min_file=None, lst_min_dir=None, lst_min_pattern=None,
                        output_filename=None, output_dir=None, output_pattern=None):
        """ Generate config file section for generating VCI.

        Generate config file entries required to create VCI for the specified country, date and interval.

        :param lst_cur_file: Land Surface Temperature (LST) file for the product date.
        :type lst_cur_file: string
        :param lst_cur_dir: Directory where the LST file for the product date is located.
        :type lst_cur_dir: string
        :param lst_cur_pattern: Regular expression pattern to used to find the LST file for the product date.
        :type lst_cur_pattern: string
        :param lst_max_file: LST long-term maximum file.
        :type lst_max_file: string
        :param lst_max_dir: Directory where the long-term maximum LST file is located.
        :type lst_max_dir: string
        :param lst_max_pattern: Regular expression pattern to used to find the LST long-term maximum file.
        :type lst_max_pattern: string
        :param lst_min_file: LST long-term minimum file.
        :type lst_min_file: string
        :param lst_min_dir: Directory where the long-term maximum LST file is located.
        :type lst_min_dir: string
        :param lst_min_pattern: Regular expression pattern to used to find the LST long-term minimum file.
        :type lst_min_pattern: string
        :param output_filename: Filename for TCI output file.
        :type output_filename: string
        :param output_dir: Directory to save the TCI output file.
        :type output_dir: string
        :param output_pattern: Pattern to be used to generate the TCI output file name. May refer to elements within the lst_cur_pattern.
        :type output_pattern: string
        :return: Config file sections required for generating TCI.
        :rtype: string
        """
        return self.impl.generate_config(lst_cur_file, lst_cur_dir, lst_cur_pattern, lst_max_file, lst_max_dir,
                                         lst_max_pattern, lst_min_file, lst_min_dir, lst_min_pattern, output_filename,
                                         output_dir, output_pattern)

@BaseProduct.register_subclass('vhi')
class VHIProduct(BaseProduct):
    """ Vegetation Health Index data product configuration.

    Manages generation of configuration file sections for Vegetation Health Index data products including product
    generation, masking the product using a boundary, and publishing.

    """

    def __init__(self, country, product_date, interval, vampire_defaults):
        """ Initialisation of VHI data product.

        Initialises the VHI data product. Creates the implementation object which does the actual work of
        generating config file sections.

        :param country: Country data product will be created for. This is used for downloading data and identifying appropriate resources and default values during processing.
        :type country: string
        :param product_date: Date for product being generated.
        :type product_date: datetime
        :param interval: Interval for product generation - daily, weekly, monthly, seasonal.
        :type interval: string
        :param vampire_defaults:
        :type vampire_defaults: VampireDefaults
        """
        self.impl = VHIProductImpl.VHIProductImpl(country, product_date, interval, vampire_defaults)
        return

    @property
    def product_file(self):
        """ Get full path to the output product file name. """
        return self.impl.product_file
    @property
    def product_dir(self):
        """ Get directory name for product output. """
        return self.impl.product_dir
    @property
    def product_pattern(self):
        """ Get output product file name pattern (regular expression used to search for the product file). """
        return self.impl.product_pattern
    @property
    def valid_from_date(self):
        """ Get date the output product file is valid from. """
        return self.impl.valid_from_date
    @property
    def valid_to_date(self):
        """ Get date the output product file is valid until. """
        return self.impl.valid_to_date

    def generate_header(self):
        """ Generate details related to VHI that go in the config file header. """
        return self.impl.generate_header()

    def generate_config(self, tci_file=None, tci_dir=None, tci_pattern=None,
                        vci_file=None, vci_dir=None, vci_pattern=None,
                        output_file=None, output_dir=None, output_pattern=None,
                        reproject='TCI'):
        """ Generate config file section for generating VCI.

        Generate config file entries required to create VCI for the specified country, date and interval.

        :param tci_file: Temperature Condition Index (TCI) file for the product date.
        :type tci_file: string
        :param tci_dir: Directory where the TCI file for the product date is located.
        :type tci_dir: string
        :param tci_pattern: Regular expression pattern to used to find the TCI file for the product date.
        :type tci_pattern: string
        :param vci_file: Vegetation Condition Index (VCI) file for the product date.
        :type vci_file: string
        :param vci_dir: Directory where the VCI file is located.
        :type vci_dir: string
        :param vci_pattern: Regular expression pattern to used to find the VCI file for the product date.
        :type vci_pattern: string
        :param output_filename: Filename for VCI output file.
        :type output_filename: string
        :param output_dir: Directory to save the VCI output file.
        :type output_dir: string
        :param output_pattern: Pattern to be used to generate the VCI output file name. May refer to elements within the evi_cur_pattern.
        :type output_pattern: string
        :param reproject: Data source to use for output resolution. The output product file will be reprojected to match the specified source. Valid options are 'TCI' and 'VCI'. The default value is 'TCI'.
        :type reproject: string
        :return: Config file sections required for generating VHI.
        :rtype: string
        """
        return self.impl.generate_config(tci_file, tci_dir, tci_pattern, vci_file, vci_dir, vci_pattern,
                                         output_file, output_dir, output_pattern, reproject)

    def generate_mask_config(self, boundary_file=None, boundary_dir=None, boundary_pattern=None, boundary_field=None,
                        output_file=None, output_dir=None, output_pattern=None):
        """ Generate config section to mask VHI data product by a boundary.

        Generates configuration file section to mask the VHI output file using a shapefile boundary.

        :param boundary_file: Name of boundary file (shapefile) to use as mask.
        :type boundary_file: string
        :param boundary_dir: Directory where the TCI file for the product date is located.
        :type boundary_dir: string
        :param boundary_pattern: Regular expression pattern to used to find the boundary file.
        :type boundary_pattern: string
        :param boundary_field:
        :type boundary_field: string
        :param output_filename: Filename for masked VHI output file.
        :type output_filename: string
        :param output_dir: Directory to save the masked VHI output file.
        :type output_dir: string
        :param output_pattern: Pattern to be used to generate the masked VHI output file name.
        :type output_pattern: string
        :return: Config file sections required for generating VHI boundary mask.
        :rtype: string
        """
        return self.impl.generate_mask_config(boundary_file=boundary_file, boundary_dir=boundary_dir,
                                              boundary_pattern=boundary_pattern, boundary_field=boundary_field,
                                              output_file=output_file, output_dir=output_dir,
                                              output_pattern=output_pattern)

    def generate_publish_config(self):
        """ Generate config section to publish VHI data product.

        Generates configuration file section to publish the VHI output file to a GIS server.

        :return: Config file sections required for publishing VHI.
        :rtype: string
        """
        return self.impl.generate_publish_config()

@BaseProduct.register_subclass('rainfall_anomaly')
class RainfallAnomalyProduct(BaseProduct):
    """ Rainfall Anomaly data product configuration.

    Manages generation of configuration file sections for Rainfall Anomaly data products including product
    generation and publishing.

    """

    def __init__(self, country, product_date, interval, vampire_defaults):
        """ Initialisation of Rainfall Anomaly data product.

        Initialises the Rainfall Anomaly data product. Creates the implementation object which does the actual work of
        generating config file sections.

        :param country: Country data product will be created for. This is used for downloading data and identifying appropriate resources and default values during processing.
        :type country: string
        :param product_date: Date for product being generated.
        :type product_date: datetime
        :param interval: Interval for product generation - daily, weekly, monthly, seasonal.
        :type interval: string
        :param vampire_defaults:
        :type vampire_defaults: VampireDefaults
        """
        self.impl = RainfallAnomalyProductImpl.RainfallAnomalyProductImpl(country, product_date, interval, vampire_defaults)
        return

    def generate_header(self):
        """ Generate details related to Rainfall Anomaly that go in the config file header. """
        return self.impl.generate_header()


    def generate_config(self, output_dir=None, cur_file=None, cur_dir=None, cur_pattern=None,
                        lta_file=None, lta_dir=None, lta_pattern=None, output_file=None,
                        output_pattern=None):
        """ Generate config file section for generating Rainfall Anomaly.

        Generate config file entries required to create Rainfall Anomaly for the specified country, date and interval.

        :param output_dir: Directory to save the Rainfall Anomaly output file.
        :type output_dir: string
        :param cur_file: Precipitation file for the product date.
        :type cur_file: string
        :param cur_dir: Directory where the precipitation file for the product date is located.
        :type cur_dir: string
        :param cur_pattern: Regular expression pattern to used to find the precipitation file for the product date.
        :type cur_pattern: string
        :param lta_file: Long-term average precipitation file for the product date.
        :type lta_file: string
        :param lta_dir: Directory where the long-term average precipitation file is located.
        :type lta_dir: string
        :param lta_pattern: Regular expression pattern to used to find the long-term average precipitation file for the product date.
        :type lta_pattern: string
        :param output_filename: Filename for Rainfall Anomaly output file.
        :type output_filename: string
        :param output_pattern: Pattern to be used to generate the Rainfall Anomaly output file name. May refer to elements within the cur_pattern.
        :type output_pattern: string
        :return: Config file sections required for generating Rainfall Anomaly.
        :rtype: string
        """
        return self.impl.generate_config(output_dir, cur_file, cur_dir, cur_pattern,
                        lta_file, lta_dir, lta_pattern, output_file,
                        output_pattern)

@BaseProduct.register_subclass('spi')
class SPIProduct(BaseProduct):
    """ Standardized Precipitation Index data product configuration.

    Manages generation of configuration file sections for Standardized Precipitation Index data products including product
    generation and publishing.

    """

    def __init__(self, country, product_date, interval, vampire_defaults):
        """ Initialisation of SPI data product.

        Initialises the SPI data product. Creates the implementation object which does the actual work of
        generating config file sections.

        :param country: Country data product will be created for. This is used for downloading data and identifying appropriate resources and default values during processing.
        :type country: string
        :param product_date: Date for product being generated.
        :type product_date: datetime
        :param interval: Interval for product generation - daily, weekly, monthly, seasonal.
        :type interval: string
        :param vampire_defaults:
        :type vampire_defaults: VampireDefaults
        """
        self.impl = SPIProductImpl.SPIProductImpl(country, product_date, interval, vampire_defaults)
        return

    def generate_header(self):
        """ Generate details related to SPI that go in the config file header. """
        return self.impl.generate_header()

    def generate_config(self, output_dir=None, cur_file=None, cur_dir=None, cur_pattern=None,
                        lta_file=None, lta_dir=None, lta_pattern=None, ltsd_file=None, ltsd_dir=None,
                        ltsd_pattern=None, output_file=None, output_pattern=None):
        """ Generate config file section for generating Standardized Precipitation Index (SPI).

        Generate config file entries required to create SPI for the specified country, date and interval.

        :param output_dir: Directory to save the SPI output file.
        :type output_dir: string
        :param cur_file: Precipitation file for the product date.
        :type cur_file: string
        :param cur_dir: Directory where the precipitation file for the product date is located.
        :type cur_dir: string
        :param cur_pattern: Regular expression pattern to used to find the precipitation file for the product date.
        :type cur_pattern: string
        :param lta_file: Long-term average precipitation file for the product date.
        :type lta_file: string
        :param lta_dir: Directory where the long-term average precipitation file is located.
        :type lta_dir: string
        :param lta_pattern: Regular expression pattern to used to find the long-term average precipitation file for the product date.
        :type lta_pattern: string
        :param ltsd_file: Long-term standard deviation precipitation file for the product date.
        :type ltsd_file: string
        :param ltsd_dir: Directory where the long-term standard deviation precipitation file is located.
        :type ltsd_dir: string
        :param ltsd_pattern: Regular expression pattern to used to find the long-term standard deviation precipitation file for the product date.
        :type ltsd_pattern: string
        :param output_file: Filename for SPI output file.
        :type output_file: string
        :param output_pattern: Pattern to be used to generate the SPI output file name. May refer to elements within the cur_pattern.
        :type output_pattern: string
        :return: Config file sections required for generating SPI.
        :rtype: string
        """
        return self.impl.generate_config(output_dir, cur_file, cur_dir, cur_pattern,
                        lta_file, lta_dir, lta_pattern, ltsd_file, ltsd_dir, ltsd_pattern,
                        output_file, output_pattern)

@BaseProduct.register_subclass('evi_longterm_average')
class MODISEVILongtermAverageProduct(BaseProduct):
    """ MODIS Enhanced Vegetation Index Long-term Average data product configuration.

    Manages generation of configuration file sections for MODIS Enhanced Vegetation Index Long-term Average data products including product
    generation.

    """

    def __init__(self, country, product_date, interval, vampire_defaults):
        """ Initialisation of MODIS EVI long-term average data product.

        Initialises the MODIS EVI long-term average data product. Creates the implementation object which does the actual work of
        generating config file sections.

        :param country: Country data product will be created for. This is used for downloading data and identifying appropriate resources and default values during processing.
        :type country: string
        :param product_date: Date for product being generated.
        :type product_date: datetime
        :param interval: Interval for product generation - daily, weekly, monthly, seasonal.
        :type interval: string
        :param vampire_defaults:
        :type vampire_defaults: VampireDefaults
        """
        self.impl = MODISEVILongtermAverageProductImpl.MODISEVILongtermAverageProductImpl(country, product_date, interval, vampire_defaults)
        return

    def generate_header(self):
        """ Generate details related to MODIS EVI long-term average that go in the config file header. """
        return self.impl.generate_header()

    def generate_config(self, input_dir=None, output_dir=None, input_pattern=None,
                        output_pattern=None, functions=None, download=True):
        """ Generate config file section for generating long-term statistics for MODIS EVI data.

        Generate config file entries required to create long-term statistics for MODIS Enhanced Vegetation Index
        (EVI) for the specified country and interval. Statistics include average, minimum, maximum, standard deviation.

        :param input_dir: Directory where the MODIS EVI files are located.
        :type input_dir: string
        :param output_dir: Directory to save the SPI output file.
        :type output_dir: string
        :param input_pattern: Regular expression pattern to used to find the files to be included in the long-term statistics calculations.
        :type input_pattern: string
        :param output_pattern: Pattern to be used to generate the EVI statistics output file name. May refer to elements within the input_pattern.
        :type output_pattern: string
        :param functions: List of functions to be calculated. Options are 'AVG', 'MIN', 'MAX', 'STD'.
        :type functions: string
        :param download: Flag specifying whether the data needs to be downloaded first. If true, appropriate download configuration sections will be generated.
        :type download: bool
        :return: Config file sections required for generating MODIS EVI long-term statistics.
        :rtype: string
        """
        return self.impl.generate_config(input_dir=input_dir, output_dir=output_dir, input_pattern=input_pattern,
                        output_pattern=output_pattern, functions=functions, download=download)


@BaseProduct.register_subclass('lst_longterm_average')
class MODISLSTLongtermAverageProduct(BaseProduct):
    """ MODIS Land Surface Temperature Long-term Average data product configuration.

    Manages generation of configuration file sections for MODIS Land Surface Temperature Long-term Average data products including product
    generation and publishing.

    """

    def __init__(self, country, product_date, interval, vampire_defaults):
        """ Initialisation of MODIS LST long-term average data product.

        Initialises the MODIS LST long-term average data product. Creates the implementation object which does the actual work of
        generating config file sections.

        :param country: Country data product will be created for. This is used for downloading data and identifying appropriate resources and default values during processing.
        :type country: string
        :param product_date: Date for product being generated.
        :type product_date: datetime
        :param interval: Interval for product generation - daily, weekly, monthly, seasonal.
        :type interval: string
        :param vampire_defaults:
        :type vampire_defaults: VampireDefaults
        """
        self.impl = MODISLSTLongtermAverageProductImpl.MODISLSTLongtermAverageProductImpl(country, product_date, interval, vampire_defaults)
        return

    def generate_header(self):
        """ Generate details related to LST long-term average that go in the config file header. """
        return self.impl.generate_header()

    def generate_config(self, input_dir=None, output_dir=None, input_pattern=None,
                        output_pattern=None, functions=None, download=True):
        """ Generate config file section for generating MODIS LST long-term statistics.

        Generate config file entries required to create long-term statistics from MODIS Land Surface Temperature data for the specified country, date and interval.

        :param input_dir: Directory where the MODIS LST files are located.
        :type input_dir: string
        :param output_dir: Directory to save the long-term statistics output files.
        :type output_dir: string
        :param input_pattern: Regular expression pattern to used to find the files to be included in the long-term statistics calculations.
        :type input_pattern: string
        :param output_pattern: Pattern to be used to generate the LST statistics output file name. May refer to elements within the input_pattern.
        :type output_pattern: string
        :param functions: List of functions to be calculated. Options are 'AVG', 'MIN', 'MAX', 'STD'.
        :type functions: string
        :param download: Flag specifying whether the data needs to be downloaded first. If true, appropriate download configuration sections will be generated.
        :type download: bool
        :return: Config file sections required for generating MODIS LST long-term averages.
        :rtype: string
        """
        return self.impl.generate_config(input_dir=input_dir, output_dir=output_dir, input_pattern=input_pattern,
                        output_pattern=output_pattern, functions=functions, download=download)


@BaseProduct.register_subclass('chirps_longterm_average')
class CHIRPSLongtermAverageProduct(BaseProduct):
    """ CHIRPS long-term statistics data product configuration.

    Manages generation of configuration file sections for CHIRPS long-term statistics data products.

    """

    def __init__(self, country, product_date, interval, vampire_defaults):
        """ Initialisation of CHIRPS long-term statistics data product.

        Initialises the CHIRPS long-term statistics data product. Creates the implementation object which does the actual work of
        generating config file sections.

        :param country: Country data product will be created for. This is used for downloading data and identifying appropriate resources and default values during processing.
        :type country: string
        :param product_date: Date for product being generated.
        :type product_date: datetime
        :param interval: Interval for product generation - daily, weekly, monthly, seasonal.
        :type interval: string
        :param vampire_defaults:
        :type vampire_defaults: VampireDefaults
        """
        self.impl = CHIRPSLongtermAverageProductImpl.CHIRPSLongtermAverageProductImpl(country, product_date, interval, vampire_defaults)
        return

    def generate_header(self):
        """ Generate details related to CHIRPS long-term statistics that go in the config file header. """
        return self.impl.generate_header()

    def generate_config(self, input_dir=None, output_dir=None, input_pattern=None,
                        output_pattern=None, functions=None, download=True):
        """ Generate config file section for generating CHIRPS long-term statistics.

        Generate config file entries required to create long-term statistics from CHIRPS rainfall data for the specified country, date and interval.

        :param input_dir: Directory where the CHIRPS precipitation files are located.
        :type input_dir: string
        :param output_dir: Directory to save the CHIRPS long-term statistics output file(s).
        :type output_dir: string
        :param input_pattern: Regular expression pattern to used to find the files to be included in the long-term statistics calculations.
        :type input_pattern: string
        :param output_pattern: Pattern to be used to generate the long-term statistics output file name(s). May refer to elements within the input_pattern.
        :type output_pattern: string
        :param functions: List of functions to be calculated. Options are 'AVG', 'MIN', 'MAX', 'STD'.
        :type functions: string
        :param download: Flag specifying whether the data needs to be downloaded first. If true, appropriate download configuration sections will be generated.
        :type download: bool
        :return: Config file sections required for generating CHIRPS long-term statistics.
        :rtype: string
        """
        return self.impl.generate_config(input_dir=input_dir, output_dir=output_dir, input_pattern=input_pattern,
                        output_pattern=output_pattern, functions=functions, download=download)

@BaseProduct.register_subclass('days_since_last_rain')
class DaysSinceLastRainProduct(BaseProduct):
    """ Days Since Last Rain data product configuration.

    Manages generation of configuration file sections for Days Since Last Rain data products including product
    generation and publishing.

    """

    def __init__(self, country, product_date, interval, vampire_defaults):
        """ Initialisation of Days Since Last Rain data product.

        Initialises the Days Since Last Rain data product. Creates the implementation object which does the actual work of
        generating config file sections.

        :param country: Country data product will be created for. This is used for downloading data and identifying appropriate resources and default values during processing.
        :type country: string
        :param product_date: Date for product being generated.
        :type product_date: datetime
        :param interval: Interval for product generation - daily, weekly, monthly, seasonal.
        :type interval: string
        :param vampire_defaults:
        :type vampire_defaults: VampireDefaults
        """
        self.impl = DaysSinceLastRainProductImpl.DaysSinceLastRainProductImpl(country, product_date, interval, vampire_defaults)
        return

    @property
    def product_file(self):
        """ Get full path to the output product file name. """
        return self.impl.product_file
    @property
    def product_dir(self):
        """ Get directory name for product output. """
        return self.impl.product_dir
    @property
    def product_pattern(self):
        """ Get output product file name pattern (regular expression used to search for the product file). """
        return self.impl.product_pattern
    @property
    def valid_from_date(self):
        """ Get date the output product file is valid from. """
        return self.impl.valid_from_date
    @property
    def valid_to_date(self):
        """ Get date the output product file is valid until. """
        return self.impl.valid_to_date

    def generate_header(self):
        """ Generate details related to Days Since Last Rain that go in the config file header. """
        return self.impl.generate_header()

    def generate_config(self, data_dir=None, output_dir=None, file_pattern=None,
                        threshold=None, max_days=None, download=True, crop=True, crop_dir=None):
        """ Generate a config file process for the Days Since Last Rain product.

        Generate VAMPIRE config file processes for the product including download and crop if specified.

        :param data_dir: Directory path for precipitation files. Default is None.
        :type data_dir: string
        :param output_dir: Path for product output. If the output_dir is None, the VAMPIRE default Days Since Last Rain product directory will be used.
        :type output_dir: string
        :param file_pattern: Regular expression pattern for finding current precipitation file. Default is None.
        :type file_pattern: string
        :param threshold: Rainfall threshold value.
        :type threshold: float
        :param max_days: Number of days to evaluate for days since last rain.
        :type max_days: int
        :param download: Flag indicating whether data should be downloaded.
        :type download: bool
        :param crop: Flag indicating whether data should be cropped to a boundary.
        :type crop: bool
        :param crop_dir: Directory for output of cropped files.
        :type crop_dir: string

        :return: Returns string containing the configuration file process.
        :rtype: string
        """
        return self.impl.generate_config(data_dir=data_dir, output_dir=output_dir, file_pattern=file_pattern,
                                         threshold=threshold, max_days=max_days, download=download,
                                         crop=crop, crop_dir=crop_dir)


@BaseProduct.register_subclass('flood_forecast')
class FloodForecastProduct(BaseProduct):
    """ Flood Forecast data product configuration.

    Manages generation of configuration file sections for Flood Forecast data products including product
    generation and publishing.

    """

    def __init__(self, country, product_date, interval, vampire_defaults):
        """ Initialisation of Flood Forecast data product.

        Initialises the Flood Forecast data product. Creates the implementation object which does the actual work of
        generating config file sections.

        :param country: Country data product will be created for. This is used for downloading data and identifying appropriate resources and default values during processing.
        :type country: string
        :param product_date: Date for product being generated.
        :type product_date: datetime
        :param interval: Interval for product generation - daily, weekly, monthly, seasonal.
        :type interval: string
        :param vampire_defaults:
        :type vampire_defaults: VampireDefaults
        """
        self.impl = FloodForecastProductImpl.FloodForecastProductImpl(country, product_date, interval, vampire_defaults)
        return

    @property
    def valid_from_date(self):
        """ Get date the output product file is valid from. """
        return self.impl.valid_from_date
    @property
    def valid_to_date(self):
        """ Get date the output product file is valid until. """
        return self.impl.valid_to_date
    @property
    def product_file(self):
        """ Get full path to the output product file name. """
        return self.impl.product_file
    @property
    def product_dir(self):
        """ Get directory name for product output. """
        return self.impl.product_dir
    @property
    def product_pattern(self):
        """ Get output product file name pattern (regular expression used to search for the product file). """
        return self.impl.product_pattern

    def generate_header(self):
        """ Generate details related to Flood Forecast that go in the config file header. """
        return self.impl.generate_header()

    def generate_config(self, data_dir=None, output_dir=None, file_pattern=None,
                        days=None):
        """ Generate config file section for generating Flood Forecasts.

        Generate config file entries required to create Flood Forecasts for the specified country, date and interval.

        :param data_dir: Directory where the GFS files for the product date are located.
        :type data_dir: string
        :param output_dir: Directory to save the Flood Forecast output files.
        :type output_dir: string
        :param file_pattern: Regular expression pattern to used to find the GFS file for the product date.
        :type file_pattern: string
        :param days: Number of days to forecast for.
        :type days: int
        :return: Config file sections required for generating Flood Forecasts.
        :rtype: string
        """
        return self.impl.generate_config(data_dir=data_dir, output_dir=output_dir, file_pattern=file_pattern,
                                         accumulate_days=days)

    def generate_publish_config(self):
        """ Generate config section to publish Flood Forecast data product.

        Generates configuration file section to publish the Flood Forecast output file to a GIS server.

        :return: Config file sections required for publishing Flood Forecasts.
        :rtype: string
        """
        return self.impl.generate_publish_config()

