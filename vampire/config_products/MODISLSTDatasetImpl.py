import MODISDatasetImpl
import datetime
import dateutil.rrule
import dateutil.relativedelta
import os
import logging
logger = logging.getLogger(__name__)

class MODISLSTDatasetImpl(MODISDatasetImpl.MODISDatasetImpl):
    """ Initialise MODISLSTDatasetImpl object.

    Implementation class for MODISLSTDataset.
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
        logger.debug('Initialising MODIS LST dataset')
        self.product = vampire_defaults.get('MODIS', 'land_surface_temperature_product')
        super(MODISLSTDatasetImpl, self).__init__(interval=interval, product_date=product_date,
                                                  vampire_defaults=vampire_defaults, product=self.product, region=region)
        self.day_of_year = self.product_date.timetuple().tm_yday
        return

    @property
    def product(self):
        return self.__product

    @product.setter
    def product(self, product):
        self.__product = product

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
    def generate_config(self, data_dir=None, download=True, mosaic_dir=None, tiles=None, crop=True, crop_dir=None):
        logger.debug('MODISLSTDataset generate_config')
        config = ''
        _output_dir = data_dir
        if download:
            config, _output_dir = super(MODISLSTDatasetImpl, self).generate_download(data_dir, mosaic_dir, tiles)

        _lst_extract_day_dir = self.vp.get('MODIS_LST', 'lst_day_dir')
        _lst_extract_night_dir = self.vp.get('MODIS_LST', 'lst_night_dir')

        config += self.generate_extract_lst(product=self.product, data_dir=_output_dir,
                                            day_dir=_lst_extract_day_dir,
                                            night_dir=_lst_extract_night_dir)
        _lst_average_dir = self.vp.get('MODIS_LST', 'lst_dir')
        config += self.generate_average_lst(day_dir=_lst_extract_day_dir, night_dir=_lst_extract_night_dir,
                                            output_dir=_lst_average_dir)
        _output_dir = _lst_average_dir
        _crop = True
        if self.region.lower() == 'global' or crop == False:
            # don't crop global
            _crop = False
        if _crop:
            if self.vp.get_country_code(self.region).upper() == self.vp.get('vampire', 'home_country'):
                _boundary_file = self.vp.get('MODIS', 'home_country_prefix')
            else:
                _boundary_file = os.path.join(self.vp.get('MODIS', 'regional_prefix'),
                                              self.vp.get_country_code(self.region).upper())
            _boundary_file = os.path.join(_boundary_file,
                                          self.vp.get('MODIS', 'boundary_dir_suffix'))
            _boundary_file = os.path.join(_boundary_file,
                                          '{country}{filename}'.format(
                                              country=self.vp.get_country_code(self.region).lower(),
                                              filename=self.vp.get('MODIS_PRODUCTS',
                                                                   '{0}.boundary_filename'.format(self.product))))
            _crop_output_pattern = self.vp.get('MODIS_LST', 'lst_regional_output_pattern')
            _crop_output_pattern = _crop_output_pattern.replace('{country}',
                                                                '{0}'.format(self.vp.get_country_code(self.region).lower()))
            if crop_dir is None:
                if self.vp.get_country_code(self.region).upper() == self.vp.get('vampire', 'home_country').upper():
                    # home country
                    _crop_dir = self.vp.get('MODIS', 'home_country_prefix')
                else:
                    # regional country - directory for output file
                    _crop_dir = os.path.join(self.vp.get('MODIS', 'regional_prefix'),
                                             self.vp.get_country_code(self.region).upper())
                _crop_dir = os.path.join(_crop_dir,
                                           self.vp.get('MODIS_LST', 'lst_dir_suffix'))
            else:
                _crop_dir = crop_dir
            _crop_pattern = self.vp.get('MODIS_LST', 'lst_average_pattern')
            # replace generic year and month in pattern with the specific ones needed so the correct file is found.
            _crop_pattern = _crop_pattern.replace('(?P<year>\d{4})', '(?P<year>{0})'.format(self.product_date.year))
            _crop_pattern = _crop_pattern.replace('(?P<dayofyear>\d{3})', '(?P<dayofyear>{0:0>3})'.
                                                    format(self.day_of_year))
            config += self.generate_crop_section(_lst_average_dir, _crop_dir, _crop_pattern, _crop_output_pattern,
                                                 _boundary_file)
            _output_dir = _crop_dir
        return config, _output_dir

    def generate_extract_lst(self, product, data_dir, day_dir, night_dir):
        if data_dir is None:
            _data_dir = self.vp.get('MODIS_LST', 'lst_download_dir')
        else:
            _data_dir = data_dir

        # setup directories for extracting Day & Night data
        if day_dir is None:
            _day_dir = self.vp.get('MODIS_LST', 'lst_day_dir')
        else:
            _day_dir = day_dir

        if night_dir is None:
            _night_dir = self.vp.get('MODIS_LST', 'lst_night_dir')
        else:
            _night_dir = night_dir

        # need to extract both day and night layers then average them
        # pattern for files to extract from
        if self.vp.get('MODIS_PRODUCTS', '{0}.mosaic_dir'.format(product)) == '': #is None:
            # no mosaic, so data uses day of year
            _modis_pattern = self.vp.get('MODIS_LST', 'lst_pattern')
        else:
            # already mosaic'd so use year.month.day format
            _modis_pattern = self.vp.get('MODIS_LST', 'lst_mosaic_pattern')
        # replace generic year and month in pattern with the specific ones needed so the correct file is found.
        _modis_pattern = _modis_pattern.replace('(?P<year>\d{4})', '(?P<year>{0})'.format(self.product_date.year))
        _modis_pattern = _modis_pattern.replace('(?P<month>\d{2})', '(?P<month>{0:0>2})'.format(self.product_date.month))
        _modis_pattern = _modis_pattern.replace('(?P<day>\d{2})', '(?P<day>{0:0>2})'.format(self.product_date.day))
        _modis_pattern = _modis_pattern.replace('(?P<dayofyear>\d{3})', '(?P<dayofyear>{0:0>3})'.format(self.day_of_year))
        _lst_output_pattern = self.vp.get('MODIS_LST', 'lst_output_pattern')
        config = super(MODISLSTDatasetImpl, self).generate_extract_section(input_dir=_data_dir, output_dir=_day_dir,
                                                                                product=product, layer='LST_Day',
                                                                                file_pattern=_modis_pattern,
                                                                                output_pattern=_lst_output_pattern)
        config += super(MODISLSTDatasetImpl, self).generate_extract_section(input_dir=_data_dir, output_dir=_night_dir,
                                                                                 product=product, layer='LST_Night',
                                                                                 file_pattern=_modis_pattern,
                                                                                 output_pattern=_lst_output_pattern)
        return config

    def generate_average_lst(self,
                         day_dir=None,
                         night_dir=None,
                         output_dir=None,
                         input_pattern=None,
                         output_pattern=None):
        if day_dir is None:
            _day_dir = self.vp.get('MODIS_LST', 'lst_day_dir')
        else:
            _day_dir = day_dir
        if night_dir is None:
            _night_dir = self.vp.get('MODIS_LST', 'lst_night_dir')
        else:
            _night_dir = night_dir
        if output_dir is None:
            _output_dir = self.vp.get('MODIS_LST', 'lst_dir')
        else:
            _output_dir = output_dir
        if input_pattern is None:
            _input_pattern = self.vp.get('MODIS_LST', 'lst_day_night_pattern')
            # have a specific date - replace generic pattern with specific values
            _input_pattern = _input_pattern.replace('(?P<year>\d{4})', '(?P<year>{0})'.format(self.product_date.year))
            _input_pattern = _input_pattern.replace('(?P<dayofyear>\d{3})', '(?P<dayofyear>{0:0>3})'.
                                                    format(self.day_of_year))
        else:
            _input_pattern = input_pattern
        if output_pattern is None:
            _output_pattern = self.vp.get('MODIS_LST', 'lst_average_output_pattern')
        else:
            _output_pattern = output_pattern

        config = self._generate_average_section(_day_dir, _night_dir, _output_dir,
                                                _input_pattern, _output_pattern)
        return config

    def _generate_average_section(self, day_dir, night_dir, output_dir, input_pattern, output_pattern):
        config = """
    # Compute average of day and night temperatures
    - process: MODIS
      type: calc_average
      layer: day_night_temp
      lst_day_dir: {lst_day_dir}
      lst_night_dir: {lst_night_dir}
      output_dir: {lst_average_dir}
      file_pattern: '{input_pattern}'
      output_pattern: '{output_pattern}'
            """.format(lst_day_dir=day_dir, lst_night_dir=night_dir,
                       lst_average_dir=output_dir, input_pattern=input_pattern,
                       output_pattern=output_pattern)
        return config
