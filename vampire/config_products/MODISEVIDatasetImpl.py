import MODISDatasetImpl
import datetime
import dateutil.rrule
import dateutil.relativedelta
import os
import logging
logger = logging.getLogger(__name__)

class MODISEVIDatasetImpl(MODISDatasetImpl.MODISDatasetImpl):
    """ Initialise MODISEVIDatasetImpl object.

    Implementation class for MODISEVIDataset.
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
        logger.debug('Initialising MODIS EVI dataset')
        _product = vampire_defaults.get('MODIS', 'vegetation_product')
        super(MODISEVIDatasetImpl, self).__init__(interval=interval, product_date=product_date,
                                                  vampire_defaults=vampire_defaults, product=_product, region=region)
        if self.product_date is not None:
            self.day_of_year = self.product_date.timetuple().tm_yday
        return

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
    def generate_config(self, data_dir=None, download=True, mosaic_dir=None, tiles=None, extract_dir=None,
                        crop=True, crop_dir=None):
        logger.debug('MODISEVIDataset generate_config')
        config = ''
        _output_dir = data_dir
        _crop = crop
        if download:
            config, _output_dir = super(MODISEVIDatasetImpl, self).generate_download(data_dir, mosaic_dir, tiles)
        # setup directories for extracting EVI data
        if extract_dir is None:
            _extract_dir = self.vp.get('MODIS_EVI', 'evi_extract_dir')
        else:
            _extract_dir = extract_dir
        config += self.generate_extract_evi(data_dir=_output_dir, output_dir=_extract_dir)
        _output_dir = _extract_dir

        _crop_dir = None
        if crop_dir is None:
            if self.region.lower() == 'global':
                # don't crop global
                _crop = False
            else:
                if self.vp.get_country_code(self.region).upper() == self.vp.get('vampire', 'home_country').upper():
                    # home country
                    _crop_dir = self.vp.get('MODIS', 'home_country_prefix')
                else:
                    # regional country - directory for output file
                    _crop_dir = os.path.join(self.vp.get('MODIS', 'regional_prefix'),
                                             self.vp.get_country_code(self.region).upper())
                _crop_dir = os.path.join(_crop_dir,
                                           self.vp.get('MODIS_EVI', 'evi_dir_suffix'))
        else:
            _crop_dir = crop_dir
        if _crop:
            _input_pattern = self.vp.get('MODIS_EVI', 'evi_pattern')
            if self.product_date is not None:
                # replace generic year and month in pattern with the specific ones needed so the correct file is found.
                _input_pattern = _input_pattern.replace('(?P<year>\d{4})', '(?P<year>{0})'.format(self.product_date.year))
                _input_pattern = _input_pattern.replace('(?P<month>\d{2})', '(?P<month>{0:0>2})'.format(self.product_date.month))
                _input_pattern = _input_pattern.replace('(?P<day>\d{2})', '(?P<day>{0:0>2})'.format(self.product_date.day))
            _output_pattern = self.vp.get('MODIS_EVI', 'evi_regional_output_pattern')
            _output_pattern = _output_pattern.replace('{country}',
                                                      '{0}'.format(self.vp.get_country_code(self.region).lower()))
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

            config += self.generate_crop_section(_extract_dir, _crop_dir, _input_pattern, _output_pattern, _boundary_file)
            _output_dir = _crop_dir
        return config, _output_dir

    def generate_extract_evi(self, data_dir, output_dir):

        if data_dir is None:
            _data_dir = self.vp.get('MODIS', 'vegetation_download_dir')
        else:
            _data_dir = data_dir

        # setup directories for extracting EVI data
        if output_dir is None:
            _output_dir = self.vp.get('MODIS_EVI', 'evi_extract_dir')
        else:
            _output_dir = output_dir

        # pattern for files to extract from
        _modis_pattern = self.vp.get('MODIS', 'modis_monthly_pattern')
        if self.product_date is not None:
            # replace generic year and month in pattern with the specific ones needed so the correct file is found.
            _modis_pattern = _modis_pattern.replace('(?P<year>\d{4})', '(?P<year>{0})'.format(self.product_date.year))
            _modis_pattern = _modis_pattern.replace('(?P<month>\d{2})', '(?P<month>{0:0>2})'.format(self.product_date.month))
            _modis_pattern = _modis_pattern.replace('(?P<day>\d{2})', '(?P<day>{0:0>2})'.format(self.product_date.day))
        _evi_output_pattern = self.vp.get('MODIS_EVI', 'evi_output_pattern')
        _evi_layer = 'EVI' #self.vampire.get('MODIS_PRODUCTS', '{0}.EVI_Name'.format(_product))
        file_string = super(MODISEVIDatasetImpl, self).generate_extract_section(input_dir=_data_dir,
                                                                                output_dir=_output_dir,
                                                                                product=self.product,
                                                                                layer=_evi_layer,
                                                                                file_pattern=_modis_pattern,
                                                                                output_pattern=_evi_output_pattern)
        return file_string
