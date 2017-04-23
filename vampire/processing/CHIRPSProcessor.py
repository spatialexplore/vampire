__author__ = 'rochelle'

import vampire.VampireDefaults
import vampire.directory_utils
import ftputil
import os
import re
import datetime

import platform
try:
    import calculate_statistics_arc as calculate_statistics
    import precipitation_analysis_arc as precip_analysis
except ImportError:
    import calculate_statistics_os as calculate_statistics
    import precipitation_analysis_os as precip_analysis


# platform = platform.system()
# if platform == "Linux":
#     import calculate_statistics_os as calculate_statistics
#     import precipitation_analysis_os as precip_analysis
# elif platform == "Windows":
#     import calculate_statistics_arc as calculate_statistics
#     import precipitation_analysis_arc as precip_analysis

class CHIRPSProcessor:
    def __init__(self):
        # load default values from .ini file
        self.vampire = vampire.VampireDefaults.VampireDefaults()
        return

    # helper function to calculate statistics for a list of files.
    def calculate_stats(self, file_list, new_filename, output_dir, function_list):
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

    # Download CHIRPS precipitation data for given interval. Will download all available data unless start and/or
    # end dates are provided.
    def download_data(self, output_dir, interval, dates=None, start_date=None, end_date=None, overwrite=False):
        _ftp_dir = self.vampire.get('CHIRPS', 'ftp_dir_{0}'.format(interval.lower()))
        files_list = []
        all_files = []
        if not os.path.exists(output_dir):
            # output directory does not exist, create it first
            os.makedirs(output_dir)
        with ftputil.FTPHost(self.vampire.get('CHIRPS', 'ftp_address'),
                             self.vampire.get('CHIRPS', 'ftp_user'),
                             self.vampire.get('CHIRPS', 'ftp_password')) as ftp_host:
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
            regex = re.compile(self.vampire.get('CHIRPS', 'global_{0}_pattern'.format(interval)))
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

