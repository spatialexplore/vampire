import BaseDataset
import RasterProductImpl
import os
import datetime
import logging
logger = logging.getLogger(__name__)

class DaysSinceLastRainProductImpl(RasterProductImpl.RasterProductImpl):
    """ Initialise DaysSinceLastRainProductImpl.

    Implementation class for DaysSinceLastRainProduct.
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
        super(DaysSinceLastRainProductImpl, self).__init__()
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

    """ Generate VAMPIRE config file header for datasets.

    Parameters
    ----------
    None

    Returns
    -------
    string
        Returns config file header section.

    """
    def generate_header(self):
        config = self.dataset.generate_header()
        return config


    """ Generate a config file process for the standardised precipitation index (SPI) product.

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
    def generate_config(self, data_dir=None, output_dir=None, file_pattern=None,
                        threshold=None, max_days=None, download=True, crop=True, crop_dir=None):

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