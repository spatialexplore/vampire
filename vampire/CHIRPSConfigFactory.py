import ConfigFactory
import dateutil.rrule
import datetime
import os

class CHIRPSConfigFactory(ConfigFactory.ConfigFactory):

    def __init__(self, name):
        ConfigFactory.ConfigFactory.__init__(self, name)

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

    def generate_download_section(self, interval, data_dir, start_date=None, end_date=None):
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

    def generate_rainfall_lta_section(self, interval, input_dir, output_dir, file_pattern):
        file_string = """
    - process: CHIRPS
      type: longterm_average
      interval: {interval}
      input_dir: {input_dir}
      output_dir: {output_dir}
      file_pattern: '{file_pattern}'
  """.format(interval=interval, input_dir=input_dir, output_dir=output_dir,
             file_pattern=file_pattern)
        return file_string

    def generate_download(self, country, interval, download_dir, start_date, end_date):
        # set up download directory
        if download_dir is None:
            # data_dir not set, use default CHIRPS data directory structure
            _download_dir = os.path.join(self.vampire.get('CHIRPS', 'data_dir'), interval.capitalize())
        else:
            _download_dir = download_dir

        # TODO: need to fix this to set a reasonable end date
        if start_date is not None and end_date is None:
            end_date = datetime.datetime.today()

        file_string = self.generate_download_section(interval=interval, data_dir=_download_dir,
                                                     start_date=start_date, end_date=end_date)
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
        file_string = """
        ## Processing chain begin - Compute CHIRPS Long Term Averages\n
        """

        _file_pattern = ''
        _interval_name = interval
        if country == 'Global':
            _country_code = ''
        else:
            # get country code abbreviation that matches country name
            _country_code = self.vampire.get_country_code(country)

        if interval.lower() == 'monthly':
            _interval_name = 'month'
            if crop_only:
                # file pattern is for global lta files
                _file_pattern = self.vampire.get('CHIRPS_Longterm_Average', 'global_lta_monthly_pattern')
                _crop_pattern = '{country}_{pattern}'.format(
                    country=_country_code.lower(),
                    pattern=self.vampire.get('CHIRPS_Longterm_Average', 'global_lta_output_monthly_pattern'))
            else:
                # file pattern is for global CHIRPS files
                _file_pattern = self.vampire.get('CHIRPS', 'global_monthly_pattern')
                _crop_pattern = "{country}{crop_output_pattern}".format(
                    country=_country_code.lower(),
                    crop_output_pattern=self.vampire.get('CHIRPS', 'crop_regional_output_monthly_pattern'))
        elif interval == 'seasonal':
            _interval_name = 'season'
            if crop_only:
                # file pattern is for global lta
                _file_pattern = self.vampire.get('CHIRPS_Longterm_Average', 'global_lta_seasonal_pattern')
                _crop_pattern = '{country}_{pattern}'.format(
                    country=_country_code.lower(),
                    pattern=self.vampire.get('CHIRPS_Longterm_Average', 'global_lta_output_seasonal_pattern'))
            else:
                # file pattern is for global CHIRPS files
                _file_pattern = self.vampire.get('CHIRPS', 'global_seasonal_pattern')
                _crop_pattern = "{country}{crop_output_pattern}".format(
                    country=_country_code.lower(),
                    crop_output_pattern=self.vampire.get('CHIRPS', 'crop_regional_output_seasonal_pattern'))
        elif interval == 'dekad':
            if crop_only:
                # file pattern is for global lta
                _file_pattern = self.vampire.get('CHIRPS_Longterm_Average', 'global_lta_dekad_pattern')
                _crop_pattern = '{country}_{pattern}'.format(
                    country=_country_code.lower(),
                    pattern=self.vampire.get('CHIRPS_Longterm_Average', 'global_lta_output_dekad_pattern'))
            else:
                _file_pattern = self.vampire.get('CHIRPS', 'global_dekad_pattern')
                _crop_pattern = "{country}{crop_output_pattern}".format(
                    country=_country_code.lower(),
                    crop_output_pattern=self.vampire.get('CHIRPS', 'crop_regional_output_dekad_pattern'))
        else:
            # interval not recognised
            raise ValueError, 'Interval not recognised as one of "monthly", "seasonal", or "dekad"'

        if data_dir is not None:
            # use specified data directory for input files
            _input_dir = data_dir
        else:
            # data_dir not set, use default CHIRPS data directory structure
            _input_dir = "{chirps_data_dir}\\{interval}".format(
                chirps_data_dir=self.vampire.get('CHIRPS', 'data_dir'),
                interval=interval.capitalize())
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
            _lta_pattern = self.vampire.get('CHIRPS', 'global_{0}_pattern'.format(interval))
            # if Global, don't add 'Global' to directory path
            # _input_dir = "{chirps_data_dir}\\{interval}".\
            #     format(chirps_data_dir=self.config.get('CHIRPS', 'data_dir'),
            #            interval=params['interval'].capitalize())
            if _output_dir is None:
                # use default directory structure for output of lta files
                _output_dir = "{chirps_global_product_dir}\\{interval}\\Statistics_By{interval_name}".format(
                    chirps_global_product_dir=self.vampire.get('CHIRPS', 'global_product_dir'),
                    interval=interval.capitalize(),
                    interval_name=_interval_name.capitalize())
        elif _country_code == self.vampire.get_home_country():
            _lta_pattern = self.vampire.get('CHIRPS', 'regional_{0}_pattern'.format(interval.lower()))
            # use default directory structure for output of lta files
            if _output_dir is None:
                _output_dir = "{chirps_home_product_dir}\\{interval}\\Statistics_By{interval_name}".format(
                    chirps_home_product_dir=self.vampire.get('CHIRPS', 'home_country_product_dir'),
                    interval=interval.capitalize(),
                    interval_name=_interval_name.capitalize())
        else:
            _lta_pattern = self.vampire.get('CHIRPS', 'regional_{0}_pattern'.format(interval.lower()))
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
    ## Processing chain begin - Compute CHIRPS Long Term Averages
        """
        # Add download section if necessary
        if download:
            file_string += self.generate_download(country=country, interval=interval, download_dir=_input_dir,
                                                  start_date=start_date, end_date=end_date)

        # Add crop to boundary if necessary - if already have global LTA OR downloading and country isn't global
        _boundary_file = None
        if crop_only or (country != 'Global' and download):
            _boundary_file = os.path.join(os.path.join(self.vampire.get('CHIRPS', 'regional_boundary_prefix'),
                                                       self.vampire.get('CHIRPS', 'regional_boundary_suffix')),
                                          '{0}{1}'.format(_country_code.lower(),
                                                          self.vampire.get('CHIRPS', 'regional_boundary_file')))
            _country_dir = "{input_dir}\\{country}".format(input_dir=_input_dir, country=_country_code)
            if crop_only:
                _country_dir = _output_dir
            file_string += self.generate_crop_section(country=country, input_dir=_input_dir,
                                                      output_dir=_country_dir, file_pattern=_file_pattern,
                                                      output_pattern=_crop_pattern, boundary_file=_boundary_file,
                                                      no_data=True)
            _input_dir = _country_dir

        if not crop_only:
            # Add long-term average calculation
            file_string += self.generate_rainfall_lta_section(interval=interval, input_dir=_input_dir,
                                                              output_dir=_output_dir, file_pattern=_lta_pattern)

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
        day = start_date.strftime("%d")
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
            if int(day) <=10:
                _dekad = 1
            elif int(day) <=20:
                _dekad = 2
            else:
                _dekad = 3
            _cur_file_pattern = _cur_file_pattern.replace('(?P<dekad>\d{1})', '(?P<dekad>{0})'.format(_dekad))
            _lta_file_pattern = _lta_file_pattern.replace('(?P<month>\d{02})', '(?P<month>{0})'.format(month))
            _lta_file_pattern = _lta_file_pattern.replace('(?P<dekad>\d{1})', '(?P<dekad>{0})'.format(_dekad))
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
        _country_code = self.vampire.get_country_code(country)
        if country != 'Global':
            _boundary_file = os.path.join(os.path.join(self.vampire.get('CHIRPS', 'regional_boundary_prefix'),
                                                       self.vampire.get('CHIRPS', 'regional_boundary_suffix')),
                                          '{0}{1}'.format(_country_code.lower(),
                                                          self.vampire.get('CHIRPS', 'regional_boundary_file')))
            #self.vampire.get_country(country)['chirps_boundary_file']

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
                                        '{suffix}\\{interval}\\Statistics_By{interval_name}'.format(
                                            suffix=self.vampire.get('CHIRPS', 'regional_product_dir_suffix'),
                                            interval=interval.capitalize(),
                                            interval_name=_interval_name.capitalize()))

        file_string = """
    ## Processing chain begin - Compute Rainfall Anomaly\n"""
        if download:
            # add commands to download data
            file_string += self.generate_download_section(interval=interval, data_dir=_dl_output,
                                                          start_date=start_date, end_date=start_date)
        if crop:
            # add commands to crop global data to region
            file_string += self.generate_crop_section(country=country, input_dir=_dl_output,
                                                      output_dir=os.path.join(_dl_output, _country_code.upper()),
                                                      file_pattern=_file_pattern, output_pattern=_crop_output_pattern,
                                                      boundary_file=_boundary_file, no_data=True
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
            file_string += self.generate_download_section(interval='Daily', data_dir=_dl_output,
                                                          start_date=_first_date, end_date=start_date)
        if crop:
            # add commands to crop global data to region
            file_string += """
        # Crop global CHIRPS data to {country}""".format(country=country)
            file_string += self.generate_crop_section(country=country, input_dir=_dl_output,
                                                      output_dir=os.path.join(_dl_output,
                                                      self.vampire.get_country_code(country).upper()),
                                                      file_pattern=_file_pattern,
                                                      output_pattern=_crop_output_pattern,
                                                      boundary_file=_boundary_file
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
