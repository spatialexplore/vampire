""" CHIRPS data handling.

    Provides classes for downloading and processing CHIRPS data.
"""
import RasterDatasetImpl
import datetime
import dateutil.rrule
import dateutil.relativedelta
import os
import logging
logger = logging.getLogger(__name__)

class CHIRPSDatasetImpl(RasterDatasetImpl.RasterDatasetImpl):
    """ CHIRPS data

    Data handling for CHIRPS data

    """

    def __init__(self, interval, product_date, vampire_defaults, region=None):
        """ Initialise CHIRPSDatasetImpl object.

        Implementation class for CHIRPSDataset.
        Initialise object parameters and calculate start and end dates for dataset using product_date and interval.

        :param interval: Data interval to retrieve/manage. Can be daily, pentad, dekad, monthly or seasonal
        :type interval: string
        :param product_date: Data acquisition date. For pentad/dekad data, the data is actually for the period immediately preceding
            the product_date. For monthly data, the data covers the month given in the product date. For seasonal data,
            the product_date refers to the start of the season (3 month period).
        :type product_date: datetime
        :param vampire_defaults:
        :type vampire_defaults: VampireDefaults
        :param region: Default is None.
        """
        logger.debug('Initialising CHIRPS dataset')
        super(CHIRPSDatasetImpl, self).__init__()
        self.interval = interval
        self.product_date = product_date
        self.vp = vampire_defaults
        self.region = region

        if self.interval.lower() == 'daily':
            self.start_date = product_date
            self.end_date = product_date
        elif self.interval.lower() == 'dekad':
            self.start_date = product_date + datetime.timedelta(days=-10)
            self.end_date = product_date
        elif self.interval.lower() == 'monthly':
            self.start_date = datetime.datetime(product_date.year, product_date.month, 1) # ensure start date is first day of month
            self.end_date = self.start_date + dateutil.relativedelta.relativedelta(months=1,days=-1) # ensure end_date is last day of month
        elif self.interval.lower() == 'seasonal':
            self.start_date = product_date
            self.end_date = self.start_date + dateutil.relativedelta.relativedelta(months=3, days=-1) # set end_date as last day of third month
        else:
            logger.error("Interval '{0}' is not a valid CHIRPS dataset interval".format(self.interval))
            raise ValueError
#        self.start_date = params['start_date']
#        self.country = params['country']
        return

    @property
    def start_date(self):
        """ Get and set start date of dataset. """
        return self.__start_date
    @start_date.setter
    def start_date(self, sd):
        self.__start_date = sd

    @property
    def end_date(self):
        """ Get and set end date of dataset. """
        return self.__end_date
    @end_date.setter
    def end_date(self, ed):
        self.__end_date = ed

    def generate_config(self, data_dir=None, download=True, crop=True, crop_dir=None):
        """ Generate a config file process for the dataset.

        Generate VAMPIRE config file process(es) for the dataset including download and crop if specified.

        :param data_dir: Path for downloaded data. The data will be stored in this path under a directory with the interval name. If the
            data_dir is None, the VAMPIRE default download directory will be used.
        :type data_dir: string
        :param download: Flag indicating whether data should be downloaded. Default is True.
        :type download: bool
        :param crop: Flag indicating whether data should be cropped to region. Default is True.
        :type crop: bool
        :param crop_dir: Path where cropped data will be stored. If None, the region code will be appended to the download data path.
        :type crop_dir: string

        :return: string containing the configuration file process.
        """
        logger.debug('CHIRPSDataset generate_config')
        config = ''
        if data_dir is None:
            _data_dir = self.vp.get('CHIRPS', 'data_dir')
        else:
            _data_dir = data_dir
        _download_dir = "{0}\\{1}".format(_data_dir, self.interval.capitalize())

        _output_dir = _download_dir

        if download:
            config += self._generate_download_section(data_dir=_download_dir)

        if crop:
            _country_code = self.vp.get_country_code(self.region)
            if crop_dir is None:
                _crop_dir = os.path.join(_download_dir, _country_code.upper())
            else:
                _crop_dir = crop_dir

            if self.region is not None and self.region.lower() is not 'global':
                # self.region should contain country name
                config += """
        # Crop data to {country}""".format(country=self.region)
                _input_pattern = self.vp.get('CHIRPS', 'global_{0}_pattern'.format(self.interval))
                _output_pattern = '{0}{1}'.format(self.vp.get_country_code(self.region).lower(),
                                                  self.vp.get('CHIRPS',
                                                              'crop_regional_output_{0}_pattern'.format(self.interval)))
                _boundary_file = self.vp.get_country('{0}'.format(self.region))['chirps_boundary_file']
                config += self.generate_crop_section(_download_dir, _crop_dir, _input_pattern, _output_pattern, _boundary_file)
                _output_dir = _crop_dir
        return config, _output_dir


    def generate_header(self):
        """ Generate VAMPIRE config file header for CHIRPS datasets.

            :return: string containing config file header section.
        """
        config = """
temp: {temp_dir}

CHIRPS:
    filenames:
        input_prefix: chirps-v2.0
        input_extension: .tiff
        output_prefix: idn_cli_chirps-v2.0
        output_ext: .tif
""".format(temp_dir=self.vp.get('directories', 'temp_dir'))
        return config

    def _generate_download_section(self, data_dir):
        """ Generate download process section for CHIRPS dataset.

        Generate VAMPIRE config file section for CHIRPS dataset download.

        :param data_dir: Path for downloaded data. The data will be stored in this path under a directory with the interval name. If the
            data_dir is None, the VAMPIRE default download directory will be used.
        :type data_dir: string
        :return: string containing config file download section.
        """
        config = """
    # download CHIRPS precipitation data
    - process: CHIRPS
      type: download
      interval: {interval}
      output_dir: {output_dir}""".format(interval=self.interval, output_dir=data_dir)
        # if start and end dates are specified, only download between these dates
        if self.product_date is not None:
            year = self.start_date.strftime("%Y")
            month = self.start_date.strftime("%m")
            # use 1st of start_date month to make sure end month is also included
            _first_date = self.start_date.replace(self.start_date.year, self.start_date.month, 1)
            dates = dateutil.rrule.rrule(dateutil.rrule.MONTHLY, dtstart=_first_date).between(_first_date,
                                                                                              self.end_date, inc=True)
            config += """
      dates: ["""
            for d in dates:
                config += '{year}-{month},'.format(year=d.strftime("%Y"), month=d.strftime("%m"))
            config = config[:-1]
            config += """]
            """
        return config
