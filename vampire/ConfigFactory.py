__author__ = 'rochelle'
#!/usr/bin/env python

import datetime, time, calendar
import dateutil.rrule
import optparse, sys, os, traceback, errno
import ast
import re
import VampireDefaults



class ConfigFactory:
    'Base Class for configuration file generation'

    # gdal_dir = None
    # mrt_dir = None
    # base_data_dir = None
    # base_product_dir = None
    # country_names = None

    def __init__(self, name):
        self.name = name
        # load default values from .ini file
        self.vampire = VampireDefaults.VampireDefaults()
        # self.config = ExtParser.ExtParser()
        # cur_dir = os.path.join(os.getcwd(), 'vampire.ini')
        # ini_files = ['..\\..\\vampire.ini',
        #              os.path.join(os.getcwd(), '..\\vampire.ini'),
        #              cur_dir]
        # dataset = self.config.read(ini_files)
        # if len(dataset) == 0:
        #     msg = "Failed to open/find vampire.ini in {0}, {1} and {2}".format(ini_files[0], ini_files[1], ini_files[2])
        #     raise ValueError, msg
        # self.countries = dict(self.config.items('country'))
        # self.countries = dict((k.title(), v) for k, v in self.countries.iteritems())
        # self.country_codes = []
        # for c in self.countries:
        #     cc = ast.literal_eval(self.countries[c].replace("\n", ""))
        #     self.country_codes.append(cc['abbreviation'])
        #
#        self.vampire.print_defaults()
        return



    def generate_header_directory(self):
        file_string = """
directory:
    GDAL: {gdal_dir}
    MRT: {mrt_dir}
""".format(gdal_dir=self.vampire.get('directories', 'gdal_dir'),
               mrt_dir=self.vampire.get('directories', 'mrt_dir'))
        return file_string

    def generate_header_run(self):
        file_string = """
run:
"""
        return file_string

    def generate_header_chirps(self):
        file_string = """
temp: {temp_dir}

CHIRPS:
    filenames:
        input_prefix: chirps-v2.0
        input_extension: .tiff
        output_prefix: idn_cli_chirps-v2.0
        output_ext: .tif
""".format(temp_dir=self.vampire.get('directories', 'temp_dir'))
        return file_string

    def generate_chirps_download(self, interval, data_dir, start_date=None, end_date=None):
        file_string = """
    # download CHIRPS precipitation data
    - process: CHIRPS
      type: download
      interval: {interval}
      output_dir: {output_dir}""".format(interval=interval, output_dir=data_dir)
        # if start and end dates are specified, only download between these dates
        if start_date is not None:
            year = start_date.strftime("%Y")
            month = start_date.strftime("%m")
            # use 1st of start_date month to make sure end month is also included
            _first_date = start_date.replace(start_date.year, start_date.month, 1)
            dates = dateutil.rrule.rrule(dateutil.rrule.MONTHLY, dtstart = _first_date).between(_first_date, end_date, inc=True)
            file_string += """
      dates: ["""
            for d in dates:
                file_string += '{year}-{month},'.format(year=d.strftime("%Y"), month=d.strftime("%m"))
            file_string = file_string[:-1]
            file_string += """]
            """
        return file_string

    def generate_crop(self, country, input_dir, output_dir, file_pattern, output_pattern, boundary_file):
        file_string = """
    - process: Raster
      type: crop
      input_dir: {input_dir}
      output_dir: {output_dir}
      file_pattern: '{file_pattern}'
      output_pattern: '{output_pattern}'
      boundary_file: {boundary_file}
                """.format(country=country,
                           input_dir=input_dir,
                           output_dir=output_dir,
                           file_pattern=file_pattern,
                           output_pattern=output_pattern,
                           boundary_file=boundary_file
                           )
        return file_string

    def _generate_modis_download(self, country, product, tiles, data_dir, mosaic_dir, start_date, end_date):
        _file_string = """
    # download MODIS for {country_name} and mosaic if necessary
    - process: MODIS
      type: download
      product: {product}
      output_dir: {data_dir}""".format(country_name=country, product=product, data_dir=data_dir)
        if mosaic_dir is not None:
            _file_string += """
      mosaic_dir: {mosaic_dir}""".format(mosaic_dir=mosaic_dir)
        if tiles is not None:
            _file_string += """
      tiles: {tiles}""".format(tiles=tiles)
        # if start and end dates are specified, only download between these dates
        if start_date is not None:
            _year = start_date.strftime("%Y")
            _month = start_date.strftime("%m")
            # use 1st of start_date month to make sure end month is also included
            _first_date = start_date.replace(start_date.year, start_date.month, 1)
            _dates = dateutil.rrule.rrule(dateutil.rrule.MONTHLY, dtstart = _first_date).between(_first_date, end_date, inc=True)
            _file_string += """
      dates: ["""
            for d in _dates:
                _file_string += '{year}-{month},'.format(year=d.strftime("%Y"), month=d.strftime("%m"))
            _file_string = _file_string[:-1]
            _file_string += """]
            """
        return _file_string

    def _generate_modis_extract(self, input_dir, output_dir, product, file_pattern, output_pattern):
        file_string = """
    # extract MODIS {product}
    - process: MODIS
      type: extract
      layer: {product}
      input_dir: {input_dir}
      output_dir: {output_dir}
      file_pattern: '{file_pattern}'
      output_pattern: '{output_pattern}'
      """.format(product=product, input_dir=input_dir, output_dir=output_dir,
                                                 file_pattern=file_pattern, output_pattern=output_pattern)
        return file_string



    # Generate config file to calculate long term averages of CHIRPS data for a country or region
    # Takes: country name, interval (MONTHLY, SEASONAL, DEKAD)
    # Returns: string of config file commands to generate long term averages for given country and interval
    # Notes: will utilise default directories for downloading, processing and output unless specified.
    def generate_rainfall_long_term_average_config(self,
                                                   country,         # country to calculate average for
                                                   interval,        # interval to calculate (monthly, seasonal, dekad)
                                                   data_dir=None,   # download directory
                                                   lta_dir=None,    # long-term average output directory
                                                   start_date=None, end_date=None, # date range to download & calculate
                                                   download=True,   # need to download data files
                                                   crop_only=False  # already have lta files (global), so just crop
                                                   ):
        _file_pattern = ''
        _interval_name = interval
        if country == 'Global':
            _country_code = ''
        else:
            # get country code abbreviation that matches country name
            _country_code = self.vampire.get_country_code(country)
#            _country_code = ast.literal_eval(self.countries[params['country']].replace("\n", ""))['abbreviation']


        if interval == 'monthly':
            _interval_name = 'month'
            if crop_only:
                # file pattern is for global lta files
                _file_pattern = self.vampire.get('CHIRPS_Longterm_Average', 'global_lta_monthly_pattern')
                _crop_pattern = '{country}_{pattern}'.format(
                    country=_country_code,
                    pattern=self.vampire.get('CHIRPS_Longterm_Average', 'global_lta_output_monthly_pattern'))
            else:
                # file pattern is for global CHIRPS files
                _file_pattern = self.vampire.get('CHIRPS', 'global_monthly_pattern')
                _crop_pattern = "{country}{crop_output_pattern}".format(
                    country=_country_code,
                    crop_output_pattern=self.vampire.get('CHIRPS', 'crop_regional_output_monthly_pattern'))
        elif interval == 'seasonal':
            _interval_name = 'season'
            if crop_only:
                # file pattern is for global lta
                _file_pattern = self.vampire.get('CHIRPS_Longterm_Average', 'global_lta_seasonal_pattern')
                _crop_pattern = '{country}_{pattern}'.format(
                    country=_country_code,
                    pattern=self.vampire.get('CHIRPS_Longterm_Average', 'global_lta_output_seasonal_pattern'))
            else:
                # file pattern is for global CHIRPS files
                _file_pattern = self.vampire.get('CHIRPS', 'global_seasonal_pattern')
                _crop_pattern = "{country}{crop_output_pattern}".format(
                    country=_country_code,
                    crop_output_pattern=self.vampire.get('CHIRPS', 'crop_regional_output_seasonal_pattern'))
        elif interval == 'dekad':
            if crop_only:
                # file pattern is for global lta
                _file_pattern = self.vampire.get('CHIRPS_Longterm_Average', 'global_lta_dekad_pattern')
                _crop_pattern = '{country}_{pattern}'.format(
                    country=_country_code,
                    pattern=self.vampire.get('CHIRPS_Longterm_Average', 'global_lta_output_dekad_pattern'))
            else:
                _file_pattern = self.vampire.get('CHIRPS', 'global_dekad_pattern')
                _crop_pattern = "{country}{crop_output_pattern}".format(
                    country=_country_code,
                    crop_output_pattern=self.vampire.get('CHIRPS', 'crop_regional_output_dekad_pattern'))
        else:
            # interval not recognised
            raise ValueError, 'Interval not recognised as one of "monthly", "seasonal", or "dekad"'

        if data_dir is not None:
            # use specified data directory for input files
            _input_dir = data_dir
        else:
            # data_dir not set, use default CHIRPS data directory structure
            _input_dir = "{chirps_data_dir}\\{interval}\\{country}".format(
                chirps_data_dir=self.vampire.get('CHIRPS', 'data_dir'),
                interval=interval.capitalize(),
                country=_country_code)
            if crop_only:
                # already have lta files, so use default directory structure to find them
                _input_dir = "{chirps_data_dir}\\{interval}\\{country}\\Statistics_By{interval_name}".format(
                    chirps_data_dir=self.vampire.get('CHIRPS', 'data_dir'),
                    interval=interval.capitalize(),
                    country=_country_code,
                    interval_name=_interval_name)

        # use specified directory for output of lta files, if provided
        _output_dir = lta_dir
        if country == 'Global':
            # if Global, don't add 'Global' to directory path
            # _input_dir = "{chirps_data_dir}\\{interval}".\
            #     format(chirps_data_dir=self.config.get('CHIRPS', 'data_dir'),
            #            interval=params['interval'].capitalize())
            if _output_dir is None:
                # use default directory structure for output of lta files
                _output_dir = "{chirps_global_product_dir}\\{interval}\\Statistics_By_{interval_name}".format(
                    chirps_global_product_dir=self.vampire.get('CHIRPS', 'global_product_dir'),
                    interval=interval.capitalize(),
                    interval_name=_interval_name.capitalize())
        elif _country_code == self.vampire.get_home_country():
            # use default directory structure for output of lta files
            if _output_dir is None:
                _output_dir = "{chirps_home_product_dir}\\{interval}\\Statistics_By_{interval_name}".format(
                    chirps_home_product_dir=self.vampire.get('CHIRPS', 'home_country_product_dir'),
                    interval=interval.capitalize(),
                    interval_name=_interval_name.capitalize())
        else:
            if _output_dir is None:
                # use default directory structure for output of lta files
                _output_dir = "{chirps_regional_product_dir_prefix}\\{country}\\{chirps_regional_product_dir_suffix}" \
                    "\\{interval}\\Statistics_By{interval_name}".format(
                    chirps_regional_product_dir_prefix=self.vampire.get('CHIRPS', 'regional_product_dir_prefix'),
                    chirps_regional_product_dir_suffix=self.vampire.get('CHIRPS', 'regional_product_dir_suffix'),
                    country=_country_code,
                    interval=interval.capitalize(),
                    interval_name=_interval_name.capitalize())

        file_string = """
        ## Processing chain begin - Compute CHIRPS Long Term Averages\n
        """
        # Add download section if necessary
        if download:
            file_string += self.generate_chirps_download(interval, _input_dir, start_date, end_date)

        # Add crop to boundary if necessary - if already have global LTA OR downloading and country isn't global
        _boundary_file = None
        if crop_only or (country != 'Global' and download):
            _boundary_file = self.vampire.get_country(country)['chirps_boundary_file']
            _country_dir = "{input_dir}\\{country}".format(input_dir=_input_dir, country=_country_code)
            if crop_only:
                _country_dir = _output_dir
            file_string += """
        # Crop global CHIRPS data to {country}""".format(country=country)
            file_string += self.generate_crop(country, _input_dir, _country_dir, _file_pattern,
                                              _crop_pattern, _boundary_file)
            _input_dir = _country_dir

        if not crop_only:
            # Add long-term average calculation
            file_string += """

    - process: CHIRPS
      type: longterm_average
      interval: {interval}
      input_dir: {input_dir}
      output_dir: {output_dir}
      file_pattern: '{file_pattern}'
  """.format(interval=interval, input_dir=_input_dir, output_dir=_output_dir,
             file_pattern=_file_pattern)

        return file_string

    # Generate rainfall anomaly for the given country, interval and month/season/dekad, downloading and cropping
    # data if necessary.
    # If the long-term average file is not specified, the default long-term average file pattern will be used instead.
    # If the current file is not specified, the default file pattern will be used instead.
    # If the output filename is not specified, the default file pattern will be used instead.
    def generate_rainfall_anomaly_config(self, country,     # country or region to process (or 'Global')
                                         interval,          # interval to process (monthly, seasonal, dekad)
                                         start_date,        # year and month to process
                                         season=None,       # season if needed
                                         dekad=None,        # dekad if needed
                                         cur_dir=None,      # directory containing the rainfall file to process
                                         cur_file=None,     # filename for the rainfall file (if not present, default dir and pattern will be used)
                                         lta_dir=None,      # directory containing long-term average files
                                         lta_file=None,     # long-term average file (if not present, lta_dir and default pattern will be used)
                                         output_dir=None,   # directory for output rainfall anomaly
                                         output_file=None,  # name of output file (default pattern will be used to generate this if not present)
                                         download=True,     # download data?
                                         crop=True):        # crop existing data?
        year = start_date.strftime("%Y")
        month = start_date.strftime("%m")
        if country == 'Global':
            crop = False

        # if output_file is specified, it will override the location of the output file.
        # if output_dir is specified, the rainfall anomaly result will be stored here.
        # the filename will be generated from the default pattern.
        if output_dir is not None:
            _out_dir = output_dir
        else:
            _out_dir = self.vampire.get('CHIRPS_Rainfall_Anomaly', 'output_dir')

        # if cur_file is specified, cur_dir is not used.
        # if cur_dir is specified, it is used with the default pattern to find the current rainfall file
        # if not specified, cur_dir is determined from the default values.
        if cur_dir is not None:
            _cur_dir = cur_dir
        else:
            if country == 'Global':
                _cur_dir = os.path.join(self.vampire.get('CHIRPS', 'data_dir'), interval.capitalize())
            else:
                _cur_dir = os.path.join(self.vampire.get('CHIRPS', 'data_dir'), '{interval}\\{ccode}'.format(
                    interval=interval, ccode=self.vampire.get_country_code(country).upper()
                ))
        if interval == 'monthly':
            _interval_name = 'month'
            _file_pattern = self.vampire.get('CHIRPS', 'global_monthly_pattern')
            if country == 'Global':
                _output_file_pattern = self.vampire.get('CHIRPS_Rainfall_Anomaly', 'ra_global_output_monthly_pattern')
                _crop_output_pattern = ''
                _cur_file_pattern = self.vampire.get('CHIRPS', 'global_monthly_pattern')
                _lta_file_pattern = self.vampire.get('CHIRPS_Longterm_Average', 'global_lta_monthly_pattern')
            else:
                _crop_output_pattern = '{0}{1}'.format(
                    self.vampire.get_country_code(country).lower(),
                    self.vampire.get('CHIRPS', 'crop_regional_output_monthly_pattern'))
                _output_file_pattern = self.vampire.get('CHIRPS_Rainfall_Anomaly', 'ra_regional_output_monthly_pattern')
                _cur_file_pattern = self.vampire.get('CHIRPS', 'regional_monthly_pattern')
                _lta_file_pattern = self.vampire.get('CHIRPS_Longterm_Average', 'regional_lta_monthly_pattern')
            # replace generic month in pattern with the specific one needed so the correct file is found.
            _cur_file_pattern = _cur_file_pattern.replace('(?P<month>\d{2})', '(?P<month>{0})'.format(month))
            _lta_file_pattern = _lta_file_pattern.replace('(?P<month>\d{2})', '(?P<month>{0})'.format(month))
        elif interval == 'seasonal':
            _interval_name = "season"
            _file_pattern = self.vampire.get('CHIRPS', 'global_seasonal_pattern')
            if country == 'Global':
                _crop_output_pattern = ''
                _output_file_pattern = self.vampire.get('CHIRPS_Rainfall_Anomaly', 'ra_global_output_seasonal_pattern')
                _cur_file_pattern = self.vampire.get('CHIRPS', 'global_seasonal_pattern')
                _lta_file_pattern = self.vampire.get('CHIRPS_Longterm_Average', 'global_lta_seasonal_pattern')
            else:
                _crop_output_pattern = '{0}{1}'.format(
                    self.vampire.get_country_code(country).lower(),
                    self.vampire.get('CHIRPS', 'crop_regional_output_seasonal_pattern'))
                _output_file_pattern = self.vampire.get('CHIRPS_Rainfall_Anomaly', 'ra_regional_output_seasonal_pattern')
                _cur_file_pattern = self.vampire.get('CHIRPS', 'regional_seasonal_pattern')
                _lta_file_pattern = self.vampire.get('CHIRPS_Longterm_Average', 'regional_lta_seasonal_pattern')
            # replace generic season in pattern with the specific one needed so the correct file is found.
            _lta_file_pattern = _lta_file_pattern.replace('(?P<season>\d{6})', '(?P<season>{0})'.format(season))
            _cur_file_pattern = _cur_file_pattern.replace('(?P<season>\d{6})', '(?P<season>{0})'.format(season))

        elif interval == 'dekad':
            _file_pattern = self.vampire.get('CHIRPS', 'global_dekad_pattern')
            _interval_name = interval
            if country == 'Global':
                _crop_output_pattern = ''
                _output_file_pattern = self.vampire.get('CHIRPS_Rainfall_Anomaly', 'ra_global_output_dekad_pattern')
                _cur_file_pattern = self.vampire.get('CHIRPS', 'global_dekad_pattern')
                _lta_file_pattern = self.vampire.get('CHIRPS_Longterm_Average', 'global_lta_dekad_pattern')
            else:
                _crop_output_pattern = '{0}{1}'.format(
                    self.vampire.get_country_code(country).lower(),
                    self.vampire.get('CHIRPS', 'crop_regional_output_dekad_pattern'))
                _output_file_pattern = self.vampire.get('CHIRPS_Rainfall_Anomaly', 'ra_regional_output_dekad_pattern')
                _cur_file_pattern = self.vampire.get('CHIRPS', 'regional_dekad_pattern')
                _lta_file_pattern = self.vampire.get('CHIRPS_Longterm_Average', 'regional_lta_dekad_pattern')
            # replace generic month and dekad in pattern with the specific one needed so the correct file is found.
            _cur_file_pattern = _cur_file_pattern.replace('(?P<month>\d{2})', '(?P<month>{0})'.format(month))
            _lta_file_pattern = _cur_file_pattern.replace('(?P<dekad>\d{1})', '(?P<dekad>{0})'.format(dekad))
            _lta_file_pattern = _lta_file_pattern.replace('(?P<month>\d{2})', '(?P<month>{0})'.format(season))
            _lta_file_pattern = _lta_file_pattern.replace('(?P<dekad>\d{1})', '(?P<dekad>{0})'.format(season))

        else:
            raise ValueError, 'Unrecognised interval {0}. Unable to generate rainfall anomaly config.'.format(
                interval)
            # _interval_name = interval
            # _crop_output_pattern = "'{0}".format(country.lower()) + "_cli_{product}.{year}.{month}{extension}'"
            # _file_pattern = ''
            # _cur_file_pattern = ''

        # replace generic year in pattern with the specific one needed so the correct file is found.
        _cur_file_pattern = _cur_file_pattern.replace('(?P<year>\d{4})', '(?P<year>{0})'.format(year))

        # directory for downloaded CHIRPS files
        _dl_output = "{0}\\{1}".format(self.vampire.get('CHIRPS','data_dir'),
                                       interval.capitalize())

        _num_yrs = int(self.vampire.get('CHIRPS_Longterm_Average', 'lta_date_range').split('-')[1]) - int(
            self.vampire.get('CHIRPS_Longterm_Average', 'lta_date_range').split('-')[0]
        )
        _boundary_file = None
        if country != 'Global':
            _boundary_file = self.vampire.get_country(country)['chirps_boundary_file']
        _country_code = self.vampire.get_country_code(country)

        # if lta_file is specified, lta_dir is not used.
        # if lta_dir is specified, it is used with the default pattern to find the long-term average rainfall file
        # if not specified, lta_dir is determined from the default values.
        if lta_dir is not None:
            _lta_dir = lta_dir
        else:
            if country == 'Global':
                _lta_dir = os.path.join(self.vampire.get('CHIRPS', 'global_product_dir'),
                                        '{interval}\\Statistics_By{interval_name}'.format(
                    interval=interval.capitalize(), interval_name=_interval_name.capitalize()))
            elif country == self.vampire.get_home_country():
                _lta_dir = os.path.join(self.vampire.get('CHIRPS', 'home_country_product_dir'),
                                        '{interval}\\Statistics_By{interval_name}'.format(
                                            interval=interval.capitalize(), interval_name=_interval_name.capitalize()))
            else:
                _lta_dir = os.path.join(self.vampire.get('CHIRPS', 'regional_product_dir_prefix'),
                                        '{country}\\{suffix}\\{interval}\\Statistics_By{interval_name}'.format(
                                            country=_country_code.upper(),
                                            suffix=self.vampire.get('CHIRPS', 'regional_product_dir_suffix'),
                                            interval=interval.capitalize(),
                                            interval_name=_interval_name.capitalize()))

        file_string = """
    ## Processing chain begin - Compute Rainfall Anomaly\n"""
        if download:
            # add commands to download data
            file_string += self.generate_chirps_download(interval, _dl_output, start_date, start_date)
        if crop:
            # add commands to crop global data to region
            file_string += """
        # Crop global CHIRPS data to {country}""".format(country=country)
            file_string += self.generate_crop(country, _dl_output,
                                              os.path.join(_dl_output, _country_code.upper()),
                                              _file_pattern, _crop_output_pattern, _boundary_file
                                                     )

        file_string += """
    # compute rainfall anomaly
    - process: Analysis
      type: rainfall_anomaly"""
        if cur_file is not None:
            file_string += """
      current_file: {cur_file}""".format(cur_file=cur_file)
        else:
            file_string += """
      current_dir: {cur_dir}
      current_file_pattern: '{cur_pattern}'""".format(cur_dir=_cur_dir, cur_pattern=_cur_file_pattern)

        if lta_file is not None:
            file_string += """
      longterm_avg_file: {lta_file}""".format(lta_file=lta_file)
        else:
            file_string += """
      longterm_avg_dir: {lta_dir}
      longterm_avg_file_pattern: '{lta_pattern}'""".format(lta_dir=_lta_dir, lta_pattern=_lta_file_pattern)

        if output_file is not None:
            file_string += """
      output_file: {output_file}""".format(output_file=output_file)
        else:
            file_string += """
      output_dir: {out_dir}
      output_file_pattern: '{out_pattern}'""".format(out_dir=_out_dir, out_pattern=_output_file_pattern)

        file_string += """
    ## Processing chain end - Compute Rainfall Anomaly
        """
        return file_string

    #
    #
    #
    def generate_days_since_last_rainfall(self, country, start_date, data_dir=None, output_dir=None,
                                          threshold=None, max_days=None, download=True, crop=True):
        if country == 'Global':
            crop = False

        _data_dir = data_dir
        if _data_dir is None:
            if country == 'Global':
                _data_dir = self.vampire.get('CHIRPS', 'data_dir')
            elif self.vampire.get_country_code(country).upper() == self.vampire.get('vampire', 'home_country'):
                _data_dir = self.vampire.get('CHIRPS', 'home_country_product_dir')
            else:
                _data_dir = os.path.join(self.vampire.get('CHIRPS', 'data_dir'),
                                        'Daily\\{1}'.format(self.vampire.get_country_code(country)))
        # threshold of precipitation to count as 'wet' day
        _threshold = threshold
        if _threshold is None:
            _threshold = self.vampire.get('CHIRPS_Days_Since_Last_Rain', 'default_threshold')

        # number of days to check for rain prior to start date
        _max_days = max_days
        if _max_days is None:
            _max_days = self.vampire.get('CHIRPS_Days_Since_Last_Rain', 'default_max_days')

        # directory for days since last rainfall output
        _output_dir = output_dir
        if _output_dir is None:
            _output_dir = self.vampire.get('CHIRPS_Days_Since_Last_Rain', 'output_dir')

        # directory for downloaded CHIRPS files
        _dl_output = "{0}\\{1}".format(self.vampire.get('CHIRPS','data_dir'),
                                       'Daily')
        _boundary_file = None
        _crop_output_pattern = None
        _file_pattern = None
        if country != 'Global':
            _boundary_file = self.vampire.get_country(country)['chirps_boundary_file']
            _crop_output_pattern = '{0}{1}'.format(
                    self.vampire.get_country_code(country).lower(),
                    self.vampire.get('CHIRPS', 'crop_regional_output_daily_pattern'))

            if crop:
                _file_pattern = self.vampire.get('CHIRPS', 'global_daily_pattern')
            else:
                _file_pattern = self.vampire.get('CHIRPS', 'regional_daily_pattern')

        _first_date = start_date - datetime.timedelta(days=int(_max_days))

        file_string = """
    ## Processing chain begin - Compute Days Since Last Rain\n"""
        if download:
            # add commands to download data
            file_string += self.generate_chirps_download('Daily', _dl_output, _first_date, start_date)
        if crop:
            # add commands to crop global data to region
            file_string += """
        # Crop global CHIRPS data to {country}""".format(country=country)
            file_string += self.generate_crop(country, _dl_output,
                                              os.path.join(_dl_output,
                                              self.vampire.get_country_code(country).upper()),
                                              _file_pattern, _crop_output_pattern, _boundary_file
                                             )
            _data_dir = os.path.join(_dl_output, self.vampire.get_country_code(country).upper())
            _file_pattern = self.vampire.get('CHIRPS', 'regional_daily_pattern')
        file_string += """
    # compute days since last rainfall
    - process: Analysis
      type: days_since_last_rain
      input_dir: {input_dir}
      output_dir: {output_dir}
      file_pattern: '{file_pattern}'
      start_date: {start_date}
      threshold: {threshold}
      max_days: {max_days}""".format(
            input_dir=_data_dir, output_dir=_output_dir, file_pattern=_file_pattern,
            start_date='{year}-{month}-{day}'.format(year=start_date.year, month=start_date.month, day=start_date.day),
            threshold=_threshold, max_days=_max_days
        )
        file_string += """
    ## Processing chain end - Compute Days Since Last Rain
        """
        return file_string

    # Generate temperature long-term averages
    def generate_temperature_long_term_average(self,
                                               country,                 # country to calculate VCI for
                                               start_date,              # start and end of date range to calculate
                                               end_date=None,           # long-term average for (uses month & year only)
                                               data_dir=None,           # directory for downloaded data
                                               lta_dir=None,            # directory for long-term average output
                                               functions=None,
                                               download=True,           # download MODIS data if True
                                               extract=True,            # extract LST if True
                                               average=True,            # calculate day/night average if True
                                               lst_extract_day_dir=None,# directory for extracted LST day
                                               lst_extract_night_dir=None,# directory for extracted LST night
                                               lst_average_dir=None,    # directory for average of LST day & night
                                               crop=True,               # crop EVI to region if True
                                               crop_dir=None,           # directory to save cropped files
                                               boundary_file=None):     # shapefile for cropping boundary
        _year = start_date.strftime("%Y")
        _month = start_date.strftime("%m")
        _base_date = datetime.datetime.strptime("2000.{0}.01".format(_month), "%Y.%m.%d")
        _day_of_year = _base_date.timetuple().tm_yday
        if calendar.isleap(int(_year)) and _day_of_year > 60:
            _day_of_year = _day_of_year - 1
        # set up functions
        if functions is None:
            _functions = ['MIN', 'MAX']
        else:
            _functions = functions
        _product = self.vampire.get('MODIS', 'land_surface_temperature_product')

        # set up download directory
        if data_dir is None:
            _data_dir = self.vampire.get('MODIS', 'temperature_download_dir')
        else:
            _data_dir = data_dir
        # set up output directory
        if lta_dir is None:
            if country == 'Global':
                _lta_dir = self.vampire.get('MODIS_LST_Long_Term_Average', 'global_lta_dir')
            elif self.vampire.get_country_code(country).upper() == self.vampire.get('vampire', 'home_country'):
                _lta_dir = self.vampire.get('MODIS_LST_Long_Term_Average', 'home_country_lta_dir')
            else:
                _lta_dir = os.path.join(self.vampire.get('MODIS_LST_Long_Term_Average', 'regional_lta_dir_prefix'),
                                        self.vampire.get_country_code(country).upper())
                _lta_dir = os.path.join(_lta_dir, self.vampire.get('MODIS_LST_Long_Term_Average',
                                                                   'regional_lta_dir_suffix'))
        # setup directories for extracting Day & Night data
        if lst_extract_day_dir is None:
            _lst_extract_day_dir = self.vampire.get('MODIS_LST', 'lst_extract_day_dir')
        else:
            _lst_extract_day_dir = lst_extract_day_dir
        if lst_extract_night_dir is None:
            _lst_extract_night_dir = self.vampire.get('MODIS_LST', 'lst_extract_night_dir')
        else:
            _lst_extract_night_dir = lst_extract_night_dir

        # setup directories for computing average of day & night
        if lst_average_dir is None:
            _lst_average_dir = self.vampire.get('MODIS_LST', 'lst_extract_dir')
        else:
            _lst_average_dir = lst_average_dir

        _lta_input_pattern = None
        _lta_output_pattern = None

        # get boundary file if needed
        if country == 'Global':
            crop = False
            _lta_input_pattern = self.vampire.get('MODIS_LST', 'lst_average_pattern')
            _lta_output_pattern = self.vampire.get('MODIS_LST_Long_Term_Average', 'lta_output_pattern')
        elif self.vampire.get_country_code(country).upper() == self.vampire.get('vampire', 'home_country'):
            _lta_input_pattern = self.vampire.get('MODIS_LST', 'lst_regional_pattern')
            _lta_output_pattern = self.vampire.get('MODIS_LST_Long_Term_Average', 'lta_regional_output_pattern')
            if boundary_file is None:
                _boundary_file = self.vampire.get('MODIS', 'home_country_temperature_boundary')
            else:
                _boundary_file = boundary_file
            if crop_dir is None:
                _crop_output_dir = self.vampire.get('MODIS_LST', 'home_country_lst_dir')
            else:
                _crop_output_dir = crop_dir
            _lst_crop_output_pattern = self.vampire.get('MODIS_LST', 'lst_regional_output_pattern')
            _lst_crop_output_pattern = _lst_crop_output_pattern.replace('{country}',
                                                                        '{0}'.format(
                                                                            self.vampire.get_country_code(country).lower()))
        else:
            _lta_input_pattern = self.vampire.get('MODIS_LST', 'lst_regional_pattern')
            _lta_output_pattern = self.vampire.get('MODIS_LST_Long_Term_Average', 'lta_regional_output_pattern')
            if boundary_file is None:
                _boundary_file = os.path.join(self.vampire.get('MODIS', 'regional_temperature_boundary_prefix'),
                                              self.vampire.get_country_code(country).upper())
                _boundary_file = os.path.join(_boundary_file,
                                              self.vampire.get('MODIS', 'regional_temperature_boundary_prefix'))
                _boundary_file = os.path.join(_boundary_file,
                                              '{country}{filename}'.format(
                                                  country=self.vampire.get_country_code(country).lower(),
                                                  filename=self.vampire.get('MODIS', 'regional_temperature_boundary_file')))
            else:
                _boundary_file = boundary_file
            if crop_dir is None:
                _crop_output_dir = self.vampire.get('MODIS_LST', 'regional_lst_dir_prefix')
                _crop_output_dir = os.path.join(_crop_output_dir, self.vampire.get_country_code(country).upper())
                _crop_output_dir = os.path.join(_crop_output_dir, self.vampire.get('MODIS_LST', 'regional_lst_dir_suffix'))
            else:
                _crop_output_dir = crop_dir
            _lst_crop_output_pattern = self.vampire.get('MODIS_LST', 'lst_regional_output_pattern')
            _lst_crop_output_pattern = _lst_crop_output_pattern.replace('{country}',
                                                                        '{0}'.format(
                                                                            self.vampire.get_country_code(country).lower()))

        file_string = """
    ## Processing chain begin - Compute Land Surface Temperature Long-term Average"""
        if download:
            # TODO: need to fix this to set a reasonable end date
            if start_date is not None and end_date is None:
                start_date = None
            _download_dir = _data_dir
            file_string += self._generate_modis_download(country=country, product=_product, tiles=None,
                                                         data_dir=_download_dir, mosaic_dir=None,
                                                         start_date=start_date, end_date=end_date)
            # MODIS downloads to a date directory
            _data_dir = os.path.join(_download_dir, '{0}.{1}.01'.format(_year, _month))
        if extract:
            # need to extract both day and night layers then average them
            # pattern for files to extract from
            _modis_pattern = self.vampire.get('MODIS_LST', 'lst_pattern')
            # replace generic year and month in pattern with the specific ones needed so the correct file is found.
            _modis_pattern = _modis_pattern.replace('(?P<year>\d{4})', '(?P<year>{0})'.format(_year))
            _modis_pattern = _modis_pattern.replace('(?P<month>\d{2})', '(?P<month>{0})'.format(_month))
            _lst_output_pattern = self.vampire.get('MODIS_LST', 'lst_output_pattern')
            file_string += self._generate_modis_extract(input_dir=_data_dir, output_dir=_lst_extract_day_dir,
                                                        product='LST_Day',
                                                        file_pattern=_modis_pattern,
                                                        output_pattern=_lst_output_pattern)
            file_string += self._generate_modis_extract(input_dir=_data_dir, output_dir=_lst_extract_night_dir,
                                                        product='LST_Night',
                                                        file_pattern=_modis_pattern,
                                                        output_pattern=_lst_output_pattern)
            _lst_day_night_pattern = self.vampire.get('MODIS_LST', 'lst_day_night_pattern')
            _lst_day_night_pattern = _lst_day_night_pattern.replace('(?P<year>\d{4})', '(?P<year>{0})'.format(_year))
            _lst_day_night_pattern = _lst_day_night_pattern.replace('(?P<dayofyear>\d{3})', '(?P<dayofyear>{0})'.format(_day_of_year))
            _lst_average_output_pattern = self.vampire.get('MODIS_LST', 'lst_average_output_pattern')
            file_string += """
    # Compute average of day and night temperatures
    - process: MODIS
      type: calc_average
      layer: day_night_temp
      lst_day_dir: {lst_day_dir}
      lst_night_dir: {lst_night_dir}
      output_dir: {lst_average_dir}
      file_pattern: '{input_pattern}'
      output_pattern: '{output_pattern}'
            """.format(lst_day_dir=_lst_extract_day_dir, lst_night_dir=_lst_extract_night_dir,
                       lst_average_dir=_lst_average_dir, input_pattern=_lst_day_night_pattern,
                       output_pattern=_lst_average_output_pattern)

        if crop:
            file_string += """
    # Crop data to {country}""".format(country=country)
            _lst_pattern = self.vampire.get('MODIS_LST', 'lst_average_pattern')
            # replace generic year and month in pattern with the specific ones needed so the correct file is found.
            _lst_pattern = _lst_pattern.replace('(?P<year>\d{4})', '(?P<year>{0})'.format(_year))
            _lst_pattern = _lst_pattern.replace('(?P<dayofyear>\d{3})', '(?P<dayofyear>{0})'.format(_day_of_year))
            file_string += self.generate_crop(boundary_file=_boundary_file, country=country,
                                              file_pattern=_lst_pattern,
                                              input_dir=_lst_average_dir,
                                              output_dir=_crop_output_dir,
                                              output_pattern=_lst_crop_output_pattern)

        file_string += """
    # calculate long-term statistics
    - process: MODIS
      type: calc_average
      layer: long_term_statistics
      input_dir: {input_dir}
      output_dir: {output_dir}
      product: {product}
      file_pattern: '{input_pattern}'
      output_pattern: '{output_pattern}'""".format(input_dir=_data_dir, output_dir=_lta_dir, product=_product,
                                               input_pattern=_lta_input_pattern, output_pattern=_lta_output_pattern)

        if start_date is not None:
            file_string += """
      start_date: {s_date}""".format(s_date=start_date)
        if end_date is not None:
            file_string += """
      end_date: {e_date}""".format(e_date=end_date)

        if _functions is not None:
            file_string += """
      functions: {fn}""".format(fn=_functions)
        file_string += """
    ## Processing chain end - Compute Temperature Long-Term Statistics
"""
        return file_string


    # Generate vegetation condition index for the given country, for the month and year in start_date.
    # If required, MODIS vegetation data will be downloaded, mosaic'd, extracted and cropped as necessary.
    # If the current EVI file is not specified, then it will be found in the directory specified in evi_cur_dir
    # using the pattern in evi_cur_pattern.
    # If the long-term maximum file is not specified, it will be found in the directory specified in evi_max_dir
    # using the pattern in evi_max_pattern.  If evi_max_pattern is not specified, the default pattern will be used
    # instead.
    # If the long-term minimum file is not specified, it will be found in the directory specified in evi_min_dir
    # using the pattern in evi_min_pattern. If evi_min_pattern is not specified, the default pattern will be used
    # instead.
    # If the output filename is not specified, a default file pattern will be generated using the output_dir and
    # output_pattern. If output_pattern is not specified, the default VCI output pattern will be used instead.
    def generate_vci_config(self, country,              # country to calculate VCI for
                            start_date,                 # date to calculate monthly VCI for (uses month & year only)
                            end_date=None,              #
                            evi_cur_file=None,          # current EVI filename for given month/year
                            evi_cur_dir=None,           # directory to look for EVI file in if not specified
                            evi_cur_pattern=None,       # pattern to use to find EVI file if not specified
                            evi_max_file=None,          # EVI long-term maximum filename
                            evi_max_dir=None,           # directory of EVI long-term maximum
                            evi_max_pattern=None,       # pattern for finding EVI long-term maximum
                            evi_min_file=None,          # EVI long-term minimum filename
                            evi_min_dir=None,           # directory of EVI long-term minimum
                            evi_min_pattern=None,       # pattern for finding long-term minimum
                            output_filename=None,       # filename for VCI output
                            output_dir=None,            # directory for VCI output
                            output_pattern=None,        # pattern for generating VCI output filename if not specified
                            tiles=None,                 # list of MODIS tiles for specified country
                            download=True,              # download MODIS data if True
                            download_dir=None,          # directory to download MODIS into
                            mosaic_dir=None,            # directory for mosaic of MODIS tiles
                            extract=True,               # extract EVI if True
                            evi_extract_dir=None,       # directory for extracted EVI
                            crop=True,                  # crop EVI to region if True
                            evi_country_dir=None,       # directory to save cropped file
                            boundary_file=None):        # shapefile for cropping boundary
        _year = start_date.strftime("%Y")
        _month = start_date.strftime("%m")
        _base_date = datetime.datetime.strptime("2000.{0}.01".format(_month), "%Y.%m.%d")
        _day_of_year = _base_date.timetuple().tm_yday
        if calendar.isleap(int(_year)) and _day_of_year > 60:
            _day_of_year = _day_of_year - 1

        # Use boundary file if specified
        if boundary_file is None:
            if self.vampire.get_country_code(country).upper() == self.vampire.get('vampire', 'home_country'):
                _boundary_file = self.vampire.get('MODIS', 'home_country_vegetation_boundary')
            else:
                _boundary_file = os.path.join(self.vampire.get('MODIS', 'regional_vegetation_boundary_prefix'),
                                              self.vampire.get_country_code(country).upper())
                _boundary_file = os.path.join(_boundary_file,
                                              self.vampire.get('MODIS', 'regional_vegetation_boundary_prefix'))
                _boundary_file = os.path.join(_boundary_file,
                                              '{country}{filename}'.format(
                                                  country=self.vampire.get_country_code(country).lower(),
                                                  filename=self.vampire.get('MODIS', 'regional_vegetation_boundary_file')))
        else:
            _boundary_file = boundary_file

        # directory for EVI file output (& crop input)
        if evi_extract_dir is None:
            _evi_extract_dir = self.vampire.get('MODIS_EVI', 'evi_extract_dir')
        else:
            _evi_extract_dir = evi_extract_dir

        _evi_crop_output_pattern = self.vampire.get('MODIS_EVI', 'evi_regional_output_pattern')
        _evi_crop_output_pattern = _evi_crop_output_pattern.replace('{country}',
                                                                    '{0}'.format(
                                                                        self.vampire.get_country_code(country).lower()))

        _output_file = output_filename
        _output_dir = None
        _output_pattern = None
        if output_filename is None:
            if output_dir is None:
                _output_dir = self.vampire.get('MODIS_VCI', 'vci_product_dir')
            else:
                _output_dir = output_dir
            if output_pattern is None:
                _output_pattern = self.vampire.get('MODIS_VCI', 'vci_output_pattern')

        _evi_crop_output_dir = evi_country_dir
        _cur_file = evi_cur_file
        _evi_dir = evi_cur_dir
        _evi_cur_pattern = evi_cur_pattern
        if evi_cur_pattern is None:
            _evi_cur_pattern = self.vampire.get('MODIS_EVI', 'evi_regional_pattern')
            # replace generic year in pattern with the specific one needed so the correct file is found.
            _evi_cur_pattern = _evi_cur_pattern.replace('(?P<year>\d{4})', '(?P<year>{0})'.format(_year))
            _evi_cur_pattern = _evi_cur_pattern.replace('(?P<month>\d{2})', '(?P<month>{0})'.format(_month))
        _evi_max_file = evi_max_file
        _evi_min_file = evi_min_file
        _evi_max_dir = evi_max_dir
        _evi_min_dir = evi_min_dir
        if evi_min_pattern is None:
            _evi_min_pattern = self.vampire.get('MODIS_EVI_Long_Term_Average', 'lta_pattern')
            _evi_min_pattern = _evi_min_pattern.replace('(?P<day_of_yr>\d{3})', '(?P<day_of_yr>{0})'.format(_day_of_year))
            _evi_min_pattern = _evi_min_pattern.replace('(?P<statistic>.*)', 'min')
        else:
            _evi_min_pattern = evi_min_pattern
        if evi_max_pattern is None:
            _evi_max_pattern = self.vampire.get('MODIS_EVI_Long_Term_Average', 'lta_pattern')
            _evi_max_pattern = _evi_max_pattern.replace('(?P<day_of_yr>\d{3})', '(?P<day_of_yr>{0})'.format(_day_of_year))
            _evi_max_pattern = _evi_max_pattern.replace('(?P<statistic>.*)', 'max')
        else:
            _evi_max_pattern = evi_max_pattern

        if self.vampire.get_country_code(country).upper() == self.vampire.get('vampire', 'home_country').upper():
            # directory for country EVI file (crop output)
            if evi_country_dir is None:
                _evi_crop_output_dir = self.vampire.get('MODIS_EVI', 'home_country_evi_dir')
            if evi_cur_file is None:
                if evi_cur_dir is None:
                    _evi_dir = self.vampire.get('MODIS_EVI', 'home_country_evi_dir')
                _cur_file = None

            if evi_max_file is None:
                if evi_max_dir is None:
                    _evi_max_dir = self.vampire.get('MODIS_EVI_Long_Term_Average', 'home_country_lta_dir')
                _evi_max_file = None

            if evi_min_file is None:
                if evi_min_dir is None:
                    _evi_min_dir = self.vampire.get('MODIS_EVI_Long_Term_Average', 'home_country_lta_dir')
                _evi_min_file = None
        elif country == 'Global':
            # Global MODIS doesn't make sense
            raise
        else:
            # directory for country EVI file (crop output)
            if evi_country_dir is None:
                _evi_crop_output_dir = os.path.join(self.vampire.get('MODIS_EVI', 'regional_evi_dir_prefix'),
                                                    os.path.join(self.vampire.get_country_code(country).upper(),
                                                                 self.vampire.get('MODIS_EVI', 'regional_evi_dir_suffix')))
            if evi_cur_file is None:
                if evi_cur_dir is None:
                    _evi_dir = os.path.join(self.vampire.get('MODIS_EVI', 'regional_evi_dir_prefix'),
                                                    os.path.join(self.vampire.get_country_code(country).lower(),
                                                                 self.vampire.get('MODIS_EVI', 'regional_evi_dir_suffix')))
                _cur_file = None

            if evi_max_file is None:
                if evi_max_dir is None:
                    _evi_max_dir = os.path.join(self.vampire.get('MODIS_EVI_Long_Term_Average',
                                                                 'regional_lta_dir_prefix'),
                                                    os.path.join(self.vampire.get_country_code(country).lower(),
                                                                 self.vampire.get('MODIS_EVI_Long_Term_Average',
                                                                                  'regional_lta_dir_suffix')))
                _evi_max_file = None

            if evi_min_file is None:
                if evi_min_dir is None:
                    _evi_min_dir = os.path.join(self.vampire.get('MODIS_EVI_Long_Term_Average',
                                                                 'regional_lta_dir_prefix'),
                                                    os.path.join(self.vampire.get_country_code(country).lower(),
                                                                 self.vampire.get('MODIS_EVI_Long_Term_Average',
                                                                                  'regional_lta_dir_suffix')))
                _evi_min_file = None

        _mosaic_dir = mosaic_dir

        file_string = """
    ## Processing chain begin - Compute Vegetation Condition Index"""
        if download:
            # Use download directory if specified.
            if download_dir is None:
                _data_dir = self.vampire.get('MODIS', 'vegetation_download_dir')
            else:
                _data_dir = download_dir
            # Use tiles if specified
            if tiles is None:
                _tiles = self.vampire.get_country(country)['modis_tiles']
                if _tiles == '':
                    # try using regional tiles & crop
                    _tiles = self.vampire.get_country('Regional Burea ROI')['modis_tiles']
                    crop = True
            else:
                _tiles = tiles
            if mosaic_dir == None:
                _mosaic_dir = self.vampire.get('MODIS', 'vegetation_mosaic_dir')
            _product = self.vampire.get('MODIS', 'vegetation_product')
            print _product

            file_string += self._generate_modis_download(country=country, product=_product, tiles=_tiles,
                                                         data_dir=_data_dir, mosaic_dir=_mosaic_dir,
                                                         start_date=start_date, end_date=end_date)
            _data_dir = _mosaic_dir

        if extract:
            if _mosaic_dir is None:
                _mosaic_dir = self.vampire.get('MODIS', 'vegetation_mosaic_dir')
            # pattern for files to extract from
            _modis_pattern = self.vampire.get('MODIS', 'modis_monthly_pattern')
            # replace generic year and month in pattern with the specific ones needed so the correct file is found.
            _modis_pattern = _modis_pattern.replace('(?P<year>\d{4})', '(?P<year>{0})'.format(_year))
            _modis_pattern = _modis_pattern.replace('(?P<month>\d{2})', '(?P<month>{0})'.format(_month))
            _evi_output_pattern = self.vampire.get('MODIS_EVI', 'evi_output_pattern')
            file_string += self._generate_modis_extract(input_dir=_mosaic_dir, output_dir=_evi_extract_dir,
                                                        product='EVI',
                                                        file_pattern=_modis_pattern,
                                                        output_pattern=_evi_output_pattern)

        if crop:
            file_string += """
    # Crop data to {country}""".format(country=country)
            _evi_pattern = self.vampire.get('MODIS_EVI', 'evi_pattern')
            # replace generic year and month in pattern with the specific ones needed so the correct file is found.
            _evi_pattern = _evi_pattern.replace('(?P<year>\d{4})', '(?P<year>{0})'.format(_year))
            _evi_pattern = _evi_pattern.replace('(?P<month>\d{2})', '(?P<month>{0})'.format(_month))
            file_string += self.generate_crop(boundary_file=_boundary_file, country=country,
                                              file_pattern=_evi_pattern,
                                              input_dir=_evi_extract_dir,
                                              output_dir=_evi_crop_output_dir,
                                              output_pattern=_evi_crop_output_pattern)

        file_string += """
    - process: Analysis
      type: VCI"""
        if _cur_file is not None:
            file_string += """
      current_file: {current_file}""".format(current_file=_cur_file)
        else:
            file_string += """
      current_dir: {current_dir}
      current_file_pattern: '{current_pattern}'""".format(current_dir=_evi_dir, current_pattern=_evi_cur_pattern)
        if _evi_max_file is not None:
            file_string += """
      EVI_max_file: {evi_max}""".format(_evi_max_file)
        else:
            file_string += """
      EVI_max_dir: {evi_max_dir}
      EVI_max_pattern: '{evi_max_pattern}'""".format(evi_max_dir=_evi_max_dir, evi_max_pattern=_evi_max_pattern)
        if _evi_min_file is not None:
            file_string += """
      EVI_min_file: {evi_min}""".format(_evi_max_file)
        else:
            file_string += """
      EVI_min_dir: {evi_min_dir}
      EVI_min_pattern: '{evi_min_pattern}'""".format(evi_min_dir=_evi_min_dir, evi_min_pattern=_evi_min_pattern)
        if _output_file is not None:
            file_string += """
      output_file: {output_file}""".format(_output_file)
        else:
            file_string += """
      output_dir: {output_dir}
      output_file_pattern: '{output_pattern}'""".format(output_dir=_output_dir, output_pattern=_output_pattern)

        file_string += """
    ## Processing chain end - Compute Vegetation Condition Index
"""
        return file_string

    # Generate temperature condition index for the given country, for the month and year in start_date.
    # If required, MODIS land surface temperature data will be downloaded, extracted and cropped as necessary.
    # If the current LST file is not specified, then it will be found in the directory specified in lst_cur_dir
    # using the pattern in lst_cur_pattern.
    # If the long-term maximum file is not specified, it will be found in the directory specified in lst_max_dir
    # using the pattern in lst_max_pattern.  If lst_max_pattern is not specified, the default pattern will be used
    # instead.
    # If the long-term minimum file is not specified, it will be found in the directory specified in lst_min_dir
    # using the pattern in lst_min_pattern. If lst_min_pattern is not specified, the default pattern will be used
    # instead.
    # If the output filename is not specified, a default file pattern will be generated using the output_dir and
    # output_pattern. If output_pattern is not specified, the default TCI output pattern will be used instead.
    def generate_tci_config(self, country,              # country to calculate TCI for
                            start_date,                 # date to calculate monthly TCI for (uses month & year only)
                            end_date=None,              #
                            lst_cur_file=None,          # current LST filename for given month/year
                            lst_cur_dir=None,           # directory to look for LST file in if not specified
                            lst_cur_pattern=None,       # pattern to use to find LST file if not specified
                            lst_max_file=None,          # LST long-term maximum filename
                            lst_max_dir=None,           # directory of LST long-term maximum
                            lst_max_pattern=None,       # pattern for finding LST long-term maximum
                            lst_min_file=None,          # LST long-term minimum filename
                            lst_min_dir=None,           # directory of LST long-term minimum
                            lst_min_pattern=None,       # pattern for finding long-term minimum
                            output_filename=None,       # filename for TCI output
                            output_dir=None,            # directory for TCI output
                            output_pattern=None,        # pattern for generating TCI output filename if not specified
                            download=True,              # download MODIS data if True
                            download_dir=None,          # directory to download MODIS into
                            extract=True,               # extract LST if True
                            lst_extract_day_dir=None,   # directory for extracted LST Day
                            lst_extract_night_dir=None, # directory for extracted LST Night
                            lst_extract_dir=None,       # directory for extracted average LST
                            crop=True,                  # crop LST to region if True
                            lst_country_dir=None,       # directory to save cropped file
                            boundary_file=None):        # shapefile for cropping boundary
        _year = start_date.strftime("%Y")
        _month = start_date.strftime("%m")
        _base_date = datetime.datetime.strptime("2000.{0}.01".format(_month), "%Y.%m.%d")
        _day_of_year = _base_date.timetuple().tm_yday
#        if calendar.isleap(int(_year)) and _day_of_year > 60:
#            _day_of_year = _day_of_year - 1

        _lst_dir = lst_cur_dir
        _lst_max_dir = lst_max_dir
        _lst_min_dir = lst_min_dir

        if lst_cur_pattern is None:
            _lst_cur_pattern = self.vampire.get('MODIS_LST', 'lst_regional_pattern')
            # replace generic year in pattern with the specific one needed so the correct file is found.
            _lst_cur_pattern = _lst_cur_pattern.replace('(?P<year>\d{4})', '(?P<year>{0})'.format(_year))
            _lst_cur_pattern = _lst_cur_pattern.replace('(?P<month>\d{2})', '(?P<month>{0})'.format(_month))
        else:
            _lst_cur_pattern = lst_cur_pattern

        if country == 'Global':
            crop = False
        else:
            # Use boundary file if specified
            if boundary_file is None:
                if self.vampire.get_country_code(country).upper() == self.vampire.get('vampire', 'home_country'):
                    _boundary_file = self.vampire.get('MODIS', 'home_country_temperature_boundary')
                else:
                    _boundary_file = os.path.join(self.vampire.get('MODIS', 'regional_temperature_boundary_prefix'),
                                                  self.vampire.get_country_code(country).upper())
                    _boundary_file = os.path.join(_boundary_file,
                                                  self.vampire.get('MODIS', 'regional_temperature_boundary_prefix'))
                    _boundary_file = os.path.join(_boundary_file,
                                                  '{country}{filename}'.format(
                                                      country=self.vampire.get_country_code(country).lower(),
                                                      filename=self.vampire.get('MODIS', 'regional_temperature_boundary_file')))
            else:
                _boundary_file = boundary_file
            _lst_crop_output_pattern = self.vampire.get('MODIS_LST', 'lst_regional_output_pattern')
            _lst_crop_output_pattern = _lst_crop_output_pattern.replace('{country}',
                                                                        '{0}'.format(
                                                                            self.vampire.get_country_code(country).lower()))
            _lst_crop_output_dir = lst_country_dir

            if self.vampire.get_country_code(country).upper() == self.vampire.get('vampire', 'home_country').upper():
                # home country
                # directory for country LST file (crop output)
                if lst_country_dir is None:
                    _lst_crop_output_dir = self.vampire.get('MODIS_LST', 'home_country_lst_dir')
                if lst_cur_file is None:
                    if lst_cur_dir is None:
                        _lst_dir = self.vampire.get('MODIS_LST', 'home_country_lst_dir')
                    _cur_file = None

                if lst_max_file is None:
                    if lst_max_dir is None:
                        _lst_max_dir = self.vampire.get('MODIS_LST_Long_Term_Average', 'home_country_lta_dir')
                    _lst_max_file = None

                if lst_min_file is None:
                    if lst_min_dir is None:
                        _lst_min_dir = self.vampire.get('MODIS_LST_Long_Term_Average', 'home_country_lta_dir')
                    _lst_min_file = None
            else:
                # regional country
                # directory for country LST file (crop output)
                if lst_country_dir is None:
                    _lst_crop_output_dir = os.path.join(self.vampire.get('MODIS_LST', 'regional_lst_dir_prefix'),
                                                        os.path.join(self.vampire.get_country_code(country).upper(),
                                                                     self.vampire.get('MODIS_LST', 'regional_lst_dir_suffix')))
                if lst_cur_file is None:
                    if lst_cur_dir is None:
                        _lst_dir = os.path.join(self.vampire.get('MODIS_LST', 'regional_lst_dir_prefix'),
                                                        os.path.join(self.vampire.get_country_code(country).lower(),
                                                                     self.vampire.get('MODIS_LST', 'regional_lst_dir_suffix')))
                    _cur_file = None

                if lst_max_file is None:
                    if lst_max_dir is None:
                        _lst_max_dir = os.path.join(self.vampire.get('MODIS_LST_Long_Term_Average',
                                                                     'regional_lta_dir_prefix'),
                                                        os.path.join(self.vampire.get_country_code(country).lower(),
                                                                     self.vampire.get('MODIS_LST_Long_Term_Average',
                                                                                      'regional_lta_dir_suffix')))
                    _lst_max_file = None

                if lst_min_file is None:
                    if lst_min_dir is None:
                        _lst_min_dir = os.path.join(self.vampire.get('MODIS_LST_Long_Term_Average',
                                                                     'regional_lta_dir_prefix'),
                                                        os.path.join(self.vampire.get_country_code(country).lower(),
                                                                     self.vampire.get('MODIS_LST_Long_Term_Average',
                                                                                      'regional_lta_dir_suffix')))
                    _lst_min_file = None

        # directory for LST file output (& crop input)
        if lst_extract_day_dir is None:
            _lst_extract_day_dir = self.vampire.get('MODIS_LST', 'lst_extract_day_dir')
        else:
            _lst_extract_day_dir = lst_extract_night_dir
        if lst_extract_night_dir is None:
            _lst_extract_night_dir = self.vampire.get('MODIS_LST', 'lst_extract_night_dir')
        else:
            _lst_extract_night_dir = lst_extract_night_dir
        if lst_extract_dir is None:
            _lst_extract_dir = self.vampire.get('MODIS_LST', 'lst_extract_dir')
        else:
            _lst_extract_dir = lst_extract_dir

        _output_file = output_filename
        _output_dir = None
        _output_pattern = None
        if output_filename is None:
            if output_dir is None:
                _output_dir = self.vampire.get('MODIS_TCI', 'tci_product_dir')
            else:
                _output_dir = output_dir
            if output_pattern is None:
                _output_pattern = self.vampire.get('MODIS_TCI', 'tci_output_pattern')

        _cur_file = lst_cur_file
#        _lst_dir = lst_cur_dir
        _lst_max_file = lst_max_file
        _lst_min_file = lst_min_file
#        _lst_max_dir = lst_max_dir
#        _lst_min_dir = lst_min_dir
        if lst_min_pattern is None:
            _lst_min_pattern = self.vampire.get('MODIS_LST_Long_Term_Average', 'lta_pattern')
            _lst_min_pattern = _lst_min_pattern.replace('(?P<day_of_yr>\d{3})', '(?P<day_of_yr>{0})'.format(_day_of_year))
            _lst_min_pattern = _lst_min_pattern.replace('(?P<statistic>.*)', 'min')
        else:
            _lst_min_pattern = lst_min_pattern
        if lst_max_pattern is None:
            _lst_max_pattern = self.vampire.get('MODIS_LST_Long_Term_Average', 'lta_pattern')
            _lst_max_pattern = _lst_max_pattern.replace('(?P<day_of_yr>\d{3})', '(?P<day_of_yr>{0})'.format(_day_of_year))
            _lst_max_pattern = _lst_max_pattern.replace('(?P<statistic>.*)', 'max')
        else:
            _lst_max_pattern = lst_max_pattern


        _data_dir = download_dir

        file_string = """
    ## Processing chain begin - Compute Temperature Condition Index"""
        if download:
            # Use download directory if specified.
            if download_dir is None:
                _data_dir = self.vampire.get('MODIS', 'temperature_download_dir')
            else:
                _data_dir = download_dir
            _product = self.vampire.get('MODIS', 'land_surface_temperature_product')
            print _product

            file_string += self._generate_modis_download(country=country, product=_product, tiles=None,
                                                         data_dir=_data_dir, mosaic_dir=None,
                                                         start_date=start_date, end_date=end_date)
            # MODIS downloads to a date directory
            _data_dir = os.path.join(_data_dir, '{0}.{1}.01'.format(_year, _month))
        if extract:
            # need to extract both day and night layers then average them
            # pattern for files to extract from
            _modis_pattern = self.vampire.get('MODIS_LST', 'lst_pattern')
            # replace generic year and month in pattern with the specific ones needed so the correct file is found.
            _modis_pattern = _modis_pattern.replace('(?P<year>\d{4})', '(?P<year>{0})'.format(_year))
            _modis_pattern = _modis_pattern.replace('(?P<month>\d{2})', '(?P<month>{0})'.format(_month))
            _lst_output_pattern = self.vampire.get('MODIS_LST', 'lst_output_pattern')
            file_string += self._generate_modis_extract(input_dir=_data_dir, output_dir=_lst_extract_day_dir,
                                                        product='LST_Day',
                                                        file_pattern=_modis_pattern,
                                                        output_pattern=_lst_output_pattern)
            file_string += self._generate_modis_extract(input_dir=_data_dir, output_dir=_lst_extract_night_dir,
                                                        product='LST_Night',
                                                        file_pattern=_modis_pattern,
                                                        output_pattern=_lst_output_pattern)
#     - process: MODIS
#       type: temp_average
#       directory_day: {data_dir}\MODIS\MOD11C3\Processed\Day
#       directory_night: {data_dir}\MODIS\MOD11C3\Processed\Night
#       directory_output: {data_dir}\MODIS\MOD11C3\Processed\Average
#       input_pattern: {input_pattern}
#       output_pattern: {avg_pattern}
            _lst_day_night_pattern = self.vampire.get('MODIS_LST', 'lst_day_night_pattern')
            _lst_day_night_pattern = _lst_day_night_pattern.replace('(?P<year>\d{4})', '(?P<year>{0})'.format(_year))
            _lst_day_night_pattern = _lst_day_night_pattern.replace('(?P<dayofyear>\d{3})', '(?P<dayofyear>{0})'.format(_day_of_year))
            _lst_average_output_pattern = self.vampire.get('MODIS_LST', 'lst_average_output_pattern')
            file_string += """
    # Compute average of day and night temperatures
    - process: MODIS
      type: calc_average
      layer: day_night_temp
      lst_day_dir: {lst_day_dir}
      lst_night_dir: {lst_night_dir}
      output_dir: {lst_average_dir}
      file_pattern: '{input_pattern}'
      output_pattern: '{output_pattern}'
            """.format(lst_day_dir=_lst_extract_day_dir, lst_night_dir=_lst_extract_night_dir,
                       lst_average_dir=_lst_extract_dir, input_pattern=_lst_day_night_pattern,
                       output_pattern=_lst_average_output_pattern)

        if crop:
            file_string += """
    # Crop data to {country}""".format(country=country)
            _lst_pattern = self.vampire.get('MODIS_LST', 'lst_average_pattern')
            # replace generic year and month in pattern with the specific ones needed so the correct file is found.
            _lst_pattern = _lst_pattern.replace('(?P<year>\d{4})', '(?P<year>{0})'.format(_year))
            _lst_pattern = _lst_pattern.replace('(?P<dayofyear>\d{3})', '(?P<dayofyear>{0})'.format(_day_of_year))
            file_string += self.generate_crop(boundary_file=_boundary_file, country=country,
                                              file_pattern=_lst_pattern,
                                              input_dir=_lst_extract_dir,
                                              output_dir=_lst_crop_output_dir,
                                              output_pattern=_lst_crop_output_pattern)

        file_string += """
    # Compute temperature condition index
    - process: Analysis
      type: TCI"""
        if _cur_file is not None:
            file_string += """
      current_file: {current_file}""".format(current_file=_cur_file)
        else:
            file_string += """
      current_dir: {current_dir}
      current_file_pattern: '{current_pattern}'""".format(current_dir=_lst_dir, current_pattern=_lst_cur_pattern)
        if _lst_max_file is not None:
            file_string += """
      LST_max_file: {lst_max}""".format(_lst_max_file)
        else:
            file_string += """
      LST_max_dir: {lst_max_dir}
      LST_max_pattern: '{lst_max_pattern}'""".format(lst_max_dir=_lst_max_dir, lst_max_pattern=_lst_max_pattern)
        if _lst_min_file is not None:
            file_string += """
      LST_min_file: {lst_min}""".format(_lst_max_file)
        else:
            file_string += """
      LST_min_dir: {lst_min_dir}
      LST_min_pattern: '{lst_min_pattern}'""".format(lst_min_dir=_lst_min_dir, lst_min_pattern=_lst_min_pattern)
        if _output_file is not None:
            file_string += """
      output_file: {output_file}""".format(_output_file)
        else:
            file_string += """
      output_dir: {output_dir}
      output_file_pattern: '{output_pattern}'""".format(output_dir=_output_dir, output_pattern=_output_pattern)

        file_string += """
    ## Processing chain end - Compute Temperature Condition Index
"""
        return file_string

#     def generate_tci_config(self, country, interval, start_date, output):
#         year = start_date.strftime("%Y")
#         month = start_date.strftime("%m")
#         basedate = datetime.datetime.strptime("2000.{0}.01".format(month), "%Y.%m.%d")
#         dayofyear = basedate.timetuple().tm_yday
#
#         _input_pattern = '^(?P<product>MOD\d{2}C\d{1}).A(?P<year>\d{4})(?P<dayofyear>\d{3}).(?P<version>\d{3}).(?P<code>.*).(?P<subset>hdf_\d{2})(?P<extension>\.tif$)'
#         _avg_output_pattern = "'{product}.A{year}{dayofyear}.{version}.{code}.avg{extension}'"
#         if country == 'IDN':
#             _boundary_file = "{0}\\01_Data\\02_IDN\ShapeFiles\Boundaries\Subset\MODIS\idn_phy_modis_lst_005_grid_diss_a.shp".format(
#                 self.vampire.get('vampire', 'base_product_dir'))
#             _output_pattern = 'idn_cli_{product}.{year}{dayofyear}.{version}{extension}'
#             _LST_max_file = '{0}\\01_Data\\02_IDN\Rasters\Climate\Temperature\MODIS\MOD11C3\Statistics_byMonth' \
#                     '\{1}'.format(self.vampire.get('vampire', 'base_product_dir'),
#                                   (_defaults['lst_max_file'][country]).format(month))
#             _LST_min_file = '{0}\\01_Data\\02_IDN\Rasters\Climate\Temperature\MODIS\MOD11C3\Statistics_byMonth' \
#                     '\{1}'.format(self.vampire.get('vampire', 'base_product_dir'),
#                                   (_defaults['lst_min_file'][country]).format(month))
#             _TCI_file = '{0}\MODIS\MOD11C3\Processed\IDN\LST\{1}' \
#                 .format(self.vampire.get('vampire', 'base_data_dir'),
#                         (_defaults['tci_file'][country]).format(year, str(dayofyear).zfill(3)))
#         else:
#
#             _boundary_file = "{0}\\01_Data\\03_Regional\{1}\ShapeFiles\Boundaries\Subset\MODIS\{2}_phy_modis_lst_005_grid_diss_a.shp".format(
#                 self.vampire.get('vampire', 'base_product_dir'), country, country.lower())
#             _output_pattern = "'{0}".format(country.lower()) + "_cli_{product}.{year}.{month}.{day}.{version}{extension}'"
#             _LST_max_file = '{0}\\01_Data\\03_Regional\{1}\Rasters\Climate\Temperature\MODIS\MOD11C3\Statistics_byMonth' \
#                     '\{2}_cli_MOD11C3.2000.2014.{3}.14yrs.max.tif'.format(self.vampire.get('vampire', 'base_product_dir'), country,
#                                                                           country.lower(), month)
#             _LST_min_file = '{0}\\01_Data\\03_Regional\{1}\Rasters\Climate\Temperature\MODIS\MOD11C3\Statistics_byMonth' \
#                     '\{2}_cli_MOD11C3.2000.2014.{3}.14yrs.min.tif'.format(self.vampire.get('vampire', 'base_product_dir'), country,
#                                                                           country.lower(), month)
#             _TCI_file = '{0}\MODIS\MOD11C3\Processed\{1}\LST\{2}_cli_MOD11C3.{3}{4}' \
#                     '.005.tif'.format(self.vampire.get('vampire', 'base_data_dir'), country, country.lower(), year, str(dayofyear).zfill(3))
#         file_pattern = '^(?P<product>MOD\d{2}C\d{1}).(?P<year>\d{4})(?P<dayofyear>\d{3}).(?P<version>\d{3}).(?P<average>avg)(?P<extension>\.tif$)'
#         file_string = """
#     ## Processing chain begin - Compute Temperature Condition Index
#     # download MODIS temperature data (MOD11C3.005)
#     - process: MODIS
#       type: download
#       output_dir: {data_dir}\MODIS\MOD11C3\HDF_MOD
#       product: MOD11C3.005
#       dates: [{year}-{month}]
#
#     - process: MODIS
#       type: extract
#       layer: LST_Day
#       input_dir: {data_dir}\MODIS\MOD11C3\HDF_MOD\{year}.{month}.01
#       output_dir: {data_dir}\MODIS\MOD11C3\Processed\Day
#
#     - process: MODIS
#       type: extract
#       layer: LST_Night
#       input_dir: {data_dir}\MODIS\MOD11C3\HDF_MOD\{year}.{month}.01
#       output_dir: {data_dir}\MODIS\MOD11C3\Processed\Night
#
#     - process: MODIS
#       type: temp_average
#       directory_day: {data_dir}\MODIS\MOD11C3\Processed\Day
#       directory_night: {data_dir}\MODIS\MOD11C3\Processed\Night
#       directory_output: {data_dir}\MODIS\MOD11C3\Processed\Average
#       input_pattern: {input_pattern}
#       output_pattern: {avg_pattern}
#
#     - process: Raster
#       type: crop
#       file_pattern: {file_pattern}
#       output_pattern: {country_output_pattern}
#       input_dir: {data_dir}\MODIS\MOD11C3\Processed\Average
#       output_dir: {data_dir}\MODIS\MOD11C3\Processed\{country}\LST
#       boundary_file: {boundary}
#
#     - process: Analysis
#       type: TCI
#       current_file: {tci_file}
#       LST_max_file: {lst_max}
#       LST_min_file: {lst_min}
#       output_file: {product_dir}\\05_Analysis\\03_Early_Warning\Temperature_Condition_Index\{country_l}_cli_MOD11C3.{year}.{month}.tci.tif
#     ## Processing chain end - Compute Temperature Condition Index
# """.format(data_dir=self.vampire.get('vampire', 'base_data_dir'), year=year, month=month, input_pattern=_input_pattern,
#        avg_pattern=_avg_output_pattern, country=country, country_output_pattern=_output_pattern,
#        boundary=_boundary_file, tci_file=_TCI_file, lst_max=_LST_max_file, lst_min=_LST_min_file, country_l=country.lower(),
#        product_dir=self.vampire.get('vampire', 'base_product_dir'), file_pattern=file_pattern)
#
#         return file_string

    def generate_vhi_config(self, country, interval, start_date, output):
        year = start_date.strftime("%Y")
        month = start_date.strftime("%m")
        basedate = datetime.datetime.strptime("2000.{0}.01".format(month), "%Y.%m.%d")
        dayofyear = basedate.timetuple().tm_yday
        _TCI_file = '{0}\\05_Analysis\\03_Early_Warning\Temperature_Condition_Index\{1}_cli_MOD11C3.{2}.{3}' \
                '.tci.tif'.format(self.vampire.get('vampire', 'base_product_dir'), country.lower(), year, month)
        _VCI_file = '{product_dir}\\05_Analysis\\03_Early_Warning\Vegetation_Condition_Index' \
            '\{country_l}_phy_MOD13A3.{year}.{month}.1_km_monthly_EVI_VCI.tif'.format\
            (product_dir=self.vampire.get('vampire', 'base_product_dir'),
             country_l=country.lower(),
             year=year, month=month)

        file_string = """
## Processing chain begin - Compute Vegetation Health Index
- process: Analysis
  type: VHI
  VCI_file: {vci_file}
  TCI_file: {tci_file}
  output_file: {product_dir}\\05_Analysis\\03_Early_Warning\Vegetation_Health_Index\{country_l}_cli_MOD11C3.{year}.{month}.1_km_monthly_EVI_LST_VHI.tif
## Processing chain end - Compute Vegetation Health Index
""".format(year=year, month=month, country=country, tci_file=_TCI_file,
       vci_file=_VCI_file, country_l=country.lower(),
       product_dir=self.vampire.get('vampire', 'base_product_dir'))

        return file_string


    def generate_config_file(self, output_file, params):
        try:
            pfile = open(output_file, 'a')
        except IOError as e:
            if e.errno == errno.EACCES:
                return "Error creating file " + output_file
            # Not a permission error.
            raise
        else:
            with pfile:
                pfile.write(self.generate_header_directory())
                if 'product' in params:
                    if params['product'] == "rainfall anomaly":
                        pfile.write(self.generate_header_chirps())
                        pfile.write(self.generate_header_run())
                        pfile.write(self.generate_rainfall_anomaly_config(params['country'], params['interval'],
                                                                       params['start_date'], params['output']))
                    elif params['product'] == "vhi":
                        pfile.write(self.generate_header_run())
                        pfile.write(self.generate_vci_config(params['country'], params['interval'],
                                                           params['start_date'], params['output']))
                        pfile.write(self.generate_tci_config(params['country'], params['interval'],
                                                           params['start_date'], params['output']))
                        pfile.write(self.generate_vhi_config(params['country'], params['interval'],
                                                           params['start_date'], params['output']))
                    elif params['product'] == "rainfall_longterm_average":
                        pfile.write(self.generate_header_chirps())
                        pfile.write(self.generate_header_run())
                        pfile.write(self.generate_rainfall_long_term_average_config(params['country'],
                                                                                    params['interval']
                                                                                    ))
                pfile.close()
        return 0


    # def generateConfig(country, product, interval, start_date, output):
    #     generateHeaderDirectory(output)
    #     if product == "rainfall anomaly":
    #         generateHeaderCHIRPS(output)
    #         generateHeaderRun(output)
    #         generateRainfallAnomalyConfig(country, interval, start_date, output)
    #     elif product == "vhi":
    #         generateHeaderRun(output)
    #         generateVCIConfig(country, interval, start_date, output)
    #         generateTCIConfig(country, interval, start_date, output)
    #         generateVHIConfig(country, interval, start_date, output)
    #     elif product == "rainfall_longterm_average":
    #         generateHeaderCHIRPS(output)
    #         generateHeaderRun(output)
    #         generateRainfallLongTermAverageConfig(country, interval, start_date, output)
    #     return 0

if __name__ == '__main__':
    try:
        start_time = time.time()
        parser = optparse.OptionParser(formatter=optparse.TitledHelpFormatter(), usage=globals()['__doc__'], version='$Id$')
        parser.add_option('-v', '--verbose', action='store_true', default=False, help='verbose output')
        parser.add_option('-c', '--country', dest='country', action='store', help='country id')
        parser.add_option('-p', '--product', dest='product', action='store', help='product')
        parser.add_option('-o', '--output', dest='output', action='store', help='output filename')
        parser.add_option('-i', '--interval', dest='interval', action='store', help='interval')
        parser.add_option('-d', '--start_date', dest='start_date', action='store', help='start year-month')
        (options, args) = parser.parse_args()
        #if len(args) < 1:
        #    parser.error ('missing argument')
        if options.verbose: print time.asctime()
        _country = None
        if options.country:
            _country = options.country
            print 'country=', _country
        _product = None
        if options.product:
            _product = options.product
            print 'product=', _product
        _output = None
        if options.output:
            _output = options.output
            print 'output=', _output
        _interval = None
        if options.interval:
            _interval = options.interval
            print 'interval=', _interval
        _start_date = None
        if options.start_date:
            _start_date = datetime.datetime.strptime(options.start_date, "%Y-%m")
            print 'start_date=', _start_date
        params = {}
        params['country'] = _country
        params['product'] = _product
        params['interval'] = _interval
        params['start_date'] = _start_date
        params['output_file'] = _output
        cf = ConfigFactory(_output)
        cf.generate_config_file(_output, params)
#        generateConfig(_country, _product, _interval, _start_date, _output)
        if options.verbose: print time.asctime()
        if options.verbose: print 'TOTAL TIME IN MINUTES:',
        if options.verbose: print (time.time() - start_time) / 60.0
        sys.exit(0)
    except KeyboardInterrupt, e: # Ctrl-C
        raise e
    except SystemExit, e: # sys.exit()
        raise e
    except Exception, e:
        print 'ERROR, UNEXPECTED EXCEPTION'
        print str(e)
        traceback.print_exc()
        os._exit(1)
