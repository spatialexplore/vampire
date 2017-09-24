import vampire.VampireDefaults as VampireDefaults
import vampire.directory_utils
import BaseTaskImpl
import ftputil
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


class CHIRPSTasksImpl():
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

@CHIRPSTasksImpl.register_subclass('download')
class CHIRPSDownloadTask(BaseTaskImpl.BaseTaskImpl):
    """ Initialise MODISDownloadTask object.

    Implementation class for downloading MODIS products.

    """
    def __init__(self, params, vampire_defaults):
        super(CHIRPSDownloadTask, self).__init__(params, vampire_defaults)
        logger.debug('Initialising CHIRPS download task')
        return

    def process(self):
        logger.debug("Downloading CHIRPS data")
        try:
            output_dir = self.params['output_dir']
        except Exception, e:
            raise BaseTaskImpl.ConfigFileError("No ouput directory 'output_dir' specified.", e)
        _dates = None
        _start_date = None
        _end_date = None
        _overwrite = False
        if 'dates' in self.params:
            _dates = self.params['dates']
        if 'start_date' in self.params:
            _start_date = self.params['start_date']
        if 'end_date' in self.params:
            _end_date = self.params['end_date']
        if 'overwrite' in self.params:
            _overwrite = True
        self.download_data(output_dir, self.params['interval'], dates=_dates, start_date=_start_date,
                         end_date=_end_date, overwrite=_overwrite)

    def download_data(self, output_dir, interval, dates=None, start_date=None, end_date=None, overwrite=False):
        """ Download CHIRPS precipitation data for given interval.

        Download CHIRPS precipitation data for given interval. Will download all available data unless start
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
        _ftp_dir = self.vp.get('CHIRPS', 'ftp_dir_{0}'.format(interval.lower()))
        files_list = []
        all_files = []
        if not os.path.exists(output_dir):
            # output directory does not exist, create it first
            os.makedirs(output_dir)
        with ftputil.FTPHost(self.vp.get('CHIRPS', 'ftp_address'),
                             self.vp.get('CHIRPS', 'ftp_user'),
                             self.vp.get('CHIRPS', 'ftp_password')) as ftp_host:
            ftp_host.chdir(_ftp_dir)
            if interval.lower() == 'daily':
                # daily files are in directory by year so create new list of files
                # loop through years in dates and get from the correct directory
                _years = []
                _ftp_years = ftp_host.listdir(ftp_host.curdir)
                if start_date is not None:
                    if end_date is not None:
                        # have both start and end dates, create list of years
                        for i in range(start_date.year, start_date.year+(end_date.year-start_date.year)):
                            _years.append(start_date.year + i)
                    else:
                        # have start date but no end date. Find last year available and download all until then
                        for fd in _ftp_years:
                            if int(fd) >= start_date.year:
                                _years.append(int(fd))
                else:
                    # no start date
                    if end_date is not None:
                        # have end date but no start date. Find all years until end_date
                        for fd in _ftp_years:
                            if int(fd) <= end_date.year:
                                _years.append(int(fd))
                    else:
                        # no start or end date.
                        if dates:
                            # have list of dates
                            for d in dates:
                                _years.append(int(d.split('-')[0]))
                _years = set(_years)
                for y in _years:
                    ftp_host.chdir(ftp_host.path.join(_ftp_dir, str(y)))
                    _files = ftp_host.listdir(ftp_host.curdir)
                    if _files is not None:
                        for f in _files:
                            _f_abs = ftp_host.path.join(ftp_host.getcwd(), f)
                            all_files.append(_f_abs)
            else:
                all_files = ftp_host.listdir(ftp_host.curdir)
            regex = re.compile(self.vp.get('CHIRPS', 'global_{0}_pattern'.format(interval)))
            for f in all_files:
                download = False
                result = regex.match(os.path.basename(f))
                f_date = None
                if result is not None:
                    if interval.lower() == 'monthly' or interval.lower() == 'dekad' or interval.lower() == 'daily':
                        f_year = result.group('year')
                        f_month = result.group('month')
                        f_day = 1
                        if interval.lower() == 'daily':
                            f_day = result.group('day')
                        f_date = datetime.datetime(int(f_year), int(f_month), int(f_day))
                    elif interval.lower() == 'seasonal':
                        f_year = result.group('year')
                        f_month = result.group('season')[0:2]
                        f_date = datetime.datetime(int(f_year), int(f_month), 1)
                    else:
                        raise ValueError, "Interval not recognised."
                    if dates:
                        if '{0}-{1}'.format(f_year, f_month) in dates:
                            download = True
                    elif (start_date is None) and (end_date is None):
                        download = True
                    elif start_date is None:
                        # have end_date, check date is before
                        if f_date is not None:
                            if f_date <= end_date:
                                download = True
                    elif end_date is None:
                        # have start_date, check date is after
                        if f_date is not None:
                            if f_date >= start_date:
                                download = True
                    else:
                        # have both start and end date
                        if f_date is not None:
                            if f_date >= start_date and f_date <= end_date:
                                download = True
                    if download:
                        if ftp_host.path.isfile(f):
                            local_f = os.path.join(output_dir, os.path.basename(f))
                            if not os.path.isfile(local_f) or overwrite:
                                ftp_host.download(f, local_f)  # remote, local
                                files_list.append(os.path.basename(f))
        return files_list


@CHIRPSTasksImpl.register_subclass('longterm_average')
class CHIRPSLongtermAverageTask(BaseTaskImpl.BaseTaskImpl):
    """ Initialise MODISDownloadTask object.

    Implementation class for downloading MODIS products.

    """
    def __init__(self, params, vampire_defaults):
        super(CHIRPSLongtermAverageTask, self).__init__(params, vampire_defaults)
        logger.debug('Initialising MODIS download task')
        return

    def process(self):
        logger.debug("Calculating CHIRPS long-term average")
        try:
            output_dir = self.params['output_dir']
        except Exception, e:
            raise BaseTaskImpl.ConfigFileError("No ouput directory 'output_dir' specified.", e)
        if 'dates' in self.params:
            dates = self.params['dates']
        try:
            input_dir = self.params['input_dir']
        except Exception, e:
            raise BaseTaskImpl.ConfigFileError("No input directory 'input_dir' specified.", e)

        if 'functions' in self.params:
            funcs = self.params['functions']
        else:
            funcs = ['AVG']

        if 'file_pattern' in self.params:
            pattern = self.params['file_pattern']
        else:
            pattern = None

        self.calculate_longterm_stats(self.params['interval'], input_dir, output_dir, pattern=pattern,
                                    function_list=funcs)
        return

    # Compute statistics for all files within a directory. Computes average unless other functions are provided.
    def calculate_longterm_stats(self, interval, base_path, output_path, pattern=None, function_list=['AVG']):
        if pattern is None:
            _pattern = self.vampire.get('CHIRPS', 'global_{0}_pattern'.format(interval.lower()))
        else:
            _pattern = pattern

        _all_files = vampire.directory_utils.get_matching_files(base_path, _pattern)
        _files_list = {}
        _months_list = {}
        _yrs = []
        _base_name = ''
        for f in _all_files:
            _fname = os.path.basename(f)
            _result = re.match(_pattern, _fname)
            if _result.groups('country') is not None:
                _base_name = '{0}_{1}-{2}'.format(_result.group('country'),
                                                  _result.group('base_name'),
                                                  _result.group('version'))
            else:
                _base_name = '{0}-{1}'.format(_result.group('base_name'), _result.group('version'))
            _yrs.append(_result.group('year'))
            if interval == 'monthly':
                _files_list.setdefault(_result.group('month'), []).append(f)
            elif interval == 'dekad':
                _files_list.setdefault(_result.group('month'), {})
                _months_list = _files_list[_result.group('month')].setdefault(_result.group('dekad'), []).append(f)
            elif interval == 'seasonal':
                _files_list.setdefault(_result.group('season'), []).append(f)
            else:
                raise ValueError, "Interval not recognised."

        _years = set(_yrs)
        _syr = min(_years) #1981
        _eyr = max(_years)
        _numyrs = str(int(_eyr) - int(_syr))
        _dekads = ['1', '2', '3']
        _months = ['01', '02', '03', '04', '05', '06', '07', '08', '09', '10', '11', '12']
        _seasons = ['010203','020304','030405','040506', '050607', '060708', '070809', '080910', '091011', '101112', '111201', '120102']
        if interval == 'monthly':
            for m in _months:
                # for each month, calculate long term average
                if m in _files_list:
                    fl = _files_list[m]
                    newfilename = '{0}.{1}-{2}.{3}.monthly.{4}yrs'.format(_base_name, _syr, _eyr, m, _numyrs)
                    newfl = vampire.directory_utils.unzip_file_list(fl)
                    self.calculate_stats(newfl, newfilename, output_path, function_list)
        elif interval == 'seasonal':
            for s in _seasons:
                # for each season, calculate long term average
                if s in _files_list:
                    fl = _files_list[s]
                    newfilename = '{0}.{1}-{2}.{3}.seasonal.{4}yrs'.format(_base_name, _syr, _eyr, s, _numyrs)
                    newfl = vampire.directory_utils.unzip_file_list(fl)
                    self.calculate_stats(newfl, newfilename, output_path, function_list)
        elif interval == 'dekad':
            for m in _months:
                for d in _dekads:
                    # for each dekad of each month, calculate long term average
                    if m in _files_list:
                        if d in _files_list[m]:
                            fl = _files_list[m][d]
                            newfilename = '{0}.{1}-{2}.{3}.{4}.dekad.{5}yrs'.format(_base_name, _syr, _eyr, m, d, _numyrs)
                            newfl = vampire.directory_utils.unzip_file_list(fl)
                            self.calculate_stats(newfl, newfilename, output_path, function_list)
        else:
            raise ValueError, "Interval not recognised."
        return None

    # helper function to calculate statistics for a list of files.
    def calculate_stats(self, file_list, new_filename, output_dir, function_list):
        """ Calculate statistics for a list of raster files and save results to output directory.

        For each raster in the list, calculate each statistic in the list of functions. All resulting
        rasters are saved in the output directory with the new filename and statistic function name.

        Parameters
        ----------
        file_list : list
            Filename of raster file
        new_filename : str
            Filename of output file
        output_dir : str
            Name of directory to save output files in
        function_list : list
            List of statistics to calculate. Valid statistic functions are AVG, SUM, STD, MIN and MAX

        Returns
        -------
        None
            Returns None

        """
        for f in function_list:
            if f == 'AVG':
                newfile = '{0}.avg.tif'.format(new_filename)
                ofl = os.path.join(output_dir, newfile)
                calculate_statistics.calc_average(file_list, ofl)
            elif f == 'STD':
                newfile = '{0}.std.tif'.format(new_filename)
                ofl = os.path.join(output_dir, newfile)
                calculate_statistics.calc_std_dev(file_list, ofl)
            elif f == 'MAX':
                newfile = '{0}.max.tif'.format(new_filename)
                ofl = os.path.join(output_dir, newfile)
                calculate_statistics.calc_max(file_list, ofl)
            elif f == 'MIN':
                newfile = '{0}.min.tif'.format(new_filename)
                ofl = os.path.join(output_dir, newfile)
                calculate_statistics.calc_min(file_list, ofl)
            elif f == 'SUM':
                newfile = '{0}.sum.tif'.format(new_filename)
                ofl = os.path.join(output_dir, newfile)
                calculate_statistics.calc_sum(file_list, ofl)
            else:
                print f, ' is not a valid function.'
        return None
