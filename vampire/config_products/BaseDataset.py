""" Dataset module.

    Provides classes for each dataset supported within Vampire. New datasets should be added here.
"""
import CHIRPSDatasetImpl
import MODISEVIDatasetImpl
import MODISLSTDatasetImpl
import IMERGDatasetImpl
import GlobalForecastSystemDatasetImpl
import logging
logger = logging.getLogger(__name__)

class BaseDataset(object):
    """ Base class for dataset configuration objects.

    Manages registration of dataset configurations and creation of dataset configuration objects.
    Dataset configurations provide the ability to generate config file sections related to the specific
    dataset (e.g. data download, pre-processing).

    """

    subclasses = {}

    @classmethod
    def register_subclass(cls, dataset_type):
        """ Register dataset with the dataset manager.

        Registers the dataset identified by datset_type with the dataset manager.
        This allows the appropriate dataset to be created automatically when requested.

        :param dataset_type: Dataset name.
        :type dataset_type: string
        """
        def decorator(subclass):
            cls.subclasses[dataset_type] = subclass
            return subclass
        return decorator

    @classmethod
    def create(cls, dataset_type, interval, product_date, vampire_defaults, region=None):
        """ Create dataset of the specified type.

        Creates the dataset identified by dataset_type and sets required values.

        :param dataset_type: Dataset name.
        :type dataset_type: string
        :param interval: Interval for dataset generation - daily, weekly, monthly, seasonal.
        :type interval: string
        :param product_date: Date for dataset being generated.
        :type product_date: datetime
        :param vampire_defaults:
        :type vampire_defaults: VampireDefaults
        :param region: Default is None
        :type region: string
        :return: Dataset object of type specified (a registered subclass of BaseDataset).
        """
        if dataset_type not in cls.subclasses:
            logger.debug('Bad dataset type {}'.format(dataset_type))
            raise ValueError('Bad dataset type {}'.format(dataset_type))

        return cls.subclasses[dataset_type](interval, product_date, vampire_defaults, region)

@BaseDataset.register_subclass('CHIRPS')
class CHIRPSDataset(BaseDataset):
    """ CHIRPS dataset configuration.

    Manages generation of configuration file sections for CHIRPS datasets including download and cropping.

    """

    def __init__(self, interval, product_date, vampire_defaults, region=None):
        """ Initialisation of CHIRPS dataset.

        Initialises the CHIRPS dataset. Creates the implementation object which does the actual work of
        generating config file sections.

        :param interval: Interval for product generation - daily, weekly, monthly, seasonal.
        :type interval: string
        :param product_date: Date for product being generated.
        :type product_date: datetime
        :param vampire_defaults:
        :type vampire_defaults: VampireDefaults
        :param region: Default is None
        :type region: string
        """
        self.impl = CHIRPSDatasetImpl.CHIRPSDatasetImpl(interval, product_date, vampire_defaults, region)
        return

    def generate_header(self):
        """ Generate details related to CHIRPS that go in the config file header. """
        return self.impl.generate_header()

    def generate_config(self, data_dir=None, download=True, crop=True, crop_dir=None):
        """ Generate config file section for generating VCI.

        Generate config file entries required to create VCI for the specified country, date and interval.

        :param data_dir: Path of directory data should be downloaded to.
        :type data_dir: string
        :param download: Flag indicating if data should be downloaded.
        :type download: bool
        :param crop: Flag indicating if data should be cropped following download.
        :type crop: bool
        :param crop_dir: Path of directory for cropped data output.
        :type crop_dir: string
        :return: Config file sections required for retrieving CHIRPS data.
        :rtype: string
        """
        return self.impl.generate_config(data_dir, download, crop, crop_dir)

    def start_date(self):
        """ Get or set start date of data in dataset. """
        return self.impl.start_date
    def set_start_date(self, sd):
        self.impl.start_date = sd
    def end_date(self):
        """ Get or set end date of data in dataset. """
        return self.impl.end_date
    def set_end_date(self, sd):
        self.impl.end_date = sd

@BaseDataset.register_subclass('IMERG')
class IMERGDataset(BaseDataset):
    def __init__(self, interval, product_date, vampire_defaults, region=None):
        """ Initialisation of IMERG dataset.

        Initialises the IMERG dataset. Creates the implementation object which does the actual work of
        generating config file sections.

        :param interval: Interval for product generation - daily, weekly, monthly, seasonal.
        :type interval: string
        :param product_date: Date for product being generated.
        :type product_date: datetime
        :param vampire_defaults:
        :type vampire_defaults: VampireDefaults
        :param region: Default is None
        :type region: string
        """
        self.impl = IMERGDatasetImpl.IMERGDatasetImpl(interval, product_date, vampire_defaults, region)
        return

    def start_date(self):
        """ Get or set start date of data in dataset. """
        return self.impl.start_date
    def set_start_date(self, sd):
        self.impl.start_date = sd

    def end_date(self):
        """ Get or set end date of data in dataset. """
        return self.impl.end_date
    def set_end_date(self, sd):
        self.impl.end_date = sd

    def generate_header(self):
        """ Generate details related to IMERG data that go in the config file header. """
        return self.impl.generate_header()

    def generate_config(self, data_dir=None, download=True, mosaic_dir=None, tiles=None, extract_dir=None,
                        crop=True, crop_dir=None):
        """ Generate config file section for generating IMERG.

        Generate config file entries required to create IMERG for the specified country, date and interval.

        :param data_dir: Path of directory data should be downloaded to.
        :type data_dir: string
        :param download: Flag indicating if data should be downloaded.
        :type download: bool
        :param mosaic_dir: Path of directory for mosaic of downloaded data tiles.
        :type mosaic_dir: string
        :param tiles: List of data tiles to download.
        :type tiles: string
        :param extract_dir: Path of directory for extracted dataset.
        :type extract_dir: string
        :param crop: Flag indicating if data should be cropped following download.
        :type crop: bool
        :param crop_dir: Path of directory for cropped data output.
        :type crop_dir: string
        :return: Config file sections required for retrieving IMERG data.
        :rtype: string
        """
        return self.impl.generate_config(data_dir=data_dir, download=download, crop=crop, crop_dir=crop_dir)



@BaseDataset.register_subclass('MODIS_EVI')
class MODISEVIDataset(BaseDataset):
    def __init__(self, interval, product_date, vampire_defaults, region=None):
        """ Initialisation of MODIS EVI dataset.

        Initialises the MODIS Enhanced Vegetation Index dataset. Creates the implementation object which does the actual work of
        generating config file sections.

        :param interval: Interval for product generation - daily, weekly, monthly, seasonal.
        :type interval: string
        :param product_date: Date for product being generated.
        :type product_date: datetime
        :param vampire_defaults:
        :type vampire_defaults: VampireDefaults
        :param region: Default is None
        """
        self.impl = MODISEVIDatasetImpl.MODISEVIDatasetImpl(interval, product_date, vampire_defaults, region)
        return

    def start_date(self):
        """ Get or set start date of data in dataset. """
        return self.impl.start_date
    def set_start_date(self, sd):
        self.impl.start_date = sd

    def end_date(self):
        """ Get or set end date of data in dataset. """
        return self.impl.end_date
    def set_end_date(self, sd):
        self.impl.end_date = sd


    def generate_config(self, data_dir=None, download=True, mosaic_dir=None, tiles=None, extract_dir=None,
                        crop=True, crop_dir=None):
        """ Generate config file section for generating MODIS EVI.

        Generate config file entries required to download MODIS EVI for the country, date and interval specified in the dataset initialization.

        :param data_dir: Path of directory data should be downloaded to.
        :type data_dir: string
        :param download: Flag indicating if data should be downloaded. Default is True.
        :type download: bool
        :param mosaic_dir: Path of directory for mosaic of downloaded data tiles.
        :type mosaic_dir: string
        :param tiles: List of data tiles to download.
        :type tiles: string
        :param extract_dir: Path of directory for extracted dataset.
        :type extract_dir: string
        :param crop: Flag indicating if data should be cropped following download.
        :type crop: bool
        :param crop_dir: Path of directory for cropped data output.
        :type crop_dir: string
        :return: Config file sections required for retrieving IMERG data.
        :rtype: string
        """
        return self.impl.generate_config(data_dir=data_dir, download=download, mosaic_dir=mosaic_dir,
                                         tiles=tiles, extract_dir=extract_dir, crop=crop, crop_dir=crop_dir)

@BaseDataset.register_subclass('MODIS_LST')
class MODISLSTDataset(BaseDataset):
    def __init__(self, interval, product_date, vampire_defaults, region=None):
        """ Initialisation of MODIS LST dataset.

        Initialises the MODIS Land Surface Temperature dataset. Creates the implementation object which does the actual work of
        generating config file sections.

        :param interval: Interval for product generation - daily, weekly, monthly, seasonal.
        :type interval: string
        :param product_date: Date for product being generated.
        :type product_date: datetime
        :param vampire_defaults:
        :type vampire_defaults: VampireDefaults
        :param region: Default is None
        """
        self.impl = MODISLSTDatasetImpl.MODISLSTDatasetImpl(interval, product_date, vampire_defaults, region)
        return


    def generate_config(self, data_dir=None, download=True, mosaic_dir=None, tiles=None, extract_dir=None,
                        crop=True, crop_dir=None):
        """ Generate config file section for downloading MODIS Land Surface Temperature dataset.

        Generate config file entries required to create MODIS LST for the country, date and interval specified in the dataset initialization.

        :param data_dir: Path of directory data should be downloaded to.
        :type data_dir: string
        :param download: Flag indicating if data should be downloaded.
        :type download: bool
        :param mosaic_dir: Path of directory for mosaic of downloaded data tiles.
        :type mosaic_dir: string
        :param tiles: List of data tiles to download.
        :type tiles: string
        :param extract_dir: Path of directory for extracted dataset.
        :type extract_dir: string
        :param crop: Flag indicating if data should be cropped following download.
        :type crop: bool
        :param crop_dir: Path of directory for cropped data output.
        :type crop_dir: string
        :return: Config file sections required for retrieving IMERG data.
        :rtype: string
        """
        return self.impl.generate_config(data_dir=data_dir, download=download, mosaic_dir=mosaic_dir,
                                         tiles=tiles, crop=crop, crop_dir=crop_dir)
    @property
    def product(self):
        """ Get or set name of dataset. """
        return self.impl.product

    @product.setter
    def product(self, product):
        self.impl.product = product

    def start_date(self):
        """ Get or set start date of data in dataset. """
        return self.impl.start_date
    def set_start_date(self, start_date):
        self.impl.start_date = start_date

    def end_date(self):
        """ Get or set end date of data in dataset. """
        return self.impl.end_date
    def set_end_date(self, end_date):
        self.impl.end_date = end_date


@BaseDataset.register_subclass('GFS')
class GlobalForecastSystemDataset(BaseDataset):
    def __init__(self, interval, product_date, vampire_defaults, region=None):
        """ Initialisation of Global Forecast System dataset.

        Initialises the Global Forecast System dataset. Creates the implementation object which does the actual work of
        generating config file sections.

        :param interval: Interval for product generation - daily, weekly, monthly, seasonal.
        :type interval: string
        :param product_date: Date for product being generated.
        :type product_date: datetime
        :param vampire_defaults:
        :type vampire_defaults: VampireDefaults
        :param region: Default is None
        """
        self.impl = GlobalForecastSystemDatasetImpl.GlobalForecastSystemDatasetImpl(interval, product_date, vampire_defaults, region)
        return

    def start_date(self):
        """ Get or set start date of data in dataset. """
        return self.impl.start_date
    def set_start_date(self, sd):
        self.impl.start_date = sd
    def end_date(self):
        """ Get or set end date of data in dataset. """
        return self.impl.end_date
    def set_end_date(self, sd):
        self.impl.end_date = sd


    def generate_config(self, data_dir=None, variable=None, level=None, forecast_hr=None, download=True,
                        crop=True, crop_dir=None, accumulate_days=None):
        """ Generate config file section for downloading and pre-processing Global Forecast System models.

        Generate config file entries required to create GFS data for the country, date and interval specified in the dataset initialization.

        :param data_dir: Path of directory data should be downloaded to.
        :type data_dir: string
        :param variable: Model variable to download.
        :type variable: string
        :param level: Data level (e.g. surface).
        :type: string
        :param forecast_hr: Hour of forecast.
        :type string:
        :param download: Flag indicating if data should be downloaded.
        :type download: bool
        :param crop: Flag indicating if data should be cropped following download.
        :type crop: bool
        :param crop_dir: Path of directory for cropped data output.
        :type crop_dir: string
        :param accumulate_days: Number of days to accumulate.
        :type accumulate_days: int
        :return: Config file sections required for retrieving GFS data.
        :rtype: string
        """
        return self.impl.generate_config(data_dir=data_dir, variable=variable, level=level, forecast_hr=forecast_hr,
                                         download=download, crop=crop, crop_dir=crop_dir, accumulate_days=accumulate_days)
