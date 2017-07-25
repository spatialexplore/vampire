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

#     def generate_header_chirps(self):
#         file_string = """
# temp: {temp_dir}
#
# CHIRPS:
#     filenames:
#         input_prefix: chirps-v2.0
#         input_extension: .tiff
#         output_prefix: idn_cli_chirps-v2.0
#         output_ext: .tif
# """.format(temp_dir=self.vampire.get('directories', 'temp_dir'))
#         return file_string
#
#     def generate_chirps_download(self, interval, data_dir, start_date=None, end_date=None):
#         file_string = """
#     # download CHIRPS precipitation data
#     - process: CHIRPS
#       type: download
#       interval: {interval}
#       output_dir: {output_dir}""".format(interval=interval, output_dir=data_dir)
#         # if start and end dates are specified, only download between these dates
#         if start_date is not None:
#             year = start_date.strftime("%Y")
#             month = start_date.strftime("%m")
#             # use 1st of start_date month to make sure end month is also included
#             _first_date = start_date.replace(start_date.year, start_date.month, 1)
#             dates = dateutil.rrule.rrule(dateutil.rrule.MONTHLY, dtstart = _first_date).between(_first_date, end_date, inc=True)
#             file_string += """
#       dates: ["""
#             for d in dates:
#                 file_string += '{year}-{month},'.format(year=d.strftime("%Y"), month=d.strftime("%m"))
#             file_string = file_string[:-1]
#             file_string += """]
#             """
#         return file_string

    def generate_crop_section(self, country, input_dir, output_dir, file_pattern, output_pattern, boundary_file,
                              no_data=False):
        file_string = """
    # Crop data to {country}
    - process: Raster
      type: crop
      input_dir: {input_dir}
      output_dir: {output_dir}
      file_pattern: '{file_pattern}'
      output_pattern: '{output_pattern}'
      boundary_file: {boundary_file}""".format(country=country,
                           input_dir=input_dir,
                           output_dir=output_dir,
                           file_pattern=file_pattern,
                           output_pattern=output_pattern,
                           boundary_file=boundary_file
                           )
        if no_data:
            file_string += """
      no_data:
      """
        else:
            file_string +="""
      """
        return file_string

    def generate_match_projection_section(self, master_dir, slave_dir, output_dir,
                                          master_pattern, slave_pattern, output_pattern):
        file_string = """
    - process: Raster
      type: match_projection
      master_dir: {master_dir}
      master_pattern: '{master_pattern}'
      slave_dir: {slave_dir}
      slave_pattern: '{slave_pattern}'
      output_dir: {output_dir}
      output_pattern:  '{output_pattern}'
    """.format(master_dir=master_dir, master_pattern=master_pattern, slave_dir=slave_dir,
                   slave_pattern=slave_pattern, output_dir=output_dir, output_pattern=output_pattern)
        return file_string

    def generate_mask_section(self, input_dir, output_dir, file_pattern, output_pattern, boundary_file,
                              no_data=False):
        file_string = """
    # Mask data with boundary
    - process: Raster
      type: apply_mask
      raster_dir: {input_dir}
      raster_pattern: '{file_pattern}'
      polygon_file: {boundary_file}
      output_dir: {output_dir}
      output_pattern: '{output_pattern}'""".format(input_dir=input_dir,
                                                   output_dir=output_dir,
                                                   file_pattern=file_pattern,
                                                   output_pattern=output_pattern,
                                                   boundary_file=boundary_file)
        if no_data:
            file_string += """
      no_data:
          """
        else:
            file_string += """
          """
        return file_string


import config_generator
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
        config_generator.generate_config_file(output_file=_output, params=params)
        # cf = ConfigFactory(_output)
        # cf.generate_config_file(_output, params)
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
