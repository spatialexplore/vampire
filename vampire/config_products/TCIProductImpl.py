import BaseDataset
import RasterProductImpl
import datetime
import os
import logging
logger = logging.getLogger(__name__)

class TCIProductImpl(RasterProductImpl.RasterProductImpl):
    """ Initialise TCIProductImpl.

    Implementation class for TCIProduct.
    Initialise object parameters.

    Parameters
    ----------
    country : string
        Region of dataset - country name or 'global'.
    product_date : datetime
        Data acquisition date. For pentad/dekad data, the data is actually for the period immediately preceding
        the product_date. For monthly data, the data covers the month given in the product date. For seasonal data,
        the product_date refers to the start of the season (3 month period).
    interval : string
        Data interval to retrieve/manage. Can be daily, pentad, dekad, monthly or seasonal
    vampire_defaults : object
        VAMPIREDefaults object containing VAMPIRE system default values.

    """
    def __init__(self, country, product_date, interval, vampire_defaults):
        super(TCIProductImpl, self).__init__()
        self.country = country
        self.interval = interval
        self.product_date = product_date
        self.vp = vampire_defaults
        self.product = self.vp.get('MODIS', 'land_surface_temperature_product')
        self.day_of_year = self.product_date.timetuple().tm_yday
        if self.interval is None:
            self.interval = self.vp.get('MODIS_PRODUCTS', '{product}.interval'.format(product=self.product))

        self.cur_lst_dataset = BaseDataset.BaseDataset.create(dataset_type='MODIS_LST', interval=self.interval,
                                                              product_date=self.product_date,
                                                              vampire_defaults=self.vp, region=self.country)
        self.valid_from_date = self.cur_lst_dataset.start_date
        self.valid_to_date = self.cur_lst_dataset.end_date
#        self.lta_max_evi_dataset = BaseProduct.BaseProduct.create(product_type='MODIS_EVI_LTA', interval=self.interval,
#                                                                  product_date=self.product_date,
#                                                                  vampire_defaults=self.vp, country=self.country)
        return

    def generate_header(self):
        return ''

    """ Generate a config file process for the vegetation condition index (VCI) product.

    Generate VAMPIRE config file processes for the product including download and crop if specified.

    Parameters
    ----------
    output_dir : string
        Path for product output. If the output_dir is None, the VAMPIRE default SPI product directory
        will be used.
    cur_file : string
        Path for current precipitation file. Default is None. If None, cur_dir and cur_pattern will be used to find
        the file.
    cur_dir : string
        Directory path for current precipitation file. Default is None. If cur_file is set, cur_dir is not used.
    cur_pattern : string
        Regular expression pattern for finding current precipitation file. Default is None. If cur_file is set,
        cur_pattern is not used.
    lta_file : string
        Path for long-term average precipitation file. Default is None. If None, lta_dir and lta_pattern will be
        used to find the file.
    lta_dir : string
        Directory path for long-term average precipitation file. Default is None. If lta_file is set, lta_dir is not
        used.
    lta_pattern : string
        Regular expression pattern for finding long-term average precipitation file. Default is None. If lta_file is
        set, lta_pattern is not used.
    output_file : string
        Directory path for output rainfall anomaly file. Default is None. If output_file is set, output_dir is not used.
    output_pattern : string
        Pattern for specifying output filename. Used in conjuction with cur_pattern. Default is None. If output_file is
        set, output_pattern is not used.

    Returns
    -------
    string
        Returns string containing the configuration file process.

    """
    def generate_config(self, lst_cur_file=None,    # current EVI filename for given month/year
                        lst_cur_dir=None,           # directory to look for EVI file in if not specified
                        lst_cur_pattern=None,       # pattern to use to find EVI file if not specified
                        lst_max_file=None,          # EVI long-term maximum filename
                        lst_max_dir=None,           # directory of EVI long-term maximum
                        lst_max_pattern=None,       # pattern for finding EVI long-term maximum
                        lst_min_file=None,          # EVI long-term minimum filename
                        lst_min_dir=None,           # directory of EVI long-term minimum
                        lst_min_pattern=None,       # pattern for finding long-term minimum
                        output_filename=None,       # filename for VCI output
                        output_dir=None,            # directory for VCI output
                        output_pattern=None,        # pattern for generating VCI output filename if not specified
                        ):
        config = """
    ## Processing chain begin - Compute Temperature Condition Index\n"""
        _cfg_section, _output_dir = self.cur_lst_dataset.generate_config(data_dir=None, download=True)
        config += _cfg_section

        _lst_interval = self.vp.get('MODIS_PRODUCTS',
                                    '{0}.interval'.format(self.product))
        _use_interval = None
        if (self.interval != _lst_interval) and (self.interval.lower() == '16days'):
            # 16 Day data, but LST is 8 days. Need to combine previous and current 8 day LST
            _prev_lst_dataset = BaseDataset.BaseDataset.create(dataset_type='MODIS_LST', interval=_lst_interval,
                                                               product_date=self.product_date + datetime.timedelta(days=-8),
                                                               vampire_defaults=self.vp, region=self.country)
            _cfg_section, _prev_output_dir = _prev_lst_dataset.generate_config(data_dir=None, download=True)
            config += _cfg_section
            _convert_interval = True
            _use_interval = self.interval
        else:
            _convert_interval = False


        if lst_cur_dir is None:
            _lst_cur_dir = _output_dir
        else:
            _lst_cur_dir = lst_cur_dir
        _lst_cur_pattern = lst_cur_pattern
        if lst_cur_pattern is None:
            _lst_cur_pattern = self.vp.get('MODIS_LST', 'lst_regional_pattern')
            # replace generic year in pattern with the specific one needed so the correct file is found.
            _lst_cur_pattern = _lst_cur_pattern.replace('(?P<year>\d{4})', '(?P<year>{0})'.format(self.product_date.year))
            _lst_cur_pattern = _lst_cur_pattern.replace('(?P<month>\d{2})', '(?P<month>{0:0>2})'.format(self.product_date.month))
            _lst_cur_pattern = _lst_cur_pattern.replace('(?P<day>\d{2})', '(?P<day>{0:0>2})'.format(self.product_date.day))
            if _convert_interval:
                _prev_pattern = self.vp.get('MODIS_LST', 'lst_regional_pattern')
                # replace generic year in pattern with the specific one needed so the correct file is found.
                _prev_pattern = _prev_pattern.replace('(?P<year>\d{4})', '(?P<year>{0})'.format((self.product_date + datetime.timedelta(days=-8)).year))
                _prev_pattern = _prev_pattern.replace('(?P<month>\d{2})', '(?P<month>{0:0>2})'.format((self.product_date + datetime.timedelta(days=-8)).month))
                _prev_pattern = _prev_pattern.replace('(?P<day>\d{2})', '(?P<day>{0:0>2})'.format((self.product_date + datetime.timedelta(days=-8)).day))
                _lst_cur_pattern = '{0}|{1}'.format(_lst_cur_pattern, _prev_pattern)

        _lst_max_file = lst_max_file
        _lst_min_file = lst_min_file
        _lst_max_dir = lst_max_dir
        _lst_min_dir = lst_min_dir
        if self.country.lower() == 'global':
            # Global MODIS VCI doesn't make sense
            raise
        elif self.vp.get_country_code(self.country).upper() == self.vp.get('vampire', 'home_country').upper():
            # home country
            _prefix = self.vp.get('MODIS', 'home_country_prefix')
        else:
            _prefix = os.path.join(self.vp.get('MODIS', 'regional_prefix'),
                                   self.vp.get_country_code(self.country).upper())
        if _lst_max_dir is None:
            _lst_max_dir = os.path.join(_prefix, self.vp.get('MODIS_LST_Long_Term_Average', 'lta_dir_suffix'))
        if _lst_min_dir is None:
            _lst_min_dir = os.path.join(_prefix, self.vp.get('MODIS_LST_Long_Term_Average', 'lta_dir_suffix'))

        if lst_min_pattern is None:
            _lst_min_pattern = self.vp.get('MODIS_LST_Long_Term_Average', 'lta_pattern')
            _lst_min_pattern = _lst_min_pattern.replace('(?P<day_of_yr>\d{3})', '(?P<day_of_yr>{0:0>3})'.
                                                        format(self.day_of_year))
            _lst_min_pattern = _lst_min_pattern.replace('(?P<statistic>.*)', 'min')
        else:
            _lst_min_pattern = lst_min_pattern
        if lst_max_pattern is None:
            _lst_max_pattern = self.vp.get('MODIS_LST_Long_Term_Average', 'lta_pattern')
            _lst_max_pattern = _lst_max_pattern.replace('(?P<day_of_yr>\d{3})', '(?P<day_of_yr>{0:0>3})'.
                                                        format(self.day_of_year))
            _lst_max_pattern = _lst_max_pattern.replace('(?P<statistic>.*)', 'max')
        else:
            _lst_max_pattern = lst_max_pattern

        if output_filename is None:
            if output_dir is None:
                _output_dir = self.vp.get('MODIS_TCI', 'tci_product_dir')
            else:
                _output_dir = output_dir
            if output_pattern is None:
                _output_pattern = self.vp.get('MODIS_TCI', 'tci_output_pattern')
            else:
                _output_pattern = output_pattern
        else:
            _output_dir = None
            _output_pattern = None

        config += self.generate_tci_section(cur_file=lst_cur_file, cur_dir=_lst_cur_dir, cur_pattern=_lst_cur_pattern,
                                            lst_max_file=_lst_max_file, lst_max_dir=_lst_max_dir,
                                            lst_max_pattern=_lst_max_pattern,
                                            lst_min_file=_lst_min_file, lst_min_dir=_lst_min_dir,
                                            lst_min_pattern=_lst_min_pattern,
                                            output_file=output_filename, output_dir=_output_dir,
                                            output_pattern=_output_pattern, interval=_use_interval)

        return config

    def generate_tci_section(self, cur_file, cur_dir, cur_pattern, lst_max_file, lst_max_dir, lst_max_pattern,
                             lst_min_file, lst_min_dir, lst_min_pattern, output_file, output_dir, output_pattern,
                             interval=None):
        cfg_string = """
    # Compute temperature condition index
    - process: Analysis
      type: TCI"""
        if cur_file is not None:
            cfg_string += """
      current_file: {current_file}""".format(current_file=cur_file)
        else:
            cfg_string += """
      current_dir: {current_dir}
      current_file_pattern: '{current_pattern}'""".format(current_dir=cur_dir, current_pattern=cur_pattern)
        if lst_max_file is not None:
            cfg_string += """
      LST_max_file: {lst_max}""".format(lst_max=lst_max_file)
        else:
            cfg_string += """
      LST_max_dir: {lst_max_dir}
      LST_max_pattern: '{lst_max_pattern}'""".format(lst_max_dir=lst_max_dir, lst_max_pattern=lst_max_pattern)
        if lst_min_file is not None:
            cfg_string += """
      LST_min_file: {lst_min}""".format(evi_min=lst_min_file)
        else:
            cfg_string += """
      LST_min_dir: {lst_min_dir}
      LST_min_pattern: '{lst_min_pattern}'""".format(lst_min_dir=lst_min_dir, lst_min_pattern=lst_min_pattern)
        if output_file is not None:
            cfg_string += """
      output_file: {output_file}""".format(output_file=output_file)
        else:
            cfg_string += """
      output_dir: {output_dir}
      output_file_pattern: '{output_pattern}'""".format(output_dir=output_dir, output_pattern=output_pattern)

        if interval is not None:
            cfg_string += """
      interval: {interval}""".format(interval=interval)



        return cfg_string

