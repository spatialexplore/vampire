import BaseDataset
import ImpactProductImpl
import os
import ast
import datetime
import dateutil.rrule
import dateutil.relativedelta
import logging
logger = logging.getLogger(__name__)

class FloodAreaImpactProductImpl(ImpactProductImpl.ImpactProductImpl):
    """ Initialise FloodAreaImpactProductImpl.

    Implementation class for FloodAreaImpactProduct.
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
    def __init__(self, country, valid_from_date, valid_to_date, vampire_defaults):
        super(FloodAreaImpactProductImpl, self).__init__()
        self.product_name = 'flood_impact_area'
        self.country = country
        self.valid_from_date = valid_from_date
        self.valid_to_date = valid_to_date
        self.vp = vampire_defaults

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
    def generate_config(self, hazard_file, hazard_dir, hazard_pattern,
                        flood_years=None, forecast_days=None, forecast_period=None,
                        boundary_file=None, boundary_dir=None, boundary_pattern=None, boundary_field=None,
                        output_file=None, output_dir=None, output_pattern=None, masked=False):
        config = """
    # Calculate area impact
        """
        _hazard_pattern = None
        _hazard_dir = None
        _hazard_file = None
        _boundary_file = None
        _boundary_pattern = None
        _boundary_dir = None
        _boundary_field = None
        _output_file = None
        _output_dir = None
        _output_pattern = None

        # if hazard_file is not None:
        #     _hazard_file = hazard_file
        # else:
        #     if hazard_pattern is not None:
        #         _hazard_pattern = hazard_pattern
        #     else:
        #         _hazard_pattern = self.vp.get('FLOOD_FORECAST', 'flood_forecast_pattern')
        #     if hazard_dir is not None:
        #         _hazard_dir = hazard_dir
        #     else:
        #         _hazard_dir = self.vp.get('FLOOD_FORECAST', 'product_dir')

        if boundary_file is not None:
            _boundary_file = boundary_file
        else:
            if boundary_dir is not None:
                _boundary_dir = boundary_dir
                _boundary_pattern = boundary_pattern
            else:
                _boundary_file = self.vp.get_country(self.country)['admin_3_boundary']
        if boundary_field is not None:
            _boundary_field = boundary_field
        else:
            _boundary_field = self.vp.get_country(self.country)['admin_3_boundary_area_code']

        if output_file is not None:
            self.output_file = output_file
        else:
            if output_dir is not None:
                self.output_dir = output_dir
                self.output_pattern = output_pattern
            else:
                self.output_dir = self.vp.get('hazard_impact', 'flood_output_dir')
                self.output_pattern = self.vp.get('hazard_impact', 'flood_area_output_pattern')

        if flood_years is None:
            _flood_years = ast.literal_eval(self.vp.get('FLOOD_FORECAST', 'flood_years'))
        else:
            _flood_years = flood_years
        if forecast_days is None:
            _forecast_days = int(self.vp.get('FLOOD_FORECAST', 'forecast_days'))
        else:
            _forecast_days = forecast_days
        if forecast_period is None:
            _forecast_period = int(self.vp.get('FLOOD_FORECAST', 'forecast_period'))
        else:
            _forecast_period = forecast_period
#        for f in _flood_years:
        _num_forecasts = _forecast_period - _forecast_days +1
        for i in range(1, _num_forecasts+1):
            _cur_forecast = ''.join(map(str, range(i, i+_forecast_days)))
#            _hazard_pattern = hazard_pattern.replace('(?P<num_years>\d{2,4})', '{0:0>2}'.format(f))
            _hazard_pattern = hazard_pattern.replace('(?P<forecast_period>fd\d{3})', 'fd{0}'.format(_cur_forecast))
#           _output_pattern = self.output_pattern.replace('{num_years}', '{0:0>2}'.format(f))
            _output_pattern = self.output_pattern.replace('{forecast_period}', '{0}'.format(_cur_forecast))
            _valid_from_date = self.valid_from_date + datetime.timedelta(i)
            _valid_to_date = self.valid_to_date + datetime.timedelta(i+_forecast_days-1)
            config += self._generate_area_impact_section(hazard_file=hazard_file, hazard_dir=hazard_dir,
                                                         hazard_pattern=_hazard_pattern, boundary_file=_boundary_file,
                                                         boundary_dir=_boundary_dir, boundary_pattern=_boundary_pattern,
                                                         boundary_field=_boundary_field,
                                                         output_file=self.output_file, output_dir=self.output_dir,
                                                         output_pattern=_output_pattern,
                                                         start_date=_valid_from_date, end_date=_valid_to_date)
        return config

    def _generate_area_impact_section(self, hazard_file, hazard_dir, hazard_pattern,
                                      boundary_file, boundary_dir, boundary_pattern, boundary_field,
                                      output_file, output_dir, output_pattern,
                                      start_date, end_date):
        cfg_string = """
    # calculate area impact (ha)
    - process: impact
      type: area
      hazard_type: flood"""
        if hazard_file is not None:
            cfg_string += """
      hazard_file: {hazard_file}""".format(hazard_file=hazard_file)
        else:
            cfg_string += """
      hazard_dir: {hazard_dir}
      hazard_pattern: '{hazard_pattern}'""".format(hazard_dir=hazard_dir, hazard_pattern=hazard_pattern)
        if boundary_file is not None:
            cfg_string += """
      boundary_file: {boundary_file}""".format(boundary_file=boundary_file)
        else:
            cfg_string += """
      boundary_dir: {boundary_dir}
      boundary_pattern: '{boundary_pattern}'""".format(boundary_dir=boundary_dir, boundary_pattern=boundary_pattern)
        cfg_string += """
      boundary_field: {boundary_field}""".format(boundary_field=boundary_field)
        if output_file is not None:
            cfg_string += """
      output_file: {output_dir}""".format(output_dir=output_dir)
        else:
            cfg_string += """
      output_dir: {output_dir}
      output_pattern: '{output_pattern}'""".format(output_dir=output_dir, output_pattern=output_pattern)
        if start_date is not None:
            cfg_string += """
      start_date: {start_date}""".format(start_date=start_date.strftime("%d/%m/%Y"))
        if end_date is not None:
            cfg_string += """
      end_date: {end_date}""".format(end_date=end_date.strftime("%d/%m/%Y"))
        cfg_string += """
        """
        return cfg_string

    def generate_publish_config(self):
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
            self.valid_from_date = _valid_from() + datetime.timedelta(days=i+1)
            self.valid_to_date = self.valid_from_date
            cfg_string += super(FloodAreaImpactProductImpl, self).generate_publish_config()
            self.product_pattern = _product_pattern
            self.valid_from_date = _valid_from
            self.valid_to_date = _valid_to
        return cfg_string
