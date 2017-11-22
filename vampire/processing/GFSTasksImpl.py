import vampire.VampireDefaults as VampireDefaults
import vampire.directory_utils
import vampire.filename_utils
import urllib
import os
import re
import datetime
import ast
import logging
logger = logging.getLogger(__name__)
try:
    import calculate_statistics_arc as calculate_statistics
    import precipitation_analysis_arc as precip_analysis
except ImportError:
    import calculate_statistics_os as calculate_statistics
    import precipitation_analysis_os as precip_analysis


class ConfigFileError(ValueError):
    def __init__(self, message, e, *args):
        '''Raise when the config file contains an error'''
        self.message = message
        self.error = e
        super(ConfigFileError, self).__init__(message, e, *args)

class GFSTasksImpl():
    subclasses = {}

    @classmethod
    def register_subclass(cls, product_type):
        def decorator(subclass):
            cls.subclasses[product_type] = subclass
            return subclass
        return decorator

    @classmethod
    def create(cls, process_type, params, vampire_defaults=None):
        if process_type not in cls.subclasses:
            raise ValueError('Bad process type {}'.format(process_type))
        if vampire_defaults is None:
            vp = VampireDefaults.VampireDefaults()
        else:
            vp = vampire_defaults

        return cls.subclasses[process_type](params, vp)

@GFSTasksImpl.register_subclass('download')
class GFSDownloadTask(object):
    """ Initialise MODISDownloadTask object.

    Implementation class for downloading MODIS products.

    """
    def __init__(self, params, vampire_defaults):
        logger.debug('Initialising GFS download task')
        self.params = params
        self.vp = vampire_defaults
        return

    def process(self):
        logger.debug("Downloading GFS data")
        try:
            output_dir = self.params['output_dir']
        except Exception, e:
            raise ConfigFileError("No ouput directory 'output_dir' specified.", e)
        _dates = None
        _start_date = None
        _end_date = None
        _overwrite = False
        _variable = None
        _level = None
        _forecast_hr = None
        _accumulate_days = None
        if 'dates' in self.params:
            _dates = self.params['dates']
        if 'start_date' in self.params:
            _start_date = self.params['start_date']
        if 'end_date' in self.params:
            _end_date = self.params['end_date']
        if 'overwrite' in self.params:
            _overwrite = True
        if 'variable' in self.params:
            _variable = self.params['variable']
        if 'level' in self.params:
            _level = self.params['level']
        if 'forecast_hr' in self.params:
            _forecast_hr = self.params['forecast_hr']
        if 'accumulate_days' in self.params:
            _accumulate_days = self.params['accumulate_days']

        _raw_dir = os.path.join(output_dir, "raw")
        # download data (and accumulate to daily)
        _raw_files_list = self.download_data(output_dir=output_dir, # interval=self.params['interval'],
                                             variable=_variable, level=_level, forecast_hr=_forecast_hr,
                                             dates=_dates, start_date=_start_date,
                                             end_date=_end_date, overwrite=_overwrite)
        return None

    def download_data(self, output_dir, #interval,
                      variable=None, level=None, forecast_hr=None, dates=None,
                      start_date=None, end_date=None, overwrite=False, accumulate_days=None, max_days=None):
        """ Download GFS precipitation data for given interval and accumulate to given number of days if specified

        Download GFS precipitation data for given interval. Will download all available data unless start
        and/or end dates are provided.

        Parameters
        ----------
        output_dir : str
            Filename of raster file
        interval : str
            Filename of vector file
        dates : str
            Name of field labelling the zones within vector file
        start_date : str
            Filename of output table (.dbf or .csv)
        end_date : str
            F
        overwrite : boolean

        Returns
        -------
        None
            Returns None

        """
        logger.info('entering download_data')
        base_url = self.vp.get('GFS', 'base_url') #'http://nomads.ncep.noaa.gov/cgi-bin/filter_gfs_0p25.pl?'
        #file=gfs.t18z.pgrb2.0p25.f006&lev_surface=on&var_APCP=on&leftlon=0&rightlon=360&toplat=90&bottomlat=-90&dir=%2Fgfs.2017080818' #pub/data/nccf/com/gfs/prod/gfs.' # real-time location
        _hh = self.vp.get('GFS', 'model_cycle_runtime') #18'
        if forecast_hr is not None:
            _fcst_hr = forecast_hr
        else:
            _fcst_hr = self.vp.get('GFS', 'forecast_hour') #'006'
        if level is not None:
            _level = level
        else:
            _level = self.vp.get('GFS', 'level') #'surface'
        if variable is not None:
            _var = variable
        else:
            _var = self.vp.get('GFS', 'variable') #'APCP'
#        _date = '20170808' + _hh
        _extent = ast.literal_eval(self.vp.get('GFS', 'extent')) #[0, 360, 90, -90]

        if accumulate_days is not None:
            _accumulate_days = accumulate_days
        else:
            _accumulate_days = self.vp.get('GFS', 'default_accumulate')
        if max_days is not None:
            _max_hrs = int(max_days) * 24
        else:
            _max_hrs = int(self.vp.get('GFS', 'max_days')) * 24

        if output_dir is not None:
            _output_dir = output_dir
        else:
            _output_dir = self.vp.get('GFS', 'data_dir')

        files_list = []
#        accum_files_list = []
        _cur_dir = os.getcwd()
        for d in dates:
#            _d = datetime.datetime.strptime(i, '%Y-%m-%d')
            _date = '{0:04d}{1:02d}{2:02d}{3}'.format(d.year, d.month, d.day, _hh)
            _file = 'gfs.t' + _hh + 'z.pgrb2.0p25.f' + _fcst_hr
            _file_str = 'file=' + _file
            _level_str = 'lev_' + _level + '=on'
            _var_str = 'var_' + _var + '=on'
            _extent_str = 'leftlon={0}&rightlon={1}&toplat={2}&bottomlat={3}'.format(_extent[0], _extent[1], _extent[2], _extent[3])
            _dir_str = 'dir=%2Fgfs.' + _date
#            _fcst_hr_num = '0:03d'.format(int(_fcst_hr))

            # if _fcst_hr_num < 100:
            #     fcst_hr_str = '0' + str(_fcst_hr_num)
            # else:
            #     fcst_hr_str = _fcst_hr

 #          # fnamein = 'gfs.t' + hh + 'z.pgrbf' + fcst_hr_str + '.grib2'
 #          # fpathin = base_url + datenow + '/' + fnamein
            _download_dir = os.path.join(_output_dir, _date)
            if not os.path.exists(_download_dir):
                os.makedirs(_download_dir)
            os.chdir(_download_dir)
            # every six hours from 6 to 240, then every 12 hours
            _step = 6
            i = _step
            while i <= _max_hrs:
                _fcst_hr_str = '{0:03d}'.format(i)
                _file = 'gfs.t' + _hh + 'z.pgrb2.0p25.f' + _fcst_hr_str
                _file_str = 'file=' + _file
                url = base_url + _file_str + '&' + _level_str + '&' + _var_str + '&' + _extent_str + '&' + _dir_str
                _fname = _file + '.grb'
                if overwrite or not os.path.exists(_fname):
                    try:
                        urllib.urlretrieve(url, _fname)
                    except urllib.ContentTooShortError, e:
                        print "Content too short!! Didn't download " + _file
                        continue
                    files_list.append(_fname)

                if i == 240:
                    # change step to 12 hrs
                    _step = 12
                i = i + _step

        os.chdir(_cur_dir) # change back to working directory
        return files_list #, accum_files_list


@GFSTasksImpl.register_subclass('accumulate')
class GFSAccumulateTask(object):
    """ Initialise MODISDownloadTask object.

    Implementation class for downloading MODIS products.

    """
    def __init__(self, params, vampire_defaults):
        logger.debug('Initialising GFS accumulate task')
        self.params = params
        self.vp = vampire_defaults
        return

    def process(self):
        logger.debug("Accumulating GFS data")
        try:
            data_dir = self.params['data_dir']
        except Exception, e:
            raise ConfigFileError("No data directory 'data_dir' specified.", e)
        try:
            output_dir = self.params['output_dir']
        except Exception, e:
            raise ConfigFileError("No output directory 'output_dir' specified.", e)
        _accumulate_days = None
        _dates = None
        _data_pattern = None
        _output_pattern = None
        _overwrite = False
        if 'number_of_days' in self.params:
            _accumulate_days = self.params['number_of_days']
        if 'dates' in self.params:
            _dates = self.params['dates']
        if 'data_pattern' in self.params:
            _data_pattern = self.params['data_pattern']
        if 'output_pattern' in self.params:
            _output_pattern = self.params['output_pattern']
        if 'overwrite' in self.params:
            _overwrite = self.params['overwrite']
        # accumulate downloaded data
        _accum_files_list = self.accumulate_data(data_dir=data_dir, data_pattern=_data_pattern,
                                                 output_dir=output_dir, output_pattern=_output_pattern,
                                                 num_days=_accumulate_days, dates=_dates, overwrite=_overwrite)
        return None

    def _accumulate_data(self, files_list, output_dir, output_file):
        _output = os.path.join(output_dir, output_file)
        calculate_statistics.calc_sum(file_list=files_list, sum_file=_output)
        return files_list

    def accumulate_data(self, data_dir=None, data_pattern=None, output_dir=None, output_pattern=None,
                        num_days=None, dates=None, overwrite=False):
        """ Accumulate GFS precipitation data for given interval and accumulate to given number of days if specified

        Download GFS precipitation data for given interval. Will download all available data unless start
        and/or end dates are provided.

        Parameters
        ----------
        output_dir : str
            Filename of raster file
        interval : str
            Filename of vector file
        dates : str
            Name of field labelling the zones within vector file
        start_date : str
            Filename of output table (.dbf or .csv)
        end_date : str
            F
        overwrite : boolean

        Returns
        -------
        None
            Returns None

        """
        logger.info('entering accumulate_data')
        files_list = []
        _dates = []
        if dates is None:
            # get date from data directory name
            _dir_s = os.path.basename(data_dir)[:-2]
            _date = datetime.datetime.strptime(_dir_s, '%Y%m%d')
            _dates.append(_date)
        else:
            _dates = dates

        for d in _dates:
            # find all files
            _allfiles = vampire.directory_utils.get_matching_files(data_dir, data_pattern)
            _cur_day = 0
            _cur_hr = 0
            _cur_accum_str = ''
            _accum_window_start = 0
            _accum_window_end = 0
            _day_ptrs = []

            _pattern = re.compile(data_pattern)

            for idx, fname in enumerate(_allfiles):
                # get forecast hour from filename
                _base_fname = os.path.basename(fname)
                _result = _pattern.match(_base_fname)
                if _result:
                    _forecast_hr = _result.group('forecast_hr')
                    if int(_forecast_hr) % 24 == 0:
                        # end of day
                        _cur_day = _cur_day + 1
                        _day_ptrs.append(idx)
                        if _cur_day >= num_days:
                            # accumulate last num_days
                            _output_pattern = output_pattern.replace('{forecast_day}', ''.join(map(str,
                                                                                                   range(_cur_day-num_days+1,
                                                                                                         _cur_day+1))))
                            _output_pattern = _output_pattern.replace('{year}', '{0}'.format(d.year))
                            _output_pattern = _output_pattern.replace('{month}', '{0:0>2}'.format(d.month))
                            _output_pattern = _output_pattern.replace('{day}', '{0:0>2}'.format(d.day))
                            _new_filename = vampire.filename_utils.generate_output_filename(_base_fname, data_pattern, _output_pattern)
                            if not os.path.exists(os.path.join(output_dir, _new_filename)) or overwrite:
                                self._accumulate_data(_allfiles[_accum_window_start:_accum_window_end+1], output_dir, _new_filename)
                            _accum_window_start = _day_ptrs[_cur_day-num_days]+1
                            files_list.append(_new_filename)
                    _accum_window_end = _accum_window_end + 1


        return files_list
