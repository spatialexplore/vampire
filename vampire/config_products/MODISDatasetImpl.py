import RasterDatasetImpl
import datetime
import dateutil.rrule
import dateutil.relativedelta
import os
import logging
logger = logging.getLogger(__name__)

class MODISDatasetImpl(RasterDatasetImpl.RasterDatasetImpl):
    """ Initialise MODISDatasetImpl object.

    Implementation class for MODISDataset.
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
    def __init__(self, interval, product_date, vampire_defaults, product, region=None):
        logger.debug('Initialising MODIS dataset')
        super(MODISDatasetImpl, self).__init__()
        self.interval = interval
        self.product_date = product_date
        self.product = product
        self.vp = vampire_defaults
        self.region = region

        if self.product_date is not None:
            if self.interval.lower() == 'dekad':
                self.start_date = self.product_date + datetime.timedelta(days=-10)
                self.end_date = product_date
            elif self.interval.lower() == '8days':
                self.start_date = self.product_date + datetime.timedelta(-8)
                self.end_date = self.product_date
            elif self.interval.lower() == '16days':
                self.start_date = self.product_date + datetime.timedelta(-16)
                self.end_date = self.product_date
            elif self.interval.lower() == 'monthly':
                self.start_date = datetime.datetime(product_date.year, product_date.month, 1) # ensure start date is first day of month
                self.end_date = self.start_date + dateutil.relativedelta.relativedelta(months=1,days=-1) # ensure end_date is last day of month
            elif self.interval.lower() == 'seasonal':
                self.start_date = product_date
                self.end_date = self.start_date + dateutil.relativedelta.relativedelta(months=3, days=-1) # set end_date as last day of third month
            else:
                logger.error("Interval '{0}' is not a valid MODIS dataset interval".format(self.interval))
                raise ValueError
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
    # def generate_config(self, data_dir=None, download=True, mosaic_dir=None, tiles=None, crop=True, crop_dir=None):
    #     logger.debug('MODISDataset generate_config')
    #     config = ''
    #     if download:
    #         # set up download directory
    #         if data_dir is None:
    #             _download_dir = self.vp.get('MODIS_PRODUCTS', '{0}.download_dir'.format(self.product))
    #         else:
    #             _download_dir = data_dir
    #
    #         output_dir = _download_dir
    #
    #         # get mosaic directory if needed
    #         if mosaic_dir is None:
    #             if self.region.lower() != 'global':
    #                 _mosaic_dir = self.vp.get('MODIS_PRODUCTS', '{0}.mosaic_dir'.format(self.product))
    #                 if _mosaic_dir == '':
    #                     _mosaic_dir = None
    #                 output_dir = _mosaic_dir
    #             else:
    #                 _mosaic_dir = None
    #         else:
    #             _mosaic_dir = mosaic_dir
    #             output_dir = _mosaic_dir
    #
    #         # set tiles if needed
    #         if tiles is not None:
    #             _tiles = tiles
    #         else:
    #             if _mosaic_dir is not None:
    #                 # need to mosaic, so must have tiles
    #                 _tiles = self.vp.get_country(self.region)['{0}_tiles'.format(self.product)]
    #             else:
    #                 _tiles = None
    #         config += self._generate_download_section(data_dir, _mosaic_dir, _tiles)
    #     return config

    def generate_download(self, data_dir=None, mosaic_dir=None, tiles=None):
        config = ''
        # set up download directory
        if data_dir is None:
            _download_dir = self.vp.get('MODIS_PRODUCTS', '{0}.download_dir'.format(self.product))
        else:
            _download_dir = data_dir

        output_dir = _download_dir

        # get mosaic directory if needed
        if mosaic_dir is None:
            if self.region.lower() != 'global':
                _mosaic_dir = self.vp.get('MODIS_PRODUCTS', '{0}.mosaic_dir'.format(self.product))
                if _mosaic_dir == '':
                    _mosaic_dir = None
                output_dir = _mosaic_dir
            else:
                _mosaic_dir = None
        else:
            _mosaic_dir = mosaic_dir
            output_dir = _mosaic_dir

        # set tiles if needed
        if tiles is not None:
            _tiles = tiles
        else:
            if _mosaic_dir is not None:
                # need to mosaic, so must have tiles
                _tiles = self.vp.get_country(self.region)['{0}_tiles'.format(self.product)]
            else:
                _tiles = None
        config += self._generate_download_section(_download_dir, _mosaic_dir, _tiles)

        return config, output_dir

    def _generate_download_section(self, download_dir, mosaic_dir, tiles):
        _file_string = """
    # download {interval} MODIS for {country_name} and mosaic if necessary
    - process: MODIS
      type: download
      product: {product}
      output_dir: {data_dir}""".format(interval=self.interval, country_name=self.region, product=self.product,
                                       data_dir=download_dir)
        if mosaic_dir is not None:
            _file_string += """
      mosaic_dir: {mosaic_dir}""".format(mosaic_dir=mosaic_dir)
        if tiles is not None:
            _file_string += """
      tiles: {tiles}""".format(tiles=tiles)
        # if start and end dates are specified, only download between these dates
        if self.product_date is not None:
            # use 1st of start_date month to make sure end month is also included
            _first_date = self.product_date.replace(self.product_date.year, self.product_date.month, 1)
            _dates = dateutil.rrule.rrule(dateutil.rrule.MONTHLY, dtstart=_first_date).between(
                _first_date, self.end_date, inc=True)
            _file_string += """
      dates: ["""
            for d in _dates:
                _file_string += '{year}-{month},'.format(year=d.strftime("%Y"), month=d.strftime("%m"))
            _file_string = _file_string[:-1]
            _file_string += """]
            """

        return _file_string

    def generate_extract_section(self, input_dir, output_dir, product, layer, file_pattern, output_pattern):
        file_string = """
    # extract MODIS {layer}
    - process: MODIS
      type: extract
      product: {product}
      layer: {layer}
      input_dir: {input_dir}
      output_dir: {output_dir}
      file_pattern: '{file_pattern}'
      output_pattern: '{output_pattern}'
      """.format(product=product, layer=layer, input_dir=input_dir, output_dir=output_dir,
                 file_pattern=file_pattern, output_pattern=output_pattern)
        return file_string
