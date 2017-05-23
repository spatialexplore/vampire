import ConfigFactory
import dateutil.rrule
import datetime
import calendar
import os

class MODISConfigFactory(ConfigFactory.ConfigFactory):

    def __init__(self, name, country, start_date, end_date=None):
        ConfigFactory.ConfigFactory.__init__(self, name)
        self.country = country
        self.set_dates(start_date, end_date)
        # self.start_date = start_date
        # self.end_date = end_date
        # self.year = self.start_date.strftime("%Y")
        # self.month = self.start_date.strftime("%m")
        # self.day = self.start_date.strftime("%d")
        # _base_date = datetime.datetime.strptime("2000.{0}.01".format(self.month), "%Y.%m.%d")
        # self.base_day_of_year = _base_date.timetuple().tm_yday
        # self.day_of_year = self.start_date.timetuple().tm_yday
        # print 'day of year: {0}'.format(self.day_of_year)
        # if calendar.isleap(int(self.year)) and self.day_of_year > 60:
        #     self.day_of_year = self.day_of_year - 1
        return

    def set_dates(self, start_date, end_date=None):
        self.start_date = start_date
        self.end_date = end_date
        self.year = self.start_date.strftime("%Y")
        self.month = self.start_date.strftime("%m")
        self.day = self.start_date.strftime("%d")
        _base_date = datetime.datetime.strptime("2000.{0}.01".format(self.month), "%Y.%m.%d")
        self.base_day_of_year = _base_date.timetuple().tm_yday
        self.day_of_year = self.start_date.timetuple().tm_yday
        print 'day of year: {0}'.format(self.day_of_year)
        print 'base day of year: {0}'.format(self.base_day_of_year)
#        if calendar.isleap(int(self.year)) and self.day_of_year > 60:
#            self.day_of_year = self.day_of_year - 1


    def generate_download_section(self, product, tiles, data_dir, mosaic_dir):
        _file_string = """
    # download MODIS for {country_name} and mosaic if necessary
    - process: MODIS
      type: download
      product: {product}
      output_dir: {data_dir}""".format(country_name=self.country, product=product, data_dir=data_dir)
        if mosaic_dir is not None:
            _file_string += """
      mosaic_dir: {mosaic_dir}""".format(mosaic_dir=mosaic_dir)
        if tiles is not None:
            _file_string += """
      tiles: {tiles}""".format(tiles=tiles)
        # if start and end dates are specified, only download between these dates
        if self.start_date is not None:
            # use 1st of start_date month to make sure end month is also included
            _first_date = self.start_date.replace(self.start_date.year, self.start_date.month, 1)
            _dates = dateutil.rrule.rrule(dateutil.rrule.MONTHLY, dtstart=_first_date).between(
                _first_date, self.end_date, inc=True)
            _file_string += """
      dates: ["""
            for d in _dates:
                _file_string += '{year}-{month},'.format(year=d.strftime("%Y"), month=d.strftime("%m"))
            _file_string = _file_string[:-1]
            _file_string += """]
            """
        return _file_string

    def generate_extract_section(self, input_dir, output_dir, product, layer, file_pattern, output_pattern):
        file_string = """
    # extract MODIS {layer}
    - process: MODIS
      type: extract
      product: {product}
      layer: {layer}
      input_dir: {input_dir}
      output_dir: {output_dir}
      file_pattern: '{file_pattern}'
      output_pattern: '{output_pattern}'
      """.format(product=product, layer=layer, input_dir=input_dir, output_dir=output_dir,
                 file_pattern=file_pattern, output_pattern=output_pattern)
        return file_string

    def generate_average_section(self, day_dir, night_dir, output_dir, input_pattern, output_pattern):
        file_string = """
    # Compute average of day and night temperatures
    - process: MODIS
      type: calc_average
      layer: day_night_temp
      lst_day_dir: {lst_day_dir}
      lst_night_dir: {lst_night_dir}
      output_dir: {lst_average_dir}
      file_pattern: '{input_pattern}'
      output_pattern: '{output_pattern}'
            """.format(lst_day_dir=day_dir, lst_night_dir=night_dir,
                       lst_average_dir=output_dir, input_pattern=input_pattern,
                       output_pattern=output_pattern)
        return file_string

    def generate_lst_lta_section(self, product, input_dir, output_dir, input_pattern, output_pattern, functions,
                                 interval):
        file_string = """
    # calculate long-term statistics
    - process: MODIS
      type: calc_average
      layer: long_term_statistics
      input_dir: {input_dir}
      output_dir: {output_dir}
      product: {product}
      file_pattern: '{input_pattern}'
      output_pattern: '{output_pattern}'""".format(input_dir=input_dir, output_dir=output_dir, product=product,
                                                   input_pattern=input_pattern, output_pattern=output_pattern)

        if self.start_date is not None:
            file_string += """
      start_date: {s_date}""".format(s_date=self.start_date)
        if self.end_date is not None:
            file_string += """
      end_date: {e_date}""".format(e_date=self.end_date)

        if functions is not None:
            file_string += """
      functions: {fn}""".format(fn=functions)

        if interval is not None:
            file_string += """
      interval: {interval}""".format(interval=interval)

        return file_string

    def generate_tci_section(self, cur_file,
                             cur_dir,
                             cur_pattern,
                             min_file,
                             min_dir,
                             min_pattern,
                             max_file,
                             max_dir,
                             max_pattern,
                             output_file,
                             output_dir,
                             output_pattern,
                             interval):
        file_string = """
    # Compute temperature condition index
    - process: Analysis
      type: TCI"""
        if cur_file is not None:
            file_string += """
      current_file: {current_file}""".format(current_file=cur_file)
        else:
            file_string += """
      current_dir: {current_dir}
      current_file_pattern: '{current_pattern}'""".format(current_dir=cur_dir, current_pattern=cur_pattern)
        if max_file is not None:
            file_string += """
      LST_max_file: {lst_max}""".format(lst_max=max_file)
        else:
            file_string += """
      LST_max_dir: {lst_max_dir}
      LST_max_pattern: '{lst_max_pattern}'""".format(lst_max_dir=max_dir, lst_max_pattern=max_pattern)
        if min_file is not None:
            file_string += """
      LST_min_file: {lst_min}""".format(lst_min=min_file)
        else:
            file_string += """
      LST_min_dir: {lst_min_dir}
      LST_min_pattern: '{lst_min_pattern}'""".format(lst_min_dir=min_dir, lst_min_pattern=min_pattern)
        if output_file is not None:
            file_string += """
      output_file: {output_file}""".format(output_file=output_file)
        else:
            file_string += """
      output_dir: {output_dir}
      output_file_pattern: '{output_pattern}'""".format(output_dir=output_dir, output_pattern=output_pattern)

        if interval is not None:
            file_string += """
      interval: {interval}""".format(interval=interval)

        return file_string

    def generate_vci_section(self, cur_file, cur_dir, cur_pattern, evi_max_file, evi_max_dir, evi_max_pattern,
                             evi_min_file, evi_min_dir, evi_min_pattern, output_file, output_dir, output_pattern):
        file_string = """
    # Compute vegetation condition index
    - process: Analysis
      type: VCI"""
        if cur_file is not None:
            file_string += """
      current_file: {current_file}""".format(current_file=cur_file)
        else:
            file_string += """
      current_dir: {current_dir}
      current_file_pattern: '{current_pattern}'""".format(current_dir=cur_dir, current_pattern=cur_pattern)
        if evi_max_file is not None:
            file_string += """
      EVI_max_file: {evi_max}""".format(evi_max=evi_max_file)
        else:
            file_string += """
      EVI_max_dir: {evi_max_dir}
      EVI_max_pattern: '{evi_max_pattern}'""".format(evi_max_dir=evi_max_dir, evi_max_pattern=evi_max_pattern)
        if evi_min_file is not None:
            file_string += """
      EVI_min_file: {evi_min}""".format(evi_min=evi_min_file)
        else:
            file_string += """
      EVI_min_dir: {evi_min_dir}
      EVI_min_pattern: '{evi_min_pattern}'""".format(evi_min_dir=evi_min_dir, evi_min_pattern=evi_min_pattern)
        if output_file is not None:
            file_string += """
      output_file: {output_file}""".format(output_file=output_file)
        else:
            file_string += """
      output_dir: {output_dir}
      output_file_pattern: '{output_pattern}'""".format(output_dir=output_dir, output_pattern=output_pattern)

        return file_string

    def generate_vhi_section(self, tci_file, tci_dir, tci_pattern,
                             vci_file, vci_dir, vci_pattern,
                             output_file, output_dir, output_pattern):
        file_string = """
    # Compute vegetation health index
    - process: Analysis
      type: VHI"""
        if vci_file is not None:
            file_string += """
      VCI_file: {vci_file}""".format(vci_file=vci_file)
        else:
            file_string += """
      VCI_dir: {vci_dir}
      VCI_pattern: '{vci_pattern}'""".format(vci_dir=vci_dir, vci_pattern=vci_pattern)

        if tci_file is not None:
            file_string += """
      TCI_file: {tci_file}""".format(tci_file=tci_file)
        else:
            file_string += """
      TCI_dir: {tci_dir}
      TCI_pattern: '{tci_pattern}'""".format(tci_dir=tci_dir, tci_pattern=tci_pattern)

        if output_file is not None:
            file_string += """
      output_file: {output_file}""".format(output_file=output_file)
        else:
            file_string += """
      output_dir: {output_dir}
      output_pattern: '{output_pattern}'""".format(output_dir=output_dir, output_pattern=output_pattern)

        return file_string
#         output_file: {product_dir}\\05_Analysis\\03_Early_Warning\Vegetation_Health_Index\{country_l}_cli_MOD11C3.{year}.{month}.1_km_monthly_EVI_LST_VHI.tif
# ## Processing chain end - Compute Vegetation Health Index
# """.format(year=year, month=month, country=country, tci_file=_TCI_file,
#        vci_file=_VCI_file, country_l=country.lower(),
#        product_dir=self.vampire.get('vampire', 'base_product_dir'))


    def generate_download(self, product, download_dir, mosaic_dir=None, tiles=None):

        # set up download directory
        if download_dir is None:
            _download_dir = self.vampire.get('MODIS_PRODUCTS', '{0}.download_dir'.format(product))
        else:
            _download_dir = download_dir

        output_dir = _download_dir

        # get mosaic directory if needed
        if mosaic_dir is None:
            if self.country != 'Global':
                _mosaic_dir = self.vampire.get('MODIS_PRODUCTS', '{0}.mosaic_dir'.format(product))
                output_dir = _mosaic_dir
            else:
                _mosaic_dir = None
        else:
            _mosaic_dir = mosaic_dir
            output_dir = _mosaic_dir

        # set tiles if needed
        if tiles is not None:
            _tiles = tiles
        else:
            if _mosaic_dir is not None:
                # need to mosaic, so must have tiles
                _tiles = self.vampire.get_country(self.country)['{0}_tiles'.format(product)]
            else:
                _tiles = None

        # TODO: need to fix this to set a reasonable end date
        if self.start_date is not None and self.end_date is None:
            self.end_date = datetime.datetime.today()

        file_string = self.generate_download_section(product=product, tiles=_tiles,
                                                     data_dir=_download_dir, mosaic_dir=_mosaic_dir)
        return file_string, output_dir


    def generate_extract_lst(self, product, data_dir, day_dir, night_dir):
        if data_dir is None:
            _data_dir = self.vampire.get('MODIS_LST', 'lst_download_dir')
        else:
            _data_dir = data_dir

        # setup directories for extracting Day & Night data
        if day_dir is None:
            _day_dir = self.vampire.get('MODIS_LST', 'lst_day_dir')
        else:
            _day_dir = day_dir

        if night_dir is None:
            _night_dir = self.vampire.get('MODIS_LST', 'lst_night_dir')
        else:
            _night_dir = night_dir

        # need to extract both day and night layers then average them
        # pattern for files to extract from
        if self.vampire.get('MODIS_PRODUCTS', '{0}.mosaic_dir'.format(product)) is None:
            # no mosaic, so data uses day of year
            _modis_pattern = self.vampire.get('MODIS_LST', 'lst_pattern')
        else:
            # already mosaic'd so use year.month.day format
            _modis_pattern = self.vampire.get('MODIS_LST', 'lst_mosaic_pattern')
        if self.start_date == self.end_date and self.start_date is not None:
            # have a specific date - replace generic pattern with specific values
            # replace generic year and month in pattern with the specific ones needed so the correct file is found.
            _modis_pattern = _modis_pattern.replace('(?P<year>\d{4})', '(?P<year>{0})'.format(self.year))
            _modis_pattern = _modis_pattern.replace('(?P<month>\d{2})', '(?P<month>{0:0>2})'.format(self.month))
            _modis_pattern = _modis_pattern.replace('(?P<day>\d{2})', '(?P<day>{0:0>2})'.format(self.day))
        _lst_output_pattern = self.vampire.get('MODIS_LST', 'lst_output_pattern')
        file_string = self.generate_extract_section(input_dir=_data_dir, output_dir=_day_dir,
                                                    product=product, layer='LST_Day',
                                                    file_pattern=_modis_pattern,
                                                    output_pattern=_lst_output_pattern)
        file_string += self.generate_extract_section(input_dir=_data_dir, output_dir=_night_dir,
                                                     product=product, layer='LST_Night',
                                                     file_pattern=_modis_pattern,
                                                     output_pattern=_lst_output_pattern)
        return file_string

    def generate_extract_evi(self, product, data_dir, output_dir):
        if product is None:
            _product = self.vampire.get('MODIS', 'vegetation_product')
        else:
            _product = product

        if data_dir is None:
            _data_dir = self.vampire.get('MODIS', 'vegetation_download_dir')
        else:
            _data_dir = data_dir

        # setup directories for extracting EVI data
        if output_dir is None:
            _output_dir = self.vampire.get('MODIS_EVI', 'evi_extract_dir')
        else:
            _output_dir = output_dir

        # pattern for files to extract from
        _modis_pattern = self.vampire.get('MODIS', 'modis_monthly_pattern')
        if self.start_date == self.end_date and self.start_date is not None:
            # have a specific date - replace generic pattern with specific values
            # replace generic year and month in pattern with the specific ones needed so the correct file is found.
            _modis_pattern = _modis_pattern.replace('(?P<year>\d{4})', '(?P<year>{0})'.format(self.year))
            _modis_pattern = _modis_pattern.replace('(?P<month>\d{2})', '(?P<month>{0:0>2})'.format(self.month))
            _modis_pattern = _modis_pattern.replace('(?P<day>\d{2})', '(?P<day>{0:0>2})'.format(self.day))
        _evi_output_pattern = self.vampire.get('MODIS_EVI', 'evi_output_pattern')
        _evi_layer = 'EVI' #self.vampire.get('MODIS_PRODUCTS', '{0}.EVI_Name'.format(_product))
        file_string = self.generate_extract_section(input_dir=_data_dir,
                                                    output_dir=_output_dir,
                                                    product=_product,
                                                    layer=_evi_layer,
                                                    file_pattern=_modis_pattern,
                                                    output_pattern=_evi_output_pattern)
        return file_string


    def generate_average_lst(self,
                             day_dir=None,
                             night_dir=None,
                             output_dir=None,
                             input_pattern=None,
                             output_pattern=None):
        if day_dir is None:
            _day_dir = self.vampire.get('MODIS_LST', 'lst_day_dir')
        else:
            _day_dir = day_dir
        if night_dir is None:
            _night_dir = self.vampire.get('MODIS_LST', 'lst_night_dir')
        else:
            _night_dir = night_dir
        if output_dir is None:
            _output_dir = self.vampire.get('MODIS_LST', 'lst_dir')
        else:
            _output_dir = output_dir
        if input_pattern is None:
            _input_pattern = self.vampire.get('MODIS_LST', 'lst_day_night_pattern')
            if self.start_date == self.end_date and self.start_date is not None:
                # have a specific date - replace generic pattern with specific values
                _input_pattern = _input_pattern.replace('(?P<year>\d{4})', '(?P<year>{0})'.format(self.year))
                _input_pattern = _input_pattern.replace('(?P<dayofyear>\d{3})', '(?P<dayofyear>{0:0>3})'.
                                                        format(self.day_of_year))
        else:
            _input_pattern = input_pattern
        if output_pattern is None:
            _output_pattern = self.vampire.get('MODIS_LST', 'lst_average_output_pattern')
        else:
            _output_pattern = output_pattern

        # _lst_day_night_pattern = self.vampire.get('MODIS_LST', 'lst_day_night_pattern')
        # _lst_day_night_pattern = _lst_day_night_pattern.replace('(?P<year>\d{4})', '(?P<year>{0})'.format(_year))
        # _lst_day_night_pattern = _lst_day_night_pattern.replace('(?P<dayofyear>\d{3})', '(?P<dayofyear>{:03})'.format(_day_of_year))
        # _lst_average_output_pattern = self.vampire.get('MODIS_LST', 'lst_average_output_pattern')
        file_string = self.generate_average_section(_day_dir, _night_dir, _output_dir,
                                                     _input_pattern, _output_pattern)
        return file_string

    def generate_crop_lst(self,
                          product=None,
                          boundary_file=None,
                          input_dir=None,
                          output_dir=None,
                          input_pattern=None,
                          output_pattern=None):
        if self.country == 'Global':
            # don't crop Global
            return ""

        if product is None:
            _product = self.vampire.get('MODIS', 'land_surface_temperature_product')
        else:
            _product = product

        # Use boundary file if specified
        if boundary_file is None:
            if self.vampire.get_country_code(self.country).upper() == self.vampire.get('vampire', 'home_country'):
                _boundary_file = self.vampire.get('MODIS', 'home_country_prefix')
            else:
                _boundary_file = os.path.join(self.vampire.get('MODIS', 'regional_prefix'),
                                              self.vampire.get_country_code(self.country).upper())
            _boundary_file = os.path.join(_boundary_file,
                                          self.vampire.get('MODIS', 'boundary_dir_suffix'))
            _boundary_file = os.path.join(_boundary_file,
                                          '{country}{filename}'.format(
                                              country=self.vampire.get_country_code(self.country).lower(),
                                              filename=self.vampire.get('MODIS_PRODUCTS',
                                                                        '{0}.boundary_filename'.format(_product))))
        else:
            _boundary_file = boundary_file

        if output_pattern is None:
            _output_pattern = self.vampire.get('MODIS_LST', 'lst_regional_output_pattern')
            _output_pattern = _output_pattern.replace('{country}',
                                                      '{0}'.format(self.vampire.get_country_code(self.country).lower()))
        else:
            _output_pattern = output_pattern

        if output_dir is None:
            if self.vampire.get_country_code(self.country).upper() == self.vampire.get('vampire', 'home_country').upper():
                # home country
                _output_dir = self.vampire.get('MODIS', 'home_country_prefix')
            else:
                # regional country - directory for output file
                _output_dir = os.path.join(self.vampire.get('MODIS', 'regional_prefix'),
                                           self.vampire.get_country_code(self.country).upper())
            _output_dir = os.path.join(_output_dir,
                                       self.vampire.get('MODIS_LST', 'lst_dir_suffix'))
        else:
            _output_dir = output_dir

        if input_dir is None:
            _input_dir = self.vampire.get('MODIS_LST', 'lst_dir')
        else:
            _input_dir = input_dir

        if input_pattern is None:
            _input_pattern = self.vampire.get('MODIS_LST', 'lst_average_pattern')
            if self.start_date == self.end_date:
                # replace generic year and month in pattern with the specific ones needed so the correct file is found.
                _input_pattern = _input_pattern.replace('(?P<year>\d{4})', '(?P<year>{0})'.format(self.year))
                _input_pattern = _input_pattern.replace('(?P<dayofyear>\d{3})', '(?P<dayofyear>{0:0>3})'.
                                                        format(self.day_of_year))
        else:
            _input_pattern = input_pattern
        file_string = self.generate_crop_section(boundary_file=_boundary_file, country=self.country,
                                         file_pattern=_input_pattern,
                                         input_dir=_input_dir,
                                         output_dir=_output_dir,
                                         output_pattern=_output_pattern)

        return file_string

    def generate_crop_evi(self,
                          product=None,
                          boundary_file=None,
                          input_dir=None,
                          output_dir=None,
                          input_pattern=None,
                          output_pattern=None):
        if self.country == 'Global':
            # don't crop Global
            return ""

        if product is None:
            _product = self.vampire.get('MODIS', 'vegetation_product')
        else:
            _product = product

        # Use boundary file if specified
        if boundary_file is None:
            if self.vampire.get_country_code(self.country).upper() == self.vampire.get('vampire', 'home_country'):
                _boundary_file = self.vampire.get('MODIS', 'home_country_prefix')
            else:
                _boundary_file = os.path.join(self.vampire.get('MODIS', 'regional_prefix'),
                                              self.vampire.get_country_code(self.country).upper())
            _boundary_file = os.path.join(_boundary_file,
                                          self.vampire.get('MODIS', 'boundary_dir_suffix'))
            _boundary_file = os.path.join(_boundary_file,
                                          '{country}{filename}'.format(
                                              country=self.vampire.get_country_code(self.country).lower(),
                                              filename=self.vampire.get('MODIS_PRODUCTS',
                                                                        '{0}.boundary_filename'.format(_product))))
        else:
            _boundary_file = boundary_file

        if output_pattern is None:
            _output_pattern = self.vampire.get('MODIS_EVI', 'evi_regional_output_pattern')
            _output_pattern = _output_pattern.replace('{country}',
                                                      '{0}'.format(self.vampire.get_country_code(self.country).lower()))
        else:
            _output_pattern = output_pattern

        if output_dir is None:
            if self.vampire.get_country_code(self.country).upper() == self.vampire.get('vampire', 'home_country').upper():
                # home country
                _output_dir = self.vampire.get('MODIS', 'home_country_prefix')
            else:
                # regional country - directory for output file
                _output_dir = os.path.join(self.vampire.get('MODIS', 'regional_prefix'),
                                           self.vampire.get_country_code(self.country).upper())
            _output_dir = os.path.join(_output_dir,
                                       self.vampire.get('MODIS_EVI', 'evi_dir_suffix'))
        else:
            _output_dir = output_dir

        if input_dir is None:
            _input_dir = self.vampire.get('MODIS_EVI', 'evi_extract_dir')
        else:
            _input_dir = input_dir

        if input_pattern is None:
            _input_pattern = self.vampire.get('MODIS_EVI', 'evi_pattern')
            if self.start_date == self.end_date and self.start_date is not None:
                # replace generic year and month in pattern with the specific ones needed so the correct file is found.
                _input_pattern = _input_pattern.replace('(?P<year>\d{4})', '(?P<year>{0})'.format(self.year))
                _input_pattern = _input_pattern.replace('(?P<month>\d{2})', '(?P<month>{0:0>2})'.format(self.month))
                _input_pattern = _input_pattern.replace('(?P<day>\d{2})', '(?P<day>{0:0>2})'.format(self.day))
        else:
            _input_pattern = input_pattern
        file_string = self.generate_crop_section(boundary_file=_boundary_file,
                                                 country=self.country,
                                                 file_pattern=_input_pattern,
                                                 input_dir=_input_dir,
                                                 output_dir=_output_dir,
                                                 output_pattern=_output_pattern)

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
    def generate_tci_config(self,product=None,          # MODIS product to use
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
                            boundary_file=None,
                            interval=None):
        file_string = """
    ## Processing chain begin - Compute Temperature Condition Index"""

        if product is None:
            _product = self.vampire.get('MODIS', 'land_surface_temperature_product')
        else:
            _product = product

        _o_dir = download_dir
        if download:
            _str, _o_dir = self.generate_download(product=_product, download_dir=download_dir)
            file_string += _str
        if extract:
            file_string += self.generate_extract_lst(product=_product, data_dir=_o_dir,
                                                     day_dir=lst_extract_day_dir,
                                                     night_dir=lst_extract_night_dir)
            file_string += self.generate_average_lst(day_dir=lst_extract_day_dir, night_dir=lst_extract_night_dir,
                                                     output_dir=lst_extract_dir)
        if crop:
            file_string += self.generate_crop_lst(product=_product, boundary_file=boundary_file,
                                                  input_dir=lst_extract_dir, output_dir=lst_country_dir)

        _lst_dir = lst_cur_dir
        _lst_max_dir = lst_max_dir
        _lst_min_dir = lst_min_dir

        if interval is not None:
            if interval != self.vampire.get('MODIS_PRODUCTS', '{0}.interval'.format(_product)):
                # need to average over interval
                if interval != '16Days':
                    print "Sorry, interval conversion other than from 8-16 days is not currently supported"
                    raise
                else:
                    # find the names of the files needed
                    if lst_cur_pattern is None:
                        _lst_cur_pattern = self.vampire.get('MODIS_LST', 'lst_regional_pattern')
                        # replace generic year in pattern with the specific ones needed so the correct files are found.
                        print self.day_of_year
                        print self.base_day_of_year
                        print self.start_date
                        _days = (self.start_date - datetime.datetime.strptime('{0}-01-01'.format(self.year), "%Y-%m-%d")).days
                        print 'Days: {0}'.format(_days)
                        _remainder = _days % 16

                        _date_test = self.day_of_year
                        if not calendar.isleap(int(self.year)):
                            _date_test = _date_test+1
                        if (_days) % 16 == 0:
                            # this is a 16-day date, use this and the previous 8-day data
                            _prev_date = datetime.datetime(int(self.year), 1, 1) + datetime.timedelta(self.day_of_year - 9)
                            # need to download and process previous 8-day data too.
                            _curr_date = self.start_date
                            _curr_end = self.end_date
                            self.set_dates(_prev_date, _prev_date)
                            if download:
                                _str, _o_dir = self.generate_download(product=_product, download_dir=download_dir)
                                file_string += _str
                            if extract:
                                file_string += self.generate_extract_lst(product=_product, data_dir=_o_dir,
                                                                         day_dir=lst_extract_day_dir,
                                                                         night_dir=lst_extract_night_dir)
                                file_string += self.generate_average_lst(day_dir=lst_extract_day_dir,
                                                                         night_dir=lst_extract_night_dir,
                                                                         output_dir=lst_extract_dir)
                            if crop:
                                file_string += self.generate_crop_lst(product=_product, boundary_file=boundary_file,
                                                                      input_dir=lst_extract_dir,
                                                                      output_dir=lst_country_dir)
                            self.set_dates(_curr_date, _curr_end)
                            _lst_tmp_pattern = _lst_cur_pattern
                            _lst_cur_pattern = _lst_cur_pattern.replace('(?P<year>\d{4})', '(?P<year>{0})'.
                                                                        format(self.year))
                            _lst_tmp_pattern = _lst_tmp_pattern.replace('(?P<year>\d{4})', '(?P<year>{0})'.
                                                                        format(_prev_date.year))
                            _lst_cur_pattern = _lst_cur_pattern.replace('(?P<month>\d{2})',
                                                                        '(?P<month>{0:0>2})'.
                                                                        format(self.month))
                            _lst_tmp_pattern = _lst_tmp_pattern.replace('(?P<month>\d{2})',
                                                                        '(?P<month>{0:0>2})'.
                                                                        format(_prev_date.month))
                            _lst_cur_pattern = _lst_cur_pattern.replace('(?P<day>\d{2})',
                                                                        '(?P<day>{0:0>2})'.
                                                                        format(self.day))
                            _lst_tmp_pattern = _lst_tmp_pattern.replace('(?P<day>\d{2})',
                                                                        '(?P<day>{0:0>2})'.
                                                                        format(_prev_date.day))
                            _lst_cur_pattern = '{0}|{1}'.format(_lst_cur_pattern, _lst_tmp_pattern)
                        else:
                            # day is not a 16-day date....
                            raise ValueError("This date isn't a 16-day date")
                    else:
                        _lst_cur_pattern = lst_cur_pattern
            else:
                if lst_cur_pattern is None:
                    _lst_cur_pattern = self.vampire.get('MODIS_LST', 'lst_regional_pattern')
                    # replace generic year in pattern with the specific one needed so the correct file is found.
                    _lst_cur_pattern = _lst_cur_pattern.replace('(?P<year>\d{4})', '(?P<year>{0})'.format(self.year))
                    _lst_cur_pattern = _lst_cur_pattern.replace('(?P<month>\d{2})', '(?P<month>{0:0>2})'.format(self.month))
                    _lst_cur_pattern = _lst_cur_pattern.replace('(?P<day>\d{2})', '(?P<day>{0:0>2})'.format(self.day))
                else:
                    _lst_cur_pattern = lst_cur_pattern
        else:
            if lst_cur_pattern is None:
                _lst_cur_pattern = self.vampire.get('MODIS_LST', 'lst_regional_pattern')
                # replace generic year in pattern with the specific one needed so the correct file is found.
                _lst_cur_pattern = _lst_cur_pattern.replace('(?P<year>\d{4})', '(?P<year>{0})'.format(self.year))
                _lst_cur_pattern = _lst_cur_pattern.replace('(?P<month>\d{2})', '(?P<month>{0:0>2})'.format(self.month))
                _lst_cur_pattern = _lst_cur_pattern.replace('(?P<day>\d{2})', '(?P<day>{0:0>2})'.format(self.day))
            else:
                _lst_cur_pattern = lst_cur_pattern

        if self.country == 'Global':
            _prefix = self.vampire.get('MODIS', 'global_prefix')
        elif self.vampire.get_country_code(self.country).upper() == self.vampire.get('vampire', 'home_country').upper():
            _prefix = self.vampire.get('MODIS', 'home_country_prefix')
        else:
            _prefix = os.path.join(self.vampire.get('MODIS', 'regional_prefix'),
                                   self.vampire.get_country_code(self.country).upper())

        if lst_cur_file is None:
            if lst_cur_dir is None:
                _lst_dir = os.path.join(_prefix,
                                        self.vampire.get('MODIS_LST', 'lst_dir_suffix'))
            _cur_file = None
        else:
            _cur_file = lst_cur_file

        if lst_max_file is None:
            if lst_max_dir is None:
                if interval is not None and interval == '16Days':
                    _split = self.vampire.get('MODIS_LST_Long_Term_Average',
                                              'lta_dir_suffix').rfind('StatisticsBy') + 12
                    _lst_max_dir = os.path.join(_prefix, '{0}{1}'.format(self.vampire.get('MODIS_LST_Long_Term_Average',
                                              'lta_dir_suffix')[:_split], interval)
                                            )
                else:
                    _lst_max_dir = os.path.join(_prefix,
                                                self.vampire.get('MODIS_LST_Long_Term_Average', 'lta_dir_suffix'))
            _lst_max_file = None
        else:
            _lst_max_file = lst_max_file

        if lst_min_file is None:
            if lst_min_dir is None:
                if interval is not None and interval == '16Days':
                    _split = self.vampire.get('MODIS_LST_Long_Term_Average',
                                              'lta_dir_suffix').rfind('StatisticsBy') + 12
                    _lst_min_dir = os.path.join(_prefix, '{0}{1}'.format(self.vampire.get('MODIS_LST_Long_Term_Average',
                                              'lta_dir_suffix')[:_split], interval)
                                            )
                else:
                    _lst_min_dir = os.path.join(_prefix,
                                                self.vampire.get('MODIS_LST_Long_Term_Average', 'lta_dir_suffix'))
            _lst_min_file = None
        else:
            _lst_min_file = lst_min_file

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

        if lst_min_pattern is None:
            _lst_min_pattern = self.vampire.get('MODIS_LST_Long_Term_Average', 'lta_pattern')
            _lst_min_pattern = _lst_min_pattern.replace('(?P<day_of_yr>\d{3})', '(?P<day_of_yr>{0:0>3})'.
                                                        format(self.day_of_year))
            _lst_min_pattern = _lst_min_pattern.replace('(?P<statistic>.*)', 'min')
        else:
            _lst_min_pattern = lst_min_pattern
        if lst_max_pattern is None:
            _lst_max_pattern = self.vampire.get('MODIS_LST_Long_Term_Average', 'lta_pattern')
            _lst_max_pattern = _lst_max_pattern.replace('(?P<day_of_yr>\d{3})', '(?P<day_of_yr>{0:0>3})'.
                                                        format(self.day_of_year))
            _lst_max_pattern = _lst_max_pattern.replace('(?P<statistic>.*)', 'max')
        else:
            _lst_max_pattern = lst_max_pattern


        file_string += self.generate_tci_section(cur_file=_cur_file, cur_dir=_lst_dir, cur_pattern=_lst_cur_pattern,
                                                 min_file=_lst_min_file, min_dir=_lst_min_dir,
                                                 min_pattern=_lst_min_pattern,
                                                 max_file=_lst_max_file, max_dir=_lst_max_dir,
                                                 max_pattern=_lst_max_pattern,
                                                 output_file=_output_file, output_dir=_output_dir,
                                                 output_pattern=_output_pattern, interval=interval)
        file_string += """
    ## Processing chain end - Compute Temperature Condition Index
"""
        return file_string


#     # Generate temperature condition index for the given country, for the month and year in start_date.
#     # If required, MODIS land surface temperature data will be downloaded, extracted and cropped as necessary.
#     # If the current LST file is not specified, then it will be found in the directory specified in lst_cur_dir
#     # using the pattern in lst_cur_pattern.
#     # If the long-term maximum file is not specified, it will be found in the directory specified in lst_max_dir
#     # using the pattern in lst_max_pattern.  If lst_max_pattern is not specified, the default pattern will be used
#     # instead.
#     # If the long-term minimum file is not specified, it will be found in the directory specified in lst_min_dir
#     # using the pattern in lst_min_pattern. If lst_min_pattern is not specified, the default pattern will be used
#     # instead.
#     # If the output filename is not specified, a default file pattern will be generated using the output_dir and
#     # output_pattern. If output_pattern is not specified, the default TCI output pattern will be used instead.
#     def generate_tci_config(self, country,              # country to calculate TCI for
#                             start_date,                 # date to calculate monthly TCI for (uses month & year only)
#                             end_date=None,              #
#                             product=None,               # MODIS product to use
#                             lst_cur_file=None,          # current LST filename for given month/year
#                             lst_cur_dir=None,           # directory to look for LST file in if not specified
#                             lst_cur_pattern=None,       # pattern to use to find LST file if not specified
#                             lst_max_file=None,          # LST long-term maximum filename
#                             lst_max_dir=None,           # directory of LST long-term maximum
#                             lst_max_pattern=None,       # pattern for finding LST long-term maximum
#                             lst_min_file=None,          # LST long-term minimum filename
#                             lst_min_dir=None,           # directory of LST long-term minimum
#                             lst_min_pattern=None,       # pattern for finding long-term minimum
#                             output_filename=None,       # filename for TCI output
#                             output_dir=None,            # directory for TCI output
#                             output_pattern=None,        # pattern for generating TCI output filename if not specified
#                             download=True,              # download MODIS data if True
#                             download_dir=None,          # directory to download MODIS into
#                             extract=True,               # extract LST if True
#                             lst_extract_day_dir=None,   # directory for extracted LST Day
#                             lst_extract_night_dir=None, # directory for extracted LST Night
#                             lst_extract_dir=None,       # directory for extracted average LST
#                             crop=True,                  # crop LST to region if True
#                             lst_country_dir=None,       # directory to save cropped file
#                             boundary_file=None):        # shapefile for cropping boundary
#         _year = start_date.strftime("%Y")
#         _month = start_date.strftime("%m")
#         _base_date = datetime.datetime.strptime("2000.{0}.01".format(_month), "%Y.%m.%d")
#         _day_of_year = _base_date.timetuple().tm_yday
# #        if calendar.isleap(int(_year)) and _day_of_year > 60:
# #            _day_of_year = _day_of_year - 1
#
#         if product is None:
#             _product = self.vampire.get('MODIS', 'land_surface_temperature_product')
#         else:
#             _product = product
#
#         _lst_dir = lst_cur_dir
#         _lst_max_dir = lst_max_dir
#         _lst_min_dir = lst_min_dir
#
#         if lst_cur_pattern is None:
#             _lst_cur_pattern = self.vampire.get('MODIS_LST', 'lst_regional_pattern')
#             # replace generic year in pattern with the specific one needed so the correct file is found.
#             _lst_cur_pattern = _lst_cur_pattern.replace('(?P<year>\d{4})', '(?P<year>{0})'.format(_year))
#             _lst_cur_pattern = _lst_cur_pattern.replace('(?P<month>\d{2})', '(?P<month>{0})'.format(_month))
#         else:
#             _lst_cur_pattern = lst_cur_pattern
#
#         if country == 'Global':
#             crop = False
#         else:
#             # Use boundary file if specified
#             if boundary_file is None:
#                 if self.vampire.get_country_code(country).upper() == self.vampire.get('vampire', 'home_country'):
#                     _boundary_file = self.vampire.get('MODIS', 'home_country_temperature_boundary')
#                 else:
#                     _boundary_file = os.path.join(self.vampire.get('MODIS', 'regional_prefix'),
#                                                   self.vampire.get_country_code(country).upper())
#                     _boundary_file = os.path.join(_boundary_file,
#                                                   self.vampire.get('MODIS', 'regional_suffix'))
#                     _boundary_file = os.path.join(_boundary_file,
#                                                   '{country}{filename}'.format(
#                                                       country=self.vampire.get_country_code(country).lower(),
#                                                       filename=self.vampire.get('MODIS_PRODUCTS',
#                                                                                 '{0}.boundary_filename'.format(_product))))
#             else:
#                 _boundary_file = boundary_file
#             _lst_crop_output_pattern = self.vampire.get('MODIS_LST', 'lst_regional_output_pattern')
#             _lst_crop_output_pattern = _lst_crop_output_pattern.replace('{country}',
#                                                                         '{0}'.format(
#                                                                             self.vampire.get_country_code(country).lower()))
#             _lst_crop_output_dir = lst_country_dir
#
#             if self.vampire.get_country_code(country).upper() == self.vampire.get('vampire', 'home_country').upper():
#                 # home country
#                 # directory for country LST file (crop output)
#                 if lst_country_dir is None:
#                     _lst_crop_output_dir = self.vampire.get('MODIS_LST', 'home_country_lst_dir')
#                 if lst_cur_file is None:
#                     if lst_cur_dir is None:
#                         _lst_dir = self.vampire.get('MODIS_LST', 'home_country_lst_dir')
#                     _cur_file = None
#
#                 if lst_max_file is None:
#                     if lst_max_dir is None:
#                         _lst_max_dir = self.vampire.get('MODIS_LST_Long_Term_Average', 'home_country_lta_dir')
#                     _lst_max_file = None
#
#                 if lst_min_file is None:
#                     if lst_min_dir is None:
#                         _lst_min_dir = self.vampire.get('MODIS_LST_Long_Term_Average', 'home_country_lta_dir')
#                     _lst_min_file = None
#             else:
#                 # regional country
#                 # directory for country LST file (crop output)
#                 if lst_country_dir is None:
#                     _lst_crop_output_dir = os.path.join(self.vampire.get('MODIS_LST', 'regional_lst_dir_prefix'),
#                                                         os.path.join(self.vampire.get_country_code(country).upper(),
#                                                                      self.vampire.get('MODIS_LST', 'regional_lst_dir_suffix')))
#                 if lst_cur_file is None:
#                     if lst_cur_dir is None:
#                         _lst_dir = os.path.join(self.vampire.get('MODIS_LST', 'regional_lst_dir_prefix'),
#                                                         os.path.join(self.vampire.get_country_code(country).upper(),
#                                                                      self.vampire.get('MODIS_LST', 'regional_lst_dir_suffix')))
#                     _cur_file = None
#
#                 if lst_max_file is None:
#                     if lst_max_dir is None:
#                         _lst_max_dir = os.path.join(self.vampire.get('MODIS_LST_Long_Term_Average',
#                                                                      'regional_lta_dir_prefix'),
#                                                     self.vampire.get_country_code(country).upper())
#                         _lst_max_dir = os.path.join(_lst_max_dir,
#                                                     self.vampire.get('MODIS_LST_Long_Term_Average',
#                                                                      'regional_lta_dir_suffix'))
#                     _lst_max_file = None
#
#                 if lst_min_file is None:
#                     if lst_min_dir is None:
#                         _lst_min_dir = os.path.join(self.vampire.get('MODIS_LST_Long_Term_Average',
#                                                                      'regional_lta_dir_prefix'),
#                                                     self.vampire.get_country_code(country).upper())
#                         _lst_min_dir = os.path.join(_lst_min_dir,
#                                                     self.vampire.get('MODIS_LST_Long_Term_Average',
#                                                                      'regional_lta_dir_suffix'))
#                     _lst_min_file = None
#
#         # directory for LST file output (& crop input)
#         if lst_extract_day_dir is None:
#             _lst_extract_day_dir = self.vampire.get('MODIS_LST', 'lst_extract_day_dir')
#         else:
#             _lst_extract_day_dir = lst_extract_night_dir
#         if lst_extract_night_dir is None:
#             _lst_extract_night_dir = self.vampire.get('MODIS_LST', 'lst_extract_night_dir')
#         else:
#             _lst_extract_night_dir = lst_extract_night_dir
#         if lst_extract_dir is None:
#             _lst_extract_dir = self.vampire.get('MODIS_LST', 'lst_extract_dir')
#         else:
#             _lst_extract_dir = lst_extract_dir
#
#         _output_file = output_filename
#         _output_dir = None
#         _output_pattern = None
#         if output_filename is None:
#             if output_dir is None:
#                 _output_dir = self.vampire.get('MODIS_TCI', 'tci_product_dir')
#             else:
#                 _output_dir = output_dir
#             if output_pattern is None:
#                 _output_pattern = self.vampire.get('MODIS_TCI', 'tci_output_pattern')
#
#         _cur_file = lst_cur_file
# #        _lst_dir = lst_cur_dir
#         _lst_max_file = lst_max_file
#         _lst_min_file = lst_min_file
# #        _lst_max_dir = lst_max_dir
# #        _lst_min_dir = lst_min_dir
#         if lst_min_pattern is None:
#             _lst_min_pattern = self.vampire.get('MODIS_LST_Long_Term_Average', 'lta_pattern')
#             _lst_min_pattern = _lst_min_pattern.replace('(?P<day_of_yr>\d{3})', '(?P<day_of_yr>{0})'.format(_day_of_year))
#             _lst_min_pattern = _lst_min_pattern.replace('(?P<statistic>.*)', 'min')
#         else:
#             _lst_min_pattern = lst_min_pattern
#         if lst_max_pattern is None:
#             _lst_max_pattern = self.vampire.get('MODIS_LST_Long_Term_Average', 'lta_pattern')
#             _lst_max_pattern = _lst_max_pattern.replace('(?P<day_of_yr>\d{3})', '(?P<day_of_yr>{0})'.format(_day_of_year))
#             _lst_max_pattern = _lst_max_pattern.replace('(?P<statistic>.*)', 'max')
#         else:
#             _lst_max_pattern = lst_max_pattern
#
#         _data_dir = download_dir
#
#         file_string = """
#     ## Processing chain begin - Compute Temperature Condition Index"""
#         if download:
#             # Use download directory if specified.
#             if download_dir is None:
#                 _data_dir = self.vampire.get('MODIS', 'temperature_download_dir')
#             else:
#                 _data_dir = download_dir
#             _mosaic_dir = self.vampire.get('MODIS_PRODUCTS', '{0}.mosaic_dir'.format(_product))
#             if _mosaic_dir is not None:
#                 # need to specify tiles
#                 _tiles = self.vampire.get_country(country=country)['modis_lst_tiles']
#             else:
#                 _tiles = None
#             file_string += self.generate_download_section(product=_product, tiles=_tiles,
#                                                          data_dir=_data_dir, mosaic_dir=_mosaic_dir)
#             if _mosaic_dir is not None:
#                 _data_dir = _mosaic_dir
#             else:
#                 # MODIS downloads to a date directory
#                 _data_dir = os.path.join(_data_dir, '{0}.{1}.01'.format(_year, _month))
#
#         if extract:
#             # need to extract both day and night layers then average them
#             # pattern for files to extract from
#             if _mosaic_dir is None:
#                 _modis_pattern = self.vampire.get('MODIS_LST', 'lst_pattern')
#             else:
#                 _modis_pattern = self.vampire.get('MODIS_LST', 'lst_mosaic_pattern')
#             # replace generic year and month in pattern with the specific ones needed so the correct file is found.
#             _modis_pattern = _modis_pattern.replace('(?P<year>\d{4})', '(?P<year>{0})'.format(_year))
#             _modis_pattern = _modis_pattern.replace('(?P<month>\d{2})', '(?P<month>{0})'.format(_month))
#             _lst_output_pattern = self.vampire.get('MODIS_LST', 'lst_output_pattern')
#             file_string += self.generate_extract_section(input_dir=_data_dir, output_dir=_lst_extract_day_dir,
#                                                         product=_product, layer='LST_Day',
#                                                         file_pattern=_modis_pattern,
#                                                         output_pattern=_lst_output_pattern)
#             file_string += self.generate_extract_section(input_dir=_data_dir, output_dir=_lst_extract_night_dir,
#                                                         product=_product, layer='LST_Night',
#                                                         file_pattern=_modis_pattern,
#                                                         output_pattern=_lst_output_pattern)
# #     - process: MODIS
# #       type: temp_average
# #       directory_day: {data_dir}\MODIS\MOD11C3\Processed\Day
# #       directory_night: {data_dir}\MODIS\MOD11C3\Processed\Night
# #       directory_output: {data_dir}\MODIS\MOD11C3\Processed\Average
# #       input_pattern: {input_pattern}
# #       output_pattern: {avg_pattern}
#             _lst_day_night_pattern = self.vampire.get('MODIS_LST', 'lst_day_night_pattern')
#             _lst_day_night_pattern = _lst_day_night_pattern.replace('(?P<year>\d{4})', '(?P<year>{0})'.format(_year))
#             _lst_day_night_pattern = _lst_day_night_pattern.replace('(?P<dayofyear>\d{3})', '(?P<dayofyear>{:03})'.format(_day_of_year))
#             _lst_average_output_pattern = self.vampire.get('MODIS_LST', 'lst_average_output_pattern')
#             file_string += self.generate_average_section(_lst_extract_day_dir, _lst_extract_night_dir, _lst_extract_dir,
#                                                          _lst_day_night_pattern, _lst_average_output_pattern)
#     #         """
#     # # Compute average of day and night temperatures
#     # - process: MODIS
#     #   type: calc_average
#     #   layer: day_night_temp
#     #   lst_day_dir: {lst_day_dir}
#     #   lst_night_dir: {lst_night_dir}
#     #   output_dir: {lst_average_dir}
#     #   file_pattern: '{input_pattern}'
#     #   output_pattern: '{output_pattern}'
#     #         """.format(lst_day_dir=_lst_extract_day_dir, lst_night_dir=_lst_extract_night_dir,
#     #                    lst_average_dir=_lst_extract_dir, input_pattern=_lst_day_night_pattern,
#     #                    output_pattern=_lst_average_output_pattern)
#
#         if crop:
#             file_string += """
#     # Crop data to {country}""".format(country=country)
#             _lst_pattern = self.vampire.get('MODIS_LST', 'lst_average_pattern')
#             # replace generic year and month in pattern with the specific ones needed so the correct file is found.
#             _lst_pattern = _lst_pattern.replace('(?P<year>\d{4})', '(?P<year>{0})'.format(_year))
#             _lst_pattern = _lst_pattern.replace('(?P<dayofyear>\d{3})', '(?P<dayofyear>{:03})'.format(_day_of_year))
#             file_string += self.generate_crop(boundary_file=_boundary_file, country=country,
#                                               file_pattern=_lst_pattern,
#                                               input_dir=_lst_extract_dir,
#                                               output_dir=_lst_crop_output_dir,
#                                               output_pattern=_lst_crop_output_pattern)
#
#         file_string += self.generate_tci_section(cur_file=_cur_file, cur_dir=_lst_dir, cur_pattern=_lst_cur_pattern,
#                                                  max_file=_lst_max_file, max_dir=_lst_max_dir,
#                                                  max_pattern=_lst_max_pattern, min_file=_lst_min_file,
#                                                  min_dir=_lst_min_dir, min_pattern=_lst_min_pattern,
#                                                  output_file=_output_file, output_dir=_output_dir,
#                                                  output_pattern=_output_pattern)
#     #     """
#     # # Compute temperature condition index
#     # - process: Analysis
#     #   type: TCI"""
#     #     if _cur_file is not None:
#     #         file_string += """
#     #   current_file: {current_file}""".format(current_file=_cur_file)
#     #     else:
#     #         file_string += """
#     #   current_dir: {current_dir}
#     #   current_file_pattern: '{current_pattern}'""".format(current_dir=_lst_dir, current_pattern=_lst_cur_pattern)
#     #     if _lst_max_file is not None:
#     #         file_string += """
#     #   LST_max_file: {lst_max}""".format(_lst_max_file)
#     #     else:
#     #         file_string += """
#     #   LST_max_dir: {lst_max_dir}
#     #   LST_max_pattern: '{lst_max_pattern}'""".format(lst_max_dir=_lst_max_dir, lst_max_pattern=_lst_max_pattern)
#     #     if _lst_min_file is not None:
#     #         file_string += """
#     #   LST_min_file: {lst_min}""".format(_lst_max_file)
#     #     else:
#     #         file_string += """
#     #   LST_min_dir: {lst_min_dir}
#     #   LST_min_pattern: '{lst_min_pattern}'""".format(lst_min_dir=_lst_min_dir, lst_min_pattern=_lst_min_pattern)
#     #     if _output_file is not None:
#     #         file_string += """
#     #   output_file: {output_file}""".format(_output_file)
#     #     else:
#     #         file_string += """
#     #   output_dir: {output_dir}
#     #   output_file_pattern: '{output_pattern}'""".format(output_dir=_output_dir, output_pattern=_output_pattern)
#
#         file_string += """
#     ## Processing chain end - Compute Temperature Condition Index
# """
#         return file_string

    # Generate temperature long-term averages
    def generate_temperature_long_term_average(self,
                                               product=None,            # MODIS product to use
                                               data_dir=None,           # directory for data files
                                               lta_dir=None,            # directory for long-term average output
                                               functions=None,
                                               download=True,           # download MODIS data if True
                                               download_dir=None,       # directory for downloaded data
                                               extract=True,            # extract LST if True
                                               average=True,            # calculate day/night average if True
                                               lst_extract_day_dir=None,# directory for extracted LST day
                                               lst_extract_night_dir=None,# directory for extracted LST night
                                               lst_average_dir=None,    # directory for average of LST day & night
                                               crop=True,               # crop EVI to region if True
                                               crop_dir=None,           # directory to save cropped files
                                               boundary_file=None,      # shapefile for cropping boundary
                                               interval=None):
        # set up functions
        if functions is None:
            _functions = ['MIN', 'MAX']
        else:
            _functions = functions
        if product is None:
            _product = self.vampire.get('MODIS', 'land_surface_temperature_product')
        else:
            _product = product

        file_string = """
    ## Processing chain begin - Compute Land Surface Temperature Long-term Average"""

        if download:
            _str, _o_dir = self.generate_download(_product, download_dir)
            file_string += _str
        if extract:
            file_string += self.generate_extract_lst(_product, download_dir, lst_extract_day_dir, lst_extract_night_dir)
        if average:
            file_string += self.generate_average_lst(day_dir=lst_extract_day_dir, night_dir=lst_extract_night_dir,
                                                     output_dir=lst_average_dir)
        if self.country == 'Global':
            crop = False
        if crop:
            file_string += self.generate_crop_lst(product=_product, boundary_file=boundary_file,
                                                  input_dir=lst_average_dir, output_dir=crop_dir)

        if self.country == 'Global':
            _prefix = self.vampire.get('MODIS', 'global_prefix')
        elif self.vampire.get_country_code(self.country).upper() == self.vampire.get('vampire', 'home_country'):
            _prefix = self.vampire.get('MODIS', 'home_country_prefix')
        else:
            _prefix = os.path.join(self.vampire.get('MODIS', 'regional_prefix'),
                                    self.vampire.get_country_code(self.country).upper())
        # set up input directory
        if data_dir is None:
            if crop_dir is not None:
                _data_dir = crop_dir
            else:
                _data_dir = os.path.join(_prefix, self.vampire.get('MODIS_LST', 'lst_dir_suffix'))
        else:
            _data_dir = data_dir

        # set up output directory
        if lta_dir is None:
            _lta_dir = os.path.join(_prefix, self.vampire.get('MODIS_LST_Long_Term_Average', 'lta_dir_suffix'))
        else:
            _lta_dir = lta_dir

        _lta_input_pattern = None
        _lta_output_pattern = None

        if self.country == 'Global':
            _lta_input_pattern = self.vampire.get('MODIS_LST', 'lst_average_pattern')
            _lta_output_pattern = self.vampire.get('MODIS_LST_Long_Term_Average', 'lta_output_pattern')
        else:
            _lta_input_pattern = self.vampire.get('MODIS_LST', 'lst_regional_pattern')
            _lta_output_pattern = self.vampire.get('MODIS_LST_Long_Term_Average', 'lta_regional_output_pattern')

        file_string += self.generate_lst_lta_section(product=_product, input_dir=_data_dir, output_dir=_lta_dir,
                                                     input_pattern=_lta_input_pattern,
                                                     output_pattern=_lta_output_pattern,
                                                     functions=_functions, interval=interval)
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
    def generate_vci_config(self,
                            product=None,
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

        file_string = """
    ## Processing chain begin - Compute Vegetation Condition Index"""

        if product is None:
            _product = self.vampire.get('MODIS', 'vegetation_product')
        else:
            _product = product
        _o_dir = download_dir
        if download:
            _str, _o_dir = self.generate_download(product=_product, download_dir=download_dir,
                                                  mosaic_dir=mosaic_dir, tiles=tiles)
            file_string += _str
        if extract:
            file_string += self.generate_extract_evi(_product, _o_dir, evi_extract_dir)

        if crop:
            file_string += self.generate_crop_evi(_product, evi_extract_dir, evi_country_dir)

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

        _cur_file = evi_cur_file
        _evi_dir = evi_cur_dir
        _evi_cur_pattern = evi_cur_pattern
        if evi_cur_pattern is None:
            _evi_cur_pattern = self.vampire.get('MODIS_EVI', 'evi_regional_pattern')
            # replace generic year in pattern with the specific one needed so the correct file is found.
            _evi_cur_pattern = _evi_cur_pattern.replace('(?P<year>\d{4})', '(?P<year>{0})'.format(self.year))
            _evi_cur_pattern = _evi_cur_pattern.replace('(?P<month>\d{2})', '(?P<month>{0:0>2})'.format(self.month))
            _evi_cur_pattern = _evi_cur_pattern.replace('(?P<day>\d{2})', '(?P<day>{0:0>2})'.format(self.day))
        _evi_max_file = evi_max_file
        _evi_min_file = evi_min_file
        _evi_max_dir = evi_max_dir
        _evi_min_dir = evi_min_dir
        if evi_min_pattern is None:
            _evi_min_pattern = self.vampire.get('MODIS_EVI_Long_Term_Average', 'lta_pattern')
            _evi_min_pattern = _evi_min_pattern.replace('(?P<day_of_yr>\d{3})', '(?P<day_of_yr>{0:0>3})'.
                                                        format(self.day_of_year))
            _evi_min_pattern = _evi_min_pattern.replace('(?P<statistic>.*)', 'min')
        else:
            _evi_min_pattern = evi_min_pattern
        if evi_max_pattern is None:
            _evi_max_pattern = self.vampire.get('MODIS_EVI_Long_Term_Average', 'lta_pattern')
            _evi_max_pattern = _evi_max_pattern.replace('(?P<day_of_yr>\d{3})', '(?P<day_of_yr>{0:0>3})'.
                                                        format(self.day_of_year))
            _evi_max_pattern = _evi_max_pattern.replace('(?P<statistic>.*)', 'max')
        else:
            _evi_max_pattern = evi_max_pattern

        if self.country == 'Global':
            # Global MODIS doesn't make sense
            raise
        elif self.vampire.get_country_code(self.country).upper() == self.vampire.get('vampire', 'home_country').upper():
            # home country
            _prefix = self.vampire.get('MODIS', 'home_country_prefix')
        else:
            _prefix = os.path.join(self.vampire.get('MODIS', 'regional_prefix'),
                                   self.vampire.get_country_code(self.country).upper())
        if evi_cur_file is None:
            if evi_cur_dir is None:
                _evi_dir = os.path.join(_prefix, self.vampire.get('MODIS_EVI', 'evi_dir_suffix'))
            _cur_file = None

        if evi_max_file is None:
            if evi_max_dir is None:
                _evi_max_dir = os.path.join(_prefix, self.vampire.get('MODIS_EVI_Long_Term_Average', 'lta_dir_suffix'))
            _evi_max_file = None

        if evi_min_file is None:
            if evi_min_dir is None:
                _evi_min_dir = os.path.join(_prefix, self.vampire.get('MODIS_EVI_Long_Term_Average', 'lta_dir_suffix'))
            _evi_min_file = None

        file_string += self.generate_vci_section(cur_file=_cur_file, cur_dir=_evi_dir, cur_pattern=_evi_cur_pattern,
                                                 evi_max_file=_evi_max_file, evi_max_dir=_evi_max_dir,
                                                 evi_max_pattern=_evi_max_pattern, evi_min_file=_evi_min_file,
                                                 evi_min_dir=_evi_min_dir, evi_min_pattern=_evi_min_pattern,
                                                 output_file=_output_file, output_dir=_output_dir,
                                                 output_pattern=_output_pattern)

        file_string += """
    ## Processing chain end - Compute Vegetation Condition Index
"""
        return file_string

    def generate_vhi_config(self,
                            tci_file=None,
                            tci_dir=None,
                            tci_pattern=None,
                            vci_file=None,
                            vci_dir=None,
                            vci_pattern=None,
                            output_file=None,
                            output_dir=None,
                            output_pattern=None,
                            reproject='TCI'):
        file_string = """
    ## Processing chain begin - Compute Vegetation Health Index"""

        _tci_pattern = None
        _vci_pattern = None
        _output_dir = None
        _output_pattern = None
        if tci_file is None:
            if tci_dir is None:
                _tci_dir = self.vampire.get('MODIS_TCI', 'tci_product_dir')
            else:
                _tci_dir = tci_dir
            _tci_file = None
            if tci_pattern is None:
                _tci_pattern = self.vampire.get('MODIS_TCI', 'tci_pattern')
                _tci_pattern = _tci_pattern.replace('(?P<year>\d{4})', '(?P<year>{0})'.format(self.year))
                _tci_pattern = _tci_pattern.replace('(?P<month>\d{2})', '(?P<month>{0})'.format(self.month))
                _tci_pattern = _tci_pattern.replace('(?P<day>\d{2})', '(?P<day>{0})'.format(self.day))
            else:
                _tci_pattern = tci_pattern
        else:
            _tci_file = tci_file
            _tci_pattern = None
            _tci_dir = None

        if vci_file is None:
            if vci_dir is None:
                _vci_dir = self.vampire.get('MODIS_VCI', 'vci_product_dir')
            else:
                _vci_dir = vci_dir
            _vci_file = None
            if vci_pattern is None:
                _vci_pattern = self.vampire.get('MODIS_VCI', 'vci_pattern')
                _vci_pattern = _vci_pattern.replace('(?P<year>\d{4})', '(?P<year>{0})'.format(self.year))
                _vci_pattern = _vci_pattern.replace('(?P<month>\d{2})', '(?P<month>{0})'.format(self.month))
                _vci_pattern = _vci_pattern.replace('(?P<day>\d{2})', '(?P<day>{0})'.format(self.day))
            else:
                _vci_pattern = vci_pattern
        else:
            _vci_file = vci_file
            _vci_pattern = None
            _vci_dir = None

        if output_file is None:
            if output_dir is None:
                _output_dir = self.vampire.get('MODIS_VHI', 'vhi_product_dir')
            else:
                _output_dir = output_dir
            if output_pattern is None:
                _output_pattern = self.vampire.get('MODIS_VHI', 'vhi_output_pattern')
            else:
                _output_pattern = output_pattern
            _output_file = None
        else:
            _output_file = output_file

        if reproject is not None:
            if reproject == 'TCI':
                _tci_resample_pattern = self.vampire.get('MODIS_TCI', 'tci_output_pattern')
                _tci_resample_pattern = _tci_resample_pattern.replace('.TCI', '.TCI_resample')
                file_string += self.generate_match_projection_section(master_dir=_vci_dir,
                                                                      slave_dir=_tci_dir,
                                                                      output_dir=_tci_dir,
                                                                      master_pattern=_vci_pattern,
                                                                      slave_pattern=_tci_pattern,
                                                                      output_pattern=_tci_resample_pattern)
                _tci_pattern = _tci_pattern.replace('.TCI', '.TCI_resample')
            elif reproject == 'VCI':
                _vci_resample_pattern = self.vampire.get('MODIS_VCI', 'vci_output_pattern')
                _vci_resample_pattern = _vci_resample_pattern.replace('.VCI', '.VCI_resample')
                file_string += self.generate_match_projection_section(master_dir=_tci_dir,
                                                                      slave_dir=_vci_dir,
                                                                      output_dir=_vci_dir,
                                                                      master_pattern=_tci_pattern,
                                                                      slave_pattern=_vci_pattern,
                                                                      output_pattern=_vci_resample_pattern)
                _vci_pattern = _vci_pattern.replace('.VCI', '.VCI_resample')


        file_string += self.generate_vhi_section(tci_file=_tci_file, tci_dir=_tci_dir, tci_pattern=_tci_pattern,
                                                 vci_file=_vci_file, vci_dir=_vci_dir, vci_pattern=_vci_pattern,
                                                 output_file=_output_file, output_dir=_output_dir,
                                                 output_pattern=_output_pattern)
        file_string += """
## Processing chain end - Compute Vegetation Health Index"""

        return file_string
