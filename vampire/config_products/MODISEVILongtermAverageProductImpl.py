import BaseDataset
import RasterProductImpl
import os
import logging
logger = logging.getLogger(__name__)

class MODISEVILongtermAverageProductImpl(RasterProductImpl.RasterProductImpl):
    """ Initialise MODISEVILongtermAverageProductImpl.

    Implementation class for MODISEVILongtermAverageProduct.
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
        super(MODISEVILongtermAverageProductImpl, self).__init__()
        self.country = country
        self.interval = interval
        self.product_date = product_date
        self.product = self.vp.get('MODIS', 'vegetation_product')
        self.vp = vampire_defaults
        if self.interval is None:
            self.interval = self.vp.get('MODIS_PRODUCTS', '{0}.interval'.format(self.product))

        # set product_date to None to retrieve all available data
        self.evi_dataset = BaseDataset.BaseDataset.create(dataset_type='MODIS_EVI', interval=self.interval,
                                                          product_date=None,
                                                          vampire_defaults=self.vp, region=self.country)
        return

    """ Generate VAMPIRE config file header for CHIRPS datasets.

    Parameters
    ----------
    None

    Returns
    -------
    string
        Returns config file header section.

    """
    def generate_header(self):
        config = self.evi_dataset.generate_header()
        return config


    """ Generate a config file process for the rainfall anomaly product.

    Generate VAMPIRE config file processes for the product including download and crop if specified.

    Parameters
    ----------
    output_dir : string
        Path for product output. If the output_dir is None, the VAMPIRE default rainfall anomaly product directory
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
    def generate_config(self, input_dir=None, output_dir=None, input_pattern=None,
                        output_pattern=None, functions=None, download=True):
        config = """
    ## Processing chain begin - Compute MODIS EVI long-term average\n"""
        if download:
            config += self.evi_dataset.generate_config(data_dir=None, download=download)

        if self.country.lower() == 'global':
            _prefix = self.vp.get('MODIS', 'global_prefix')
            _input_pattern = self.vp.get('MODIS_EVI', 'evi_pattern')
            _output_pattern = self.vp.get('MODIS_EVI_Long_Term_Average', 'lta_output_pattern')
        elif self.vp.get_country_code(self.country).upper() == self.vp.get('vampire', 'home_country'):
            _prefix = self.vp.get('MODIS', 'home_country_prefix')
            _input_pattern = self.vp.get('MODIS_EVI', 'evi_regional_pattern')
            _output_pattern = self.vp.get('MODIS_EVI_Long_Term_Average', 'lta_output_pattern')
        else:
            _prefix = os.path.join(self.vp.get('MODIS', 'regional_prefix'),
                                    self.vp.get_country_code(self.country).upper())
            _input_pattern = self.vp.get('MODIS_EVI', 'evi_regional_pattern')
            _output_pattern = self.vp.get('MODIS_EVI_Long_Term_Average', 'lta_output_pattern')

        if input_dir is None:
            _input_dir = os.path.join(_prefix, self.vp.get('MODIS', 'evi_dir_suffix'))
        else:
            _input_dir = input_dir

        if output_dir is None:
            _output_dir = os.path.join(_prefix, self.vp.get('MODIS_EVI_Long_Term_Average', 'lta_dir_suffix'))
        else:
            _output_dir = output_dir

        if input_pattern is not None:
            _input_pattern = input_pattern

        if output_pattern is not None:
            _output_pattern = output_pattern

        if functions is None:
            _functions = ['MIN', 'MAX']
        else:
            _functions = functions

        config += self.generate_longterm_average_section(input_dir=_input_dir, output_dir=_output_dir,
                                                         input_pattern=_input_pattern, output_pattern=_output_pattern,
                                                         functions=_functions)
        return config

    def generate_longterm_average_section(self, input_dir, output_dir, input_pattern, output_pattern, functions):
        cfg_string = """
    # calculate long-term statistics
    - process: MODIS
      type: calc_average
      layer: long_term_statistics
      input_dir: {input_dir}
      output_dir: {output_dir}
      product: {product}
      file_pattern: '{input_pattern}'
      output_pattern: '{output_pattern}'""".format(input_dir=input_dir, output_dir=output_dir, product=self.product,
                                                   input_pattern=input_pattern, output_pattern=output_pattern)

        if self.valid_from_date is not None:
            cfg_string += """
      start_date: {s_date}""".format(s_date=self.valid_from_date)
        if self.valid_to_date is not None:
            cfg_string += """
      end_date: {e_date}""".format(e_date=self.valid_to_date)

        if functions is not None:
            cfg_string += """
      functions: {fn}""".format(fn=functions)

        if self.interval is not None:
            cfg_string += """
      interval: {interval}""".format(interval=self.interval)

        return cfg_string
