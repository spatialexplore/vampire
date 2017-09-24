import vampire.VampireDefaults as VampireDefaults
import vampire.directory_utils
import urllib
import os
import re
import datetime
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

        self.download_data(output_dir=output_dir, interval=self.params['interval'], variable=_variable,
                           level=_level, forecast_hr=_forecast_hr, dates=_dates, start_date=_start_date,
                           end_date=_end_date, overwrite=_overwrite)
        return None

    def download_data(self, output_dir, interval, variable=None, level=None, forecast_hr=None, dates=None,
                      start_date=None, end_date=None, overwrite=False):
        """ Download GFS precipitation data for given interval.

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
        _hh = self.vp.get('GFS', 'hh') #18'
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
        _extent = self.vp.get('GFS', 'extent') #[0, 360, 90, -90]

        if output_dir is not None:
            _output_dir = output_dir
        else:
            _output_dir = self.vp.get('GFS', 'data_dir')

        files_list = []
        for i in dates:
            _date = '{0:04d}{1:02d}{2:02d}{3}'.format(i.year, i.month, i.day, _hh)
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
            for i in range(6, 390, 6):
                _fcst_hr_str = '{0:03d}'.format(i)
                _file = 'gfs.t' + _hh + 'z.pgrb2.0p25.f' + _fcst_hr_str
                _file_str = 'file=' + _file
                url = base_url + _file_str + '&' + _level_str + '&' + _var_str + '&' + _extent_str + '&' + _dir_str
                if overwrite or not os.path.exists(_file + '.grb'):
                    urllib.urlretrieve(url, _file + '.grb')
                    files_list.append(_file + '.grb')
        return files_list


