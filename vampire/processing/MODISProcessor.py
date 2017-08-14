import vampire.VampireDefaults
import vampire.directory_utils
import vampire.filename_utils
import os
import re
import errno
import glob
import gdal
import json
import datetime
import dateutil
import dateutil.parser
import subprocess
#from subprocess import check_call, CalledProcessError
from pymodis import downmodis

try:
    import calculate_statistics_arc as calculate_statistics
except ImportError:
    import calculate_statistics_os as calculate_statistics

try:
    import vegetation_analysis_arc as vegetation_analysis
except ImportError:
    import vegetation_analysis_os as vegetation_analysis

import platform
platform = platform.system()
#if platform == "Linux":
#    import calculate_statistics_os as calculate_statistics
#    import vegetation_analysis_os as vegetation_analysis
##elif platform == "Windows":
##    import calculate_statistics_arc as calculate_statistics
##    import vegetation_analysis_arc as vegetation_analysis

class MODISProcessor:
    def __init__(self):
        # load default values from .ini file
        self.vampire = vampire.VampireDefaults.VampireDefaults()
        return


    # Get MODIS tiles and mosaic into one HDF4Image format file.
    # No changes to projection are performed.
    def download_data(self, output_dir, product,
                      dates=None, tiles=None, mosaic_dir=None, overwrite=False):
        self.vampire.logger.info('entering download_data')


    #def getMODISDataFromURL(output_dir, product, tiles, dates, mosaic_dir,
    #                        tools_dir = None, logger = None):
        files = None
        _m_files = []
        _dl_files = []
        _delta = 1
        _user = self.vampire.get('MODIS', 'user')
        _password = self.vampire.get('MODIS', 'password')
        _dates = []
#        if dates is None:
        # need to get list of dates first
        if not os.path.exists(output_dir):
            self.vampire.logger.debug("%s does not exist. Creating directory", output_dir)
            os.makedirs(output_dir)

        _modis_connect = downmodis.downModis(destinationFolder=output_dir, user=_user, password=_password,
                                             product=product, today=None, delta=_delta, tiles=tiles)
        _modis_connect.connect()
        _days_list = _modis_connect.getAllDays()
        for i in _days_list:
            if dates is None:
                _dates.append(i) #('{0}-{1}'.format(i.split('.')[0], i.split('.')[1]))
            else:
                # check if in month/year
                if '{0}-{1}'.format(i.split('.')[0], i.split('.')[1]) in dates:
                    _dates.append(i)
#        else:
#            _dates = dates

        for d in _dates:
            self.vampire.logger.debug("downloading data for %s", d)
            _month = d #'{date}-01'.format(date=d)
            _folder_date = datetime.datetime.strptime(_month, '%Y.%m.%d').strftime('%Y.%m.%d')
            _new_folder = output_dir #os.path.join(output_dir, _folder_date)
# don't need anymore? done above instead?
             # create folder if it doesn't already exist
            if not os.path.exists(_new_folder):
                self.vampire.logger.debug("%s does not exist. Creating directory", _new_folder)
                os.makedirs(_new_folder)
            _modis_download = downmodis.downModis(destinationFolder=_new_folder, tiles=tiles,
                                                  product=product, today=_month, delta=_delta,
                                                  user=_user, password=_password)
            _modis_download.connect()
            _check_files = _modis_download.getFilesList(_folder_date)
    #            if logger: logger.debug("check files: %s", _check_files)
            _dl_files = _modis_download.checkDataExist(_check_files)
            try:
                _modis_download.downloadsAllDay(clean=True)
            except Exception, e:
                self.vampire.logger.debug('Error in pymodis.modisDown.downloadsAllDay downloading %s', _dl_files)
                raise ValueError('Error in pymodis.modisDown.downloadsAllDay')
            _modis_download.removeEmptyFiles()
            _modis_download.closeFilelist()
            # want list of files downloaded (or files for this day)
            _files_list = []
            for f in _check_files:
                if os.path.splitext(os.path.join(_new_folder, f))[1] == '.hdf':
                    _files_list.append(os.path.join(_new_folder, f))
            _files = glob.glob(os.path.join(_new_folder, '{product}*.hdf'.format(product=product[:-4])))
    #            if logger: logger.debug("files: %s", _files)
            self.vampire.logger.debug("downloaded files: %s", _files_list)
            if mosaic_dir:
                # mosaic files
                mosaic_file = self.mosaic_tiles(_files_list, mosaic_dir, product)
                _m_files.append(mosaic_file)

        if mosaic_dir:
            return _m_files
        self.vampire.logger.info('leaving download_data')
        return _dl_files

    def mosaic_tiles(self, files, output_dir, product, overwrite=False):
        self.vampire.logger.info('entering mosaic_tiles')
#def mosaicTiles(files, output_dir, tools_dir="", overwrite = False, subset=[1,1,0,0,0,0,0,0,0,0,0], ofmt='HDF4Image',
#                gdal=False, logger = None):
        # use MRTools
        _mrt_path = self.vampire.get('directories', 'mrt_dir')
        _list_filename = os.path.join(output_dir, "file_list.txt")
        self._write_mosaic_list(_list_filename, files)
        _new_filename = vampire.filename_utils.generate_output_filename(input_filename=os.path.basename(files[0]),
                                                                        in_pattern=self.vampire.get('MODIS',
                                                                                         'modis_tile_pattern'),
                                                                        out_pattern=self.vampire.get('MODIS',
                                                                                         'modis_mosaic_output_pattern'),
                                                                        ignore_leap_year=False)
        _spectral_subset = self.vampire.get('MODIS_PRODUCTS', product)
        if not os.path.exists(os.path.normpath(os.path.join(output_dir, _new_filename))) or overwrite:
            self._mosaic_files(os.path.normpath(_list_filename),
                               os.path.normpath(os.path.join(output_dir, _new_filename)),
                               _spectral_subset)
        os.remove(_list_filename)
        self.vampire.logger.info('leaving mosaic_tiles')
        return _new_filename

    def extract_NDVI(self, input_dir, output_dir, patterns=None, product=None, overwrite=False):
        self.vampire.logger.info('entering extract_NDVI')
#def extractNDVI(base_path, output_path, tools_path,
#                patterns = None, suffix = modis_constants['ndvi_subset'], overwrite = False, logger = None):
        if not patterns:
            patterns = (self.vampire.get('MODIS_NDVI', 'ndvi_input_pattern'),
                        self.vampire.get('MODIS_NDVI', 'ndvi_output_pattern'))
        if product is None:
            _product = self.vampire.get('MODIS', 'vegetation_product')
        else:
            _product = product
        _spectral_subset = json.loads(self.vampire.get('MODIS_PRODUCTS', '{0}.NDVI'.format(_product)))
        _subset_name = self.vampire.get('MODIS_PRODUCTS', '{0}.NDVI_Name'.format(_product))
        new_files = self._extract_subset(input_dir, output_dir, patterns,
                                         _spectral_subset, _subset_name,
                                         #self.vampire.get('MODIS_NDVI', 'ndvi_spectral_subset'),
                                         #self.vampire.get('MODIS_NDVI', 'ndvi_subset_name'),
                                         overwrite)
        self.vampire.logger.info('leaving extract_NDVI')
        return new_files

    def extract_EVI(self, input_dir, output_dir, file_pattern=None, output_pattern=None, product=None, overwrite = False):
        self.vampire.logger.info('entering extract_EVI')
        if file_pattern is None:
            _file_pattern = self.vampire.get('MODIS', 'modis_monthly_pattern')
        else:
            _file_pattern = file_pattern

        if output_pattern is None:
            _output_pattern = self.vampire.get('MODIS_EVI', 'evi_output_pattern')
        else:
            _output_pattern = output_pattern
        patterns = (_file_pattern, _output_pattern)
        if product is None:
            _product = self.vampire.get('MODIS', 'vegetation_product')
        else:
            _product = product
        _spectral_subset = json.loads(self.vampire.get('MODIS_PRODUCTS', '{0}.EVI'.format(_product)))
        _subset_name = self.vampire.get('MODIS_PRODUCTS', '{0}.EVI_Name'.format(_product))
        new_files = self._extract_subset(input_dir, output_dir, patterns,
                                         _spectral_subset, _subset_name,
                                         #json.loads(self.vampire.get('MODIS_EVI', 'evi_spectral_subset')),
                                         #self.vampire.get('MODIS_EVI', 'evi_subset_name'),
                                         overwrite)
        self.vampire.logger.info('leaving extract_EVI')
        return new_files

    def extract_LST(self, input_dir, output_dir, file_pattern=None, output_pattern=None, layer=None,
                    product=None, overwrite = False):
        self.vampire.logger.info('entering extract_LST')
        if file_pattern is None:
            _file_pattern = self.vampire.get('MODIS', 'modis_monthly_pattern')
        else:
            _file_pattern = file_pattern

        if output_pattern is None:
            _output_pattern = self.vampire.get('MODIS_LST', 'lst_output_pattern')
        else:
            _output_pattern = output_pattern
        patterns = (_file_pattern, _output_pattern)

        if product is None:
            _product = self.vampire.get('MODIS', 'land_surface_temperature_product')
        else:
            _product = product

        if layer is None or layer == 'LST_Day':
            # extract day by default
            _spectral_subset = json.loads(self.vampire.get('MODIS_PRODUCTS', '{0}.LST_Day'.format(_product)))
            _subset_name = self.vampire.get('MODIS_PRODUCTS', '{0}.LST_Day_Name'.format(_product))
        elif layer == 'LST_Night':
            _spectral_subset = json.loads(self.vampire.get('MODIS_PRODUCTS', '{0}.LST_Night'.format(_product)))
            _subset_name = self.vampire.get('MODIS_PRODUCTS', '{0}.LST_Night_Name'.format(_product))
        else:
            raise

        new_files = self._extract_subset(input_dir, output_dir, patterns,
                                         _spectral_subset,
                                         _subset_name,
                                         overwrite)
        self.vampire.logger.info('leaving extract_LST')
        return new_files

    def match_day_night_files(self, day_dir, night_dir, output_dir, patterns=None):
        self.vampire.logger.info('entering match_day_night_files')
        nightFiles = set(os.listdir(night_dir))
        if patterns[0]:
            if not os.path.isdir(day_dir):
                dayFiles = vampire.directory_utils.get_matching_files(os.path.dirname(day_dir), patterns[0],
                                                                      self.vampire.logger)
            else:
                dayFiles = vampire.directory_utils.get_matching_files(day_dir, patterns[0], self.vampire.logger)
        else:
            dayFiles = list(os.listdir(day_dir))
        print "Day files: ", dayFiles
        print "Night files: ", nightFiles

        if not os.path.exists(output_dir):
            os.makedirs(output_dir)

        for fl in dayFiles:
            # find matching night file
            d_fl, ext = os.path.splitext(os.path.basename(os.path.normpath(fl)))
            if (ext == '.tif'):
                d_t = d_fl.rpartition('.')
                # create regex pattern
                _pattern = re.compile('^{0}{1}LST_Night\w*.tif$'.format(d_t[0], d_t[1]))
                for n_fl in nightFiles:
                    if _pattern.match(n_fl):
                        avg_fl = os.path.join(output_dir, d_t[0] + d_t[1] + 'avg' + ext)
                        dp = os.path.join(day_dir, d_fl+ext)
                        np = os.path.join(night_dir, n_fl)
                        calculate_statistics.calc_average_of_day_night(dp, np, avg_file=avg_fl)
                        break
        self.vampire.logger.info('leaving match_day_night_files')
        return None

    def calc_longterm_stats(self, input_dir, output_dir, product,
                            interval, country=None, input_pattern=None, output_pattern=None,
                            start_date=None, end_date=None,
                            function_list=None):
        self.vampire.logger.info('entering calc_longterm_stats')
        if output_pattern is None:
            if product == self.vampire.get('MODIS', 'vegetation_product'):
                _output_pattern = self.vampire.get('MODIS_EVI_Long_Term_Average', 'lta_output_pattern')
            elif product == self.vampire.get('MODIS', 'land_surface_temperature_product'):
                _output_pattern = self.vampire.get('MODIS_LST_Long_Term_Average', 'lta_output_pattern')
            else:
                raise # product unknown
        else:
            _output_pattern = output_pattern
        if country is None:
            _country = self.vampire.get('vampire', 'home_country')
        else:
            _country = country
        if input_pattern is None:
            if country == 'Global':
                if product == self.vampire.get('MODIS', 'vegetation_product'):
                    _input_pattern = self.vampire.get('MODIS', 'evi_pattern')
                elif product == self.vampire.get('MODIS', 'land_surface_temperature_product'):
                    _input_pattern = self.vampire.get('MODIS_LST', 'lst_pattern')
                else:
                    raise # product unknown
            else:
                if product == self.vampire.get('MODIS', 'vegetation_product'):
                    _input_pattern = self.vampire.get('MODIS_EVI', 'evi_regional_pattern')
                elif product == self.vampire.get('MODIS', 'land_surface_temperature_product'):
                    _input_pattern = self.vampire.get('MODIS_LST', 'lst_regional_pattern')
                else:
                    raise # product unknown
        else:
            _input_pattern = input_pattern

        _convert_interval = False
        _new_interval = None
        if interval is not None:
            if interval != self.vampire.get('MODIS_PRODUCTS', '{0}.interval'.format(product)):
                _convert_interval = True
                _new_interval = interval
                _interval = self.vampire.get('MODIS_PRODUCTS', '{0}.interval'.format(product))
            else:
                _interval = interval
        else:
            _interval = self.vampire.get('MODIS_PRODUCTS', '{0}.interval'.format(product))

        # if product is not None:
        #     _interval = self.vampire.get('MODIS_PRODUCTS', '{0}.interval'.format(product))
        # else:
        #     # use default - monthly
        #     _interval = interval

        _all_files = vampire.directory_utils.get_matching_files(input_dir, input_pattern, self.vampire.logger)
        _file_list = {}
        _yrs = []
        _doy = []
        for f in _all_files:
            _fname = os.path.basename(f)
            _result = re.match(_input_pattern, _fname)
            if not 'month' in _result.groupdict():
                if 'dayofyear' in _result.groupdict():
                    _dt = datetime.datetime(int(_result.group('year')), 1,1) + \
                          datetime.timedelta(int(_result.group('dayofyear'))-1)
                    _month = _dt.month
                    _day = _dt.day
                else:
                    raise ValueError('No month or day of year in file pattern')
            else:
                _month = int(_result.group('month'))
                _day = int(_result.group('day'))

            _f_date = datetime.date(int(_result.group('year')), _month, _day)
            # TODO: base date should be from start of long-term average data, not necessarily 2000
            _base_date = datetime.date(2000, _month, _day)
#            _base_name = '{0}-{1}'.format(_result.group('base_name'), _result.group('version'))
            # check if start_date is a datetime object or a string
            if start_date is not None:
                if type(start_date) is datetime.date or type(start_date) is datetime.datetime:
                    if _f_date < start_date.date():
                        break
                else:
                    if _f_date < (dateutil.parser.parse(start_date)).date():
                        break
            else:
                if end_date is not None:
                    if type(end_date) is datetime.date or type(end_date) is datetime.datetime:
                        if _f_date > end_date:
                            break
                    else:
                        if _f_date > (dateutil.parser.parse(end_date)).date():
                            break
#                else:
            _yrs.append(_result.group('year'))
            _doy.append(_f_date.timetuple().tm_yday)
            _file_list.setdefault(_f_date.timetuple().tm_yday, []).append(f)

        _years = set(_yrs)
        _syr = min(_years) #1981
        _eyr = max(_years)
        _num_yrs = str(int(_eyr) - int(_syr))
        # if need to convert 8-days to 16-days, do the next section to combine files into correct
        # lists. NOTE: This will only work for 8-day to 16-day conversion
        # TODO: make this generic so it works for other conversions.
        if _convert_interval and _new_interval == '16-days':
            _doys = set(_doy)
            _sorted_doy = sorted(_doys)
            _new_doys = []
            _new_file_list = {}
            _new_temp_list = []
            for x in _sorted_doy:
                if (x-1) % 16 == 0:
                    # yes
                    _new_doys.append(x)
                    _new_file_list.setdefault(x, []).extend(_file_list[x])
                    _new_file_list.setdefault(x, []).extend(_new_temp_list)
                    _new_temp_list = []
                else:
                    _new_temp_list.extend(_file_list[x])
            if _new_temp_list:
                # add last data to first item
                _new_file_list.setdefault(1, []).extend(_new_temp_list)
            _interval = _new_interval
            _file_list = _new_file_list

        _output_pattern = _output_pattern.replace('{yr_range}', '{0}-{1}'.format(_syr, _eyr))
        _output_pattern = _output_pattern.replace('{num_yrs}', '{0}yrs'.format(_num_yrs))
        _output_pattern = _output_pattern.replace('{subset}', '{0}'.format(_interval.lower()))
        if function_list is None:
            _function_list = ['AVG']
        else:
            _function_list = function_list

        if not os.path.isdir(output_dir):
            # directory doesn't exist....create it first
            os.makedirs(output_dir)
        for d in _file_list:
            fl = _file_list[d]
            newfl = vampire.directory_utils.unzip_file_list(fl)
            if len(fl) != 0:
                for func in function_list:
                    _fn_output_pattern = _output_pattern.replace('{statistic}', func.lower())
                    newfilename = vampire.filename_utils.generate_output_filename(os.path.basename(fl[0]),
                                                                                  _input_pattern, _fn_output_pattern)
                    self._calculate_stats(newfl, newfilename, output_dir, [func])


#         if interval == 'monthly':
#             for m in _months:
#                 # for each month, calculate long term average
#                 if m in _file_list:
#                     fl = _file_list[m]
#                     newfl = vampire.directory_utils.unzip_file_list(fl)
#                     for func in function_list:
#                         _fn_output_pattern = _output_pattern.replace('{statistic}', func.lower())
#                         newfilename = vampire.filename_utils.generate_output_filename(fl, _input_pattern, _fn_output_pattern)
# #                    newfilename = '{0}.{1}-{2}.{3}.monthly.{4}yrs'.format(_base_name, _syr, _eyr, m, _numyrs)
#                         self._calculate_stats(newfl, newfilename, output_dir, [func])

        self.vampire.logger.info('leaving calc_longterm_stats')
        return None

    def _extract_subset(self, input_dir, output_dir, patterns, subset, subset_name, overwrite = False):
        self.vampire.logger.info('entering _extract_subset')
        _all_files = vampire.directory_utils.get_matching_files(input_dir, patterns[0], self.vampire.logger)
        if not _all_files:
            self.vampire.logger.debug('Extracting subset {0}. No files found in {1} with pattern {2}'.format(
                subset_name, input_dir, patterns[0]))
            print 'No files found in ' + input_dir + ', please check directory and try again'
            return -1

        # check output directory exists and create it if not
        if not os.path.isdir(output_dir):
            os.makedirs(output_dir)
        new_files = []
        for _ifl in _all_files:
            # generate parameter file
            _nfl = vampire.filename_utils.generate_output_filename(os.path.basename(_ifl), patterns[0], patterns[1])
            _ofl = os.path.join(output_dir, _nfl)
            _checkfl = "{0}.{1}{2}".format(os.path.splitext(_ofl)[0], subset_name, os.path.splitext(_ofl)[1])
            if not os.path.exists(_checkfl) or overwrite == True:
                try:
                    src_ds = gdal.Open(_ifl)
                except RuntimeError, e:
                    self.vampire.logger.debug('Unable to open file')
                    return -1
                sds = src_ds.GetSubDatasets()
#                if logger: logger.debug("Number of bands: %s",src_ds.RasterCount)
                self._convert_to_tiff(_ifl, _ofl, self.vampire.get('directories', 'gdal_dir'))
                for idx, sbs in enumerate(sds):
#                    if logger: logger.debug("Subdataset: %s", sbs[0])
                    # get subset name (without spaces)
                    _n = (sbs[0].rsplit(':', 1)[1]).replace(' ', '_')
                    _rf = "{0}.{1}{2}".format(os.path.splitext(os.path.basename(_ofl))[0], _n, os.path.splitext(_ofl)[1])
                    _cf = "{0}_{1}{2}".format(os.path.splitext(os.path.basename(_ofl))[0], str(idx+1).zfill(2), os.path.splitext(_ofl)[1])
                    if not os.path.exists(os.path.join(output_dir, _cf)) or overwrite:
                        _cf = "{0}_{1}{2}".format(os.path.splitext(os.path.basename(_ofl))[0], str(idx+1), os.path.splitext(_ofl)[1])
                    if idx+1 not in subset:
                        # remove un-needed files (including .aux & .aux.xml)
                        os.remove(os.path.join(output_dir, _cf))
                        _aux_f = os.path.join(output_dir,"{0}.aux.xml".format(_cf))
                        if os.path.exists(_aux_f):
                            os.remove(_aux_f)
                    else:
                        # keep this file - rename with subset name
                        if os.path.exists(os.path.join(output_dir, _rf)):
                            if overwrite:
                                # file already exists....delete first
                                os.remove(os.path.join(output_dir, _rf))
                                os.rename(os.path.join(output_dir, _cf), os.path.join(output_dir, _rf))
                            else:
                                # just remove the new file
                                os.remove(os.path.join(output_dir, _cf))
                        else:
                            os.rename(os.path.join(output_dir, _cf), os.path.join(output_dir, _rf))

                        _aux_f = os.path.join(output_dir,"{0}.aux.xml".format(_cf))
                        if os.path.exists(_aux_f):
                            if os.path.exists(os.path.join(output_dir, "{0}.aux.xml".format(_rf))):
                                # can't rename, delete first
                                os.remove(os.path.join(output_dir, "{0}.aux.xml".format(_rf)))
                            os.rename(_aux_f, os.path.join(output_dir, "{0}.aux.xml".format(_rf)))
                        new_files.append(_rf)
        self.vampire.logger.info('leaving _extract_subset')
        return new_files



    def _write_mosaic_list(self, filename, files=None):
        self.vampire.logger.info('entering _write_mosaic_list')
        if files:
            try:
                if not os.path.exists(os.path.dirname(filename)):
                    # directory doesn't exist, create it first
                    os.makedirs(os.path.dirname(filename))
                pfile = open(filename, 'w')
            except IOError as e:
                if e.errno == errno.EACCES:
                    return "Error creating file " + filename
                # Not a permission error.
                raise
            else:
                with pfile:
                    for f in files:
                        pfile.write('"' + f + '"')
                        pfile.write('\n')
                    pfile.close()
        self.vampire.logger.info('leaving _write_mosaic_list')
        return None

    def _mosaic_files(self, file_list, output_filename, subset):
        self.vampire.logger.info('entering _mosaic_files')
        # call mrtmosaic using input filename
        try:
            mrt_path = os.path.normpath(self.vampire.get('directories', 'mrt_dir'))
        except OSError as e:
            print "Cannot find mrt_dir"
            raise
        try:
            if platform == 'Windows':
                subprocess.check_call([os.path.join(mrt_path,'mrtmosaic.exe'),
                                       '-i', file_list, '-o', output_filename,
                                       '-s', subset])
            elif platform == 'Linux':
                subprocess.check_call([os.path.join(mrt_path,'mrtmosaic'),
                                       '-i', file_list, '-o', output_filename,
                                       '-s', subset])
        except subprocess.CalledProcessError as e:
            print("Error in mrtmosaic")
            print(e.output)
            raise
        self.vampire.logger.info('leaving _mosaic_files')
        return None

    def _convert_to_tiff(self, ifl, ofl, gdal_dir, overwrite=False):
        self.vampire.logger.info('entering _convert_to_tiff')
        try:
            _gdal_translate = None
            if platform == 'Windows':
                _gdal_translate = os.path.join(gdal_dir, 'gdal_translate.exe')
            elif platform == 'Linux':
                _gdal_translate = os.path.join(gdal_dir, 'gdal_translate')
            subprocess.check_call([_gdal_translate, '-sds', ifl, ofl])
        except subprocess.CalledProcessError as e:
            print("Error in converting to .tif")
            print(e.output)
            raise
        self.vampire.logger.info('leaving _convert_to_tiff')
        return None

    def _calculate_stats(self, file_list, new_filename, output_dir, function_list):
        self.vampire.logger.info('entering _calculate_stats')
        for f in function_list:
            if f == 'AVG':
#                newfile = '{0}.avg.tif'.format(new_filename)
                ofl = os.path.join(output_dir, new_filename)
                calculate_statistics.calc_average(file_list, ofl)
            elif f == 'STD':
#                newfile = '{0}.std.tif'.format(new_filename)
                ofl = os.path.join(output_dir, new_filename)
                calculate_statistics.calc_std_dev(file_list, ofl)
            elif f == 'MAX':
#                newfile = '{0}.max.tif'.format(new_filename)
                ofl = os.path.join(output_dir, new_filename)
                calculate_statistics.calc_max(file_list, ofl)
            elif f == 'MIN':
#                newfile = '{0}.min.tif'.format(new_filename)
                ofl = os.path.join(output_dir, new_filename)
                calculate_statistics.calc_min(file_list, ofl)
            elif f == 'SUM':
#                newfile = '{0}.sum.tif'.format(new_filename)
                ofl = os.path.join(output_dir, new_filename)
                calculate_statistics.calc_sum(file_list, ofl)
            else:
                print f, ' is not a valid function.'
        self.vampire.logger.info('entering _calculate_stats')
        return None

