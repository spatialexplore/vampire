import ast
import os
import logging

import BaseDataset
import RasterProductImpl
import RasterDatasetImpl

logger = logging.getLogger(__name__)

class FloodForecastProductImpl(RasterProductImpl.RasterProductImpl):
    """ Initialise FloodForecastProductImpl.

    Implementation class for FloodForecastProduct.
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
        super(FloodForecastProductImpl, self).__init__()
        self.country = country
        self.interval = interval
        self.product_date = product_date
        self.vp = vampire_defaults
#        self.product = self.vp.get('MODIS', 'vegetation_product')
        self.day_of_year = self.product_date.timetuple().tm_yday
#        if self.interval is None:
#            self.interval = self.vp.get('MODIS_PRODUCTS', '{product}.interval'.format(product=self.product))

        self.gfs_dataset = BaseDataset.BaseDataset.create(dataset_type='GFS', interval=self.interval,
                                                          product_date=self.product_date,
                                                          vampire_defaults=self.vp, region=self.country)
        self.valid_from_date = self.gfs_dataset.start_date
        self.valid_to_date = self.gfs_dataset.end_date
        self.product_file = None
        self.product_dir = None
        self.product_pattern = None
        return

    def generate_header(self):
        return ''

    """ Generate a config file process for the flood forecast product.

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
    def generate_config(self,
                        data_dir=None,
                        file_pattern=None,
                        threshold_file=None,
                        threshold_dir=None,
                        threshold_pattern=None,
                        accumulate_days=None,
                        flood_years=None,
                        output_file=None,
                        output_dir=None,
                        output_pattern=None
                        ):
        if accumulate_days is None:
            _days = ast.literal_eval(self.vp.get('FLOOD_FORECAST', 'forecast_days'))
        else:
            _days = accumulate_days

        _num_forecasts = ast.literal_eval(self.vp.get('FLOOD_FORECAST', 'forecast_period')) - _days +1

        config = """
    ## Processing chain begin - Compute Flood Forecast\n"""
        _cfg_section, _output_dir = self.gfs_dataset.generate_config(data_dir=None, download=True, crop=True, accumulate_days=_days)
        config += _cfg_section

        if data_dir is None:
            _data_dir = _output_dir
        else:
            _data_dir = data_dir


        if flood_years is None:
            _flood_years = ast.literal_eval(self.vp.get('FLOOD_FORECAST', 'flood_years'))
        else:
            _flood_years = flood_years

        if output_file is None:
            if output_dir is None:
                _output_dir = self.vp.get('FLOOD_FORECAST', 'product_dir')
            else:
                _output_dir = output_dir
            if output_pattern is None:
                _output_pattern = self.vp.get('FLOOD_FORECAST', 'output_pattern')
            else:
                _output_pattern = output_pattern
            self.product_dir = _output_dir
            self.product_pattern = _output_pattern
        else:
            _output_dir = None
            _output_pattern = None
            self.product_file = output_file

        if threshold_dir is None:
            _threshold_dir = self.vp.get('FLOOD_FORECAST', 'threshold_dir')
        else:
            _threshold_dir = threshold_dir
        _file_pattern = file_pattern
        if _file_pattern is None:
            _file_pattern = self.vp.get('GFS', 'regional_accum_pattern')
            # replace generic year in pattern with the specific one needed so the correct file is found.
            _file_pattern = _file_pattern.replace('(?P<year>\d{4})', '(?P<year>{0})'.format(self.product_date.year))
            _file_pattern = _file_pattern.replace('(?P<month>\d{2})', '(?P<month>{0:0>2})'.format(self.product_date.month))
            _file_pattern = _file_pattern.replace('(?P<day>\d{2})', '(?P<day>{0:0>2})'.format(self.product_date.day))

        for f in _flood_years:
            _threshold_file = None
            if threshold_file is None:
                _threshold_pattern = self.vp.get('FLOOD_FORECAST', 'threshold_pattern')
                _threshold_pattern = _threshold_pattern.replace('(?P<num_years>\d{2,4})', '{0:0>2}'.format(f))
            else:
                _threshold_pattern = None
                _threshold_file = threshold_file

            config += self.generate_flood_forecast_section(data_dir=_data_dir, file_pattern=_file_pattern,
                                                           threshold_file=_threshold_file, threshold_dir=_threshold_dir,
                                                           threshold_pattern=_threshold_pattern,
                                                           output_file=None, output_dir=_output_dir,
                                                           output_pattern=_output_pattern, num_years=f)

        self.product_pattern = self.vp.get('FLOOD_FORECAST', 'flood_forecast_pattern')
        self.product_pattern = self.product_pattern.replace('(?P<year>\d{4})', '(?P<year>{0})'.format(self.product_date.year))
        self.product_pattern = self.product_pattern.replace('(?P<month>\d{2})', '(?P<month>{0:0>2})'.format(self.product_date.month))
        self.product_pattern = self.product_pattern.replace('(?P<day>\d{2})', '(?P<day>{0:0>2})'.format(self.product_date.day))

        for i in range(0, _num_forecasts):
            # mosaic all the flood return periods for this set of days
            _mosaic_pattern = ''
            _forecast_days = ''.join(map(str, range(i+1,i+_num_forecasts)))
            _mosaic_output_pattern = self.vp.get('FLOOD_FORECAST', 'output_mosaic_pattern')
            _mosaic_output_pattern = _mosaic_output_pattern.replace('{forecast_day}', '{0}'.format(_forecast_days))

            for y in _flood_years:
                _forecast_pattern = self.product_pattern
                _forecast_pattern = _forecast_pattern.replace('(?P<num_years>\d{2,4})', '{0:0>2}'.format(y))
                _forecast_pattern = _forecast_pattern.replace('(?P<forecast_period>fd\d{3})',
                                                              'fd{0}'.format(_forecast_days))
                _mosaic_pattern = '{0}|{1}'.format(_mosaic_pattern, _forecast_pattern)
            _mosaic_pattern = _mosaic_pattern[1:]  # remove initial '|'
            _raster = RasterDatasetImpl.RasterDatasetImpl()
            config += _raster.generate_mosaic_section(input_dir=_output_dir, file_pattern=_mosaic_pattern,
                                                      output_dir=_output_dir, output_pattern=_mosaic_output_pattern)
        self.product_pattern = self.vp.get('FLOOD_FORECAST', 'flood_mosaic_pattern')
        self.product_pattern = self.product_pattern.replace('(?P<year>\d{4})', '(?P<year>{0})'.format(self.product_date.year))
        self.product_pattern = self.product_pattern.replace('(?P<month>\d{2})', '(?P<month>{0:0>2})'.format(self.product_date.month))
        self.product_pattern = self.product_pattern.replace('(?P<day>\d{2})', '(?P<day>{0:0>2})'.format(self.product_date.day))

        return config

    def generate_flood_forecast_section(self, data_dir, file_pattern,
                                        threshold_file, threshold_dir, threshold_pattern,
                                        output_file, output_dir, output_pattern, num_years):
        cfg_string = """
    # Compute flood forecast
    - process: Analysis
      type: flood_alert"""
        cfg_string += """
      num_years: {num_years}""".format(num_years=num_years)
        cfg_string += """
      forecast_dir: {forecast_dir}
      forecast_pattern: '{forecast_pattern}'""".format(forecast_dir=data_dir, forecast_pattern=file_pattern)
        if threshold_file is not None:
            cfg_string += """
      threshold_file: {threshold_file}""".format(threshold_file=threshold_file)
        else:
            cfg_string += """
      threshold_dir: {threshold_dir}
      threshold_pattern: '{threshold_pattern}'""".format(threshold_dir=threshold_dir, threshold_pattern=threshold_pattern)
        if output_file is not None:
            cfg_string += """
      output_file: {output_file}""".format(output_file=output_file)
        else:
            cfg_string += """
      output_dir: {output_dir}
      output_pattern: '{output_pattern}'
      """.format(output_dir=output_dir, output_pattern=output_pattern)

        return cfg_string


