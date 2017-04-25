
import os
import regex
import datetime
import dateutil
import functools
import vampire.VampireDefaults as VampireDefaults
import vampire.directory_utils as directory_utils
import vampire.filename_utils as filename_utils
import platform
try:
    import precipitation_analysis_arc as precipitation_analysis
    import vegetation_analysis_arc as vegetation_analysis
    import temperature_analysis_arc as temperature_analysis
    import calculate_statistics_arc as calculate_statistics
except ImportError:
    import precipitation_analysis_os as precipitation_analysis
    import vegetation_analysis_os as vegetation_analysis
    import temperature_analysis_os as temperature_analysis
    import calculate_statistics_os as calculate_statistics


# platform = platform.system()
# if platform == "Linux":
#     import precipitation_analysis_os as precipitation_analysis
#     import vegetation_analysis_os as vegetation_analysis
#     import temperature_analysis_os as temperature_analysis
#     import calculate_statistics_os as calculate_statistics
# elif platform == "Windows":
#     import precipitation_analysis_arc as precipitation_analysis
#     import vegetation_analysis_arc as vegetation_analysis
#     import temperature_analysis_arc as temperature_analysis
#     import calculate_statistics_arc as calculate_statistics


class ClimateAnalysis():
    def __init__(self):
        # load default values from .ini file
        self.vampire = VampireDefaults.VampireDefaults()
        return

    # Calculate rainfall anomaly given a precipitation file, long-term average and output result to file.
    # Precipitation file can be given specifically, or as a pattern and directory to search in.
    # Long-term average file can be given specifically, of as a pattern and directory to search in.
    # Destination file can be given specifically, of a filename can be generated based on a pattern with parameters
    # from the precipitation file, and saved in the directory specified.
    # Actual calculation of rainfall anomaly is carried out in the calc_rainfall_anomaly function appropriate to the
    # system (i.e. ArcPy or opensource)
    def calc_rainfall_anomaly(self, dst_filename=None, cur_filename=None, lta_filename=None,
                              cur_dir=None, lta_dir=None,
                              cur_pattern=None, lta_pattern=None, dst_pattern=None,
                              dst_dir=None
                             ):
        self.vampire.logger.info('entering calc_rainfall_anomaly')
        if cur_filename is None:
            # get filename from pattern and directory
            files_list = directory_utils.get_matching_files(cur_dir, cur_pattern)
            try:
                cur_filename = files_list[0]
            except IndexError, e:
                raise ValueError('Cannot find matching rainfall file in directory')
        if lta_filename is None:
            # get filename from pattern and diretory
            files_list = directory_utils.get_matching_files(lta_dir, lta_pattern)
            try:
                lta_filename = files_list[0]
            except IndexError, e:
                raise ValueError('Cannot find matching long-term average file.')

        if dst_filename is None:
            # get new filename from directory and pattern
            dst_filename = os.path.join(dst_dir, filename_utils.generate_output_filename(
                os.path.split(cur_filename)[1], cur_pattern, dst_pattern))
        if not os.path.exists(dst_dir):
            os.makedirs(dst_dir)
        precipitation_analysis.calc_rainfall_anomaly(cur_filename=cur_filename,
                                                     lta_filename=lta_filename,
                                                     dst_filename=dst_filename)
        self.vampire.logger.info('leaving calc_rainfall_anomaly')
        return None

    def calc_vci(self, cur_filename=None, cur_dir=None, cur_pattern=None,
                 evi_max_filename=None, evi_max_dir=None, evi_max_pattern=None,
                 evi_min_filename=None, evi_min_dir=None, evi_min_pattern=None,
                 dst_filename=None, dst_dir=None, dst_pattern=None):
        self.vampire.logger.info('entering calc_vci')
        if cur_filename is None:
            # get filename from pattern and directory
            files_list = directory_utils.get_matching_files(cur_dir, cur_pattern)
            try:
                _cur_filename = files_list[0]
            except IndexError, e:
                raise ValueError('Cannot find matching vegetation file in directory')
        else:
            _cur_filename = cur_filename

        _evi_max_filename = evi_max_filename
        if _evi_max_filename is None:
            # get filename from pattern and directory
            files_list = directory_utils.get_matching_files(evi_max_dir, evi_max_pattern)
            try:
                _evi_max_filename = files_list[0]
            except IndexError, e:
                raise ValueError('Cannot find matching EVI long-term maximum file in directory')

        _evi_min_filename = evi_min_filename
        if _evi_min_filename is None:
            # get filename from pattern and directory
            files_list = directory_utils.get_matching_files(evi_min_dir, evi_min_pattern)
            try:
                _evi_min_filename = files_list[0]
            except IndexError, e:
                raise ValueError('Cannot find matching EVI long-term minimum file in directory')

        if dst_filename is None:
            # get new filename from directory and pattern
            _dst_filename = os.path.join(dst_dir, filename_utils.generate_output_filename(
                os.path.split(_cur_filename)[1], cur_pattern, dst_pattern))
        else:
            _dst_filename = dst_filename

        vegetation_analysis.calc_VCI(_cur_filename, _evi_max_filename, _evi_min_filename, _dst_filename)
        self.vampire.logger.info('leaving calc_vci')
        return None

    def calc_tci(self, cur_filename=None, cur_dir=None, cur_pattern=None,
                 lst_max_filename=None, lst_max_dir=None, lst_max_pattern=None,
                 lst_min_filename=None, lst_min_dir=None, lst_min_pattern=None,
                 dst_filename=None, dst_dir=None, dst_pattern=None):
        self.vampire.logger.info('entering calc_tci')
        _temp_file = None
        if dst_dir is None:
            _dst_dir = self.vampire.get('MODIS_VCI', 'vci_product_dir')
        else:
            _dst_dir = dst_dir
        if cur_filename is None:
            # get filename from pattern and directory
            files_list = directory_utils.get_matching_files(cur_dir, cur_pattern)
            try:
                if files_list and len(files_list) > 1:
                    # more than one match - average files
                    print 'Found more than one matching temperature file in directory - averaging '
                    print files_list
                    _temp_file = '{0}'.format(os.path.join(_dst_dir,
                                                           os.path.basename(files_list[len(files_list)-1])))
                    calculate_statistics.calc_average(files_list, _temp_file)
                    _cur_filename = _temp_file
                else:
                    _cur_filename = files_list[0]
            except IndexError, e:
                raise ValueError('Cannot find matching temperature file in directory')
        else:
            if not isinstance(cur_filename, basestring) and isinstance(cur_filename, list):
                # cur_filename is a list - need to average
                print 'More than one current file provided - averaging '
                print cur_filename
                _temp_file = '{0}'.format(os.path.join(_dst_dir, os.path.basename(cur_filename[len(cur_filename)-1])))
                calculate_statistics.calc_average(cur_filename, _temp_file)
                _cur_filename = _temp_file
            else:
                _cur_filename = cur_filename

        _lst_max_filename = lst_max_filename
        if _lst_max_filename is None:
            # get filename from pattern and directory
            files_list = directory_utils.get_matching_files(lst_max_dir, lst_max_pattern)
            try:
                _lst_max_filename = files_list[0]
            except IndexError, e:
                raise ValueError('Cannot find matching LST long-term maximum file in directory')

        _lst_min_filename = lst_min_filename
        if _lst_min_filename is None:
            # get filename from pattern and directory
            files_list = directory_utils.get_matching_files(lst_min_dir, lst_min_pattern)
            try:
                _lst_min_filename = files_list[0]
            except IndexError, e:
                raise ValueError('Cannot find matching LST long-term minimum file in directory')

        if dst_filename is None:
            # get new filename from directory and pattern
            if cur_pattern is None:
                _cur_pattern = self.vampire.get('MODIS_LST', 'lst_regional_pattern')
            else:
                _cur_pattern = cur_pattern
            _dst_filename = os.path.join(dst_dir, filename_utils.generate_output_filename(
                os.path.split(_cur_filename)[1], _cur_pattern, dst_pattern))
        else:
            _dst_filename = dst_filename
        if not os.path.isdir(dst_dir):
            # make directory if not existing
            os.makedirs(dst_dir)

        temperature_analysis.calc_TCI(cur_filename=_cur_filename,
                                      lta_max_filename=_lst_max_filename,
                                      lta_min_filename=_lst_min_filename,
                                      dst_filename=_dst_filename
                                      )
        if _temp_file is not None:
            os.remove(os.path.join(_dst_dir, _temp_file))
        self.vampire.logger.info('leaving calc_tci')
        return None

    def calc_vhi(self, vci_filename=None, vci_dir=None, vci_pattern=None,
                 tci_filename=None, tci_dir=None, tci_pattern=None,
                 dst_filename=None, dst_dir=None, dst_pattern=None):
        self.vampire.logger.info('entering calc_vhi')
        if vci_filename is None:
            # get filename from pattern and directory
            files_list = directory_utils.get_matching_files(vci_dir, vci_pattern)
            try:
                _vci_filename = files_list[0]
            except IndexError, e:
                raise ValueError('Cannot find matching Vegetation Condition Index file in directory')
        else:
            _vci_filename = vci_filename
        if tci_filename is None:
            # get filename from pattern and directory
            files_list = directory_utils.get_matching_files(tci_dir, tci_pattern)
            try:
                _tci_filename = files_list[0]
            except IndexError, e:
                raise ValueError('Cannot find matching Temperature Condition Index file in directory')
        else:
            _tci_filename = tci_filename
        if dst_filename is None:
            # get new filename from directory and pattern
            _dst_filename = os.path.join(dst_dir, filename_utils.generate_output_filename(
                os.path.split(_vci_filename)[1], vci_pattern, dst_pattern))
        else:
            _dst_filename = dst_filename
        if not os.path.isdir(dst_dir):
            # destination directory does not exist, create it first
            os.makedirs(dst_dir)
        vegetation_analysis.calc_VHI(vci_filename=_vci_filename,
                                     tci_filename=_tci_filename,
                                     dst_filename=_dst_filename
                                     )
        self.vampire.logger.info('leaving calc_vhi')
        return None

    def calc_drought_impact(self, vhi_filename, poverty_filename):
        self.vampire.logger.info('entering calc_drought_impact')

        self.vampire.logger.info('leaving calc_drought_impact')
        return None

    def calc_days_since_last_rainfall(self, data_dir, data_pattern, dst_dir, start_date, threshold, max_days):
        self.vampire.logger.info('entering calc_days_since_last_rainfall')
        # get list of files from start_date back max_days
        files_list = directory_utils.get_matching_files(data_dir, data_pattern)
        raster_list = []
        _r_in = regex.compile(data_pattern)
        for f in files_list:
            _m = _r_in.match(os.path.basename(f))
            max_date = start_date - datetime.timedelta(days=max_days)
            f_date = datetime.date(int(_m.group('year')), int(_m.group('month')), int(_m.group('day')))
            if max_date <= f_date <= start_date:
                raster_list.append(f)

        def replace_closure(subgroup, replacement, m):
            if m.group(subgroup) not in [None, '']:
                start = m.start(subgroup)
                end = m.end(subgroup)
                return m.group()[:start] + replacement + m.group()[end:]

        _ref_file = regex.sub(data_pattern, functools.partial(replace_closure, 'year', '{0}'.format(start_date.year)),
                           os.path.basename(files_list[0]))
        _ref_file = regex.sub(data_pattern, functools.partial(replace_closure, 'month', '{0}'.format(start_date.month)),
                           _ref_file)
        _ref_file = regex.sub(data_pattern, functools.partial(replace_closure, 'day', '{0}'.format(start_date.day)),
                           _ref_file)
        dslw_file = os.path.join(dst_dir,
                                 filename_utils.generate_output_filename(_ref_file, data_pattern,
                                                                         self.vampire.get(
                                                                             'CHIRPS_Days_Since_Last_Rain',
                                                                             'regional_dslr_output_pattern')))
        dsld_file = os.path.join(dst_dir,
                                 filename_utils.generate_output_filename(_ref_file, data_pattern,
                                                                         self.vampire.get(
                                                                             'CHIRPS_Days_Since_Last_Rain',
                                                                             'regional_dsld_output_pattern')))
        num_wet_file = os.path.join(dst_dir,
                                    filename_utils.generate_output_filename(_ref_file, data_pattern,
                                                                            self.vampire.get(
                                                                                'CHIRPS_Days_Since_Last_Rain',
                                                                                'regional_wet_accum_output_pattern')))
        ra_file = os.path.join(dst_dir,
                               filename_utils.generate_output_filename(_ref_file, data_pattern,
                                                                       self.vampire.get(
                                                                            'CHIRPS_Days_Since_Last_Rain',
                                                                           'regional_accum_output_pattern')))
        precipitation_analysis.days_since_last_rain(raster_list=raster_list,
                                                    dslw_filename=dslw_file,
                                                    dsld_filename=dsld_file,
                                                    num_wet_days_filename=num_wet_file,
                                                    rainfall_accum_filename=ra_file,
                                                    temp_dir=self.vampire.get('directories', 'temp_dir'),
                                                    threshold=threshold, max_days=max_days)
        self.vampire.logger.info('leaving calc_days_since_last_rainfall')
        return None