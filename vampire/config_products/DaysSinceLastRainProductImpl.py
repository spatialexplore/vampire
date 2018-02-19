import BaseDataset
import RasterProductImpl
import os
import datetime
import logging
logger = logging.getLogger(__name__)

class DaysSinceLastRainProductImpl(RasterProductImpl.RasterProductImpl):
    """ Days Since Last Rain config file process generation.

    Data handling for generating config file entries for Days Since Last Rain data product.

    """

    def __init__(self, country, product_date, interval, vampire_defaults):
        """ Initialise DaysSinceLastRainProductImpl.

        Implementation class for DaysSinceLastRainProduct.
        Initialise object parameters.

        :param country: Region of dataset - country name or 'global'.
        :type country: string
        :param product_date: Data acquisition date. For pentad/dekad data, the data is actually for the period immediately preceding
            the product_date. For monthly data, the data covers the month given in the product date. For seasonal data,
            the product_date refers to the start of the season (3 month period).
        :type product_date:  datetime
        :param interval: Data interval to retrieve/manage. Can be daily, pentad, dekad, monthly or seasonal
        :type interval: string
        :param vampire_defaults: VAMPIREDefaults object containing VAMPIRE system default values.
        :type vampire_defaults: VampireDefaults object
        """
        super(DaysSinceLastRainProductImpl, self).__init__()
        self.product_name = 'days_since_last_rain'
        self.country = country
        self.interval = interval
        self.product_date = product_date
        self.vp = vampire_defaults
        self.data_source = self.vp.get('Days_Since_Last_Rain', 'default_data')

        if self.interval is None:
            self.interval = self.vp.get('Days_Since_Last_Rain'.format(self.data_source), 'default_interval')

        self.dataset = BaseDataset.BaseDataset.create(dataset_type=self.data_source, interval=self.interval,
                                                      product_date=self.product_date,
                                                      vampire_defaults=self.vp, region=self.country)
        self.valid_from_date = self.dataset.start_date()
        self.valid_to_date = self.dataset.end_date()
        return

    def generate_header(self):
        """ Generate VAMPIRE config file header for Days Since Last Rain.

        :return: Returns config file header section.
        :rtype: string
        """
        config = self.dataset.generate_header()
        return config


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
        if self.country.lower() == 'global':
            crop = False
        cfg_string = """
    ## Processing chain begin - Compute Days Since Last Rain\n"""
        _max_days = max_days # number of days to check for rain prior to start date
        if _max_days is None:
            _max_days = int(self.vp.get('Days_Since_Last_Rain', 'default_max_days'))
        # set dataset start and end dates to cover the range required.
        self.dataset.set_start_date(self.product_date + datetime.timedelta(days=-_max_days))
        self.dataset.set_end_date(self.product_date)

        _c_str, _data_dir = self.dataset.generate_config(data_dir, download, crop, crop_dir)
        cfg_string += _c_str

        _threshold = threshold # threshold of precipitation to count as 'wet' day
        if _threshold is None:
            _threshold = self.vp.get('Days_Since_Last_Rain', 'default_threshold')

        _data_pattern = file_pattern
        if _data_pattern is None:
            if self.country.lower() == 'global':
                _data_pattern = self.vp.get(self.data_source, 'global_daily_pattern')
            else:
                _data_pattern = self.vp.get(self.data_source, 'regional_daily_pattern')

        # directory for days since last rainfall output
        _output_dir = output_dir
        if _output_dir is None:
            _output_dir = self.vp.get('Days_Since_Last_Rain', 'output_dir')
        if not os.path.dirname(_output_dir):
            os.makedirs(_output_dir)

        self.product_file = None
        self.product_dir = _output_dir
        self.product_pattern = self.vp.get('Days_Since_Last_Rain', 'regional_dslr_pattern')
        self.product_pattern = self.product_pattern.replace('(?P<year>\d{4})', '(?P<year>{0})'.format(self.product_date.year))
        self.product_pattern = self.product_pattern.replace('(?P<month>\d{2})', '(?P<month>{0:0>2})'.format(self.product_date.month))
        self.product_pattern = self.product_pattern.replace('(?P<day>\d{2})', '(?P<day>{0:0>2})'.format(self.product_date.day))

        cfg_string += """
    # compute days since last rainfall
    - process: Analysis
      type: days_since_last_rain
      input_dir: {input_dir}
      output_dir: {output_dir}
      file_pattern: '{file_pattern}'
      start_date: {start_date}
      threshold: {threshold}
      max_days: {max_days}""".format(
            input_dir=_data_dir, output_dir=_output_dir, file_pattern=_data_pattern,
            start_date='{0}-{1:0>2}-{2:0>2}'.format(self.valid_from_date.year, self.valid_from_date.month,
                                                    self.valid_from_date.day),
            threshold=_threshold, max_days=_max_days
        )
        cfg_string += """
    ## Processing chain end - Compute Days Since Last Rain
        """
        return cfg_string