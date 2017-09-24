import RasterDatasetImpl
import datetime
import dateutil.rrule
import dateutil.relativedelta
import os
import logging
logger = logging.getLogger(__name__)

class IMERGDatasetImpl(RasterDatasetImpl.RasterDatasetImpl):
    """ Initialise IMERGDatasetImpl object.

    Implementation class for IMERGDataset.
    Initialise object parameters and calculate start and end dates for dataset using product_date and interval.

    Parameters
    ----------
    interval : string
        Data interval to retrieve/manage. Can be daily, pentad, dekad, monthly or seasonal
    product_date : datetime
        Data acquisition date. For pentad/dekad data, the data is actually for the period immediately preceding
        the product_date. For monthly data, the data covers the month given in the product date. For seasonal data,
        the product_date refers to the start of the season (3 month period).
    """
    def __init__(self, interval, product_date, vampire_defaults, region=None):
        logger.debug('Initialising IMERG dataset')
        super(IMERGDatasetImpl, self).__init__()
        self.interval = interval
        self.product_date = product_date
        self.vp = vampire_defaults
        self.region = region

        self.start_date = product_date
        self.end_date = product_date
        return

    @property
    def start_date(self):
        return self.__start_date
    @start_date.setter
    def start_date(self, sd):
        self.__start_date = sd

    @property
    def end_date(self):
        return self.__end_date
    @end_date.setter
    def end_date(self, ed):
        self.__end_date = ed

    def generate_header(self):
        return ""

    """ Generate a config file process for the dataset.

    Generate VAMPIRE config file process(es) for the dataset including download and crop if specified.

    Parameters
    ----------
    data_dir : string
        Path for downloaded data. The data will be stored in this path under a directory with the interval name. If the
        data_dir is None, the VAMPIRE default download directory will be used.
    download : boolean
        Flag indicating whether data should be downloaded. Default is True.
    crop : boolean
        Flag indicating whether data should be cropped to region. Default is True.
    crop_dir : string
        Path where cropped data will be stored. If None, the region code will be appended to the download data path.

    Returns
    -------
    string
        Returns string containing the configuration file process.

    """
    def generate_config(self, data_dir=None, extract_dir=None, download=True, crop=True, crop_dir=None):
        logger.debug('IMERGDataset generate_config')
        config = ''
        if data_dir is None:
            _data_dir = self.vp.get('IMERG', 'data_dir')
        else:
            _data_dir = data_dir
        _download_dir = "{0}\\{1}".format(_data_dir, self.interval.capitalize())

        if download:
            config += self._generate_download_section(data_dir=_download_dir)

        # setup directories for extracting precipitation data
        if extract_dir is None:
            _extract_dir = self.vp.get('IMERG', 'precip_extract_dir')
        else:
            _extract_dir = extract_dir
        _output_dir = _extract_dir
        # pattern for files to extract from
        _imerg_pattern = self.vp.get('IMERG', 'global_{0}_pattern'.format(self.interval))
        _precip_output_pattern = self.vp.get('IMERG', 'global_precip_output_pattern')
        _precip_var = self.vp.get('IMERG', 'subset_name')
        config += self._generate_extract_section(data_dir=_download_dir, output_dir=_output_dir,
                                                 variable=_precip_var, file_pattern=_imerg_pattern,
                                                 output_pattern=_precip_output_pattern)

        if crop:
            _country_code = self.vp.get_country_code(self.region)
            if crop_dir is None:
                _crop_dir = os.path.join(_output_dir, _country_code.upper())
            else:
                _crop_dir = crop_dir

            if self.region is not None and self.region.lower() is not 'global':
                # self.region should contain country name
                config += """
        # Crop data to {country}""".format(country=self.region)
                _input_pattern = self.vp.get('IMERG', 'global_{0}_precip_pattern'.format(self.interval))
                _output_pattern = '{0}{1}'.format(self.vp.get_country_code(self.region).lower(),
                                                  self.vp.get('IMERG',
                                                              'crop_regional_output_{0}_pattern'.format(self.interval)))
                _boundary_file = self.vp.get_country('{0}'.format(self.region))['imerg_boundary_file']
                config += self.generate_crop_section(_output_dir, _crop_dir, _input_pattern, _output_pattern,
                                                     _boundary_file, no_data=True)
                _output_dir = _crop_dir
        return config, _output_dir


    """ Generate VAMPIRE config file header for IMERG datasets.

    Parameters
    ----------
    None

    Returns
    -------
    string
        Returns config file header section.

    """
    def generate_header(self):
        config = ""
        return config

    """ Generate download process section for IMERG dataset.

    Generate VAMPIRE config file process for IMERG dataset download.

    Parameters
    ----------
    data_dir : string
        Path for downloaded data. The data will be stored in this path under a directory with the interval name. If the
        data_dir is None, the VAMPIRE default download directory will be used.

    Returns
    -------
    string
        Returns string containing the configuration file process.

    """
    def _generate_download_section(self, data_dir):
        config = """
    # download IMERG precipitation data
    - process: IMERG
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

    def _generate_extract_section(self, data_dir, output_dir, variable, file_pattern, output_pattern):
        config = """
    # extract IMERG precipitation data
    - process: IMERG
      type: extract
      layer: {variable}
      input_dir: {input_dir}
      output_dir: {output_dir}
      file_pattern: '{file_pattern}'
      output_pattern: '{output_pattern}'""".format(variable=variable, input_dir=data_dir, output_dir=output_dir,
                                                 file_pattern=file_pattern, output_pattern=output_pattern)
        return config