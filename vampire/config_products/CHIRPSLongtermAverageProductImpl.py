import BaseDataset
import RasterProductImpl
import os
import logging
logger = logging.getLogger(__name__)

class CHIRPSLongtermAverageProductImpl(RasterProductImpl.RasterProductImpl):
    """ CHIRPS long-term average.

    Data handling for generating CHIRPS long-term averages.

    """

    def __init__(self, country, product_date, interval, vampire_defaults):
        """ Initialise MODISEVILongtermAverageProductImpl.

        Implementation class for MODISEVILongtermAverageProduct.
        Initialise object parameters.

        :param country: Region of dataset - country name or 'global'.
        :type country: string
        :param product_date: Data acquisition date. For pentad/dekad data, the data is actually for the period immediately preceding
            the product_date. For monthly data, the data covers the month given in the product date. For seasonal data,
            the product_date refers to the start of the season (3 month period).
        :type product_date: datetime
        :param interval: Data interval to retrieve/manage. Can be daily, pentad, dekad, monthly or seasonal
        :type interval: string
        :param vampire_defaults:
        :type vampire_defaults: VampireDefaults
        :param region: Default is None.
        """
        super(CHIRPSLongtermAverageProductImpl, self).__init__()
        self.country = country
        self.interval = interval
        self.product_date = product_date
        self.vp = vampire_defaults
        if self.interval is None:
            raise ValueError("An interval is needed for computing CHIRPS longterm average.")

        # set product_date to None to retrieve all available data
        self.chirps_dataset = BaseDataset.BaseDataset.create(dataset_type='CHIRPS', interval=self.interval,
                                                             product_date=None,
                                                             vampire_defaults=self.vp, region=self.country)
        return

    def generate_header(self):
        """ Generate VAMPIRE config file header for CHIRPS long-term average datasets.

        :return: Returns config file header section.
        :rtype: string
        """
        config = self.chirps_dataset.generate_header()
        return config


    def generate_config(self, input_dir=None, output_dir=None, input_pattern=None,
                        output_pattern=None, functions=None, download=True):
        """ Generate a config file process for CHIRPS long-term average product.

        Generate VAMPIRE config file processes to generate long-term averages from CHIRPS data.

        Parameters
        ----------
        :param input_dir: Directory path for CHIRPS precipitation files. Default is None.
        :type input_dir: string
        :param output_dir: Path for product output. If the output_dir is None, the VAMPIRE default rainfall anomaly product directory will be used.
        :type output_dir: string
        :param input_pattern: Regular expression pattern for finding CHIRPS precipitation files. Default is None.
        :type input_pattern: string
        :param output_pattern: Pattern for specifying output filename. Used in conjuction with input_pattern. Default is None.
        :type output_pattern: string
        :param functions: List of functions to calculate. Valid options include 'AVG', 'MIN', 'MAX', 'STD'.
        :type functions: list of string
        :param download: Flag indicating whether data should be downloaded or not.
        :type download: bool

        :return: Returns string containing the configuration file process.
        :rtype: string
        """
        config = """
    ## Processing chain begin - Compute CHIRPS long-term average\n"""
        if download:
            config += self.chirps_dataset.generate_config(data_dir=None, download=download)

        if input_dir is None:
            _input_dir = self.vp.get('CHIRPS', 'data_dir')
        else:
            _input_dir = input_dir
        if output_dir is None:
            _output_dir = os.path.join(self.vp.get('CHIRPS', 'home_country_product_dir'), 'StatisticsBy{0}'.format(self.interval))
        else:
            _output_dir = output_dir
        if input_pattern is None:
            _input_pattern = self.vp.get('CHIRPS', 'regional_{0}_pattern'.format(self.interval))
        else:
            _input_pattern = input_pattern
        if output_pattern is None:
            _output_pattern = self.vp.get('CHIRPS_Longterm_Average', 'regional_lta_{0}_pattern'.format(self.interval))
        else:
            _output_pattern = output_pattern
        if functions is None:
            _functions = ['AVG', 'STD', 'MIN', 'MAX']
        else:
            _functions = functions

        config += self.generate_longterm_average_section(input_dir=_input_dir, output_dir=_output_dir,
                                                         input_pattern=_input_pattern, output_pattern=_output_pattern,
                                                         functions=_functions)
        return config

    def generate_longterm_average_section(self, input_dir, output_dir, input_pattern, output_pattern, functions):
        """ Generate config file string for CHIRPS long-term average product.

        Generate VAMPIRE config file string to generate long-term averages from CHIRPS data.

        Parameters
        ----------
        :param input_dir: Directory path for CHIRPS precipitation files. Default is None.
        :type input_dir: string
        :param output_dir: Path for product output. If the output_dir is None, the VAMPIRE default rainfall anomaly product directory will be used.
        :type output_dir: string
        :param input_pattern: Regular expression pattern for finding CHIRPS precipitation files. Default is None.
        :type input_pattern: string
        :param output_pattern: Pattern for specifying output filename. Used in conjuction with input_pattern. Default is None.
        :type output_pattern: string
        :param functions: List of functions to calculate. Valid options include 'AVG', 'MIN', 'MAX', 'STD'.
        :type functions: list of string

        :return: Returns string containing the configuration file process.
        :rtype: string
        """
        cfg_string = """
    - process: CHIRPS
      type: longterm_average
      interval: {interval}
      input_dir: {input_dir}
      output_dir: {output_dir}
      file_pattern: '{file_pattern}'
        """.format(interval=self.interval, input_dir=input_dir, output_dir=output_dir,
                   file_pattern=input_pattern)
        return cfg_string

