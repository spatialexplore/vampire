import ast
import os
import logging
import datetime

import BaseDataset
import RasterProductImpl
import RasterDatasetImpl

logger = logging.getLogger(__name__)

class FloodForecastProductImpl(RasterProductImpl.RasterProductImpl):
    """ Implementation of Flood Area Impact config file process generation.

    Implementation class for generating config file entries for Area impact of Flood Forecasting data product.

    """

    def __init__(self, country, product_date, interval, vampire_defaults):
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
        super(FloodForecastProductImpl, self).__init__()
        self.product_name = 'flood_forecast'
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
        self.publish_name = None
        return

    def generate_header(self):
        """ Generate details related to Flood Forecast that go in the config file header. """
        return ''

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
        """ Generate config file section for generating Flood Forecasts.

        Generate config file entries required to create Flood Forecasts for the specified country, date and interval.

        :param data_dir: Directory where the GFS files for the product date are located.
        :type data_dir: string
        :param file_pattern: Regular expression pattern to used to find the GFS file for the product date.
        :type file_pattern: string
        :param threshold_file:
        :type threshold_file: string
        :param threshold_dir:
        :type threshold_dir: string
        :param threshold_pattern:
        :type threshold_pattern: string
        :param accumulate_days: Number of days to forecast for.
        :type accumulate_days: int
        :param flood_years:
        :type flood_years: int
        :param output_file:
        :type output_file: string
        :param output_dir: Directory to save the Flood Forecast output files.
        :type output_dir: string
        :param output_pattern:
        :type output_pattern: string
        :return: Config file sections required for generating Flood Forecasts.
        :rtype: string
        """
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


    def generate_publish_config(self):
        """ Generate config section to publish Flood Forecast data product.

        Generates configuration file section to publish the Flood Forecast output file to a GIS server.

        :return: Config file sections required for publishing Flood Forecasts.
        :rtype: string
        """
        cfg_string = """"""
        _days = ast.literal_eval(self.vp.get('FLOOD_FORECAST', 'forecast_days'))
        _num_forecasts = ast.literal_eval(self.vp.get('FLOOD_FORECAST', 'forecast_period')) - _days +1
        _product_pattern = self.product_pattern
        _valid_from = self.valid_from_date
        _valid_to = self.valid_to_date()

        for i in range(0, _num_forecasts):
            _forecast_days = ''.join(map(str, range(i+1,i+_num_forecasts)))
            self.product_pattern = self.product_pattern.replace('(?P<forecast_period>fd\d{3})',
                                                              'fd{0}'.format(_forecast_days))
            self.publish_name = self.product_name
#            self.publish_name = '{0}_{1}'.format(self.product_name, _forecast_days)
            self.valid_from_date = _valid_from() + datetime.timedelta(days=i+1)
            self.valid_to_date = _valid_from() + datetime.timedelta(days=i+_num_forecasts)
            cfg_string += super(FloodForecastProductImpl, self).generate_publish_config()
            self.product_pattern = _product_pattern
            self.ingestion_date = self.valid_to_date
#            self.valid_from_date = _valid_from
#            self.valid_to_date = _valid_to

        return cfg_string
